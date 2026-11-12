import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.domain.enums import OperationType
from app.models.warehouse import Warehouse
from app.repositories.catalog import get_warehouse
from app.services.operations import log_operation


async def create_warehouse(session: AsyncSession, name: str) -> Warehouse:
    normalized = name.strip()
    if not normalized:
        raise DomainError(
            "invalid_warehouse_name", "Название склада не может быть пустым", status_code=422
        )
    try:
        async with session.begin():
            existing = await session.scalar(
                select(Warehouse).where(
                    Warehouse.name == normalized, Warehouse.archived_at.is_(None)
                )
            )
            if existing:
                raise DomainError(
                    "warehouse_name_exists", "Активный склад с таким названием уже существует"
                )
            warehouse = Warehouse(name=normalized)
            session.add(warehouse)
            await session.flush()
            log_operation(
                session,
                OperationType.WAREHOUSE_CREATED,
                destination_warehouse_id=warehouse.id,
                entity_type="warehouse",
                entity_id=warehouse.id,
                details={"name": warehouse.name},
            )
        return warehouse
    except IntegrityError as error:
        raise DomainError(
            "warehouse_name_exists", "Активный склад с таким названием уже существует"
        ) from error


async def rename_warehouse(session: AsyncSession, warehouse_id: uuid.UUID, name: str) -> Warehouse:
    normalized = name.strip()
    if not normalized:
        raise DomainError(
            "invalid_warehouse_name", "Название склада не может быть пустым", status_code=422
        )
    try:
        async with session.begin():
            warehouse = await get_warehouse(session, warehouse_id, require_active=True)
            previous_name = warehouse.name
            warehouse.name = normalized
            await session.flush()
            log_operation(
                session,
                OperationType.WAREHOUSE_RENAMED,
                destination_warehouse_id=warehouse.id,
                entity_type="warehouse",
                entity_id=warehouse.id,
                details={"previous_name": previous_name, "name": normalized},
            )
        return warehouse
    except IntegrityError as error:
        raise DomainError(
            "warehouse_name_exists", "Активный склад с таким названием уже существует"
        ) from error


async def archive_warehouse(session: AsyncSession, warehouse_id: uuid.UUID) -> Warehouse:
    async with session.begin():
        warehouse = await get_warehouse(session, warehouse_id)
        if warehouse.archived_at is None:
            warehouse.archived_at = datetime.now(UTC)
            log_operation(
                session,
                OperationType.WAREHOUSE_ARCHIVED,
                source_warehouse_id=warehouse.id,
                entity_type="warehouse",
                entity_id=warehouse.id,
                details={"name": warehouse.name},
            )
    return warehouse
