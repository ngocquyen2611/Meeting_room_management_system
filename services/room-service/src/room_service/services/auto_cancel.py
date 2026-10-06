"""
services/auto_cancel.py — FR-05: Background worker tự động hủy booking không check-in

Logic:
    Chạy mỗi 60 giây, tìm tất cả booking CONFIRMED mà:
        start_time + checkin_grace_period_minutes < NOW()
        AND checked_in_at IS NULL

    → Đổi status thành AUTO_CANCELLED
    → Ghi audit log
"""
import logging
import threading
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from room_service.database import SessionLocal
from room_service.models import Booking, BookingPolicy
from room_service.services.audit_service import log_audit

logger = logging.getLogger(__name__)


def _run_auto_cancel(db: Session) -> int:
    """
    Thực thi auto-cancel trong một DB session.
    Trả về số booking đã hủy.
    """
    policy = db.query(BookingPolicy).filter(BookingPolicy.id == 1).first()
    grace_minutes = policy.checkin_grace_period_minutes if policy else 15

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=grace_minutes)

    expired_bookings = (
        db.query(Booking)
        .filter(
            Booking.status == "CONFIRMED",
            Booking.start_time < cutoff,
            Booking.checked_in_at.is_(None),
        )
        .all()
    )

    count = 0
    for booking in expired_bookings:
        booking.status = "AUTO_CANCELLED"
        booking.cancellation_reason = f"Tự động hủy: không check-in sau {grace_minutes} phút"
        db.flush()

        log_audit(
            db=db,
            correlation_id=f"auto-cancel-{booking.id}",
            action="AUTO_CANCEL_BOOKING",
            entity_name="BOOKING",
            entity_id=str(booking.id),
            user_id=booking.organizer_id,
            result="SUCCESS",
            details={
                "room_id": str(booking.room_id),
                "start_time": booking.start_time.isoformat(),
                "grace_minutes": grace_minutes,
            },
        )
        count += 1
        logger.info("Auto-cancelled booking %s (room %s)", booking.id, booking.room_id)

    if count:
        db.commit()

    return count


def auto_cancel_worker(interval_seconds: int = 60) -> None:
    """
    Vòng lặp chạy trong background thread.
    Gọi từ lifespan của FastAPI app.
    """
    logger.info("Auto-cancel worker started (interval=%ds)", interval_seconds)
    while True:
        try:
            db = SessionLocal()
            try:
                cancelled = _run_auto_cancel(db)
                if cancelled:
                    logger.info("Auto-cancel: %d booking(s) cancelled", cancelled)
            finally:
                db.close()
        except Exception as exc:  # noqa: BLE001
            logger.error("Auto-cancel worker error: %s", exc)

        time.sleep(interval_seconds)


def start_auto_cancel_worker(interval_seconds: int = 60) -> threading.Thread:
    """Khởi động background thread cho auto-cancel."""
    t = threading.Thread(
        target=auto_cancel_worker,
        args=(interval_seconds,),
        daemon=True,  # Thread sẽ tự kết thúc khi main process dừng
        name="auto-cancel-worker",
    )
    t.start()
    return t
