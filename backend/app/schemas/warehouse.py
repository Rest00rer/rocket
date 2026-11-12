from pydantic import BaseModel, Field


class WarehouseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class WarehouseUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
