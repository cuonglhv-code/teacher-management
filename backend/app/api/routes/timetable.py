"""Timetable API routes — generate drafts, override slots, publish."""

import json
import logging
from datetime import date, time
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.teacher import (
    Centre, Teacher, TeacherAvailability, Leave, Room, Class,
    ClassStatus, TimetableSlot, TimetableDraft, DraftStatus,
)
from app.schemas.timetable import (
    DraftResponse, SlotResponse, SlotOverrideRequest, GenerateDraftInput,
)
from app.scheduling.engine import (
    TeacherSlot, ClassToSchedule, RoomInfo, ScheduleInput, run_schedule,
)

logger = logging.getLogger(__name__)
router = APIRouter()

ROLE_ACADEMIC = "academic_manager"


def _require_role(role: str):
    if role != ROLE_ACADEMIC:
        raise HTTPException(status_code=403, detail="Only Academic Manager can perform this action")


# ─── POST /generate-draft ──────────────────────────────────────────────────

@router.post("/generate-draft", response_model=dict, status_code=201)
async def generate_draft(
    inp: GenerateDraftInput,
    role: str = Query(ROLE_ACADEMIC),
    db: Session = Depends(get_db),
):
    """Run the scheduling engine for a centre and date range. Returns draft ID."""
    _require_role(role)

    centre = db.query(Centre).filter(Centre.id == inp.centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")

    # ── 1. Fetch approved classes for this centre ──────────────────────
    db_classes = db.query(Class).filter(
        Class.centre_id == inp.centre_id,
        Class.status == ClassStatus.APPROVED,
    ).all()
    if not db_classes:
        raise HTTPException(status_code=400, detail="No approved classes found for this centre")

    # ── 2. Fetch active teachers with availability (excluding leave) ───
    db_teachers = db.query(Teacher).filter(
        Teacher.primary_centre_id == inp.centre_id,
        Teacher.status == "active",
    ).all()

    # Build a set of teacher_ids on leave during the target week
    leave_tids = set()
    for t in db_teachers:
        leaves = db.query(Leave).filter(
            Leave.teacher_id == t.id,
            Leave.is_approved == True,
            Leave.start_date <= inp.week_end,
            Leave.end_date >= inp.week_start,
        ).all()
        if leaves:
            leave_tids.add(t.id)

    teacher_slots: list[TeacherSlot] = []
    for t in db_teachers:
        if t.id in leave_tids:
            continue  # skip teachers on leave
        avail_rows = db.query(TeacherAvailability).filter(
            TeacherAvailability.teacher_id == t.id,
            TeacherAvailability.is_available == True,
        ).all()
        for av in avail_rows:
            teacher_slots.append(TeacherSlot(
                teacher_id=t.id,
                contract_type=t.contract_type.value if t.contract_type else "full_time",
                contracted_hours=t.contracted_hours or 0,
                primary_centre_id=t.primary_centre_id,
                qualifications=t.qualifications or "",
                day_of_week=av.day_of_week,
                start_time=av.start_time,
                end_time=av.end_time,
                is_available=True,
            ))

    # ── 3. Fetch rooms for this centre ─────────────────────────────────
    db_rooms = db.query(Room).filter(Room.centre_id == inp.centre_id).all()
    room_infos = [RoomInfo(id=r.id, centre_id=r.centre_id, name=r.name, capacity=r.capacity) for r in db_rooms]

    # ── 4. Convert to engine input ─────────────────────────────────────
    class_list = [
        ClassToSchedule(
            id=c.id,
            name=c.name,
            centre_id=c.centre_id,
            max_students=c.max_students or 1,
            required_qualification=c.required_teacher_qualification or "",
            preferred_day=c.preferred_day,
            preferred_start_time=c.preferred_start_time,
            preferred_end_time=c.preferred_end_time,
            duration_minutes=c.duration_minutes or 90,
            status=c.status.value if c.status else "approved",
        )
        for c in db_classes
    ]

    schedule_inp = ScheduleInput(classes=class_list, teachers=teacher_slots, rooms=room_infos)
    result = run_schedule(schedule_inp)

    # ── 5. Persist the draft ───────────────────────────────────────────
    draft = TimetableDraft(
        centre_id=inp.centre_id,
        week_start=inp.week_start,
        week_end=inp.week_end,
        status=DraftStatus.DRAFT,
        conflict_report=json.dumps(result.conflict_report.details) if result.conflict_report.details else None,
        unassigned_report=json.dumps([{"class_id": u.class_id, "reason": u.reason} for u in result.unassigned]) if result.unassigned else None,
        total_slots=len(result.slots),
        total_unassigned=len(result.unassigned),
        created_by=inp.created_by,
    )
    db.add(draft)
    db.flush()  # get draft.id

    # ── 6. Persist the slots ───────────────────────────────────────────
    for s in result.slots:
        db_slot = TimetableSlot(
            draft_id=draft.id,
            class_id=s.class_id,
            teacher_id=s.teacher_id,
            room_id=s.room_id,
            day_of_week=s.day_of_week,
            start_time=s.start_time,
            end_time=s.end_time,
            is_draft=True,
        )
        db.add(db_slot)

    db.commit()
    db.refresh(draft)

    return {
        "draft_id": draft.id,
        "total_slots": draft.total_slots,
        "total_unassigned": draft.total_unassigned,
        "conflict_count": result.conflict_report.total_conflicts,
        "stats": result.stats,
    }


# ─── GET /drafts/{centre_id} ───────────────────────────────────────────────

@router.get("/drafts/{centre_id}", response_model=dict)
async def get_current_draft(
    centre_id: int,
    db: Session = Depends(get_db),
):
    """Return the current (latest) draft timetable with conflict details for a centre."""
    draft = db.query(TimetableDraft).filter(
        TimetableDraft.centre_id == centre_id,
    ).order_by(TimetableDraft.created_at.desc()).first()
    if not draft:
        raise HTTPException(status_code=404, detail="No draft found for this centre")

    slots = db.query(TimetableSlot).filter(
        TimetableSlot.draft_id == draft.id,
    ).all()

    return {
        "draft": DraftResponse.model_validate(draft.__dict__).model_dump(),
        "slots": [SlotResponse.model_validate(s.__dict__).model_dump() for s in slots],
        "conflict_report": json.loads(draft.conflict_report) if draft.conflict_report else [],
        "unassigned_report": json.loads(draft.unassigned_report) if draft.unassigned_report else [],
    }


# ─── PUT /slots/{slot_id}/override ─────────────────────────────────────────

@router.put("/slots/{slot_id}/override", response_model=SlotResponse)
async def override_slot(
    slot_id: int,
    override: SlotOverrideRequest,
    role: str = Query(ROLE_ACADEMIC),
    db: Session = Depends(get_db),
):
    """Override teacher, room, or time for a specific slot (Academic Manager only)."""
    _require_role(role)

    slot = db.query(TimetableSlot).filter(TimetableSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    # Check the parent draft is still draft
    draft = db.query(TimetableDraft).filter(TimetableDraft.id == slot.draft_id).first()
    if draft and draft.status != DraftStatus.DRAFT:
        raise HTTPException(status_code=422, detail="Cannot override a slot in a published/cancelled draft")

    update_data = override.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(slot, key, value)

    db.commit()
    db.refresh(slot)
    return SlotResponse.model_validate(slot.__dict__)


# ─── POST /publish/{draft_id} ──────────────────────────────────────────────

@router.post("/publish/{draft_id}", response_model=dict)
async def publish_draft(
    draft_id: int,
    role: str = Query(ROLE_ACADEMIC),
    db: Session = Depends(get_db),
):
    """Approve a draft: mark slots as published, set classes as Timetabled."""
    _require_role(role)

    draft = db.query(TimetableDraft).filter(TimetableDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != DraftStatus.DRAFT:
        raise HTTPException(status_code=422, detail=f"Draft is already '{draft.status.value}'")

    # 1. Find all slots for this draft
    slots = db.query(TimetableSlot).filter(TimetableSlot.draft_id == draft_id).all()
    if not slots:
        raise HTTPException(status_code=400, detail="No slots in this draft to publish")

    # 2. Mark slots as published (is_draft = False)
    for s in slots:
        s.is_draft = False

    # 3. Mark all classes in the draft as Timetabled
    class_ids = {s.class_id for s in slots}
    for cid in class_ids:
        cls = db.query(Class).filter(Class.id == cid).first()
        if cls and cls.status == ClassStatus.APPROVED:
            cls.status = ClassStatus.TIMETABLED

    # 4. Update draft status
    draft.status = DraftStatus.PUBLISHED
    from datetime import datetime as dt
    draft.published_at = dt.utcnow()

    db.commit()

    return {
        "draft_id": draft_id,
        "status": "published",
        "slots_published": len(slots),
        "classes_timetabled": len(class_ids),
    }