from typing import List, Optional, Union

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from room_service.core.security import verify_jwt
from room_service.database import get_db
from room_service.models import User
from room_service.schemas.user import Role
from room_service.services.audit_service import log_audit

# Cấu hình HTTPBearer scheme để Swagger UI hiển thị nút Authorize "Bearer <token>"
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency xác thực danh tính người dùng:
    1. Kiểm tra header Authorization: Bearer <token>
    2. Xác minh cryptographic signature RS256 của JWT
    3. Mapping Auth0 sub -> users.auth0_user_id
    4. Auto-provisioning nếu user lần đầu đăng nhập
    5. Kiểm tra trạng thái tài khoản (chặn nếu INACTIVE)
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Verify token
    payload = verify_jwt(credentials.credentials)

    sub: Optional[str] = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token: missing subject claim.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Tìm user trong PostgreSQL theo auth0_user_id
    user = db.query(User).filter(User.auth0_user_id == sub).first()

    # 3. Auto-provisioning nếu user chưa tồn tại
    if not user:
        email = payload.get("email") or f"{sub.replace('|', '_')}@autocreated.local"
        name = payload.get("name") or payload.get("nickname") or email.split("@")[0]

        # Kiểm tra xem email đã có người dùng khác dùng chưa
        existing_email_user = db.query(User).filter(User.email == email).first()
        if existing_email_user:
            # Liên kết auth0_user_id vào user có sẵn
            existing_email_user.auth0_user_id = sub
            db.commit()
            db.refresh(existing_email_user)
            user = existing_email_user
        else:
            user = User(
                auth0_user_id=sub,
                email=email,
                name=name,
                role=Role.EMPLOYEE.value,
                status="ACTIVE",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            correlation_id = request.headers.get("X-Correlation-ID") or "system-init"
            log_audit(
                db=db,
                correlation_id=correlation_id,
                action="USER_AUTO_PROVISION",
                entity_name="USER",
                entity_id=str(user.id),
                user_id=user.id,
                user_email=user.email,
                user_role=user.role,
                result="SUCCESS",
                details={"auth0_user_id": sub, "initial_role": user.role},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
            )

    # 4. Kiểm tra trạng thái tài khoản
    if user.status != "ACTIVE":
        correlation_id = request.headers.get("X-Correlation-ID") or "security-check"
        log_audit(
            db=db,
            correlation_id=correlation_id,
            action="ACCESS_DENIED_INACTIVE_ACCOUNT",
            entity_name="USER",
            entity_id=str(user.id),
            user_id=user.id,
            user_email=user.email,
            user_role=user.role,
            result="DENIED",
            details={"status": user.status},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive or suspended. Please contact Administrator.",
        )

    return user


def require_role(*allowed_roles: Union[Role, str]):
    """
    Factory dependency kiểm tra phân quyền (RBAC):
    Ví dụ:
        @router.post("/rooms", dependencies=[Depends(require_role(Role.ADMIN, Role.ROOM_MANAGER))])
    """
    valid_roles_str = [r.value if isinstance(r, Role) else str(r) for r in allowed_roles]

    def role_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if current_user.role not in valid_roles_str:
            correlation_id = request.headers.get("X-Correlation-ID") or "rbac-check"
            log_audit(
                db=db,
                correlation_id=correlation_id,
                action="ACCESS_DENIED",
                entity_name="ENDPOINT",
                entity_id=request.url.path,
                user_id=current_user.id,
                user_email=current_user.email,
                user_role=current_user.role,
                result="FORBIDDEN",
                details={
                    "path": request.url.path,
                    "method": request.method,
                    "required_roles": valid_roles_str,
                    "user_role": current_user.role,
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: You do not have permission to access this resource. Required roles: {valid_roles_str}.",
            )
        return current_user

    return role_checker
