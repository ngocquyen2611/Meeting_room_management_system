"""
test_rooms.py — Tests cho FR-02 Room CRUD + FR-03 Search

Cases:
    - Danh sách phòng (filter location, capacity, status)
    - Tạo phòng [MANAGER/ADMIN] — thành công, trùng tên, không có quyền
    - Cập nhật phòng
    - Soft delete (có/không có booking tương lai)
    - Thêm/bỏ thiết bị
    - FR-03: Search phòng trống theo time slot
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from room_service.models import Booking, Equipment, Room, RoomEquipment, User
from tests.conftest import make_user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_room(
    db: Session,
    name: str = "Phòng A",
    location: str = "Tầng 1",
    capacity: int = 10,
    status: str = "AVAILABLE",
) -> Room:
    room = Room(
        id=uuid.uuid4(),
        name=name,
        location=location,
        capacity=capacity,
        status=status,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


def make_equipment(db: Session, code: str = "TV", name: str = "TV") -> Equipment:
    eq = Equipment(id=uuid.uuid4(), code=code, name=name)
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq


def make_booking(
    db: Session,
    room: Room,
    organizer: User,
    start_offset_hours: float = 1,
    duration_hours: float = 1,
    status: str = "CONFIRMED",
) -> Booking:
    now = datetime.now(timezone.utc)
    start = now + timedelta(hours=start_offset_hours)
    end = start + timedelta(hours=duration_hours)
    booking = Booking(
        id=uuid.uuid4(),
        room_id=room.id,
        organizer_id=organizer.id,
        title="Test Meeting",
        start_time=start,
        end_time=end,
        status=status,
        version=1,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def _auth_headers(sub: str) -> dict:
    return {"Authorization": f"Bearer token-for-{sub}"}


def _patch_jwt(sub: str, email: str):
    return patch(
        "room_service.api.deps.verify_jwt",
        return_value={
            "sub": sub, "email": email, "name": "Test",
            "iss": "https://dev-example.us.auth0.com/",
            "aud": "https://meeting-room-api",
        },
    )


# ---------------------------------------------------------------------------
# FR-02: Room CRUD
# ---------------------------------------------------------------------------
class TestRoomList:
    def test_list_rooms_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/rooms")
        assert resp.status_code == 401

    def test_list_rooms_returns_all_active(
        self, client: TestClient, db_session: Session
    ):
        manager = make_user(db_session, auth0_user_id="auth0|m1", email="m1@t.com", role="ROOM_MANAGER")
        make_room(db_session, name="Room A")
        make_room(db_session, name="Room B")

        with _patch_jwt("auth0|m1", "m1@t.com"):
            resp = client.get("/api/v1/rooms", headers=_auth_headers("auth0|m1"))

        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_list_rooms_filter_by_location(
        self, client: TestClient, db_session: Session
    ):
        make_user(db_session, auth0_user_id="auth0|emp1", email="emp1@t.com")
        make_room(db_session, name="Room Floor1", location="Tầng 1")
        make_room(db_session, name="Room Floor2", location="Tầng 2")

        with _patch_jwt("auth0|emp1", "emp1@t.com"):
            resp = client.get("/api/v1/rooms?location=Tầng+1", headers=_auth_headers("auth0|emp1"))

        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()]
        assert "Room Floor1" in names
        assert "Room Floor2" not in names

    def test_list_rooms_filter_by_capacity(
        self, client: TestClient, db_session: Session
    ):
        make_user(db_session, auth0_user_id="auth0|emp2", email="emp2@t.com")
        make_room(db_session, name="Small Room", capacity=5)
        make_room(db_session, name="Big Room", capacity=20)

        with _patch_jwt("auth0|emp2", "emp2@t.com"):
            resp = client.get("/api/v1/rooms?min_capacity=10", headers=_auth_headers("auth0|emp2"))

        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()]
        assert "Big Room" in names
        assert "Small Room" not in names


class TestRoomCreate:
    def test_employee_cannot_create_room(
        self, client: TestClient, db_session: Session
    ):
        make_user(db_session, auth0_user_id="auth0|emp3", email="emp3@t.com", role="EMPLOYEE")

        with _patch_jwt("auth0|emp3", "emp3@t.com"):
            resp = client.post(
                "/api/v1/rooms",
                headers=_auth_headers("auth0|emp3"),
                json={"name": "New Room", "location": "T1", "capacity": 8},
            )
        assert resp.status_code == 403

    def test_manager_can_create_room(
        self, client: TestClient, db_session: Session
    ):
        make_user(db_session, auth0_user_id="auth0|mgr1", email="mgr1@t.com", role="ROOM_MANAGER")

        with _patch_jwt("auth0|mgr1", "mgr1@t.com"):
            resp = client.post(
                "/api/v1/rooms",
                headers=_auth_headers("auth0|mgr1"),
                json={"name": "New Room MGR", "location": "T2", "capacity": 12},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Room MGR"
        assert data["capacity"] == 12
        assert data["status"] == "AVAILABLE"

    def test_duplicate_room_name_returns_409(
        self, client: TestClient, db_session: Session
    ):
        make_user(db_session, auth0_user_id="auth0|mgr2", email="mgr2@t.com", role="ROOM_MANAGER")
        make_room(db_session, name="Existing Room")

        with _patch_jwt("auth0|mgr2", "mgr2@t.com"):
            resp = client.post(
                "/api/v1/rooms",
                headers=_auth_headers("auth0|mgr2"),
                json={"name": "Existing Room", "location": "T1", "capacity": 5},
            )
        assert resp.status_code == 409


class TestRoomUpdate:
    def test_update_room_status_to_maintenance(
        self, client: TestClient, db_session: Session
    ):
        make_user(db_session, auth0_user_id="auth0|mgr3", email="mgr3@t.com", role="ROOM_MANAGER")
        room = make_room(db_session, name="Room Update")

        with _patch_jwt("auth0|mgr3", "mgr3@t.com"):
            resp = client.put(
                f"/api/v1/rooms/{room.id}",
                headers=_auth_headers("auth0|mgr3"),
                json={"status": "MAINTENANCE"},
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "MAINTENANCE"


class TestRoomDelete:
    def test_soft_delete_room(self, client: TestClient, db_session: Session):
        make_user(db_session, auth0_user_id="auth0|mgr4", email="mgr4@t.com", role="ROOM_MANAGER")
        room = make_room(db_session, name="Room To Delete")

        with _patch_jwt("auth0|mgr4", "mgr4@t.com"):
            resp = client.delete(
                f"/api/v1/rooms/{room.id}",
                headers=_auth_headers("auth0|mgr4"),
            )
        assert resp.status_code == 204

        # Room không còn xuất hiện trong danh sách
        with _patch_jwt("auth0|mgr4", "mgr4@t.com"):
            list_resp = client.get("/api/v1/rooms", headers=_auth_headers("auth0|mgr4"))
        names = [r["name"] for r in list_resp.json()]
        assert "Room To Delete" not in names

    def test_cannot_delete_room_with_future_booking(
        self, client: TestClient, db_session: Session
    ):
        mgr = make_user(db_session, auth0_user_id="auth0|mgr5", email="mgr5@t.com", role="ROOM_MANAGER")
        emp = make_user(db_session, auth0_user_id="auth0|emp5", email="emp5@t.com", role="EMPLOYEE")
        room = make_room(db_session, name="Busy Room")
        make_booking(db_session, room, emp, start_offset_hours=2)

        with _patch_jwt("auth0|mgr5", "mgr5@t.com"):
            resp = client.delete(
                f"/api/v1/rooms/{room.id}",
                headers=_auth_headers("auth0|mgr5"),
            )
        assert resp.status_code == 409


class TestRoomEquipment:
    def test_add_equipment_to_room(self, client: TestClient, db_session: Session):
        make_user(db_session, auth0_user_id="auth0|mgr6", email="mgr6@t.com", role="ROOM_MANAGER")
        room = make_room(db_session, name="Room Equip")
        eq = make_equipment(db_session, code="PROJECTOR", name="Máy chiếu")

        with _patch_jwt("auth0|mgr6", "mgr6@t.com"):
            resp = client.post(
                f"/api/v1/rooms/{room.id}/equipments",
                headers=_auth_headers("auth0|mgr6"),
                json={"equipment_id": str(eq.id), "quantity": 1},
            )
        assert resp.status_code == 200
        eqs = resp.json()["equipments"]
        assert any(e["equipment"]["code"] == "PROJECTOR" for e in eqs)


# ---------------------------------------------------------------------------
# FR-03: Search rooms
# ---------------------------------------------------------------------------
class TestRoomSearch:
    def _search(self, client, user_sub, params: dict):
        with _patch_jwt(user_sub, f"{user_sub}@t.com"):
            return client.get(
                "/api/v1/rooms/search",
                headers=_auth_headers(user_sub),
                params=params,
            )

    def test_search_returns_available_rooms(
        self, client: TestClient, db_session: Session
    ):
        make_user(db_session, auth0_user_id="auth0|s1", email="s1@t.com")
        make_room(db_session, name="Free Room", capacity=10)

        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
        resp = self._search(client, "auth0|s1", {
            "date": tomorrow, "start_time": "09:00", "end_time": "11:00"
        })
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_search_excludes_booked_rooms(
        self, client: TestClient, db_session: Session
    ):
        make_user(db_session, auth0_user_id="auth0|s2", email="s2@t.com")
        emp = make_user(db_session, auth0_user_id="auth0|s2emp", email="s2emp@t.com")
        booked_room = make_room(db_session, name="Booked Room")
        free_room = make_room(db_session, name="Free Room 2")

        # Tạo booking vào ngày mai 9h-11h
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        start = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        end = tomorrow.replace(hour=11, minute=0, second=0, microsecond=0)
        booking = Booking(
            id=uuid.uuid4(),
            room_id=booked_room.id,
            organizer_id=emp.id,
            title="Blocked",
            start_time=start,
            end_time=end,
            status="CONFIRMED",
            version=1,
        )
        db_session.add(booking)
        db_session.commit()

        resp = self._search(client, "auth0|s2", {
            "date": tomorrow.strftime("%Y-%m-%d"),
            "start_time": "09:00",
            "end_time": "11:00",
        })
        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()]
        assert "Booked Room" not in names
        assert "Free Room 2" in names

    def test_search_requires_date_and_time(
        self, client: TestClient, db_session: Session
    ):
        make_user(db_session, auth0_user_id="auth0|s3", email="s3@t.com")
        with _patch_jwt("auth0|s3", "s3@t.com"):
            resp = client.get(
                "/api/v1/rooms/search",
                headers=_auth_headers("auth0|s3"),
                params={"date": "2026-10-08"},  # thiếu start_time, end_time
            )
        assert resp.status_code == 422

    def test_search_filter_by_capacity(
        self, client: TestClient, db_session: Session
    ):
        make_user(db_session, auth0_user_id="auth0|s4", email="s4@t.com")
        make_room(db_session, name="Small Srch", capacity=5)
        make_room(db_session, name="Large Srch", capacity=50)

        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
        resp = self._search(client, "auth0|s4", {
            "date": tomorrow, "start_time": "10:00", "end_time": "12:00",
            "min_capacity": 20,
        })
        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()]
        assert "Large Srch" in names
        assert "Small Srch" not in names

    def test_search_maintenance_room_excluded(
        self, client: TestClient, db_session: Session
    ):
        make_user(db_session, auth0_user_id="auth0|s5", email="s5@t.com")
        make_room(db_session, name="Under Maint", status="MAINTENANCE")

        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
        resp = self._search(client, "auth0|s5", {
            "date": tomorrow, "start_time": "09:00", "end_time": "10:00"
        })
        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()]
        assert "Under Maint" not in names
