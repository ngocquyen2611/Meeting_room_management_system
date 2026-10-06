"""
api/routes/users.py — Quản lý người dùng (Admin only)

Endpoints:
    GET    /api/v1/users           — danh sách user [ADMIN]
    GET    /api/v1/users/{id}      — chi tiết user [ADMIN]
    PATCH  /api/v1/users/{id}/role — đổi role [ADMIN]
    PATCH  /api/v1/users/{id}/status — enable/disable [ADMIN]
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from room_service.api.deps import get_current_user, require_role
from room_service.database import get_db
from room_service.models import User
from room_service.schemas.booking import (
    UserListResponse,
    UserRoleUpdateRequest,
    UserStatusUpdateRequest,
)
from room_service.schemas.user import Role
from room_service.services.audit_service import log_audit

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=List[UserListResponse],
    summary="Danh sách người dùng [ADMIN]",
)
def list_users(
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> List[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


@router.get(
    "/{user_id}",
    response_model=UserListResponse,
    summary="Chi tiết người dùng [ADMIN]",
)
def get_user(
    user_id: UUID,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Người dùng không tồn tại.")
    return user


@router.patch(
    "/{user_id}/role",
    response_model=UserListResponse,
    summary="Đổi role người dùng [ADMIN]",
)
def update_user_role(
    user_id: UUID,
    body: UserRoleUpdateRequest,
    request: Request,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Người dùng không tồn tại.")

    old_role = user.role
    user.role = body.role
    db.commit()
    db.refresh(user)

    log_audit(
        db=db,
        correlation_id=request.headers.get("X-Correlation-ID", str(user_id)),
        action="ROLE_CHANGED",
        entity_name="USER",
        entity_id=str(user_id),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        result="SUCCESS",
        details={"old_role": old_role, "new_role": body.role, "target_email": user.email},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    return user


@router.patch(
    "/{user_id}/status",
    response_model=UserListResponse,
    summary="Enable/disable tài khoản [ADMIN]",
)
def update_user_status(
    user_id: UUID,
    body: UserStatusUpdateRequest,
    request: Request,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Người dùng không tồn tại.")

    if user.id == current_user.id:
        raise HTTPException(400, "Không thể tự vô hiệu hóa tài khoản của chính mình.")

    old_status = user.status
    user.status = body.status
    db.commit()
    db.refresh(user)

    log_audit(
        db=db,
        correlation_id=request.headers.get("X-Correlation-ID", str(user_id)),
        action="USER_STATUS_CHANGED",
        entity_name="USER",
        entity_id=str(user_id),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        result="SUCCESS",
        details={"old_status": old_status, "new_status": body.status, "target_email": user.email},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    return user
