import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class InventoryBalance(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "inventory_balances"
    __table_args__ = (
        UniqueConstraint("product_id", "warehouse_id", name="uq_inventory_product_warehouse"),
        CheckConstraint("on_hand >= 0", name="ck_inventory_on_hand_nonnegative"),
        CheckConstraint("reserved_fbs >= 0", name="ck_inventory_reserved_nonnegative"),
        CheckConstraint("reserved_fbs <= on_hand", name="ck_inventory_reserved_lte_on_hand"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_fbs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
