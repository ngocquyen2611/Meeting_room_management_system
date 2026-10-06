"""
api/routes/rooms.py — FR-02: Room CRUD + Equipment management
                     FR-03: Room search (tìm phòng trống theo time slot)

Endpoints:
    GET    /api/v1/rooms                     — danh sách phòng (có filter)
    POST   /api/v1/rooms                     — tạo phòng [ADMIN, ROOM_MANAGER]
    GET    /api/v1/rooms/search              — tìm phòng trống (FR-03)
    GET    /api/v1/rooms/equipments          — danh sách thiết bị
    GET    /api/v1/rooms/{room_id}           — chi tiết phòng
    PUT    /api/v1/rooms/{room_id}           — cập nhật [ADMIN, ROOM_MANAGER]
    DELETE /api/v1/rooms/{room_id}           — soft delete [ADMIN, ROOM_MANAGER]
    POST   /api/v1/rooms/{room_id}/equipments       — thêm thiết bị
    DELETE /api/v1/rooms/{room_id}/equipments/{eq_id} — bỏ thiết bị
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select as sa_select
from sqlalchemy.orm import Session, joinedload

from room_service.api.deps import get_current_user, require_role
from room_service.database import get_db
from room_service.models import Booking, Equipment, Room, RoomEquipment, User
from room_service.schemas.room import (
    EquipmentAdd,
    EquipmentResponse,
    RoomCreate,
    RoomListResponse,
    RoomResponse,
    RoomUpdate,
)
from room_service.schemas.user import Role
from room_service.services.audit_service import log_audit

router = APIRouter(prefix="/rooms", tags=["rooms"])

MANAGER_OR_ADMIN = [Role.ROOM_MANAGER, Role.ADMIN]


# ---------------------------------------------------------------------------
# Helper: get active room or 404
# ---------------------------------------------------------------------------
def _get_active_room(room_id: UUID, db: Session) -> Room:
    db.expire_all()   # Đảm bảo joinedload không dùng cache cũ sau commit
    room = (
        db.query(Room)
        .options(joinedload(Room.equipments).joinedload(RoomEquipment.equipment))
        .filter(Room.id == room_id, Room.deleted_at.is_(None))
        .first()
    )
    if not room:
        raise HTTPException(status_code=404, detail="Phòng không tồn tại hoặc đã bị xóa.")
    return room


# ---------------------------------------------------------------------------
# GET /rooms — danh sách phòng
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=List[RoomListResponse],
    summary="Danh sách phòng họp",
)
def list_rooms(
    location: Optional[str] = Query(default=None, description="Lọc theo vị trí"),
    min_capacity: Optional[int] = Query(default=None, ge=1, description="Sức chứa tối thiểu"),
    status: Optional[str] = Query(default=None, description="Trạng thái: AVAILABLE/MAINTENANCE/DISABLED"),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Room]:
    """Trả danh sách phòng chưa bị xóa. Hỗ trợ filter theo location, capacity, status."""
    q = (
        db.query(Room)
        .options(joinedload(Room.equipments).joinedload(RoomEquipment.equipment))
        .filter(Room.deleted_at.is_(None))
    )
    if location:
        q = q.filter(Room.location.ilike(f"%{location}%"))
    if min_capacity:
        q = q.filter(Room.capacity >= min_capacity)
    if status:
        q = q.filter(Room.status == status.upper())

    return q.order_by(Room.name).all()


# ---------------------------------------------------------------------------
# GET /rooms/search — tìm phòng TRỐNG (FR-03)
# ---------------------------------------------------------------------------
@router.get(
    "/search",
    response_model=List[RoomListResponse],
    summary="Tìm phòng trống theo khung giờ (FR-03)",
)
def search_available_rooms(
    date: str = Query(..., description="Ngày họp: YYYY-MM-DD"),
    start_time: str = Query(..., description="Giờ bắt đầu: HH:MM"),
    end_time: str = Query(..., description="Giờ kết thúc: HH:MM"),
    min_capacity: Optional[int] = Query(default=None, ge=1),
    location: Optional[str] = Query(default=None),
    equipment_codes: Optional[str] = Query(
        default=None, description="Mã thiết bị cách nhau bởi dấu phẩy: TV,PROJECTOR"
    ),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Room]:
    """
    FR-03: Tìm phòng còn trống trong khoảng thời gian yêu cầu.

    - Chỉ trả phòng status=AVAILABLE
    - Loại trừ phòng có booking CONFIRMED/CHECKED_IN trùng giờ
    - Filter thêm theo sức chứa, vị trí, thiết bị
    """
    # Parse datetime
    try:
        slot_start = datetime.fromisoformat(f"{date}T{start_time}:00").replace(
            tzinfo=timezone.utc
        )
        slot_end = datetime.fromisoformat(f"{date}T{end_time}:00").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="date phải là YYYY-MM-DD, start_time/end_time phải là HH:MM",
        )

    if slot_end <= slot_start:
        raise HTTPException(status_code=422, detail="end_time phải sau start_time")

    # Select phòng đang bị đặt trong khung giờ đó
    conflicting_room_ids = sa_select(Booking.room_id).where(
        Booking.status.in_(["CONFIRMED", "CHECKED_IN"]),
        Booking.start_time < slot_end,
        Booking.end_time > slot_start,
    )

    q = (
        db.query(Room)
        .options(joinedload(Room.equipments).joinedload(RoomEquipment.equipment))
        .filter(
            Room.deleted_at.is_(None),
            Room.status == "AVAILABLE",
            Room.id.not_in(conflicting_room_ids),
        )
    )

    if min_capacity:
        q = q.filter(Room.capacity >= min_capacity)
    if location:
        q = q.filter(Room.location.ilike(f"%{location}%"))

    # Filter theo thiết bị: phòng phải có TẤT CẢ thiết bị yêu cầu
    if equipment_codes:
        codes = [c.strip().upper() for c in equipment_codes.split(",") if c.strip()]
        for code in codes:
            has_equipment = (
                db.query(RoomEquipment)
                .join(Equipment)
                .filter(
                    RoomEquipment.room_id == Room.id,
                    Equipment.code == code,
                )
                .exists()
            )
            q = q.filter(has_equipment)

    return q.order_by(Room.capacity).all()


# ---------------------------------------------------------------------------
# GET /rooms/equipments — danh sách tất cả thiết bị
# ---------------------------------------------------------------------------
@router.get(
    "/equipments",
    response_model=List[EquipmentResponse],
    summary="Danh sách thiết bị",
)
def list_equipments(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Equipment]:
    """Trả tất cả thiết bị có trong hệ thống (dùng khi thêm thiết bị vào phòng)."""
    return db.query(Equipment).order_by(Equipment.code).all()


# ---------------------------------------------------------------------------
# GET /rooms/{room_id} — chi tiết phòng
# ---------------------------------------------------------------------------
@router.get(
    "/{room_id}",
    response_model=RoomResponse,
    summary="Chi tiết phòng họp",
)
def get_room(
    room_id: UUID,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Room:
    return _get_active_room(room_id, db)


# ---------------------------------------------------------------------------
# POST /rooms — tạo phòng [ADMIN, ROOM_MANAGER]
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo phòng họp mới",
)
def create_room(
    body: RoomCreate,
    request: Request,
    current_user: User = Depends(require_role(Role.ROOM_MANAGER, Role.ADMIN)),
    db: Session = Depends(get_db),
) -> Room:
    """Chỉ ROOM_MANAGER hoặc ADMIN mới được tạo phòng."""
    # Kiểm tra tên phòng trùng (chưa bị xóa)
    existing = db.query(Room).filter(
        Room.name == body.name, Room.deleted_at.is_(None)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Phòng tên '{body.name}' đã tồn tại.",
        )

    room = Room(
        name=body.name,
        location=body.location,
        capacity=body.capacity,
        status=body.status,
        image_url=body.image_url,
        notes=body.notes,
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    log_audit(
        db=db,
        correlation_id=request.headers.get("X-Correlation-ID", str(room.id)),
        action="CREATE_ROOM",
        entity_name="ROOM",
        entity_id=str(room.id),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        result="SUCCESS",
        details={"name": room.name, "capacity": room.capacity},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    # reload với equipments
    return _get_active_room(room.id, db)


# ---------------------------------------------------------------------------
# PUT /rooms/{room_id} — cập nhật [ADMIN, ROOM_MANAGER]
# ---------------------------------------------------------------------------
@router.put(
    "/{room_id}",
    response_model=RoomResponse,
    summary="Cập nhật thông tin phòng",
)
def update_room(
    room_id: UUID,
    body: RoomUpdate,
    request: Request,
    current_user: User = Depends(require_role(Role.ROOM_MANAGER, Role.ADMIN)),
    db: Session = Depends(get_db),
) -> Room:
    room = _get_active_room(room_id, db)

    updated_fields: dict = {}
    if body.name is not None:
        # Kiểm tra tên trùng với phòng khác
        conflict = db.query(Room).filter(
            Room.name == body.name,
            Room.deleted_at.is_(None),
            Room.id != room_id,
        ).first()
        if conflict:
            raise HTTPException(409, f"Phòng tên '{body.name}' đã tồn tại.")
        room.name = body.name
        updated_fields["name"] = body.name
    if body.location is not None:
        room.location = body.location
        updated_fields["location"] = body.location
    if body.capacity is not None:
        room.capacity = body.capacity
        updated_fields["capacity"] = body.capacity
    if body.status is not None:
        allowed = {"AVAILABLE", "MAINTENANCE", "DISABLED"}
        if body.status not in allowed:
            raise HTTPException(422, f"status phải là một trong: {allowed}")
        room.status = body.status
        updated_fields["status"] = body.status
    if body.image_url is not None:
        room.image_url = body.image_url
    if body.notes is not None:
        room.notes = body.notes

    db.commit()

    log_audit(
        db=db,
        correlation_id=request.headers.get("X-Correlation-ID", str(room_id)),
        action="UPDATE_ROOM",
        entity_name="ROOM",
        entity_id=str(room_id),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        result="SUCCESS",
        details={"updated": updated_fields},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return _get_active_room(room_id, db)


# ---------------------------------------------------------------------------
# DELETE /rooms/{room_id} — soft delete [ADMIN, ROOM_MANAGER]
# ---------------------------------------------------------------------------
@router.delete(
    "/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa phòng (soft delete)",
)
def delete_room(
    room_id: UUID,
    request: Request,
    current_user: User = Depends(require_role(Role.ROOM_MANAGER, Role.ADMIN)),
    db: Session = Depends(get_db),
) -> None:
    room = _get_active_room(room_id, db)

    # Kiểm tra có booking CONFIRMED trong tương lai không
    future_booking = db.query(Booking).filter(
        Booking.room_id == room_id,
        Booking.status == "CONFIRMED",
        Booking.start_time > datetime.now(timezone.utc),
    ).first()
    if future_booking:
        raise HTTPException(
            status_code=409,
            detail="Không thể xóa phòng đang có lịch đặt trong tương lai. Hủy các lịch trước.",
        )

    room.deleted_at = datetime.now(timezone.utc)
    db.commit()

    log_audit(
        db=db,
        correlation_id=request.headers.get("X-Correlation-ID", str(room_id)),
        action="DELETE_ROOM",
        entity_name="ROOM",
        entity_id=str(room_id),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        result="SUCCESS",
        details={"room_name": room.name},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )


# ---------------------------------------------------------------------------
# POST /rooms/{room_id}/equipments — thêm thiết bị vào phòng
# ---------------------------------------------------------------------------
@router.post(
    "/{room_id}/equipments",
    response_model=RoomResponse,
    summary="Thêm thiết bị vào phòng",
)
def add_equipment(
    room_id: UUID,
    body: EquipmentAdd,
    request: Request,
    current_user: User = Depends(require_role(Role.ROOM_MANAGER, Role.ADMIN)),
    db: Session = Depends(get_db),
) -> Room:
    room = _get_active_room(room_id, db)

    # Kiểm tra equipment tồn tại
    eq = db.query(Equipment).filter(Equipment.id == body.equipment_id).first()
    if not eq:
        raise HTTPException(404, "Thiết bị không tồn tại.")

    # Kiểm tra đã có chưa
    existing = db.query(RoomEquipment).filter(
        RoomEquipment.room_id == room_id,
        RoomEquipment.equipment_id == body.equipment_id,
    ).first()
    if existing:
        # Cập nhật số lượng
        existing.quantity = body.quantity
    else:
        db.add(RoomEquipment(
            room_id=room_id,
            equipment_id=body.equipment_id,
            quantity=body.quantity,
        ))
    db.commit()

    log_audit(
        db=db,
        correlation_id=request.headers.get("X-Correlation-ID", str(room_id)),
        action="ADD_EQUIPMENT",
        entity_name="ROOM",
        entity_id=str(room_id),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        result="SUCCESS",
        details={"equipment_code": eq.code, "quantity": body.quantity},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return _get_active_room(room_id, db)


# ---------------------------------------------------------------------------
# DELETE /rooms/{room_id}/equipments/{equipment_id} — bỏ thiết bị
# ---------------------------------------------------------------------------
@router.delete(
    "/{room_id}/equipments/{equipment_id}",
    response_model=RoomResponse,
    summary="Bỏ thiết bị khỏi phòng",
)
def remove_equipment(
    room_id: UUID,
    equipment_id: UUID,
    request: Request,
    current_user: User = Depends(require_role(Role.ROOM_MANAGER, Role.ADMIN)),
    db: Session = Depends(get_db),
) -> Room:
    _get_active_room(room_id, db)

    re = db.query(RoomEquipment).filter(
        RoomEquipment.room_id == room_id,
        RoomEquipment.equipment_id == equipment_id,
    ).first()
    if not re:
        raise HTTPException(404, "Thiết bị này không có trong phòng.")

    db.delete(re)
    db.commit()

    log_audit(
        db=db,
        correlation_id=request.headers.get("X-Correlation-ID", str(room_id)),
        action="REMOVE_EQUIPMENT",
        entity_name="ROOM",
        entity_id=str(room_id),
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        result="SUCCESS",
        details={"equipment_id": str(equipment_id)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return _get_active_room(room_id, db)
