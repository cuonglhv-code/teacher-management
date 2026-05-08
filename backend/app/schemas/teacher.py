"""Pydantic schemas for Teacher, Availability, and Leave."""

from datetime import date, time, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.models.teacher import ContractType, TeacherStatus


# ─── Teacher ────────────────────────────────────────────────────────────────

class TeacherBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: str = Field(..., max_length=255)
    phone: Optional[str] = None
    contract_type: ContractType
    contracted_hours: float = 0
    hourly_rate: Optional[float] = None  # HR-only
    salary: Optional[float] = None       # HR-only
    primary_centre_id: int
    status: TeacherStatus = TeacherStatus.ACTIVE
    qualifications: Optional[str] = None
    notes: Optional[str] = None


class TeacherCreate(TeacherBase):
    pass


class TeacherUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    contract_type: Optional[ContractType] = None
    contracted_hours: Optional[float] = None
    hourly_rate: Optional[float] = None
    salary: Optional[float] = None
    primary_centre_id: Optional[int] = None
    status: Optional[TeacherStatus] = None
    qualifications: Optional[str] = None
    notes: Optional[str] = None


class TeacherResponse(TeacherBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TeacherListResponse(BaseModel):
    teachers: list[TeacherResponse]
    total: int


# ─── Availability ───────────────────────────────────────────────────────────

class TeacherAvailabilityBase(BaseModel):
    day_of_week: str = Field(..., pattern=r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)$")
    start_time: time
    end_time: time
    is_available: bool = True


class TeacherAvailabilityCreate(TeacherAvailabilityBase):
    teacher_id: int


class TeacherAvailabilityResponse(TeacherAvailabilityBase):
    id: int
    teacher_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BulkAvailabilityCreate(BaseModel):
    """Set availability for multiple days at once."""
    teacher_id: int
    slots: list[TeacherAvailabilityBase]


# ─── Leave ──────────────────────────────────────────────────────────────────

class LeaveBase(BaseModel):
    start_date: date
    end_date: date
    reason: Optional[str] = None
    is_approved: bool = False


class LeaveCreate(LeaveBase):
    teacher_id: int


class LeaveResponse(LeaveBase):
    id: int
    teacher_id: int
    created_at: datetime

    model_config = {"from_attributes": True}