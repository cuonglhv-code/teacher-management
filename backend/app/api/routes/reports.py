"""Reporting API routes — KPIs, metrics, and CSV export."""

from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.models.teacher import (
    Teacher, TeacherStatus, ContractType, Class, ClassStatus,
    TimetableSlot, TimetableDraft, DraftStatus, Centre, ForecastPeriod
)
import csv
import io

router = APIRouter()


@router.get("/kpi/fill-rate")
async def get_fill_rate(
    centre_id: Optional[int] = Query(None),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    """Calculate fill rate: percentage of approved classes that got timetabled."""
    q = db.query(Class).filter(
        Class.status.in_([ClassStatus.APPROVED, ClassStatus.TIMETABLED]),
        Class.created_at >= start_date,
        Class.created_at <= end_date,
    )
    if centre_id:
        q = q.filter(Class.centre_id == centre_id)
    
    classes = q.all()
    total = len(classes)
    timetabled = sum(1 for c in classes if c.status == ClassStatus.TIMETABLED)
    
    fill_rate = (timetabled / total * 100) if total > 0 else 0
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_classes": total,
        "timetabled_classes": timetabled,
        "fill_rate_percentage": round(fill_rate, 2),
    }


@router.get("/kpi/utilisation")
async def get_utilisation_report(
    centre_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Get utilisation report per teacher/centre."""
    q = db.query(Teacher).filter(Teacher.status == TeacherStatus.ACTIVE)
    if centre_id:
        q = q.filter(Teacher.primary_centre_id == centre_id)
    
    teachers = q.all()
    report = []
    
    for t in teachers:
        contracted = t.contracted_hours or 0
        # Get published slots for this teacher
        slots = db.query(TimetableSlot).join(TimetableDraft).filter(
            TimetableSlot.teacher_id == t.id,
            TimetableDraft.status == DraftStatus.PUBLISHED,
        ).all()
        
        assigned_hours = len(slots) * 1.5  # Assume 1.5 hrs per slot on average
        util_pct = (assigned_hours / contracted * 100) if contracted > 0 else 0
        
        report.append({
            "teacher_id": t.id,
            "teacher_name": f"{t.first_name} {t.last_name}",
            "centre_id": t.primary_centre_id,
            "contract_type": t.contract_type.value if t.contract_type else None,
            "contracted_hours": contracted,
            "assigned_hours": round(assigned_hours, 2),
            "utilisation_percentage": round(util_pct, 2),
        })
    
    return {
        "total_teachers": len(report),
        "teachers": report,
    }


@router.get("/kpi/cost-efficiency")
async def get_cost_efficiency(
    centre_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Cost efficiency: actual vs planned labour cost (HR only data)."""
    q = db.query(Teacher).filter(Teacher.status == TeacherStatus.ACTIVE)
    if centre_id:
        q = q.filter(Teacher.primary_centre_id == centre_id)
    
    teachers = q.all()
    total_planned_cost = 0
    total_actual_cost = 0
    
    for t in teachers:
        if t.contract_type == ContractType.FULL_TIME:
            planned = t.salary or 0
            total_planned_cost += planned
            total_actual_cost += planned  # Simplified: assume FT paid full salary
        else:
            hourly = t.hourly_rate or 0
            slots = db.query(TimetableSlot).join(TimetableDraft).filter(
                TimetableSlot.teacher_id == t.id,
                TimetableDraft.status == DraftStatus.PUBLISHED,
            ).all()
            actual_hours = len(slots) * 1.5
            total_planned_cost += actual_hours * hourly
            total_actual_cost += actual_hours * hourly
    
    efficiency = 100
    if total_planned_cost > 0:
        efficiency = (total_actual_cost / total_planned_cost) * 100
    
    return {
        "total_planned_cost": round(total_planned_cost, 2),
        "total_actual_cost": round(total_actual_cost, 2),
        "efficiency_percentage": round(efficiency, 2),
    }


@router.get("/export/csv")
async def export_report_csv(
    report_type: str = Query(..., description="fill-rate, utilisation, or cost-efficiency"),
    centre_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """Export report as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    if report_type == "utilisation":
        writer.writerow(['Teacher ID', 'Name', 'Centre ID', 'Contract Type', 
                     'Contracted Hours', 'Assigned Hours', 'Utilisation %'])
        q = db.query(Teacher).filter(Teacher.status == TeacherStatus.ACTIVE)
        if centre_id:
            q = q.filter(Teacher.primary_centre_id == centre_id)
        
        for t in q.all():
            contracted = t.contracted_hours or 0
            slots = db.query(TimetableSlot).join(TimetableDraft).filter(
                TimetableSlot.teacher_id == t.id,
                TimetableDraft.status == DraftStatus.PUBLISHED,
            ).all()
            assigned = len(slots) * 1.5
            util = (assigned / contracted * 100) if contracted > 0 else 0
            writer.writerow([t.id, f"{t.first_name} {t.last_name}", t.primary_centre_id,
                           t.contract_type.value if t.contract_type else '',
                           contracted, round(assigned, 2), round(util, 2)])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report_type}_report.csv"}
    )