"""
test_auth.py — Unit tests cho Authentication & Authorization

Covers (theo plan Phase 7):
    Case 1:  GET /auth/me  — không có token         → 401
    Case 2:  GET /auth/me  — token sai/malformed     → 401
    Case 3:  GET /auth/me  — token expired           → 401
    Case 4:  GET /auth/me  — token đúng             → 200
    Case 5:  Employee tự tạo room                   → 403
    Case 6:  Manager tạo room (future endpoint)     → pass RBAC
    Case 7:  Inactive user dù JWT valid             → 403
    Case 8:  Auth0 sub → DB mapping chính xác       → đúng user
    Case 9:  Auto-provision user mới                → tạo EMPLOYEE
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from room_service.main import app
from room_service.models import User
from tests.conftest import make_user


# ---------------------------------------------------------------------------
# Helpers: fake JWT payload
# ---------------------------------------------------------------------------
def _fake_payload(
    sub: str = "auth0|test-user",
    email: str = "test@test.com",
    expired: bool = False,
) -> dict[str, Any]:
    now = datetime.now(UTC)
    exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    return {
        "sub": sub,
        "email": email,
        "name": "Test User",
        "iss": "https://dev-example.us.auth0.com/",
        "aud": "https://meeting-room-api",
        "exp": exp.timestamp(),
        "iat": now.timestamp(),
    }


# ---------------------------------------------------------------------------
# Test: GET /auth/health  (no auth)
# ---------------------------------------------------------------------------
class TestAuthHealth:
    def test_health_no_token(self, client: TestClient):
        """Health endpoint luôn trả 200 không cần token."""
        response = client.get("/api/v1/auth/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


# ---------------------------------------------------------------------------
# Test: GET /auth/me — Authentication cases
# ---------------------------------------------------------------------------
class TestGetMe:
    # Case 1: Không có token → 401
    def test_no_token_returns_401(self, client: TestClient):
        """Không gửi Authorization header → 401 Unauthorized."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert "Bearer" in response.headers.get("WWW-Authenticate", "")

    # Case 2: Token malformed → 401
    def test_malformed_token_returns_401(self, client: TestClient):
        """Token không phải JWT hợp lệ → 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not.a.real.jwt"},
        )
        assert response.status_code == 401

    # Case 2b: Bearer scheme sai → 401
    def test_wrong_scheme_returns_401(self, client: TestClient):
        """Dùng Basic auth thay vì Bearer → 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Basic somebase64stuff"},
        )
        # HTTPBearer auto_error=False → dependency trả 401 vì credentials None
        assert response.status_code == 401

    # Case 3: Token expired → 401
    def test_expired_token_returns_401(self, client: TestClient, db_session: Session):
        """JWT expired → verify_jwt() raise 401 ExpiredSignatureError."""
        make_user(db_session, auth0_user_id="auth0|expired-user")

        # Patch verify_jwt để raise HTTPException 401 như khi token expired
        from fastapi import HTTPException
        from fastapi import status as http_status

        with patch("room_service.api.deps.verify_jwt") as mock_verify:
            mock_verify.side_effect = HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer expired.jwt.token"},
            )
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    # Case 4: Token đúng → 200 với thông tin user
    def test_valid_token_returns_200(self, client: TestClient, db_session: Session):
        """JWT hợp lệ, user tồn tại → 200 UserResponse."""
        make_user(
            db_session,
            auth0_user_id="auth0|valid-user",
            email="valid@test.com",
            name="Valid User",
            role="EMPLOYEE",
        )
        payload = _fake_payload(sub="auth0|valid-user", email="valid@test.com")

        with patch("room_service.api.deps.verify_jwt", return_value=payload):
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer valid.jwt.token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["auth0_user_id"] == "auth0|valid-user"
        assert data["email"] == "valid@test.com"
        assert data["role"] == "EMPLOYEE"
        assert data["status"] == "ACTIVE"

    # Case 7: Inactive user dù JWT valid → 403
    def test_inactive_user_returns_403(self, client: TestClient, db_session: Session):
        """
        Chứng minh Authentication ≠ Authorization:
        JWT vẫn hợp lệ nhưng account INACTIVE → 403.
        """
        make_user(
            db_session,
            auth0_user_id="auth0|inactive-user",
            email="inactive@test.com",
            status="INACTIVE",
        )
        payload = _fake_payload(sub="auth0|inactive-user", email="inactive@test.com")

        with patch("room_service.api.deps.verify_jwt", return_value=payload):
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer valid.but.inactive"},
            )

        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()

    # Case 8: Auth0 sub → DB mapping chính xác
    def test_sub_maps_to_correct_user(self, client: TestClient, db_session: Session):
        """
        sub trong JWT phải map đúng vào đúng user DB.
        Tạo 2 user, verify token của user A không trả về user B.
        """
        make_user(
            db_session,
            auth0_user_id="auth0|user-A",
            email="user-a@test.com",
            name="User A",
        )
        make_user(
            db_session,
            auth0_user_id="auth0|user-B",
            email="user-b@test.com",
            name="User B",
        )

        payload = _fake_payload(sub="auth0|user-A", email="user-a@test.com")
        with patch("room_service.api.deps.verify_jwt", return_value=payload):
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer token-for-user-A"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["auth0_user_id"] == "auth0|user-A"
        assert data["email"] == "user-a@test.com"
        # Đảm bảo không trả user B
        assert data["email"] != "user-b@test.com"

    # Case 9: Auto-provision user mới
    def test_auto_provision_new_user(self, client: TestClient, db_session: Session):
        """
        sub chưa tồn tại trong DB → backend tự tạo user với role=EMPLOYEE.
        """
        payload = _fake_payload(
            sub="auth0|brand-new-user",
            email="newuser@test.com",
        )
        payload["name"] = "Brand New User"

        with patch("room_service.api.deps.verify_jwt", return_value=payload):
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer new.user.token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["auth0_user_id"] == "auth0|brand-new-user"
        assert data["email"] == "newuser@test.com"
        # Auto-provision → role mặc định là EMPLOYEE
        assert data["role"] == "EMPLOYEE"
        assert data["status"] == "ACTIVE"

        # Kiểm tra user đã thực sự được tạo trong DB
        user_in_db = (
            db_session.query(User)
            .filter(User.auth0_user_id == "auth0|brand-new-user")
            .first()
        )
        assert user_in_db is not None
        assert user_in_db.role == "EMPLOYEE"


