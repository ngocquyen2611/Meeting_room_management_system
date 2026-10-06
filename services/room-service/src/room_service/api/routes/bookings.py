"""
api/routes/bookings.py — FR-04: Đặt phòng, sửa, hủy, mời attendee
                         FR-05: Check-in
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from room_service.api.deps import get_current_user, require_role
from room_service.database import get_db
from room_service.models import (
    Booking,
    BookingAttendee,
    BookingPolicy,
    Room,
    User,
)
from room_service.schemas.booking import (
    BookingCancelRequest,
    BookingCreate,
    BookingListResponse,
    BookingResponse,
    BookingUpdate,
)
from room_service.schemas.user import Role
from room_service.services.audit_service import log_audit

router = APIRouter(prefix="/bookings", tags=["bookings"])


# ---------------------------------------------------------------------------
# Helper: kiểm tra overlap với SELECT FOR UPDATE (chống race condition)
# ---------------------------------------------------------------------------
def _check_overlap(
    db: Session,
    room_id: UUID,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: Optional[UUID] = None,
) -> None:
    """
    Raise 409 nếu phòng đã có booking CONFIRMED/CHECKED_IN trùng giờ.
    Dùng subquery atomic — phải gọi trong cùng transaction với INSERT.
    """
    q = db.query(Booking).filter(
        Booking.room_id == room_id,
        Booking.status.in_(["CONFIRMED", "CHECKED_IN"]),
        Booking.start_time < end_time,
        Booking.end_time > start_time,
    )
    if exclude_booking_id:
        q = q.filter(Booking.id != exclude_booking_id)

    conflict = q.first()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Phòng đã được đặt trong khoảng "
                f"{conflict.start_time.strftime('%H:%M')} – "
                f"{conflict.end_time.strftime('%H:%M')} "
                f"ngày {conflict.start_time.strftime('%d/%m/%Y')}."
            ),
        )


def _get_policy(db: Session) -> BookingPolicy:
    policy = db.query(BookingPolicy).filter(BookingPolicy.id == 1).first()
    if not policy:
        # Fallback default nếu chưa seed
        return BookingPolicy(
            max_booking_duration_hours=4,
            max_advance_days=30,
            checkin_grace_period_minutes=15,
            require_checkin=True,
        )
    return policy


def _get_booking_or_404(booking_id: UUID, db: Session) -> Booking:
    booking = (
        db.query(Booking)
        .options(joinedload(Booking.attendees))
        .filter(Booking.id == booking_id)
        .first()
    )
    if not booking:
        raise HTTPException(404, "Booking không tồn tại.")
    return booking


# ---------------------------------------------------------------------------
# GET /bookings — lịch đặt phòng của tôi
# ---------------------------------------------------------------------------
@router.get(
    "/me",
    response_model=List[BookingListResponse],
    summary="Lịch đặt phòng của tôi",
)
def my_bookings(
    upcoming_only: bool = Query(default=False, description="Chỉ lấy lịch sắp tới"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Booking]:
    q = db.query(Booking).filter(Booking.organizer_id == current_user.id)
    if upcoming_only:
        q = q.filter(Booking.end_time > datetime.now(timezone.utc))
    return q.order_by(Booking.start_time.desc()).all()


# ---------------------------------------------------------------------------
# GET /bookings — ADMIN/MANAGER xem tất cả booking
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=List[BookingListResponse],
    summary="Tất cả booking [ADMIN, ROOM_MANAGER]",
)
def list_all_bookings(
    room_id: Optional[UUID] = Query(default=None),
    date: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    booking_status: Optional[str] = Query(default=None),
    current_user: User = Depends(require_role(Role.ROOM_MANAGER, Role.ADMIN)),
    db: Session = Depends(get_db),
) -> List[Booking]:
    q = db.query(Booking)
    if room_id:
        q = q.filter(Booking.room_id == room_id)
    if date:
        try:
            day_start = datetime.fromisoformat(f"{date}T00:00:00").replace(tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)
            q = q.filter(Booking.start_time >= day_start, Booking.start_time < day_end)
        except ValueError:
            raise HTTPException(422, "date phải là YYYY-MM-DD")
    if booking_status:
        q = q.filter(Booking.status == booking_status.upper())
    return q.order_by(Booking.start_time.desc()).all()


# ---------------------------------------------------------------------------
# GET /bookings/{booking_id}
# ---------------------------------------------------------------------------
@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Chi tiết booking",
)
def get_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Booking:
    booking = _get_booking_or_404(booking_id, db)
    # Chỉ organizer hoặc ADMIN/ROOM_MANAGER xem được
    if (
        booking.organizer_id != current_user.id
        and current_user.role not in ("ADMIN", "ROOM_MANAGER")
    ):
        raise HTTPException(403, "Bạn không có quyền xem booking này.")
    return booking


# ---------------------------------------------------------------------------
# POST /bookings — tạo booking (FR-04)
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đặt phòng họp (FR-04)",
)
def create_booking(
    body: BookingCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Booking:
    """
    Tạo booking với các kiểm tra:
    - Phòng phải tồn tại và AVAILABLE
    - Không trùng thời gian với booking khác (overlap check)
    - Thời lượng không vượt max_booking_duration_hours
    - Không đặt quá max_advance_days ngày trước
    - Số attendee không vượt sức chứa phòng
    """
    # 1. Kiểm tra phòng
    room = db.query(Room).filter(
        Room.id == body.room_id, Room.deleted_at.is_(None)
    ).first()
    if not room:
        raise HTTPException(404, "Phòng không tồn tại.")
    if room.status != "AVAILABLE":
        raise HTTPException(
            409, f"Phòng đang ở trạng thái {room.status}, không thể đặt."
        )

    # 2. Policy validation
    policy = _get_policy(db)
    now = datetime.now(timezone.utc)

    duration_hours = (body.end_time - body.start_time).total_seconds() / 3600
    if duration_hours > policy.max_booking_duration_hours:
        raise HTTPException(
            422,
            f"Thời lượng tối đa là {policy.max_booking_duration_hours} giờ.",
        )

    days_ahead = (body.start_time.date() - now.date()).days
    if days_ahead > policy.max_advance_days:
        raise HTTPException(
            422,
            f"Chỉ được đặt trước tối đa {policy.max_advance_days} ngày.",
        )

    if body.start_time < now - timedelta(minutes=5):
        raise HTTPException(422, "Không thể đặt phòng trong quá khứ.")

    # 3. Kiểm tra sức chứa
    total_people = 1 + len(body.attendee_ids)  # organizer + attendees
    if total_people > room.capacity:
        raise HTTPException(
            422,
            f"Phòng chỉ chứa {room.capacity} người, bạn đang mời {total_people} người.",
        )

    # 4. Overlap check (atomic)
    _check_overlap(db, body.room_id, body.start_time, body.end_time)

    # 5. Tạo booking
    booking = Booking(
        room_id=body.room_id,
        organizer_id=current_user.id,
        title=body.title,
        description=body.description,
        start_time=body.start_time,
        end_time=body.end_time,
        meeting_type=body.meeting_type,
        meeting_link=body.meeting_link,
        status="CONFIRMED",
        version=1,
    )
    db.add(booking)
    db.flush()  # Lấy booking.id trước khi commit

    # 6. Thêm attendees
    for uid in body.attendee_ids:
        attendee_user = db.query(User).filter(User.id == uid).first()
        if attendee_user:
            db.add(BookingAttendee(
                booking_id=booking.id,
                user_id=uid,
                status="INVITED",
            ))

    db.commit()
    db.refresh(booking)

    log_audit(
        db=db,
        correlation_id=request.headers.get("X-Correlation-ID", str(booking.id)),
        action="CREATE_BOOKING",
        entity_name="BOOKING",
        entity_id=str(booking.id),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        result="SUCCESS",
        details={
            "room_id": str(body.room_id),
            "room_name": room.name,
            "start_time": body.start_time.isoformat(),
            "end_time": body.end_time.isoformat(),
            "attendees": len(body.attendee_ids),
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return _get_booking_or_404(booking.id, db)


# ---------------------------------------------------------------------------
# PUT /bookings/{booking_id} — sửa booking (chỉ organizer)
# ---------------------------------------------------------------------------
@router.put(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Sửa booking",
)
def update_booking(
    booking_id: UUID,
    body: BookingUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Booking:
    booking = _get_booking_or_404(booking_id, db)

    if booking.organizer_id != current_user.id and current_user.role not in ("ADMIN",):
        raise HTTPException(403, "Chỉ người tạo booking mới có thể sửa.")

    if booking.status not in ("CONFIRMED",):
        raise HTTPException(
            409,
            f"Không thể sửa booking đang ở trạng thái {booking.status}.",
        )

    new_start = body.start_time or booking.start_time
    new_end = body.end_time or booking.end_time

    if new_end <= new_start:
        raise HTTPException(422, "end_time phải sau start_time.")

    # Overlap check (loại trừ chính booking này)
    _check_overlap(db, booking.room_id, new_start, new_end, exclude_booking_id=booking_id)

    # Optimistic locking check
    if body.start_time:
        booking.start_time = body.start_time
    if body.end_time:
        booking.end_time = body.end_time
    if body.title:
        booking.title = body.title
    if body.description is not None:
        booking.description = body.description
    if body.meeting_type:
        booking.meeting_type = body.meeting_type
    if body.meeting_link is not None:
        booking.meeting_link = body.meeting_link

    # Cập nhật attendees nếu có
    if body.attendee_ids is not None:
        # Xóa attendees cũ
        db.query(BookingAttendee).filter(
            BookingAttendee.booking_id == booking_id
        ).delete()
        for uid in body.attendee_ids:
            user_exists = db.query(User).filter(User.id == uid).first()
            if user_exists:
                db.add(BookingAttendee(
                    booking_id=booking_id,
                    user_id=uid,
                    status="INVITED",
                ))

    booking.version += 1
    db.commit()

    log_audit(
        db=db,
        correlation_id=request.headers.get("X-Correlation-ID", str(booking_id)),
        action="UPDATE_BOOKING",
        entity_name="BOOKING",
        entity_id=str(booking_id),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        result="SUCCESS",
        details={"new_start": new_start.isoformat(), "new_end": new_end.isoformat()},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return _get_booking_or_404(booking_id, db)


# ---------------------------------------------------------------------------
# DELETE /bookings/{booking_id} — hủy booking
# ---------------------------------------------------------------------------
@router.delete(
    "/{booking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hủy booking",
)
def cancel_booking(
    booking_id: UUID,
    body: BookingCancelRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    booking = _get_booking_or_404(booking_id, db)

    is_owner = booking.organizer_id == current_user.id
    is_privileged = current_user.role in ("ADMIN", "ROOM_MANAGER")

    if not is_owner and not is_privileged:
        raise HTTPException(403, "Bạn không có quyền hủy booking này.")

    if booking.status not in ("CONFIRMED",):
        raise HTTPException(
            409,
            f"Không thể hủy booking đang ở trạng thái {booking.status}.",
        )

    booking.status = "CANCELLED"
    booking.cancellation_reason = body.reason or "Hủy bởi người dùng"
    db.commit()

    log_audit(
        db=db,
        correlation_id=request.headers.get("X-Correlation-ID", str(booking_id)),
        action="CANCEL_BOOKING",
        entity_name="BOOKING",
        entity_id=str(booking_id),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        result="SUCCESS",
        details={"reason": body.reason},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )


# ---------------------------------------------------------------------------
# POST /bookings/{booking_id}/checkin — Check-in (FR-05)
# ---------------------------------------------------------------------------
@router.post(
    "/{booking_id}/checkin",
    response_model=BookingResponse,
    summary="Check-in cuộc họp (FR-05)",
)
def checkin_booking(
    booking_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Booking:
    """
    FR-05: Check-in trong khoảng grace_period trước/sau thời gian bắt đầu.
    Mặc định: 15 phút trước đến 15 phút sau start_time.
    """
    booking = _get_booking_or_404(booking_id, db)

    if booking.organizer_id != current_user.id:
        raise HTTPException(403, "Chỉ người tạo booking mới có thể check-in.")

    if booking.status != "CONFIRMED":
        raise HTTPException(
            409,
            f"Không thể check-in booking đang ở trạng thái {booking.status}.",
        )

    policy = _get_policy(db)
    now = datetime.now(timezone.utc)
    grace = timedelta(minutes=policy.checkin_grace_period_minutes)

    # Được check-in từ (start_time - grace) đến (start_time + grace)
    earliest_checkin = booking.start_time - grace
    latest_checkin = booking.start_time + grace

    if now < earliest_checkin:
        minutes_left = int((earliest_checkin - now).total_seconds() / 60)
        raise HTTPException(
            422,
            f"Check-in quá sớm. Vui lòng check-in sau {minutes_left} phút nữa.",
        )

    if now > booking.end_time:
        raise HTTPException(422, "Cuộc họp đã kết thúc.")

    booking.status = "CHECKED_IN"
    booking.checked_in_at = now
    db.commit()

    log_audit(
        db=db,
        correlation_id=request.headers.get("X-Correlation-ID", str(booking_id)),
        action="CHECKIN_BOOKING",
        entity_name="BOOKING",
        entity_id=str(booking_id),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        result="SUCCESS",
        details={"checked_in_at": now.isoformat()},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return _get_booking_or_404(booking_id, db)
