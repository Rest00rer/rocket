import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operation import Operation


def log_operation(
    session: AsyncSession,
    operation_type: str,
    *,
    product_id: uuid.UUID | None = None,
    quantity: int | None = None,
    source_warehouse_id: uuid.UUID | None = None,
    destination_warehouse_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    details: dict | None = None,
) -> Operation:
    operation = Operation(
        operation_type=operation_type,
        product_id=product_id,
        quantity=quantity,
        source_warehouse_id=source_warehouse_id,
        destination_warehouse_id=destination_warehouse_id,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
    )
    session.add(operation)
    return operation
