"""Class API routes — CRUD with status workflow."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import time

from app.db.database import get_db
from app.models.teacher import Class, ClassStatus, TimetableSlot
from app.schemas.class_room import ClassCreate, ClassUpdate, ClassResponse

router = APIRouter()

VALID_TRANSITIONS = {
    ClassStatus.PLANNED: [ClassStatus.APPROVED, ClassStatus.CANCELLED],
    ClassStatus.APPROVED: [ClassStatus.TIMETABLED, ClassStatus.CANCELLED, ClassStatus.PLANNED],
    ClassStatus.TIMETABLED: [ClassStatus.OPEN, ClassStatus.CANCELLED],
    ClassStatus.OPEN: [ClassStatus.COMPLETED, ClassStatus.CANCELLED],
    ClassStatus.COMPLETED: [],
    ClassStatus.CANCELLED: [],
}


def _validate_status_transition(current: ClassStatus, new: ClassStatus):
    if current == new:
        return
    allowed = VALID_TRANSITIONS.get(current, [])
    if new not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Cannot transition from '{current.value}' to '{new.value}'. "
                   f"Allowed transitions: {[s.value for s in allowed] or 'none'}",
        )


@router.get("/", response_model=list[ClassResponse])
async def list_classes(
    centre_id: Optional[int] = Query(None),
    status: Optional[ClassStatus] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Class)
    if centre_id:
        q = q.filter(Class.centre_id == centre_id)
    if status:
        q = q.filter(Class.status == status)
    classes = q.all()
    return [ClassResponse.model_validate(c.__dict__) for c in classes]


@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    return ClassResponse.model_validate(cls.__dict__)


@router.post("/", response_model=ClassResponse, status_code=201)
async def create_class(data: ClassCreate, db: Session = Depends(get_db)):
    cls = Class(**data.model_dump())
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return ClassResponse.model_validate(cls.__dict__)


@router.put("/{class_id}", response_model=ClassResponse)
async def update_class(class_id: int, data: ClassUpdate, db: Session = Depends(get_db)):
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    update_data = data.model_dump(exclude_unset=True)

    # Validate status transition if status is being changed
    if "status" in update_data:
        new_status = update_data["status"]
        if isinstance(new_status, str):
            new_status = ClassStatus(new_status)
        _validate_status_transition(cls.status, new_status)

    for key, value in update_data.items():
        setattr(cls, key, value)
    db.commit()
    db.refresh(cls)
    return ClassResponse.model_validate(cls.__dict__)


@router.delete("/{class_id}", status_code=204)
async def delete_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    db.delete(cls)
    db.commit()


# ─── Room Booking Validation ──────────────────────────────────────────────

@router.get("/validate/room-booking")
async def validate_room_booking(
    room_id: int,
    day_of_week: str,
    start_time: time,
    end_time: time,
    exclude_slot_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Check if a room is already booked for the given time slot."""
    q = db.query(TimetableSlot).filter(
        TimetableSlot.room_id == room_id,
        TimetableSlot.day_of_week == day_of_week,
        TimetableSlot.start_time < end_time,
        TimetableSlot.end_time > start_time,
    )
    if exclude_slot_id:
        q = q.filter(TimetableSlot.id != exclude_slot_id)
    conflicts = q.all()
    return {
        "available": len(conflicts) == 0,
        "conflicts": [{"slot_id": s.id, "class_id": s.class_id} for s in conflicts],
    }