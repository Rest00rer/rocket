import uuid

from fastapi import APIRouter, status

from app.core.database import SessionDependency
from app.schemas.common import WarehouseOut
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate
from app.services.warehouses import archive_warehouse, create_warehouse, rename_warehouse

router = APIRouter()


@router.post("", response_model=WarehouseOut, status_code=status.HTTP_201_CREATED)
async def create(payload: WarehouseCreate, session: SessionDependency):
    return await create_warehouse(session, payload.name)


@router.patch("/{warehouse_id}", response_model=WarehouseOut)
async def rename(warehouse_id: uuid.UUID, payload: WarehouseUpdate, session: SessionDependency):
    return await rename_warehouse(session, warehouse_id, payload.name)


@router.delete("/{warehouse_id}", response_model=WarehouseOut)
async def archive(warehouse_id: uuid.UUID, session: SessionDependency):
    return await archive_warehouse(session, warehouse_id)
