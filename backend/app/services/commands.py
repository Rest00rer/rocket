import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.domain.enums import (
    FboShipmentStatus,
    FbsReservationStatus,
    OperationType,
    TransferStatus,
)
from app.models.fbo import FboShipment
from app.models.fbs import FbsReservation
from app.models.transfer import Transfer
from app.repositories.catalog import get_product, get_warehouse
from app.repositories.inventory import ensure_available, get_balance_for_update
from app.schemas.common import QuantityCommand
from app.schemas.transfer import TransferCreate
from app.services.idempotency import remember, replay
from app.services.operations import log_operation


def balance_result(entity_id: uuid.UUID, status: str, balance) -> dict:
    return {
        "entity_id": str(entity_id),
        "status": status,
        "balance": {
            "product_id": str(balance.product_id),
            "warehouse_id": str(balance.warehouse_id),
            "on_hand": balance.on_hand,
            "reserved_fbs": balance.reserved_fbs,
            "available": balance.on_hand - balance.reserved_fbs,
        },
    }


async def receive_stock(session: AsyncSession, command: QuantityCommand, key: str) -> dict:
    payload = command.model_dump(mode="json")
    async with session.begin():
        previous, digest = await replay(session, key, "receipt", payload)
        if previous:
            return previous
        await get_product(session, command.product_id)
        await get_warehouse(session, command.warehouse_id, require_active=True)
        balance = await get_balance_for_update(session, command.product_id, command.warehouse_id)
        balance.on_hand += command.quantity
        balance.version += 1
        operation = log_operation(
            session,
            OperationType.RECEIPT,
            product_id=command.product_id,
            quantity=command.quantity,
            destination_warehouse_id=command.warehouse_id,
            entity_type="receipt",
        )
        await session.flush()
        operation.entity_id = operation.id
        response = balance_result(operation.id, "received", balance)
        remember(
            session,
            key=key,
            command="receipt",
            digest=digest,
            response=response,
            status_code=201,
        )
    return response


async def create_transfer(session: AsyncSession, command: TransferCreate) -> Transfer:
    if command.source_warehouse_id == command.destination_warehouse_id:
        raise DomainError(
            "same_warehouse",
            "Склады отправления и назначения должны отличаться",
            status_code=422,
        )
    async with session.begin():
        await get_product(session, command.product_id)
        await get_warehouse(session, command.source_warehouse_id)
        await get_warehouse(session, command.destination_warehouse_id, require_active=True)
        transfer = Transfer(**command.model_dump())
        session.add(transfer)
        await session.flush()
        log_operation(
            session,
            OperationType.TRANSFER_CREATED,
            product_id=command.product_id,
            quantity=command.quantity,
            source_warehouse_id=command.source_warehouse_id,
            destination_warehouse_id=command.destination_warehouse_id,
            entity_type="transfer",
            entity_id=transfer.id,
        )
    return transfer


async def dispatch_transfer(session: AsyncSession, transfer_id: uuid.UUID, key: str) -> dict:
    payload = {"transfer_id": str(transfer_id)}
    async with session.begin():
        previous, digest = await replay(session, key, "transfer_dispatch", payload)
        if previous:
            return previous
        transfer = await session.scalar(
            select(Transfer).where(Transfer.id == transfer_id).with_for_update()
        )
        if transfer is None:
            raise DomainError("transfer_not_found", "Перемещение не найдено", status_code=404)
        if transfer.status != TransferStatus.DRAFT:
            raise DomainError("invalid_transfer_state", "Перемещение уже отправлено или принято")
        source = await get_warehouse(session, transfer.source_warehouse_id)
        await get_warehouse(session, transfer.destination_warehouse_id, require_active=True)
        balance = await get_balance_for_update(
            session, transfer.product_id, transfer.source_warehouse_id
        )
        await ensure_available(session, balance, transfer.quantity, source)
        balance.on_hand -= transfer.quantity
        balance.version += 1
        transfer.status = TransferStatus.IN_TRANSIT
        transfer.dispatched_at = datetime.now(UTC)
        log_operation(
            session,
            OperationType.TRANSFER_DISPATCHED,
            product_id=transfer.product_id,
            quantity=transfer.quantity,
            source_warehouse_id=transfer.source_warehouse_id,
            destination_warehouse_id=transfer.destination_warehouse_id,
            entity_type="transfer",
            entity_id=transfer.id,
        )
        response = balance_result(transfer.id, transfer.status, balance)
        remember(
            session,
            key=key,
            command="transfer_dispatch",
            digest=digest,
            response=response,
        )
    return response


async def receive_transfer(session: AsyncSession, transfer_id: uuid.UUID, key: str) -> dict:
    payload = {"transfer_id": str(transfer_id)}
    async with session.begin():
        previous, digest = await replay(session, key, "transfer_receive", payload)
        if previous:
            return previous
        transfer = await session.scalar(
            select(Transfer).where(Transfer.id == transfer_id).with_for_update()
        )
        if transfer is None:
            raise DomainError("transfer_not_found", "Перемещение не найдено", status_code=404)
        if transfer.status != TransferStatus.IN_TRANSIT:
            raise DomainError(
                "invalid_transfer_state", "Принять можно только отправленное перемещение"
            )
        await get_warehouse(session, transfer.destination_warehouse_id, require_active=True)
        balance = await get_balance_for_update(
            session, transfer.product_id, transfer.destination_warehouse_id
        )
        balance.on_hand += transfer.quantity
        balance.version += 1
        transfer.status = TransferStatus.RECEIVED
        transfer.received_at = datetime.now(UTC)
        log_operation(
            session,
            OperationType.TRANSFER_RECEIVED,
            product_id=transfer.product_id,
            quantity=transfer.quantity,
            source_warehouse_id=transfer.source_warehouse_id,
            destination_warehouse_id=transfer.destination_warehouse_id,
            entity_type="transfer",
            entity_id=transfer.id,
        )
        response = balance_result(transfer.id, transfer.status, balance)
        remember(
            session,
            key=key,
            command="transfer_receive",
            digest=digest,
            response=response,
        )
    return response


