from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import dispose_engine
from app.core.errors import DomainError
from app.core.http import RequestIdMiddleware, domain_error_handler
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await dispose_engine()


settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)
app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(DomainError, domain_error_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Idempotency-Key", "X-Request-ID"],
)
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"service": settings.app_name, "docs": "/docs"}
