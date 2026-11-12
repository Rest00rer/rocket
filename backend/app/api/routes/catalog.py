from fastapi import APIRouter

from app.core.database import SessionDependency
from app.repositories.catalog import list_products, list_warehouses
from app.schemas.common import ProductOut, WarehouseOut

router = APIRouter()


@router.get("/products", response_model=list[ProductOut])
async def products(session: SessionDependency):
    return await list_products(session)


@router.get("/warehouses", response_model=list[WarehouseOut])
async def warehouses(session: SessionDependency):
    return await list_warehouses(session)
