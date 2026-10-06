"""
schemas/room.py — Pydantic schemas cho Room & Equipment (FR-02, FR-03)
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Equipment schemas
# ---------------------------------------------------------------------------
class EquipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: Optional[str] = None


class RoomEquipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    equipment: EquipmentResponse
    quantity: int


class EquipmentAdd(BaseModel):
    equipment_id: UUID
    quantity: int = Field(default=1, ge=1)


# ---------------------------------------------------------------------------
# Room schemas
# ---------------------------------------------------------------------------
class RoomCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=100)
    capacity: int = Field(..., ge=1)
    status: str = Field(default="AVAILABLE")
    image_url: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = None

    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"AVAILABLE", "MAINTENANCE", "DISABLED"}
        if v not in allowed:
            raise ValueError(f"status phải là một trong: {allowed}")
        return v


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    location: Optional[str] = Field(default=None, min_length=1, max_length=100)
    capacity: Optional[int] = Field(default=None, ge=1)
    status: Optional[str] = None
    image_url: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = None


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    location: str
    capacity: int
    status: str
    image_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    equipments: List[RoomEquipmentResponse] = []


class RoomListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    location: str
    capacity: int
    status: str
    image_url: Optional[str] = None
    equipments: List[RoomEquipmentResponse] = []


# ---------------------------------------------------------------------------
# Search schema (FR-03)
# ---------------------------------------------------------------------------
class RoomSearchParams(BaseModel):
    """Query parameters cho tìm kiếm phòng trống."""
    date: Optional[str] = None           # YYYY-MM-DD
    start_time: Optional[str] = None     # HH:MM
    end_time: Optional[str] = None       # HH:MM
    min_capacity: Optional[int] = Field(default=None, ge=1)
    location: Optional[str] = None
    equipment_codes: Optional[str] = None  # "TV,PROJECTOR"
