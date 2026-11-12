from fastapi import APIRouter

from app.api.routes.catalog import router as catalog_router
from app.api.routes.commands import router as commands_router
from app.api.routes.health import router as health_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.operations import router as operations_router
from app.api.routes.warehouses import router as warehouses_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(catalog_router, tags=["catalog"])
api_router.include_router(warehouses_router, prefix="/warehouses", tags=["warehouses"])
api_router.include_router(inventory_router, prefix="/inventory", tags=["inventory"])
api_router.include_router(commands_router, tags=["commands"])
api_router.include_router(operations_router, prefix="/operations", tags=["operations"])
