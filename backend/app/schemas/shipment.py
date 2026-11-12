import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FbsReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: int
    status: str
    created_at: datetime
    cancelled_at: datetime | None
    shipped_at: datetime | None


class FboShipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: int
    status: str
    created_at: datetime
    received_at: datetime | None
