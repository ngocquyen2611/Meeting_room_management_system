"""
main.py — Entry point của FastAPI Room Service

Khởi động:
    uvicorn room_service.main:app --reload --port 8001
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from room_service.api.routes import auth as auth_router
from room_service.api.routes import bookings as bookings_router
from room_service.api.routes import rooms as rooms_router
from room_service.api.routes import users as users_router
from room_service.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown hooks)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hooks cho FastAPI app."""
    logger.info(
        "Starting Room Service [env=%s, port=%s]",
        settings.ENVIRONMENT,
        settings.PORT,
    )

    # Warm-up: pre-fetch JWKS từ Auth0
    try:
        from room_service.core.security import get_jwks
        get_jwks()
        logger.info("JWKS pre-fetched from Auth0 successfully.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not pre-fetch JWKS (Auth0 unreachable?): %s", exc)

    # Khởi động auto-cancel background worker (FR-05)
    try:
        from room_service.services.auto_cancel import start_auto_cancel_worker
        worker = start_auto_cancel_worker(interval_seconds=60)
        logger.info("Auto-cancel worker started: %s", worker.name)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not start auto-cancel worker: %s", exc)

    yield

    logger.info("Room Service shutting down.")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Meeting Room Management — Room Service",
    description=(
        "Backend API cho he thong quan ly dat phong hop.\n\n"
        "**Auth**: Auth0 OAuth2/OIDC — RS256 JWT\n\n"
        "**Roles**: EMPLOYEE, ROOM_MANAGER, ADMIN\n\n"
        "**FR**: FR-01 Auth, FR-02 Rooms, FR-03 Search, FR-04 Booking, FR-05 Check-in"
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
API_V1_PREFIX = "/api/v1"

app.include_router(auth_router.router, prefix=API_V1_PREFIX)
app.include_router(rooms_router.router, prefix=API_V1_PREFIX)
app.include_router(bookings_router.router, prefix=API_V1_PREFIX)
app.include_router(users_router.router, prefix=API_V1_PREFIX)


# ---------------------------------------------------------------------------
# Root health-check
# ---------------------------------------------------------------------------
@app.get("/", tags=["root"], summary="Root health check")
def root():
    """Ping endpoint - khong can token."""
    return {
        "service": "room-service",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }
