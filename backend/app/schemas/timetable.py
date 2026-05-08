"""Pydantic schemas for TimetableDraft and TimetableSlot management."""

from datetime import date, time, datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─── TimetableDraft ─────────────────────────────────────────────────────────

class DraftResponse(BaseModel):
    id: int
    centre_id: int
    week_start: date
    week_end: date
    status: str
    conflict_report: Optional[str] = None
    unassigned_report: Optional[str] = None
    total_slots: int = 0
    total_unassigned: int = 0
    created_by: Optional[str] = None
    created_at: datetime
    published_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── TimetableSlot ──────────────────────────────────────────────────────────

class SlotResponse(BaseModel):
    id: int
    draft_id: Optional[int] = None
    class_id: int
    teacher_id: Optional[int] = None
    room_id: Optional[int] = None
    day_of_week: str
    start_time: time
    end_time: time
    is_draft: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SlotOverrideRequest(BaseModel):
    teacher_id: Optional[int] = None
    room_id: Optional[int] = None
    day_of_week: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class GenerateDraftInput(BaseModel):
    centre_id: int
    week_start: date
    week_end: date
    created_by: Optional[str] = None