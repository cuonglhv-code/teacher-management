"""Teacher and related database models."""

import enum
from datetime import date, time, datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, Date, Time, Boolean,
    ForeignKey, Enum as SAEnum, Text, DateTime, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class ContractType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"


class TeacherStatus(str, enum.Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"
    ONBOARDING = "onboarding"


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)

    contract_type = Column(SAEnum(ContractType), nullable=False)
    contracted_hours = Column(Float, nullable=False, default=0)
    hourly_rate = Column(Float, nullable=True)  # HR-only field
    salary = Column(Float, nullable=True)  # HR-only field (monthly for FT)

    # Workload tracking fields
    under_utilized_weeks = Column(Integer, default=0)
    is_under_utilized = Column(Boolean, default=False)
    
    # Contract renewal fields
    contract_end_date = Column(Date, nullable=True)
    renewal_status = Column(String(50), nullable=True)  # 'pending', 'approved', 'not_applicable'

    primary_centre_id = Column(Integer, ForeignKey("centres.id"), nullable=False)
    status = Column(SAEnum(TeacherStatus), default=TeacherStatus.ACTIVE)

    qualifications = Column(Text, nullable=True)  # JSON list or comma-separated
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    primary_centre = relationship("Centre", back_populates="teachers")
    availability = relationship("TeacherAvailability", back_populates="teacher",
                                cascade="all, delete-orphan")
    leaves = relationship("Leave", back_populates="teacher", cascade="all, delete-orphan")


class Centre(Base):
    __tablename__ = "centres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    teachers = relationship("Teacher", back_populates="primary_centre")
    rooms = relationship("Room", back_populates="centre", cascade="all, delete-orphan")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(Integer, ForeignKey("centres.id"), nullable=False)
    name = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False, default=1)
    has_projector = Column(Boolean, default=False)
    has_whiteboard = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    centre = relationship("Centre", back_populates="rooms")

    __table_args__ = (
        UniqueConstraint("centre_id", "name", name="uq_room_per_centre"),
    )


class ClassStatus(str, enum.Enum):
    PLANNED = "planned"
    APPROVED = "approved"
    TIMETABLED = "timetabled"
    OPEN = "open"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(Integer, ForeignKey("centres.id"), nullable=False)
    name = Column(String(200), nullable=False)
    level = Column(String(50), nullable=True)  # e.g. A1, B2, IELTS
    required_teacher_qualification = Column(String(100), nullable=True)

    preferred_day = Column(String(20), nullable=True)  # Monday, Tuesday, etc.
    preferred_start_time = Column(Time, nullable=True)
    preferred_end_time = Column(Time, nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    status = Column(SAEnum(ClassStatus), default=ClassStatus.PLANNED)
    max_students = Column(Integer, default=1)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    centre = relationship("Centre")


class TeacherAvailability(Base):
    __tablename__ = "teacher_availability"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    day_of_week = Column(String(20), nullable=False)  # Monday..Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_available = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("Teacher", back_populates="availability")

    __table_args__ = (
        UniqueConstraint("teacher_id", "day_of_week", "start_time",
                         name="uq_teacher_availability_slot"),
    )


class Leave(Base):
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String(255), nullable=True)
    is_approved = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("Teacher", back_populates="leaves")


class TimetableSlot(Base):
    __tablename__ = "timetable_slots"

    id = Column(Integer, primary_key=True, index=True)
    draft_id = Column(Integer, ForeignKey("timetable_drafts.id"), nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    day_of_week = Column(String(20), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_draft = Column(Boolean, default=True)  # human approval gate

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DraftStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class TimetableDraft(Base):
    """A generated draft timetable for a centre, containing many slots."""
    __tablename__ = "timetable_drafts"

    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(Integer, ForeignKey("centres.id"), nullable=False)
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)
    status = Column(SAEnum(DraftStatus), default=DraftStatus.DRAFT)
    conflict_report = Column(Text, nullable=True)  # JSON: list of conflict strings
    unassigned_report = Column(Text, nullable=True)  # JSON: [{class_id, reason}, ...]
    total_slots = Column(Integer, default=0)
    total_unassigned = Column(Integer, default=0)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)


class HeadcountRequestStatus(str, enum.Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    FILLED = "filled"
    CANCELLED = "cancelled"


class HeadcountRequest(Base):
    __tablename__ = "headcount_requests"

    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(Integer, ForeignKey("centres.id"), nullable=False)
    contract_type = Column(SAEnum(ContractType), nullable=False)
    hours_per_week = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(SAEnum(HeadcountRequestStatus), default=HeadcountRequestStatus.OPEN)
    requested_by = Column(String(100), nullable=True)
    approved_by = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ForecastPeriod(Base):
    __tablename__ = "forecast_periods"

    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(Integer, ForeignKey("centres.id"), nullable=False)
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)
    projected_demand_hours = Column(Float, nullable=True)
    available_ft_hours = Column(Float, nullable=True)
    available_pt_hours = Column(Float, nullable=True)
    unassigned_ft_rate = Column(Float, nullable=True)
    available_teacher_rate = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)