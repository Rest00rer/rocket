from pydantic import BaseModel

from app.schemas.common import ProductOut, WarehouseOut


class InventoryItem(BaseModel):
    product: ProductOut
    warehouse: WarehouseOut
    on_hand: int
    reserved_fbs: int
    available: int


class InTransitTotals(BaseModel):
    between_warehouses: int
    fbo: int
    fbs_to_customer: int


class TransitItem(BaseModel):
    kind: str
    product: ProductOut
    quantity: int
    source: WarehouseOut | None = None
    destination: WarehouseOut | None = None
    status: str


class InventorySummary(BaseModel):
    items: list[InventoryItem]
    in_transit: InTransitTotals
    transit_items: list[TransitItem]
