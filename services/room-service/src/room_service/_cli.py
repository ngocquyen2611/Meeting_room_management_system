"""
_cli.py — CLI entry point cho `room-service` script.

Chạy:
    room-service             (dùng PORT từ .env, default 8001)
    uvicorn room_service.main:app --reload --port 8001
"""

import uvicorn

from room_service.core.config import settings


def run() -> None:
    uvicorn.run(
        "room_service.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info",
    )


if __name__ == "__main__":
    run()