# ---------------------------------------------------------------------------
# Test: RBAC — Authorization cases
# ---------------------------------------------------------------------------
class TestRBAC:
    """
    Test require_role() dependency.
    Dùng fake endpoint /api/v1/auth/test-admin-only để test RBAC
    mà không cần implement Room CRUD trước.
    """

    def _register_test_route(self):
        """Đăng ký route test tạm thời nếu chưa có."""
        # route được đăng ký ở test_admin_endpoint_*

    def test_employee_cannot_access_admin_endpoint(
        self, client: TestClient, db_session: Session
    ):
        """
        Case 5: Employee token → endpoint chỉ dành cho ADMIN → 403.
        """
        from fastapi import Depends

        from room_service.api.deps import require_role
        from room_service.schemas.user import Role

        make_user(
            db_session,
            auth0_user_id="auth0|employee-rbac",
            email="employee-rbac@test.com",
            role="EMPLOYEE",
        )
        payload = _fake_payload(sub="auth0|employee-rbac")

        # Tạo fake endpoint để kiểm tra RBAC

        @app.get("/api/v1/test/admin-only", include_in_schema=False)
        def admin_only_endpoint(
            current_user: User = Depends(require_role(Role.ADMIN)),
        ):
            return {"ok": True}

        with patch("room_service.api.deps.verify_jwt", return_value=payload):
            response = client.get(
                "/api/v1/test/admin-only",
                headers={"Authorization": "Bearer employee.token"},
            )

        assert response.status_code == 403
        detail = response.json()["detail"]
        assert "ADMIN" in detail or "permission" in detail.lower()

        # Dọn dẹp route test
        app.routes[:] = [
            r
            for r in app.routes
            if getattr(r, "path", None) != "/api/v1/test/admin-only"
        ]

    def test_admin_can_access_admin_endpoint(
        self, client: TestClient, db_session: Session
    ):
        """
        Case 8 (RBAC): Admin token → endpoint ADMIN-only → 200.
        """
        from fastapi import Depends

        from room_service.api.deps import require_role
        from room_service.schemas.user import Role

        make_user(
            db_session,
            auth0_user_id="auth0|admin-rbac",
            email="admin-rbac@test.com",
            role="ADMIN",
        )
        payload = _fake_payload(sub="auth0|admin-rbac", email="admin-rbac@test.com")

        @app.get("/api/v1/test/admin-only-2", include_in_schema=False)
        def admin_only_2(
            current_user: User = Depends(require_role(Role.ADMIN)),
        ):
            return {"ok": True, "role": current_user.role}

        with patch("room_service.api.deps.verify_jwt", return_value=payload):
            response = client.get(
                "/api/v1/test/admin-only-2",
                headers={"Authorization": "Bearer admin.token"},
            )

        assert response.status_code == 200
        assert response.json()["role"] == "ADMIN"

        app.routes[:] = [
            r
            for r in app.routes
            if getattr(r, "path", None) != "/api/v1/test/admin-only-2"
        ]

    def test_manager_can_access_manager_or_admin_endpoint(
        self, client: TestClient, db_session: Session
    ):
        """
        Room Manager → endpoint cho phép ROOM_MANAGER và ADMIN → 200.
        """
        from fastapi import Depends

        from room_service.api.deps import require_role
        from room_service.schemas.user import Role

        make_user(
            db_session,
            auth0_user_id="auth0|manager-rbac",
            email="manager-rbac@test.com",
            role="ROOM_MANAGER",
        )
        payload = _fake_payload(sub="auth0|manager-rbac", email="manager-rbac@test.com")

        @app.get("/api/v1/test/manager-or-admin", include_in_schema=False)
        def manager_or_admin(
            current_user: User = Depends(require_role(Role.ROOM_MANAGER, Role.ADMIN)),
        ):
            return {"ok": True, "role": current_user.role}

        with patch("room_service.api.deps.verify_jwt", return_value=payload):
            response = client.get(
                "/api/v1/test/manager-or-admin",
                headers={"Authorization": "Bearer manager.token"},
            )

        assert response.status_code == 200
        assert response.json()["role"] == "ROOM_MANAGER"

        app.routes[:] = [
            r
            for r in app.routes
            if getattr(r, "path", None) != "/api/v1/test/manager-or-admin"
        ]

    def test_employee_blocked_from_manager_endpoint(
        self, client: TestClient, db_session: Session
    ):
        """
        Employee → endpoint dành cho ROOM_MANAGER/ADMIN → 403.
        Đây là test điển hình mô tả bảng phân quyền CRUD phòng.
        """
        from fastapi import Depends

        from room_service.api.deps import require_role
        from room_service.schemas.user import Role

        make_user(
            db_session,
            auth0_user_id="auth0|employee-blocked",
            email="employee-blocked@test.com",
            role="EMPLOYEE",
        )
        payload = _fake_payload(
            sub="auth0|employee-blocked", email="employee-blocked@test.com"
        )

        @app.get("/api/v1/test/rooms-manage", include_in_schema=False)
        def rooms_manage(
            current_user: User = Depends(require_role(Role.ROOM_MANAGER, Role.ADMIN)),
        ):
            return {"ok": True}

        with patch("room_service.api.deps.verify_jwt", return_value=payload):
            response = client.get(
                "/api/v1/test/rooms-manage",
                headers={"Authorization": "Bearer employee.blocked.token"},
            )

        assert response.status_code == 403

        app.routes[:] = [
            r
            for r in app.routes
            if getattr(r, "path", None) != "/api/v1/test/rooms-manage"
        ]
