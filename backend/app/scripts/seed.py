import asyncio

from sqlalchemy import select

from app.core.database import session_factory
from app.models.inventory import InventoryBalance
from app.models.product import Product
from app.models.warehouse import Warehouse

PRODUCTS = [
    ("SKU-101", "Органайзер"),
    ("SKU-102", "Контейнер"),
    ("SKU-103", "Корзина"),
]
INITIAL_BALANCES = {
    "SKU-101": {"Север": 10, "Юг": 6},
    "SKU-102": {"Север": 5, "Юг": 0},
    "SKU-103": {"Север": 0, "Юг": 4},
}


async def seed() -> None:
    async with session_factory() as session, session.begin():
        products: dict[str, Product] = {}
        for sku, name in PRODUCTS:
            product = await session.scalar(select(Product).where(Product.sku == sku))
            if product is None:
                product = Product(sku=sku, name=name)
                session.add(product)
                await session.flush()
            products[sku] = product

        warehouses: dict[str, Warehouse] = {}
        for name in ("Север", "Юг"):
            warehouse = await session.scalar(
                select(Warehouse).where(Warehouse.name == name, Warehouse.archived_at.is_(None))
            )
            if warehouse is None:
                warehouse = Warehouse(name=name)
                session.add(warehouse)
                await session.flush()
            warehouses[name] = warehouse

        for sku, values in INITIAL_BALANCES.items():
            for warehouse_name, on_hand in values.items():
                existing = await session.scalar(
                    select(InventoryBalance).where(
                        InventoryBalance.product_id == products[sku].id,
                        InventoryBalance.warehouse_id == warehouses[warehouse_name].id,
                    )
                )
                if existing is None:
                    session.add(
                        InventoryBalance(
                            product_id=products[sku].id,
                            warehouse_id=warehouses[warehouse_name].id,
                            on_hand=on_hand,
                        )
                    )


if __name__ == "__main__":
    asyncio.run(seed())
