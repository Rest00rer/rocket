import hashlib
import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.models.idempotency import IdempotencyRecord


def request_hash(command: str, payload: dict) -> str:
    canonical = json.dumps(
        {"command": command, "payload": payload}, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


async def replay(
    session: AsyncSession, key: str, command: str, payload: dict
) -> tuple[dict | None, str]:
    digest = request_hash(command, payload)
    record = await session.get(IdempotencyRecord, key)
    if record is None:
        return None, digest
    if record.request_hash != digest or record.command != command:
        raise DomainError(
            "idempotency_conflict",
            "Этот Idempotency-Key уже использован для другого запроса",
        )
    return record.response_body, digest


def remember(
    session: AsyncSession,
    *,
    key: str,
    command: str,
    digest: str,
    response: dict,
    status_code: int = 200,
) -> None:
    session.add(
        IdempotencyRecord(
            key=key,
            command=command,
            request_hash=digest,
            status_code=status_code,
            response_body=response,
        )
    )
