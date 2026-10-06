"""
conftest.py — pytest fixtures dùng chung cho tất cả test

Fixtures:
    db_session  — SQLite in-memory, rollback sau mỗi test
    client      — TestClient với DB override
    make_token  — helper tạo JWT fake (RS256 mock)
"""

import uuid
from collections.abc import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from room_service.database import Base, get_db
from room_service.main import app
from room_service.models import User

# ---------------------------------------------------------------------------
# In-memory SQLite database cho tests
# ---------------------------------------------------------------------------
# Dùng named shared in-memory database để tất cả SQLAlchemy connections
# (kể cả từ TestClient thread) dùng cùng một SQLite instance.
SQLALCHEMY_TEST_URL = (
    "sqlite+pysqlite:///file:memdb_test?mode=memory&cache=shared&uri=true"
)

engine_test = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Tránh lazy-load sau commit
    bind=engine_test,
)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session]:
    """SQLite in-memory DB — tạo lại toàn bộ schema trước mỗi test."""
    Base.metadata.create_all(bind=engine_test)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient]:
    """
    TestClient với dependency override get_db → SQLite in-memory.
    JWKS được mock hoàn toàn — không gọi Auth0 thật.
    audit_log được mock để không phụ thuộc vào audit_logs table.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    # Mock log_audit để tránh phụ thuộc vào bảng audit_logs trong SQLite test
    with (
        patch("room_service.api.deps.log_audit", return_value=None),
        patch("room_service.api.routes.auth.log_audit", return_value=None),
        TestClient(app, raise_server_exceptions=True) as c,
    ):
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_user(
    db: Session,
    auth0_user_id: str = "auth0|test-employee",
    email: str = "employee@test.com",
    name: str = "Test Employee",
    role: str = "EMPLOYEE",
    status: str = "ACTIVE",
) -> User:
    """Tạo User trong DB test."""
    user = User(
        id=uuid.uuid4(),
        auth0_user_id=auth0_user_id,
        email=email,
        name=name,
        role=role,
        status=status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
