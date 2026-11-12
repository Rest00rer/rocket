from typing import Annotated

from fastapi import Header

IdempotencyKey = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=8,
        max_length=255,
        description="Уникальный ключ команды для защиты от повторного списания",
    ),
]
