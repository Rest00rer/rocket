import hashlib
import json

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
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
    insert_factory = (
        postgresql_insert if session.get_bind().dialect.name == "postgresql" else sqlite_insert
    )
    await session.execute(
        insert_factory(IdempotencyRecord)
        .values(
            key=key,
            command=command,
            request_hash=digest,
            status_code=0,
            response_body={},
        )
        .on_conflict_do_nothing(index_elements=[IdempotencyRecord.key])
    )
    record = await session.scalar(
        select(IdempotencyRecord).where(IdempotencyRecord.key == key).with_for_update()
    )
    if record is None:
        return None, digest
    if record.status_code == 0:
        return None, digest
    if record.request_hash != digest or record.command != command:
        raise DomainError(
            "idempotency_conflict",
            "Этот Idempotency-Key уже использован для другого запроса",
        )
    return record.response_body, digest


async def remember(
    session: AsyncSession,
    *,
    key: str,
    command: str,
    digest: str,
    response: dict,
    status_code: int = 200,
) -> None:
    record = await session.get(IdempotencyRecord, key)
    if record is None:
        session.add(
            IdempotencyRecord(
                key=key,
                command=command,
                request_hash=digest,
                status_code=status_code,
                response_body=response,
            )
        )
        return
    record.command = command
    record.request_hash = digest
    record.status_code = status_code
    record.response_body = response
