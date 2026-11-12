from fastapi import APIRouter

from app.core.database import SessionDependency
from app.schemas.inventory import InventorySummary
from app.services.queries import get_inventory_summary

router = APIRouter()


@router.get("", response_model=InventorySummary)
async def inventory(session: SessionDependency):
    return await get_inventory_summary(session)
