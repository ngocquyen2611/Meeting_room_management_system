from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class Role(str, Enum):
    EMPLOYEE = "EMPLOYEE"
    ROOM_MANAGER = "ROOM_MANAGER"
    ADMIN = "ADMIN"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    auth0_user_id: str
    email: str
    name: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime


class UserRoleUpdate(BaseModel):
    role: Role
