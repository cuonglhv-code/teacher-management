"""Teacher API routes — CRUD + Availability + Leave with role-based access."""

from datetime import date, datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.models.teacher import Teacher, TeacherAvailability, Leave, TimetableSlot, TimetableDraft, DraftStatus, TeacherStatus
from app.schemas.teacher import (
    TeacherCreate, TeacherUpdate, TeacherResponse, TeacherListResponse,
    TeacherAvailabilityCreate, TeacherAvailabilityResponse, BulkAvailabilityCreate,
    LeaveCreate, LeaveResponse,
)

router = APIRouter()


def _calculate_hours_from_time(start_time, end_time):
    """Calculate hours between two time objects."""
    start_minutes = start_time.hour * 60 + start_time.minute
    end_minutes = end_time.hour * 60 + end_time.minute
    return (end_minutes - start_minutes) / 60.0


@router.get("/{teacher_id}/workload")
async def get_teacher_workload(
    teacher_id: int,
    week_start: date = Query(...),
    week_end: date = Query(...),
    db: Session = Depends(get_db),
):
    """Get teacher workload for a specific week."""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Get contracted hours
    contracted_hours = teacher.contracted_hours or 0
    
    # Calculate actual assigned hours from published timetable slots
    assigned_hours = 0
    slots = db.query(TimetableSlot).join(TimetableDraft).filter(
        TimetableSlot.teacher_id == teacher_id,
        TimetableDraft.status == DraftStatus.PUBLISHED,
        TimetableDraft.week_start <= week_end,
        TimetableDraft.week_end >= week_start,
        TimetableSlot.is_draft == False,
    ).all()
    
    for slot in slots:
        hours = _calculate_hours_from_time(slot.start_time, slot.end_time)
        assigned_hours += hours
    
    # Calculate utilization percentage
    utilization = 0
    if contracted_hours > 0:
        utilization = (assigned_hours / contracted_hours) * 100
    
    return {
        "teacher_id": teacher_id,
        "week_start": week_start,
        "week_end": week_end,
        "contracted_hours": contracted_hours,
        "assigned_hours": round(assigned_hours, 2),
        "utilization_percentage": round(utilization, 2),
    }


ROLE_HR = "hr"
ROLE_ACADEMIC = "academic_manager"


def _mask_salary_fields(teacher: Teacher, role: str) -> dict:
    """Return teacher dict; mask salary/hourly_rate for non-HR roles."""
    data = {
        "id": teacher.id,
        "first_name": teacher.first_name,
        "last_name": teacher.last_name,
        "email": teacher.email,
        "phone": teacher.phone,
        "contract_type": teacher.contract_type.value if teacher.contract_type else None,
        "contract_type": teacher.contract_type,
        "contracted_hours": teacher.contracted_hours,
        "hourly_rate": teacher.hourly_rate if role == ROLE_HR else None,
        "salary": teacher.salary if role == ROLE_HR else None,
        "primary_centre_id": teacher.primary_centre_id,
        "status": teacher.status,
        "qualifications": teacher.qualifications,
        "notes": teacher.notes,
        "created_at": teacher.created_at,
        "updated_at": teacher.updated_at,
    }
    return data


# ─── CRUD ───────────────────────────────────────────────────────────────────

