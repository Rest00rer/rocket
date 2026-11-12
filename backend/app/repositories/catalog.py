import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.models.product import Product
from app.models.warehouse import Warehouse


async def get_product(session: AsyncSession, product_id: uuid.UUID) -> Product:
    product = await session.get(Product, product_id)
    if product is None:
        raise DomainError("product_not_found", "Товар не найден", status_code=404)
    return product


async def get_warehouse(
    session: AsyncSession, warehouse_id: uuid.UUID, *, require_active: bool = False
) -> Warehouse:
    warehouse = await session.get(Warehouse, warehouse_id)
    if warehouse is None:
        raise DomainError("warehouse_not_found", "Склад не найден", status_code=404)
    if require_active and warehouse.archived_at is not None:
        raise DomainError("warehouse_archived", "Склад находится в архиве")
    return warehouse


async def list_products(session: AsyncSession) -> list[Product]:
    return list((await session.scalars(select(Product).order_by(Product.sku))).all())


async def list_warehouses(session: AsyncSession) -> list[Warehouse]:
    query = select(Warehouse).order_by(Warehouse.archived_at.is_not(None), Warehouse.name)
    return list((await session.scalars(query)).all())
