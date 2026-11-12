import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import FbsReservationStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FbsReservation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "fbs_reservations"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_fbs_quantity_positive"),)

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=FbsReservationStatus.RESERVED.value, index=True, nullable=False
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
