import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.core.database import SessionDependency
from app.schemas.operation import OperationList
from app.services.queries import list_operations

router = APIRouter()


@router.get("", response_model=OperationList)
async def operations(
    session: SessionDependency,
    sku: str | None = None,
    warehouse_id: uuid.UUID | None = None,
    operation_type: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    return {
        "items": await list_operations(
            session,
            sku=sku,
            warehouse_id=warehouse_id,
            operation_types=operation_type,
            limit=limit,
        )
    }
