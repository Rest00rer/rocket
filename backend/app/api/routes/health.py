from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import SessionDependency
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness(session: SessionDependency) -> HealthResponse:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "database_unavailable", "message": "PostgreSQL is unavailable"},
        ) from error
    return await health()
