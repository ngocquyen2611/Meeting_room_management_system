"""
test_bookings.py — Tests cho FR-04 Booking + FR-05 Check-in

Cases:
    - Tạo booking thành công
    - Overlap detection (2 người đặt cùng phòng cùng giờ)
    - Phòng đang maintenance không đặt được
    - Quá sức chứa → 422
    - Sửa booking
    - Hủy booking (owner + admin)
    - Check-in (đúng giờ, quá sớm)
    - Xem lịch của mình
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from room_service.models import Booking, BookingPolicy, Room, User
from tests.conftest import make_user
from tests.test_rooms import make_room


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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


def future_dt(hours: float = 2, minutes: int = 0) -> str:
    """Trả ISO string datetime trong tương lai."""
    dt = datetime.now(timezone.utc) + timedelta(hours=hours, minutes=minutes)
    return dt.isoformat()


def make_policy(db: Session) -> BookingPolicy:
    policy = db.query(BookingPolicy).filter(BookingPolicy.id == 1).first()
    if not policy:
        policy = BookingPolicy(
            id=1,
            max_booking_duration_hours=4,
            max_advance_days=30,
            checkin_grace_period_minutes=15,
            require_checkin=True,
        )
        db.add(policy)
        db.commit()
    return policy


# ---------------------------------------------------------------------------
# FR-04: Create Booking
# ---------------------------------------------------------------------------
class TestCreateBooking:
    def test_create_booking_success(self, client: TestClient, db_session: Session):
        emp = make_user(db_session, auth0_user_id="auth0|b-emp1", email="b-emp1@t.com")
        room = make_room(db_session, name="Book Room 1", capacity=10)
        make_policy(db_session)

        with _patch_jwt("auth0|b-emp1", "b-emp1@t.com"):
            resp = client.post(
                "/api/v1/bookings",
                headers=_auth_headers("auth0|b-emp1"),
                json={
                    "room_id": str(room.id),
                    "title": "Sprint Planning",
                    "start_time": future_dt(2),
                    "end_time": future_dt(3),
                    "meeting_type": "OFFLINE",
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Sprint Planning"
        assert data["status"] == "CONFIRMED"
        assert data["room_id"] == str(room.id)

    def test_create_booking_requires_auth(self, client: TestClient, db_session: Session):
        room = make_room(db_session, name="Book Room Auth")
        resp = client.post(
            "/api/v1/bookings",
            json={
                "room_id": str(room.id),
                "title": "Test",
                "start_time": future_dt(2),
                "end_time": future_dt(3),
            },
        )
        assert resp.status_code == 401

    def test_create_booking_end_before_start_returns_422(
        self, client: TestClient, db_session: Session
    ):
        make_user(db_session, auth0_user_id="auth0|b-emp2", email="b-emp2@t.com")
        room = make_room(db_session, name="Book Room 2")
        make_policy(db_session)

        with _patch_jwt("auth0|b-emp2", "b-emp2@t.com"):
            resp = client.post(
                "/api/v1/bookings",
                headers=_auth_headers("auth0|b-emp2"),
                json={
                    "room_id": str(room.id),
                    "title": "Bad Time",
                    "start_time": future_dt(3),
                    "end_time": future_dt(2),   # end < start
                },
            )
        assert resp.status_code == 422

    def test_create_booking_maintenance_room_returns_409(
        self, client: TestClient, db_session: Session
    ):
        make_user(db_session, auth0_user_id="auth0|b-emp3", email="b-emp3@t.com")
        room = make_room(db_session, name="Maintenance Room", status="MAINTENANCE")
        make_policy(db_session)

        with _patch_jwt("auth0|b-emp3", "b-emp3@t.com"):
            resp = client.post(
                "/api/v1/bookings",
                headers=_auth_headers("auth0|b-emp3"),
                json={
                    "room_id": str(room.id),
                    "title": "Meeting",
                    "start_time": future_dt(2),
                    "end_time": future_dt(3),
                },
            )
        assert resp.status_code == 409
        assert "MAINTENANCE" in resp.json()["detail"]

    def test_create_booking_exceeds_capacity_returns_422(
        self, client: TestClient, db_session: Session
    ):
        """3 người đặt phòng chứa tối đa 2 người → 422."""
        emp = make_user(db_session, auth0_user_id="auth0|b-cap", email="b-cap@t.com")
        attendee1 = make_user(db_session, auth0_user_id="auth0|att1", email="att1@t.com")
        attendee2 = make_user(db_session, auth0_user_id="auth0|att2", email="att2@t.com")
        room = make_room(db_session, name="Tiny Room", capacity=2)
        make_policy(db_session)

        with _patch_jwt("auth0|b-cap", "b-cap@t.com"):
            resp = client.post(
                "/api/v1/bookings",
                headers=_auth_headers("auth0|b-cap"),
                json={
                    "room_id": str(room.id),
                    "title": "Too Many People",
                    "start_time": future_dt(2),
                    "end_time": future_dt(3),
                    "attendee_ids": [str(attendee1.id), str(attendee2.id)],
                    # organizer + 2 attendees = 3 > capacity 2
                },
            )
        assert resp.status_code == 422
        assert "chứa" in resp.json()["detail"]

    # -----------------------------------------------------------------------
    # QUAN TRỌNG: Overlap detection — FR-04
    # -----------------------------------------------------------------------
    def test_overlap_booking_returns_409(
        self, client: TestClient, db_session: Session
    ):
        """
        Test case bắt buộc từ đề:
        Hai request đặt cùng phòng trong cùng thời điểm → người thứ 2 bị 409.
        """
        emp1 = make_user(db_session, auth0_user_id="auth0|ov1", email="ov1@t.com")
        emp2 = make_user(db_session, auth0_user_id="auth0|ov2", email="ov2@t.com")
        room = make_room(db_session, name="Overlap Room", capacity=20)
        make_policy(db_session)

        start = future_dt(4)
        end = future_dt(5)

        # Booking đầu tiên thành công
        with _patch_jwt("auth0|ov1", "ov1@t.com"):
            resp1 = client.post(
                "/api/v1/bookings",
                headers=_auth_headers("auth0|ov1"),
                json={"room_id": str(room.id), "title": "Meeting 1",
                      "start_time": start, "end_time": end},
            )
        assert resp1.status_code == 201

        # Booking thứ 2 trùng giờ → 409
        with _patch_jwt("auth0|ov2", "ov2@t.com"):
            resp2 = client.post(
                "/api/v1/bookings",
                headers=_auth_headers("auth0|ov2"),
                json={"room_id": str(room.id), "title": "Meeting 2",
                      "start_time": start, "end_time": end},
            )
        assert resp2.status_code == 409

    def test_partial_overlap_returns_409(
        self, client: TestClient, db_session: Session
    ):
        """Booking mới chỉ overlap một phần thời gian → vẫn phải 409."""
        emp1 = make_user(db_session, auth0_user_id="auth0|po1", email="po1@t.com")
        emp2 = make_user(db_session, auth0_user_id="auth0|po2", email="po2@t.com")
        room = make_room(db_session, name="Partial Overlap Room", capacity=20)
        make_policy(db_session)

        # Booking 1: 10:00 - 12:00
        with _patch_jwt("auth0|po1", "po1@t.com"):
            resp1 = client.post(
                "/api/v1/bookings",
                headers=_auth_headers("auth0|po1"),
                json={
                    "room_id": str(room.id),
                    "title": "First",
                    "start_time": future_dt(10),
                    "end_time": future_dt(12),
                },
            )
        assert resp1.status_code == 201

        # Booking 2: 11:00 - 13:00 → overlap 1 giờ
        with _patch_jwt("auth0|po2", "po2@t.com"):
            resp2 = client.post(
                "/api/v1/bookings",
                headers=_auth_headers("auth0|po2"),
                json={
                    "room_id": str(room.id),
                    "title": "Second Overlap",
                    "start_time": future_dt(11),
                    "end_time": future_dt(13),
                },
            )
        assert resp2.status_code == 409

    def test_adjacent_booking_is_allowed(
        self, client: TestClient, db_session: Session
    ):
        """Booking mới bắt đầu đúng lúc booking cũ kết thúc → OK (không overlap)."""
        emp1 = make_user(db_session, auth0_user_id="auth0|adj1", email="adj1@t.com")
        emp2 = make_user(db_session, auth0_user_id="auth0|adj2", email="adj2@t.com")
        room = make_room(db_session, name="Adjacent Room", capacity=20)
        make_policy(db_session)

        with _patch_jwt("auth0|adj1", "adj1@t.com"):
            resp1 = client.post(
                "/api/v1/bookings",
                headers=_auth_headers("auth0|adj1"),
                json={
                    "room_id": str(room.id),
                    "title": "First",
                    "start_time": future_dt(6),
                    "end_time": future_dt(7),
                },
            )
        assert resp1.status_code == 201

        # Booking thứ 2 bắt đầu đúng khi booking 1 kết thúc → hợp lệ
        with _patch_jwt("auth0|adj2", "adj2@t.com"):
            resp2 = client.post(
                "/api/v1/bookings",
                headers=_auth_headers("auth0|adj2"),
                json={
                    "room_id": str(room.id),
                    "title": "Second Adjacent",
                    "start_time": future_dt(7),
                    "end_time": future_dt(8),
                },
            )
        assert resp2.status_code == 201


# ---------------------------------------------------------------------------
# FR-04: Cancel Booking
# ---------------------------------------------------------------------------
class TestCancelBooking:
    def test_owner_can_cancel(self, client: TestClient, db_session: Session):
        emp = make_user(db_session, auth0_user_id="auth0|can1", email="can1@t.com")
        room = make_room(db_session, name="Cancel Room")
        make_policy(db_session)

        with _patch_jwt("auth0|can1", "can1@t.com"):
            create_resp = client.post(
                "/api/v1/bookings",
                headers=_auth_headers("auth0|can1"),
                json={"room_id": str(room.id), "title": "To Cancel",
                      "start_time": future_dt(5), "end_time": future_dt(6)},
            )
        assert create_resp.status_code == 201
        booking_id = create_resp.json()["id"]

        with _patch_jwt("auth0|can1", "can1@t.com"):
            cancel_resp = client.delete(
                f"/api/v1/bookings/{booking_id}",
                headers=_auth_headers("auth0|can1"),
                json={"reason": "Họp bị dời"},
            )
        assert cancel_resp.status_code == 204

    def test_other_employee_cannot_cancel(
        self, client: TestClient, db_session: Session
    ):
        owner = make_user(db_session, auth0_user_id="auth0|own1", email="own1@t.com")
        other = make_user(db_session, auth0_user_id="auth0|oth1", email="oth1@t.com")
        room = make_room(db_session, name="Private Room")
        make_policy(db_session)

        with _patch_jwt("auth0|own1", "own1@t.com"):
            create_resp = client.post(
                "/api/v1/bookings",
                headers=_auth_headers("auth0|own1"),
                json={"room_id": str(room.id), "title": "Private",
                      "start_time": future_dt(5), "end_time": future_dt(6)},
            )
        assert create_resp.status_code == 201
        booking_id = create_resp.json()["id"]

        with _patch_jwt("auth0|oth1", "oth1@t.com"):
            cancel_resp = client.delete(
                f"/api/v1/bookings/{booking_id}",
                headers=_auth_headers("auth0|oth1"),
                json={"reason": "Tôi muốn hủy"},
            )
        assert cancel_resp.status_code == 403

    def test_cancelled_booking_frees_room(
        self, client: TestClient, db_session: Session
    ):
        """Sau khi hủy booking, phòng phải có thể đặt lại cùng giờ đó."""
        emp1 = make_user(db_session, auth0_user_id="auth0|fr1", email="fr1@t.com")
        emp2 = make_user(db_session, auth0_user_id="auth0|fr2", email="fr2@t.com")
        room = make_room(db_session, name="Free After Cancel", capacity=10)
        make_policy(db_session)

        start, end = future_dt(8), future_dt(9)

        with _patch_jwt("auth0|fr1", "fr1@t.com"):
            b1 = client.post(
                "/api/v1/bookings",
                headers=_auth_headers("auth0|fr1"),
                json={"room_id": str(room.id), "title": "B1",
                      "start_time": start, "end_time": end},
            )
        assert b1.status_code == 201
        booking_id = b1.json()["id"]

        # Hủy booking đầu
        with _patch_jwt("auth0|fr1", "fr1@t.com"):
            client.delete(f"/api/v1/bookings/{booking_id}",
                          headers=_auth_headers("auth0|fr1"),
                          json={"reason": "Hủy"})

        # Người khác đặt lại cùng giờ → phải thành công
        with _patch_jwt("auth0|fr2", "fr2@t.com"):
            b2 = client.post(
                "/api/v1/bookings",
                headers=_auth_headers("auth0|fr2"),
                json={"room_id": str(room.id), "title": "B2",
                      "start_time": start, "end_time": end},
            )
        assert b2.status_code == 201


# ---------------------------------------------------------------------------
# FR-05: Check-in
# ---------------------------------------------------------------------------
class TestCheckin:
    def _create_booking_in_db(
        self,
        db: Session,
        room: Room,
        user: User,
        start_offset_minutes: float = 5,
        duration_minutes: float = 60,
        status: str = "CONFIRMED",
    ) -> Booking:
        """Tạo booking trực tiếp trong DB để kiểm soát thời gian check-in."""
        now = datetime.now(timezone.utc)
        start = now + timedelta(minutes=start_offset_minutes)
        end = start + timedelta(minutes=duration_minutes)
        b = Booking(
            id=uuid.uuid4(),
            room_id=room.id,
            organizer_id=user.id,
            title="Checkin Test",
            start_time=start,
            end_time=end,
            status=status,
            version=1,
        )
        db.add(b)
        db.commit()
        db.refresh(b)
        return b

    def test_checkin_within_grace_period(
        self, client: TestClient, db_session: Session
    ):
        """Check-in khi thời gian hiện tại nằm trong grace period → 200 CHECKED_IN."""
        emp = make_user(db_session, auth0_user_id="auth0|ci1", email="ci1@t.com")
        room = make_room(db_session, name="CI Room 1")
        make_policy(db_session)

        # Booking bắt đầu sau 5 phút (nằm trong grace period 15 phút)
        booking = self._create_booking_in_db(db_session, room, emp, start_offset_minutes=5)

        with _patch_jwt("auth0|ci1", "ci1@t.com"):
            resp = client.post(
                f"/api/v1/bookings/{booking.id}/checkin",
                headers=_auth_headers("auth0|ci1"),
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "CHECKED_IN"
        assert resp.json()["checked_in_at"] is not None

    def test_checkin_too_early_returns_422(
        self, client: TestClient, db_session: Session
    ):
        """Check-in quá sớm (trước grace period) → 422."""
        emp = make_user(db_session, auth0_user_id="auth0|ci2", email="ci2@t.com")
        room = make_room(db_session, name="CI Room 2")
        make_policy(db_session)

        # Booking bắt đầu sau 60 phút → quá sớm để check-in (grace=15 phút)
        booking = self._create_booking_in_db(db_session, room, emp, start_offset_minutes=60)

        with _patch_jwt("auth0|ci2", "ci2@t.com"):
            resp = client.post(
                f"/api/v1/bookings/{booking.id}/checkin",
                headers=_auth_headers("auth0|ci2"),
            )
        assert resp.status_code == 422
        assert "sớm" in resp.json()["detail"]

    def test_checkin_other_user_returns_403(
        self, client: TestClient, db_session: Session
    ):
        """Người khác không thể check-in thay chủ booking → 403."""
        owner = make_user(db_session, auth0_user_id="auth0|ci3", email="ci3@t.com")
        other = make_user(db_session, auth0_user_id="auth0|ci3b", email="ci3b@t.com")
        room = make_room(db_session, name="CI Room 3")
        make_policy(db_session)

        booking = self._create_booking_in_db(db_session, room, owner, start_offset_minutes=5)

        with _patch_jwt("auth0|ci3b", "ci3b@t.com"):
            resp = client.post(
                f"/api/v1/bookings/{booking.id}/checkin",
                headers=_auth_headers("auth0|ci3b"),
            )
        assert resp.status_code == 403

    def test_cannot_checkin_cancelled_booking(
        self, client: TestClient, db_session: Session
    ):
        emp = make_user(db_session, auth0_user_id="auth0|ci4", email="ci4@t.com")
        room = make_room(db_session, name="CI Room 4")
        make_policy(db_session)

        booking = self._create_booking_in_db(
            db_session, room, emp, start_offset_minutes=5, status="CANCELLED"
        )

        with _patch_jwt("auth0|ci4", "ci4@t.com"):
            resp = client.post(
                f"/api/v1/bookings/{booking.id}/checkin",
                headers=_auth_headers("auth0|ci4"),
            )
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# My Bookings
# ---------------------------------------------------------------------------
class TestMyBookings:
    def test_get_my_bookings(self, client: TestClient, db_session: Session):
        emp = make_user(db_session, auth0_user_id="auth0|me1", email="me1@t.com")
        room = make_room(db_session, name="My Room")
        make_policy(db_session)

        with _patch_jwt("auth0|me1", "me1@t.com"):
            client.post(
                "/api/v1/bookings",
                headers=_auth_headers("auth0|me1"),
                json={"room_id": str(room.id), "title": "My Meeting",
                      "start_time": future_dt(10), "end_time": future_dt(11)},
            )
            resp = client.get("/api/v1/bookings/me", headers=_auth_headers("auth0|me1"))

        assert resp.status_code == 200
        assert len(resp.json()) >= 1
        assert resp.json()[0]["title"] == "My Meeting"
