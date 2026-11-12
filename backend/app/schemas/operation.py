import uuid
from datetime import datetime

from pydantic import BaseModel


class OperationOut(BaseModel):
    id: uuid.UUID
    operation_type: str
    product_id: uuid.UUID | None
    sku: str | None
    product_name: str | None
    quantity: int | None
    source_warehouse_id: uuid.UUID | None
    source_warehouse_name: str | None
    destination_warehouse_id: uuid.UUID | None
    destination_warehouse_name: str | None
    entity_type: str | None
    entity_id: uuid.UUID | None
    details: dict
    created_at: datetime


class OperationList(BaseModel):
    items: list[OperationOut]
