from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.models.inventory import InventoryBalance
from app.models.warehouse import Warehouse
from app.repositories.inventory import balances_for_product


async def ensure_available(
    session: AsyncSession, balance: InventoryBalance, quantity: int, warehouse: Warehouse
) -> None:
    available = balance.on_hand - balance.reserved_fbs
    if available >= quantity:
        return

    rows = await balances_for_product(session, balance.product_id)
    alternatives = [
        {
            "warehouse_id": str(other_warehouse.id),
            "name": other_warehouse.name,
            "available": other_balance.on_hand - other_balance.reserved_fbs,
        }
        for other_balance, other_warehouse in rows
        if other_warehouse.id != warehouse.id
        and other_balance.on_hand - other_balance.reserved_fbs > 0
    ]
    total = sum(other.on_hand - other.reserved_fbs for other, _ in rows)
    raise DomainError(
        "insufficient_stock",
        f"На складе {warehouse.name} доступно {available} из {quantity} единиц",
        details={
            "requested": quantity,
            "available_here": available,
            "available_total": total,
            "alternatives": alternatives,
        },
    )
