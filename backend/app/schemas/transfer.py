import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TransferCreate(BaseModel):
    product_id: uuid.UUID
    source_warehouse_id: uuid.UUID
    destination_warehouse_id: uuid.UUID
    quantity: int = Field(gt=0)


class TransferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    source_warehouse_id: uuid.UUID
    destination_warehouse_id: uuid.UUID
    quantity: int
    status: str
    created_at: datetime
    dispatched_at: datetime | None
    received_at: datetime | None
