import os
import uuid
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.core.database import get_session
from app.main import app
from app.models.base import Base
from app.models.inventory import InventoryBalance
from app.models.product import Product
from app.models.warehouse import Warehouse


@pytest_asyncio.fixture
async def session_factory():
    database_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    admin_engine = None
    schema_name = None
    if database_url and database_url.startswith("postgresql"):
        schema_name = f"test_{uuid.uuid4().hex}"
        admin_engine = create_async_engine(database_url)
        async with admin_engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
        engine = create_async_engine(
            database_url,
            connect_args={"server_settings": {"search_path": schema_name}},
        )
    else:
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session, session.begin():
        products = [
            Product(sku="SKU-101", name="Органайзер"),
            Product(sku="SKU-102", name="Контейнер"),
            Product(sku="SKU-103", name="Корзина"),
        ]
        north = Warehouse(name="Север")
        south = Warehouse(name="Юг")
        session.add_all([*products, north, south])
        await session.flush()
        values = ((10, 6), (5, 0), (0, 4))
        session.add_all(
            InventoryBalance(product_id=product.id, warehouse_id=warehouse.id, on_hand=quantity)
            for product, quantities in zip(products, values, strict=True)
            for warehouse, quantity in zip((north, south), quantities, strict=True)
        )

    yield factory
    await engine.dispose()
    if admin_engine is not None and schema_name is not None:
        async with admin_engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema_name}" CASCADE'))
        await admin_engine.dispose()


@pytest_asyncio.fixture
async def client(session_factory) -> AsyncIterator[AsyncClient]:
    async def override_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def catalog(client: AsyncClient) -> dict:
    products = (await client.get("/api/products")).json()
    warehouses = (await client.get("/api/warehouses")).json()
    return {
        "products": {item["sku"]: item for item in products},
        "warehouses": {item["name"]: item for item in warehouses},
    }
