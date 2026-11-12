import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sku: str
    name: str


class WarehouseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    archived_at: datetime | None

    @computed_field
    @property
    def archived(self) -> bool:
        return self.archived_at is not None


class QuantityCommand(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: int = Field(gt=0)


class BalanceOut(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    on_hand: int
    reserved_fbs: int
    available: int


class CommandResult(BaseModel):
    entity_id: uuid.UUID
    status: str
    balance: BalanceOut | None = None
