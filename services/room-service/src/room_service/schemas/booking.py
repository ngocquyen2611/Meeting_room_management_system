"""
schemas/booking.py — Pydantic schemas cho Booking (FR-04, FR-05)
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Booking schemas
# ---------------------------------------------------------------------------
class AttendeeIn(BaseModel):
    user_id: UUID


class BookingCreate(BaseModel):
    room_id: UUID
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    meeting_type: str = Field(default="OFFLINE")   # OFFLINE, ONLINE, HYBRID
    meeting_link: Optional[str] = Field(default=None, max_length=500)
    attendee_ids: List[UUID] = []

    @model_validator(mode="after")
    def validate_times(self) -> "BookingCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time phải sau start_time")
        return self

    @model_validator(mode="after")
    def validate_meeting_type(self) -> "BookingCreate":
        allowed = {"OFFLINE", "ONLINE", "HYBRID"}
        if self.meeting_type not in allowed:
            raise ValueError(f"meeting_type phải là một trong: {allowed}")
        return self


class BookingUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    meeting_type: Optional[str] = None
    meeting_link: Optional[str] = None
    attendee_ids: Optional[List[UUID]] = None

    @model_validator(mode="after")
    def validate_times(self) -> "BookingUpdate":
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("end_time phải sau start_time")
        return self


class BookingCancelRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=255)


class AttendeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    status: str
    responded_at: Optional[datetime] = None


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_id: UUID
    organizer_id: UUID
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    meeting_type: str
    meeting_link: Optional[str] = None
    status: str
    checked_in_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime
    attendees: List[AttendeeResponse] = []


class BookingListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_id: UUID
    title: str
    start_time: datetime
    end_time: datetime
    meeting_type: str
    status: str
    checked_in_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# User management schemas
# ---------------------------------------------------------------------------
class UserListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    auth0_user_id: str
    email: str
    name: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime


class UserRoleUpdateRequest(BaseModel):
    role: str

    @model_validator(mode="after")
    def validate_role(self) -> "UserRoleUpdateRequest":
        allowed = {"EMPLOYEE", "ROOM_MANAGER", "ADMIN"}
        if self.role not in allowed:
            raise ValueError(f"role phải là một trong: {allowed}")
        return self


class UserStatusUpdateRequest(BaseModel):
    status: str

    @model_validator(mode="after")
    def validate_status(self) -> "UserStatusUpdateRequest":
        allowed = {"ACTIVE", "INACTIVE"}
        if self.status not in allowed:
            raise ValueError(f"status phải là một trong: {allowed}")
        return self
