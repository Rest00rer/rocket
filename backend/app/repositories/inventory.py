import uuid

from sqlalchemy import select, true
from sqlalchemy.ext.asyncio import AsyncSession

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


async def balances_for_product(session: AsyncSession, product_id: uuid.UUID):
    return (
        await session.execute(
            select(InventoryBalance, Warehouse)
            .join(Warehouse, Warehouse.id == InventoryBalance.warehouse_id)
            .where(
                InventoryBalance.product_id == product_id,
                Warehouse.archived_at.is_(None),
            )
        )
    ).all()


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
