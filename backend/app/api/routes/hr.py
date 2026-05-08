"""HR API routes — alerts, headcount requests, and contract management."""

from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.models.teacher import (
    Teacher, TeacherStatus, HeadcountRequest, HeadcountRequestStatus,
    ContractType, Centre
)

router = APIRouter()


@router.get("/alerts")
async def get_hr_alerts(
    centre_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Get all active HR alerts."""
    alerts = []
    
    # 1. Check for under-utilized teachers (2+ consecutive weeks)
    teachers_query = db.query(Teacher)
    if centre_id:
        teachers_query = teachers_query.filter(Teacher.primary_centre_id == centre_id)
    
    under_utilized = teachers_query.filter(
        Teacher.is_under_utilized == True,
        Teacher.under_utilized_weeks >= 2
    ).all()
    
    for t in under_utilized:
        alerts.append({
            "type": "under_utilization",
            "severity": "medium",
            "teacher_id": t.id,
            "teacher_name": f"{t.first_name} {t.last_name}",
            "centre_id": t.primary_centre_id,
            "message": f"Teacher under-utilized for {t.under_utilized_weeks} consecutive weeks",
            "weeks": t.under_utilized_weeks,
        })
    
    # 2. Check for contracts expiring within 60 days
    sixty_days_from_now = date.today() + timedelta(days=60)
    expiring_contracts = teachers_query.filter(
        Teacher.contract_end_date.isnot(None),
        Teacher.contract_end_date <= sixty_days_from_now,
        Teacher.contract_end_date >= date.today(),
        Teacher.status == TeacherStatus.ACTIVE
    ).all()
    
    for t in expiring_contracts:
        days_until_expiry = (t.contract_end_date - date.today()).days
        alerts.append({
            "type": "contract_expiry",
            "severity": "high" if days_until_expiry < 30 else "medium",
            "teacher_id": t.id,
            "teacher_name": f"{t.first_name} {t.last_name}",
            "centre_id": t.primary_centre_id,
            "message": f"Contract expires in {days_until_expiry} days",
            "expiry_date": t.contract_end_date,
            "days_remaining": days_until_expiry,
        })
    
    # 3. Check for open headcount requests
    requests_query = db.query(HeadcountRequest)
    if centre_id:
        requests_query = requests_query.filter(HeadcountRequest.centre_id == centre_id)
    
    open_requests = requests_query.filter(
        HeadcountRequest.status == HeadcountRequestStatus.OPEN
    ).all()
    
    for r in open_requests:
        alerts.append({
            "type": "open_headcount_request",
            "severity": "low",
            "request_id": r.id,
            "centre_id": r.centre_id,
            "message": f"Open headcount request for {r.contract_type.value if r.contract_type else 'unknown'} - {r.hours_per_week}h/week",
            "hours_per_week": r.hours_per_week,
            "contract_type": r.contract_type.value if r.contract_type else None,
        })
    
    return {
        "total_alerts": len(alerts),
        "alerts": alerts,
    }


@router.get("/headcount-requests", response_model=List[dict])
async def list_headcount_requests(
    centre_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List headcount requests with optional filters."""
    q = db.query(HeadcountRequest)
    if centre_id:
        q = q.filter(HeadcountRequest.centre_id == centre_id)
    if status:
        q = q.filter(HeadcountRequest.status == status)
    
    requests = q.order_by(HeadcountRequest.created_at.desc()).all()
    
    return [
        {
            "id": r.id,
            "centre_id": r.centre_id,
            "centre_name": r.centre.name if r.centre else None,
            "contract_type": r.contract_type.value if r.contract_type else None,
            "hours_per_week": r.hours_per_week,
            "reason": r.reason,
            "status": r.status.value if r.status else None,
            "requested_by": r.requested_by,
            "approved_by": r.approved_by,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        for r in requests
    ]


@router.put("/headcount-requests/{request_id}/approve")
async def approve_headcount_request(
    request_id: int,
    approved_by: str = Query(...),
    db: Session = Depends(get_db),
):
    """Approve a headcount request."""
    req = db.query(HeadcountRequest).filter(HeadcountRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Headcount request not found")
    if req.status != HeadcountRequestStatus.OPEN:
        raise HTTPException(status_code=422, detail=f"Request is already {req.status}")
    
    req.status = HeadcountRequestStatus.APPROVED
    req.approved_by = approved_by
    req.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Headcount request approved", "request_id": request_id}


@router.put("/headcount-requests/{request_id}/reject")
async def reject_headcount_request(
    request_id: int,
    db: Session = Depends(get_db),
):
    """Reject/cancel a headcount request."""
    req = db.query(HeadcountRequest).filter(HeadcountRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Headcount request not found")
    
    req.status = HeadcountRequestStatus.CANCELLED
    req.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Headcount request rejected", "request_id": request_id}


@router.post("/headcount-requests/{request_id}/mark-filled")
async def mark_request_filled(
    request_id: int,
    db: Session = Depends(get_db),
):
    """Mark a headcount request as filled."""
    req = db.query(HeadcountRequest).filter(HeadcountRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Headcount request not found")
    
    req.status = HeadcountRequestStatus.FILLED
    req.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Headcount request marked as filled", "request_id": request_id}