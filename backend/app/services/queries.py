import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.domain.enums import FboShipmentStatus, FbsReservationStatus, TransferStatus
from app.models.fbo import FboShipment
from app.models.fbs import FbsReservation
from app.models.operation import Operation
from app.models.product import Product
from app.models.transfer import Transfer
from app.models.warehouse import Warehouse
from app.repositories.inventory import inventory_rows


async def get_inventory_summary(session: AsyncSession) -> dict:
    rows = await inventory_rows(session)
    items = [
        {
            "product": product,
            "warehouse": warehouse,
            "on_hand": balance.on_hand if balance else 0,
            "reserved_fbs": balance.reserved_fbs if balance else 0,
            "available": (balance.on_hand - balance.reserved_fbs) if balance else 0,
        }
        for product, warehouse, balance in rows
    ]

    source = aliased(Warehouse)
    destination = aliased(Warehouse)
    transfer_rows = (
        await session.execute(
            select(Transfer, Product, source, destination)
            .join(Product, Product.id == Transfer.product_id)
            .join(source, source.id == Transfer.source_warehouse_id)
            .join(destination, destination.id == Transfer.destination_warehouse_id)
            .where(Transfer.status == TransferStatus.IN_TRANSIT)
        )
    ).all()
    transfer_items = [
        {
            "kind": "between_warehouses",
            "product": product,
            "quantity": transfer.quantity,
            "source": source_warehouse,
            "destination": destination_warehouse,
            "status": transfer.status,
        }
        for transfer, product, source_warehouse, destination_warehouse in transfer_rows
    ]

    fbo_rows = (
        await session.execute(
            select(FboShipment, Product, Warehouse)
            .join(Product, Product.id == FboShipment.product_id)
            .join(Warehouse, Warehouse.id == FboShipment.warehouse_id)
            .where(FboShipment.status == FboShipmentStatus.IN_TRANSIT)
        )
    ).all()
    fbo_items = [
        {
            "kind": "fbo",
            "product": product,
            "quantity": shipment.quantity,
            "source": warehouse,
            "destination": None,
            "status": shipment.status,
        }
        for shipment, product, warehouse in fbo_rows
    ]

    fbs_rows = (
        await session.execute(
            select(FbsReservation, Product, Warehouse)
            .join(Product, Product.id == FbsReservation.product_id)
            .join(Warehouse, Warehouse.id == FbsReservation.warehouse_id)
            .where(FbsReservation.status == FbsReservationStatus.SHIPPED)
        )
    ).all()
    fbs_items = [
        {
            "kind": "fbs_to_customer",
            "product": product,
            "quantity": reservation.quantity,
            "source": warehouse,
            "destination": None,
            "status": reservation.status,
        }
        for reservation, product, warehouse in fbs_rows
    ]
    transit_items = transfer_items + fbo_items + fbs_items
    return {
        "items": items,
        "in_transit": {
            "between_warehouses": sum(item["quantity"] for item in transfer_items),
            "fbo": sum(item["quantity"] for item in fbo_items),
            "fbs_to_customer": sum(item["quantity"] for item in fbs_items),
        },
        "transit_items": transit_items,
    }


async def list_operations(
    session: AsyncSession,
    *,
    sku: str | None = None,
    warehouse_id: uuid.UUID | None = None,
    operation_types: list[str] | None = None,
    limit: int = 100,
) -> list[dict]:
    source = Warehouse.__table__.alias("source_warehouse")
    destination = Warehouse.__table__.alias("destination_warehouse")
    query = (
        select(
            Operation,
            Product.sku,
            Product.name,
            source.c.name.label("source_name"),
            destination.c.name.label("destination_name"),
        )
        .outerjoin(Product, Product.id == Operation.product_id)
        .outerjoin(source, source.c.id == Operation.source_warehouse_id)
        .outerjoin(destination, destination.c.id == Operation.destination_warehouse_id)
        .order_by(Operation.created_at.desc())
        .limit(limit)
    )
    if sku:
        query = query.where(Product.sku == sku)
    if warehouse_id:
        query = query.where(
            or_(
                Operation.source_warehouse_id == warehouse_id,
                Operation.destination_warehouse_id == warehouse_id,
            )
        )
    if operation_types:
        query = query.where(Operation.operation_type.in_(operation_types))
    rows = (await session.execute(query)).all()
    return [
        {
            "id": operation.id,
            "operation_type": operation.operation_type,
            "product_id": operation.product_id,
            "sku": product_sku,
            "product_name": product_name,
            "quantity": operation.quantity,
            "source_warehouse_id": operation.source_warehouse_id,
            "source_warehouse_name": source_name,
            "destination_warehouse_id": operation.destination_warehouse_id,
            "destination_warehouse_name": destination_name,
            "entity_type": operation.entity_type,
            "entity_id": operation.entity_id,
            "details": operation.details,
            "created_at": operation.created_at,
        }
        for operation, product_sku, product_name, source_name, destination_name in rows
    ]


async def list_transfers(session: AsyncSession) -> list[Transfer]:
    query = select(Transfer).order_by(Transfer.created_at.desc())
    return list((await session.scalars(query)).all())


async def list_fbs(session: AsyncSession) -> list[FbsReservation]:
    query = select(FbsReservation).order_by(FbsReservation.created_at.desc())
    return list((await session.scalars(query)).all())


async def list_fbo(session: AsyncSession) -> list[FboShipment]:
    query = select(FboShipment).order_by(FboShipment.created_at.desc())
    return list((await session.scalars(query)).all())
