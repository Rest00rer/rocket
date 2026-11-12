import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import TransferStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Transfer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transfers"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_transfers_quantity_positive"),
        CheckConstraint(
            "source_warehouse_id <> destination_warehouse_id",
            name="ck_transfers_distinct_warehouses",
        ),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    source_warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    destination_warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=TransferStatus.DRAFT.value, index=True, nullable=False
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
