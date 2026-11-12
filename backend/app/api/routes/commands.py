import uuid

from fastapi import APIRouter, status

from app.api.dependencies import IdempotencyKey
from app.core.database import SessionDependency
from app.schemas.common import CommandResult, QuantityCommand
from app.schemas.shipment import FboShipmentOut, FbsReservationOut
from app.schemas.transfer import TransferCreate, TransferOut
from app.services.commands import (
    create_transfer,
    dispatch_fbo,
    dispatch_transfer,
    receive_fbo,
    receive_stock,
    receive_transfer,
    reserve_fbs,
    transition_fbs,
)
from app.services.queries import list_fbo, list_fbs, list_transfers

router = APIRouter()


@router.post("/receipts", response_model=CommandResult, status_code=status.HTTP_201_CREATED)
async def receipt(payload: QuantityCommand, session: SessionDependency, key: IdempotencyKey):
    return await receive_stock(session, payload, key)


@router.get("/transfers", response_model=list[TransferOut])
async def transfers(session: SessionDependency):
    return await list_transfers(session)


@router.post("/transfers", response_model=TransferOut, status_code=status.HTTP_201_CREATED)
async def transfer_create(payload: TransferCreate, session: SessionDependency):
    return await create_transfer(session, payload)


@router.post("/transfers/{transfer_id}/dispatch", response_model=CommandResult)
async def transfer_dispatch(
    transfer_id: uuid.UUID, session: SessionDependency, key: IdempotencyKey
):
    return await dispatch_transfer(session, transfer_id, key)


@router.post("/transfers/{transfer_id}/receive", response_model=CommandResult)
async def transfer_receive(transfer_id: uuid.UUID, session: SessionDependency, key: IdempotencyKey):
    return await receive_transfer(session, transfer_id, key)


@router.get("/fbs/reservations", response_model=list[FbsReservationOut])
async def fbs_reservations(session: SessionDependency):
    return await list_fbs(session)


@router.post("/fbs/reservations", response_model=CommandResult, status_code=status.HTTP_201_CREATED)
async def fbs_reserve(payload: QuantityCommand, session: SessionDependency, key: IdempotencyKey):
    return await reserve_fbs(session, payload, key)


@router.post("/fbs/reservations/{reservation_id}/cancel", response_model=CommandResult)
async def fbs_cancel(reservation_id: uuid.UUID, session: SessionDependency, key: IdempotencyKey):
    return await transition_fbs(session, reservation_id, key, action="cancel")


@router.post("/fbs/reservations/{reservation_id}/ship", response_model=CommandResult)
async def fbs_ship(reservation_id: uuid.UUID, session: SessionDependency, key: IdempotencyKey):
    return await transition_fbs(session, reservation_id, key, action="ship")


@router.get("/fbo/shipments", response_model=list[FboShipmentOut])
async def fbo_shipments(session: SessionDependency):
    return await list_fbo(session)


@router.post("/fbo/shipments", response_model=CommandResult, status_code=status.HTTP_201_CREATED)
async def fbo_dispatch(payload: QuantityCommand, session: SessionDependency, key: IdempotencyKey):
    return await dispatch_fbo(session, payload, key)


@router.post("/fbo/shipments/{shipment_id}/receive", response_model=CommandResult)
async def fbo_receive(shipment_id: uuid.UUID, session: SessionDependency, key: IdempotencyKey):
    return await receive_fbo(session, shipment_id, key)
