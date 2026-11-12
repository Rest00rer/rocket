import uuid

from sqlalchemy import select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.models.inventory import InventoryBalance
from app.models.product import Product
from app.models.warehouse import Warehouse


async def get_balance_for_update(
    session: AsyncSession, product_id: uuid.UUID, warehouse_id: uuid.UUID
) -> InventoryBalance:
    balance = await session.scalar(
        select(InventoryBalance)
        .where(
            InventoryBalance.product_id == product_id,
            InventoryBalance.warehouse_id == warehouse_id,
        )
        .with_for_update()
    )
    if balance is None:
        balance = InventoryBalance(product_id=product_id, warehouse_id=warehouse_id)
        session.add(balance)
        await session.flush()
    return balance


async def ensure_available(
    session: AsyncSession, balance: InventoryBalance, quantity: int, warehouse: Warehouse
) -> None:
    available = balance.on_hand - balance.reserved_fbs
    if available >= quantity:
        return
    rows = (
        await session.execute(
            select(InventoryBalance, Warehouse)
            .join(Warehouse, Warehouse.id == InventoryBalance.warehouse_id)
            .where(
                InventoryBalance.product_id == balance.product_id,
                Warehouse.archived_at.is_(None),
            )
        )
    ).all()
    alternatives = [
        {
            "warehouse_id": str(other_warehouse.id),
            "name": other_warehouse.name,
            "available": other_balance.on_hand - other_balance.reserved_fbs,
        }
        for other_balance, other_warehouse in rows
        if other_warehouse.id != warehouse.id
        and other_balance.on_hand - other_balance.reserved_fbs > 0
    ]
    total = sum(other.on_hand - other.reserved_fbs for other, _ in rows)
    raise DomainError(
        "insufficient_stock",
        f"На складе {warehouse.name} доступно {available} из {quantity} единиц",
        details={
            "requested": quantity,
            "available_here": available,
            "available_total": total,
            "alternatives": alternatives,
        },
    )


async def inventory_rows(session: AsyncSession):
    query = (
        select(Product, Warehouse, InventoryBalance)
        .select_from(Product)
        .join(Warehouse, true())
        .outerjoin(
            InventoryBalance,
            (InventoryBalance.product_id == Product.id)
            & (InventoryBalance.warehouse_id == Warehouse.id),
        )
        .order_by(Product.sku, Warehouse.archived_at.is_not(None), Warehouse.name)
    )
    return (await session.execute(query)).all()
