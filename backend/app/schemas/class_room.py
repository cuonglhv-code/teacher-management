"""Pydantic schemas for Centre, Room, and Class."""

from typing import Optional
from datetime import datetime, time
from pydantic import BaseModel, Field

from app.models.teacher import ClassStatus


# ─── Centre ────────────────────────────────────────────────────────────────

class CentreBase(BaseModel):
    name: str = Field(..., max_length=200)
    code: str = Field(..., max_length=10)
    address: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True


class CentreCreate(CentreBase):
    pass


class CentreUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class CentreResponse(CentreBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Room ──────────────────────────────────────────────────────────────────

class RoomBase(BaseModel):
    centre_id: int
    name: str = Field(..., max_length=100)
    capacity: int = 1
    has_projector: bool = False
    has_whiteboard: bool = True
    notes: Optional[str] = None


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    has_projector: Optional[bool] = None
    has_whiteboard: Optional[bool] = None
    notes: Optional[str] = None


class RoomResponse(RoomBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Class ─────────────────────────────────────────────────────────────────

class ClassBase(BaseModel):
    centre_id: int
    name: str = Field(..., max_length=200)
    level: Optional[str] = None
    required_teacher_qualification: Optional[str] = None
    preferred_day: Optional[str] = None
    preferred_start_time: Optional[time] = None
    preferred_end_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    max_students: int = 1
    notes: Optional[str] = None


class ClassCreate(ClassBase):
    pass


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[str] = None
    required_teacher_qualification: Optional[str] = None
    preferred_day: Optional[str] = None
    preferred_start_time: Optional[time] = None
    preferred_end_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    status: Optional[ClassStatus] = None
    max_students: Optional[int] = None
    notes: Optional[str] = None


class ClassResponse(ClassBase):
    id: int
    status: ClassStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}