async def reserve_fbs(session: AsyncSession, command: QuantityCommand, key: str) -> dict:
    payload = command.model_dump(mode="json")
    async with session.begin():
        previous, digest = await replay(session, key, "fbs_reserve", payload)
        if previous:
            return previous
        await get_product(session, command.product_id)
        warehouse = await get_warehouse(session, command.warehouse_id, require_active=True)
        balance = await get_balance_for_update(session, command.product_id, command.warehouse_id)
        await ensure_available(session, balance, command.quantity, warehouse)
        balance.reserved_fbs += command.quantity
        balance.version += 1
        reservation = FbsReservation(**command.model_dump())
        session.add(reservation)
        await session.flush()
        log_operation(
            session,
            OperationType.FBS_RESERVED,
            product_id=command.product_id,
            quantity=command.quantity,
            source_warehouse_id=command.warehouse_id,
            entity_type="fbs_reservation",
            entity_id=reservation.id,
        )
        response = balance_result(reservation.id, reservation.status, balance)
        remember(
            session,
            key=key,
            command="fbs_reserve",
            digest=digest,
            response=response,
            status_code=201,
        )
    return response


async def transition_fbs(
    session: AsyncSession, reservation_id: uuid.UUID, key: str, *, action: str
) -> dict:
    payload = {"reservation_id": str(reservation_id)}
    command_name = f"fbs_{action}"
    async with session.begin():
        previous, digest = await replay(session, key, command_name, payload)
        if previous:
            return previous
        reservation = await session.scalar(
            select(FbsReservation).where(FbsReservation.id == reservation_id).with_for_update()
        )
        if reservation is None:
            raise DomainError("fbs_reservation_not_found", "Резерв FBS не найден", status_code=404)
        if reservation.status != FbsReservationStatus.RESERVED:
            raise DomainError("invalid_fbs_state", "Резерв уже отменён или отправлен")
        balance = await get_balance_for_update(
            session, reservation.product_id, reservation.warehouse_id
        )
        if action == "cancel":
            balance.reserved_fbs -= reservation.quantity
            reservation.status = FbsReservationStatus.CANCELLED
            reservation.cancelled_at = datetime.now(UTC)
            operation_type = OperationType.FBS_CANCELLED
        elif action == "ship":
            balance.reserved_fbs -= reservation.quantity
            balance.on_hand -= reservation.quantity
            reservation.status = FbsReservationStatus.SHIPPED
            reservation.shipped_at = datetime.now(UTC)
            operation_type = OperationType.FBS_SHIPPED
        else:
            raise ValueError(f"Unsupported FBS action: {action}")
        balance.version += 1
        log_operation(
            session,
            operation_type,
            product_id=reservation.product_id,
            quantity=reservation.quantity,
            source_warehouse_id=reservation.warehouse_id,
            entity_type="fbs_reservation",
            entity_id=reservation.id,
        )
        response = balance_result(reservation.id, reservation.status, balance)
        remember(
            session,
            key=key,
            command=command_name,
            digest=digest,
            response=response,
        )
    return response


async def dispatch_fbo(session: AsyncSession, command: QuantityCommand, key: str) -> dict:
    payload = command.model_dump(mode="json")
    async with session.begin():
        previous, digest = await replay(session, key, "fbo_dispatch", payload)
        if previous:
            return previous
        await get_product(session, command.product_id)
        warehouse = await get_warehouse(session, command.warehouse_id, require_active=True)
        balance = await get_balance_for_update(session, command.product_id, command.warehouse_id)
        await ensure_available(session, balance, command.quantity, warehouse)
        balance.on_hand -= command.quantity
        balance.version += 1
        shipment = FboShipment(**command.model_dump())
        session.add(shipment)
        await session.flush()
        log_operation(
            session,
            OperationType.FBO_DISPATCHED,
            product_id=command.product_id,
            quantity=command.quantity,
            source_warehouse_id=command.warehouse_id,
            entity_type="fbo_shipment",
            entity_id=shipment.id,
        )
        response = balance_result(shipment.id, shipment.status, balance)
        remember(
            session,
            key=key,
            command="fbo_dispatch",
            digest=digest,
            response=response,
            status_code=201,
        )
    return response


async def receive_fbo(session: AsyncSession, shipment_id: uuid.UUID, key: str) -> dict:
    payload = {"shipment_id": str(shipment_id)}
    async with session.begin():
        previous, digest = await replay(session, key, "fbo_receive", payload)
        if previous:
            return previous
        shipment = await session.scalar(
            select(FboShipment).where(FboShipment.id == shipment_id).with_for_update()
        )
        if shipment is None:
            raise DomainError("fbo_shipment_not_found", "Отправка FBO не найдена", status_code=404)
        if shipment.status != FboShipmentStatus.IN_TRANSIT:
            raise DomainError("invalid_fbo_state", "Отправка FBO уже принята")
        shipment.status = FboShipmentStatus.RECEIVED
        shipment.received_at = datetime.now(UTC)
        log_operation(
            session,
            OperationType.FBO_RECEIVED,
            product_id=shipment.product_id,
            quantity=shipment.quantity,
            source_warehouse_id=shipment.warehouse_id,
            entity_type="fbo_shipment",
            entity_id=shipment.id,
        )
        response = {"entity_id": str(shipment.id), "status": shipment.status, "balance": None}
        remember(
            session,
            key=key,
            command="fbo_receive",
            digest=digest,
            response=response,
        )
    return response
