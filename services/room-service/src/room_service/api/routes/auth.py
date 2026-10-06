"""
Auth routes — Phase 6: API
GET  /api/v1/auth/me          → Trả thông tin user hiện tại (require login)
GET  /api/v1/auth/health      → Health-check không cần token
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from room_service.api.deps import get_current_user
from room_service.database import get_db
from room_service.models import User
from room_service.schemas.user import UserResponse
from room_service.services.audit_service import log_audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get(
    "/health",
    summary="Health check (no auth required)",
    response_model=dict,
)
def auth_health():
    """
    Endpoint kiểm tra service còn sống — không cần token.
    Dùng để liveness probe.
    """
    return {"status": "ok", "service": "room-service", "auth": "auth0/RS256"}


@router.get(
    "/me",
    summary="Get current authenticated user",
    response_model=UserResponse,
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Account inactive or suspended"},
    },
)
def get_me(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Trả về thông tin user đang đăng nhập.

    Frontend gọi endpoint này ngay sau khi lấy được Access Token từ Auth0
    để biết:
    - Ai đang login
    - Role là gì (EMPLOYEE / ROOM_MANAGER / ADMIN)
    - Account còn ACTIVE không

    Flow:
        Authorization: Bearer <JWT>
            ↓
        verify_jwt()  — RS256 signature, iss, aud, exp
            ↓
        auth0_user_id (sub)  →  users table
            ↓
        auto-provision nếu user chưa tồn tại
            ↓
        kiểm tra status == ACTIVE
            ↓
        return UserResponse
    """
    correlation_id = request.headers.get("X-Correlation-ID", "me-endpoint")
    log_audit(
        db=db,
        correlation_id=correlation_id,
        action="GET_ME",
        entity_name="USER",
        entity_id=str(current_user.id),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        result="SUCCESS",
        details={"role": current_user.role, "status": current_user.status},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    # Serialize sang Pydantic trước khi return để tránh lazy-load
    # sau khi audit commit (SQLAlchemy expire_on_commit)
    return UserResponse.model_validate(current_user)
