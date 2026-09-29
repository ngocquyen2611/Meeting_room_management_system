import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from room_service.database import Base


def utc_now():
    return datetime.now(timezone.utc)


# ==========================================
# 1. USER & AUTHENTICATION (FR-01)
# ==========================================
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth0_user_id = Column(String(128), unique=True, nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    role = Column(String(30), nullable=False, default="EMPLOYEE")  # EMPLOYEE, ROOM_MANAGER, ADMIN
    status = Column(String(20), nullable=False, default="ACTIVE")  # ACTIVE, INACTIVE
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    bookings = relationship("Booking", back_populates="organizer")
    attendees = relationship("BookingAttendee", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


# ==========================================
# 2. ROOM & EQUIPMENT (FR-02)
# ==========================================
class Room(Base):
    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="AVAILABLE")  # AVAILABLE, MAINTENANCE, DISABLED
    image_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    # Soft delete: NULL nghĩa là đang hoạt động
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    equipments = relationship("RoomEquipment", back_populates="room", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="room")


class Equipment(Base):
    __tablename__ = "equipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)  # TV, PROJECTOR, CAMERA, MIC, WHITEBOARD
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    rooms = relationship("RoomEquipment", back_populates="equipment")


class RoomEquipment(Base):
    __tablename__ = "room_equipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipments.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    room = relationship("Room", back_populates="equipments")
    equipment = relationship("Equipment", back_populates="rooms")

    __table_args__ = (
        UniqueConstraint("room_id", "equipment_id", name="uq_room_equipment"),
    )


# ==========================================
# 3. BOOKING & ATTENDEES (FR-03, FR-04, FR-05)
# ==========================================
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="RESTRICT"), nullable=False, index=True)
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    meeting_type = Column(String(20), nullable=False, default="OFFLINE")  # OFFLINE, ONLINE, HYBRID
    meeting_link = Column(String(500), nullable=True)
    status = Column(String(30), nullable=False, default="CONFIRMED", index=True)  # CONFIRMED, CHECKED_IN, CANCELLED, AUTO_CANCELLED, COMPLETED
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(String(255), nullable=True)
    version = Column(Integer, default=1, nullable=False)  # Optimistic Locking
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    room = relationship("Room", back_populates="bookings")
    organizer = relationship("User", back_populates="bookings")
    attendees = relationship("BookingAttendee", back_populates="booking", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="booking")


class BookingAttendee(Base):
    __tablename__ = "booking_attendees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="INVITED")  # INVITED, ACCEPTED, DECLINED
    responded_at = Column(DateTime(timezone=True), nullable=True)

    booking = relationship("Booking", back_populates="attendees")
    user = relationship("User", back_populates="attendees")

    __table_args__ = (
        UniqueConstraint("booking_id", "user_id", name="uq_booking_attendee"),
    )


class BookingPolicy(Base):
    __tablename__ = "booking_policies"

    id = Column(Integer, primary_key=True, default=1)  # Singleton ID = 1
    max_booking_duration_hours = Column(Integer, default=4, nullable=False)
    max_advance_days = Column(Integer, default=30, nullable=False)
    checkin_grace_period_minutes = Column(Integer, default=15, nullable=False)
    require_checkin = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


# ==========================================
# 4. NOTIFICATION & MESSAGE QUEUE (FR-06)
# ==========================================
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True)
    type = Column(String(50), nullable=False)  # BOOKING_CREATED, CANCELLED, AUTO_CANCELLED, REMINDER
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    channel = Column(String(20), default="IN_APP", nullable=False)  # IN_APP, EMAIL
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="notifications")
    booking = relationship("Booking", back_populates="notifications")


class ProcessedEvent(Base):
    """Bảo đảm Idempotency khi nhận message từ RabbitMQ"""
    __tablename__ = "processed_events"

    event_id = Column(String(100), primary_key=True)  # RabbitMQ Message ID
    event_type = Column(String(50), nullable=False)
    processed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


# ==========================================
# 5. AUDIT LOG (FR-07, FR-08)
# ==========================================
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    correlation_id = Column(String(100), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email = Column(String(150), nullable=True)  # Snapshot email lúc thực hiện
    user_role = Column(String(30), nullable=True)   # Snapshot role lúc thực hiện
    action = Column(String(50), nullable=False, index=True)  # CREATE_BOOKING, CANCEL_BOOKING, UPDATE_ROOM...
    entity_name = Column(String(50), nullable=False, index=True)  # ROOM, BOOKING, USER, POLICY
    entity_id = Column(String(100), nullable=True)
    result = Column(String(20), nullable=False)  # SUCCESS, FAILED, FORBIDDEN
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")