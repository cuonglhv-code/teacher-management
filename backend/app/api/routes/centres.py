"""Centre API routes — CRUD."""

from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.models.teacher import Centre, Teacher, TeacherStatus
from app.schemas.class_room import CentreCreate, CentreUpdate, CentreResponse

router = APIRouter()


@router.get("/{centre_id}/utilization")
async def get_centre_utilization(
    centre_id: int,
    week_start: date = Query(...),
    week_end: date = Query(...),
    db: Session = Depends(get_db),
):
    """Get centre utilization summary stats."""
    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    
    # Get all active teachers at this centre
    teachers = db.query(Teacher).filter(
        Teacher.primary_centre_id == centre_id,
        Teacher.status == TeacherStatus.ACTIVE,
    ).all()
    
    under_utilized_count = 0
    overload_incidents = 0
    
    for teacher in teachers:
        # Calculate utilization for this week (simplified - using workload endpoint logic)
        contracted_hours = teacher.contracted_hours or 0
        if teacher.is_under_utilized:
            under_utilized_count += 1
        if teacher.under_utilized_weeks >= 2:
            under_utilized_count += 1
        
        # Check for overload (assigned > contracted)
        # This would need actual timetable slot calculation
        # For now, just track the flag
    
    return {
        "centre_id": centre_id,
        "week_start": week_start,
        "week_end": week_end,
        "total_teachers": len(teachers),
        "under_utilized_teachers": under_utilized_count,
        "under_utilization_rate": round((under_utilized_count / len(teachers) * 100) if teachers else 0, 2),
        "overload_incidents": overload_incidents,
    }


@router.get("/", response_model=list[CentreResponse])
async def list_centres(db: Session = Depends(get_db)):
    centres = db.query(Centre).all()
    return [CentreResponse.model_validate(c.__dict__) for c in centres]


@router.get("/{centre_id}", response_model=CentreResponse)
async def get_centre(centre_id: int, db: Session = Depends(get_db)):
    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    return CentreResponse.model_validate(centre.__dict__)


@router.post("/", response_model=CentreResponse, status_code=201)
async def create_centre(data: CentreCreate, db: Session = Depends(get_db)):
    existing = db.query(Centre).filter(Centre.code == data.code).first()
    if existing:
        raise HTTPException(status_code=409, detail="Centre code already exists")
    centre = Centre(**data.model_dump())
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return CentreResponse.model_validate(centre.__dict__)


@router.put("/{centre_id}", response_model=CentreResponse)
async def update_centre(centre_id: int, data: CentreUpdate, db: Session = Depends(get_db)):
    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(centre, key, value)
    db.commit()
    db.refresh(centre)
    return CentreResponse.model_validate(centre.__dict__)


@router.delete("/{centre_id}", status_code=204)
async def delete_centre(centre_id: int, db: Session = Depends(get_db)):
    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    db.delete(centre)
    db.commit()