@router.get("/", response_model=TeacherListResponse)
async def list_teachers(
    role: str = Query("academic_manager", description="User role for RBAC"),
    centre_id: Optional[int] = Query(None),
    contract_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List teachers with optional filters. Masks salary fields for non-HR."""
    q = db.query(Teacher)
    if centre_id:
        q = q.filter(Teacher.primary_centre_id == centre_id)
    if contract_type:
        q = q.filter(Teacher.contract_type == contract_type)
    if status:
        q = q.filter(Teacher.status == status)
    teachers = q.all()
    return TeacherListResponse(
        teachers=[TeacherResponse.model_validate(_mask_salary_fields(t, role)) for t in teachers],
        total=len(teachers),
    )


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: int,
    role: str = Query("academic_manager"),
    db: Session = Depends(get_db),
):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return TeacherResponse.model_validate(_mask_salary_fields(teacher, role))


@router.post("/", response_model=TeacherResponse, status_code=201)
async def create_teacher(
    data: TeacherCreate,
    role: str = Query("academic_manager"),
    db: Session = Depends(get_db),
):
    existing = db.query(Teacher).filter(Teacher.email == data.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")
    teacher = Teacher(**data.model_dump())
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return TeacherResponse.model_validate(_mask_salary_fields(teacher, role))


@router.put("/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: int,
    data: TeacherUpdate,
    role: str = Query("academic_manager"),
    db: Session = Depends(get_db),
):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(teacher, key, value)
    db.commit()
    db.refresh(teacher)
    return TeacherResponse.model_validate(_mask_salary_fields(teacher, role))


@router.delete("/{teacher_id}", status_code=204)
async def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    db.delete(teacher)
    db.commit()


# ─── Availability ───────────────────────────────────────────────────────────

@router.get("/{teacher_id}/availability", response_model=list[TeacherAvailabilityResponse])
async def list_availability(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    slots = db.query(TeacherAvailability).filter(
        TeacherAvailability.teacher_id == teacher_id
    ).all()
    return [TeacherAvailabilityResponse.model_validate(s.__dict__) for s in slots]


@router.post("/{teacher_id}/availability/bulk", status_code=201)
async def bulk_set_availability(
    teacher_id: int,
    data: BulkAvailabilityCreate,
    db: Session = Depends(get_db),
):
    """Replace all availability slots for a teacher with the provided set."""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Delete existing slots
    db.query(TeacherAvailability).filter(
        TeacherAvailability.teacher_id == teacher_id
    ).delete()
    # Insert new slots
    for slot in data.slots:
        db.add(TeacherAvailability(
            teacher_id=teacher_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
            is_available=slot.is_available,
        ))
    db.commit()
    return {"message": "Availability updated", "teacher_id": teacher_id, "slots_count": len(data.slots)}


@router.delete("/{teacher_id}/availability", status_code=204)
async def clear_availability(teacher_id: int, db: Session = Depends(get_db)):
    db.query(TeacherAvailability).filter(
        TeacherAvailability.teacher_id == teacher_id
    ).delete()
    db.commit()


# ─── Leave ──────────────────────────────────────────────────────────────────

@router.get("/{teacher_id}/leaves", response_model=list[LeaveResponse])
async def list_leaves(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    leaves = db.query(Leave).filter(Leave.teacher_id == teacher_id).all()
    return [LeaveResponse.model_validate(l.__dict__) for l in leaves]


@router.post("/{teacher_id}/leaves", response_model=LeaveResponse, status_code=201)
async def create_leave(teacher_id: int, data: LeaveCreate, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    leave = Leave(teacher_id=teacher_id, **data.model_dump(exclude={"teacher_id"}))
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return LeaveResponse.model_validate(leave.__dict__)


@router.delete("/leaves/{leave_id}", status_code=204)
async def delete_leave(leave_id: int, db: Session = Depends(get_db)):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    db.delete(leave)
    db.commit()


# ─── Contract Renewal & Exit Management ─────────────────────────────────


@router.put("/{teacher_id}/contract-renewal")
async def update_contract_renewal(
    teacher_id: int,
    contract_end_date: date,
    renewal_status: str,  # 'pending', 'approved', 'not_applicable'
    db: Session = Depends(get_db),
):
    """Update contract end date and renewal status."""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    teacher.contract_end_date = contract_end_date
    teacher.renewal_status = renewal_status
    db.commit()
    db.refresh(teacher)
    
    return {
        "teacher_id": teacher.id,
        "contract_end_date": teacher.contract_end_date,
        "renewal_status": teacher.renewal_status,
    }


@router.put("/{teacher_id}/resign")
async def resign_teacher(
    teacher_id: int,
    resignation_date: date = Query(...),
    db: Session = Depends(get_db),
):
    """Mark teacher as resigned and run impact assessment."""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Update status to resigned
    teacher.status = TeacherStatus.TERMINATED
    db.commit()
    
    # Impact assessment: find future timetable slots
    future_slots = db.query(TimetableSlot).join(TimetableDraft).filter(
        TimetableSlot.teacher_id == teacher_id,
        TimetableDraft.status == DraftStatus.PUBLISHED,
        TimetableDraft.week_start >= resignation_date,
    ).all()
    
    affected_classes = []
    for slot in future_slots:
        # Mark slot for reassignment
        slot.teacher_id = None
        affected_classes.append({
            "slot_id": slot.id,
            "class_id": slot.class_id,
            "day": slot.day_of_week,
            "time": f"{slot.start_time}-{slot.end_time}",
        })
    
    db.commit()
    
    return {
        "teacher_id": teacher_id,
        "status": "resigned",
        "resignation_date": resignation_date,
        "affected_slots_count": len(future_slots),
        "affected_classes": affected_classes,
        "message": "Teacher marked as resigned. Future slots require reassignment.",
    }


def check_contract_expiry_and_notify():
    """Daily check for contracts expiring within 60 days."""
    from datetime import date, timedelta
    from sqlalchemy.orm import Session
    from app.db.database import SessionLocal
    
    db = SessionLocal()
    try:
        sixty_days = date.today() + timedelta(days=60)
        expiring = db.query(Teacher).filter(
            Teacher.contract_end_date.isnot(None),
            Teacher.contract_end_date <= sixty_days,
            Teacher.contract_end_date >= date.today(),
            Teacher.status == TeacherStatus.ACTIVE
        ).all()
        
        for teacher in expiring:
            days_left = (teacher.contract_end_date - date.today()).days
            # Create renewal task (simplified: print to log)
            print(f"RENEWAL TASK: Teacher {teacher.id} ({teacher.first_name} {teacher.last_name}) "
                  f"contract expires in {days_left} days. Notify Academic Manager.")
            
            # Update renewal status if not already set
            if not teacher.renewal_status:
                teacher.renewal_status = 'pending'
        
        db.commit()
    except Exception as e:
        print(f"Error in contract expiry check: {e}")
        db.rollback()
    finally:
        db.close()
