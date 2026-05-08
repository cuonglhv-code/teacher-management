"""12-week forecast module for teacher workforce planning."""

from datetime import date, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.teacher import (
    Teacher, TeacherStatus, ContractType, Class, ClassStatus,
    ForecastPeriod, HeadcountRequest, HeadcountRequestStatus, Centre
)


def compute_12_week_forecast(centre_id: int, start_date: date, db: Session) -> List[ForecastPeriod]:
    """
    Compute 12-week forecast for a centre.
    
    For each week:
    - Demand hours: sum of approved/open classes hours
    - Supply hours: simplified FT-first assignment simulation
    - Gap: demand - supply
    - Unassigned FT Rate: % of FT teachers with 0 forecast hours
    - Available Teacher Rate: % of teachers with >=25% capacity unassigned
    - Write results to ForecastPeriod table
    """
    results = []
    
    for week in range(12):
        week_start = start_date + timedelta(weeks=week)
        week_end = week_start + timedelta(days=6)
        
        # Get demand: sum of approved/open class hours for this centre
        classes = db.query(Class).filter(
            Class.centre_id == centre_id,
            Class.status.in_([ClassStatus.APPROVED, ClassStatus.OPEN, ClassStatus.TIMETABLED])
        ).all()
        
        demand_hours = 0
        for cls in classes:
            duration = (cls.duration_minutes or 90) / 60.0  # Convert to hours
            # Assume 1 class per week for simplicity
            demand_hours += duration
        
        # Get teachers for this centre
        teachers = db.query(Teacher).filter(
            Teacher.primary_centre_id == centre_id,
            Teacher.status == TeacherStatus.ACTIVE
        ).all()
        
        # Simplified supply simulation: FT-first assignment
        ft_teachers = [t for t in teachers if t.contract_type == ContractType.FULL_TIME]
        pt_teachers = [t for t in teachers if t.contract_type == ContractType.PART_TIME]
        
        # Simulate FT teachers getting assigned first
        remaining_demand = demand_hours
        ft_assigned_hours = 0
        pt_assigned_hours = 0
        ft_unassigned_count = 0
        
        for ft in ft_teachers:
            if remaining_demand <= 0:
                ft_unassigned_count += 1
                continue
            # Assign up to contracted hours
            assign_hours = min(ft.contracted_hours or 0, remaining_demand)
            ft_assigned_hours += assign_hours
            remaining_demand -= assign_hours
            if assign_hours == 0:
                ft_unassigned_count += 1
        
        # PT teachers handle overflow
        for pt in pt_teachers:
            if remaining_demand <= 0:
                break
            assign_hours = min(20, remaining_demand)  # Assume max 20 hrs/week for PT
            pt_assigned_hours += assign_hours
            remaining_demand -= assign_hours
        
        supply_hours = ft_assigned_hours + pt_assigned_hours
        gap = demand_hours - supply_hours
        
        # Calculate unassigned FT rate
        unassigned_ft_rate = 0
        if ft_teachers:
            unassigned_ft_rate = (ft_unassigned_count / len(ft_teachers)) * 100
        
        # Calculate available teacher rate (teachers with >=25% capacity unassigned)
        available_teacher_count = 0
        for t in teachers:
            total_capacity = t.contracted_hours or 0
            if total_capacity > 0:
                assigned = 0
                if t in ft_teachers:
                    assigned = min(total_capacity, demand_hours)
                else:
                    assigned = min(20, demand_hours)
                unassigned_pct = ((total_capacity - assigned) / total_capacity) * 100
                if unassigned_pct >= 25:
                    available_teacher_count += 1
        
        available_teacher_rate = 0
        if teachers:
            available_teacher_rate = (available_teacher_count / len(teachers)) * 100
        
        # Check for alerts and create headcount requests
        check_and_trigger_alerts(centre_id, week_start, week_end, unassigned_ft_rate, 
                                available_teacher_rate, gap, db)
        
        # Save to ForecastPeriod table
        forecast = db.query(ForecastPeriod).filter(
            ForecastPeriod.centre_id == centre_id,
            ForecastPeriod.week_start == week_start
        ).first()
        
        if not forecast:
            forecast = ForecastPeriod(
                centre_id=centre_id,
                week_start=week_start,
                week_end=week_end,
            )
            db.add(forecast)
        
        forecast.projected_demand_hours = demand_hours
        forecast.available_ft_hours = ft_assigned_hours
        forecast.available_pt_hours = pt_assigned_hours
        forecast.unassigned_ft_rate = unassigned_ft_rate
        forecast.available_teacher_rate = available_teacher_rate
        forecast.notes = f"Gap: {gap:.1f} hours. Supply simulation complete."
        
        results.append(forecast)
    
    db.commit()
    return results


def check_and_trigger_alerts(centre_id: int, week_start: date, week_end: date,
                            unassigned_ft_rate: float, available_teacher_rate: float,
                            gap: float, db: Session):
    """Check forecast metrics and trigger alerts/headcount requests."""
    
    # Check Unassigned FT Rate > 50% over next 4 weeks
    # (Simplified: check current week, in production would track 4-week rolling)
    if unassigned_ft_rate > 50:
        # Create Staff Reduction Review alert (log to notes or new alerts table)
        print(f"ALERT: Centre {centre_id} - Unassigned FT Rate {unassigned_ft_rate:.1f}% > 50%")
    
    # Check Available Teacher Rate < 20%
    if available_teacher_rate < 20:
        # Check if there's already an open headcount request
        existing_request = db.query(HeadcountRequest).filter(
            HeadcountRequest.centre_id == centre_id,
            HeadcountRequest.status == HeadcountRequestStatus.OPEN
        ).first()
        
        if not existing_request:
            # Create new headcount request
            new_request = HeadcountRequest(
                centre_id=centre_id,
                contract_type=ContractType.FULL_TIME,
                hours_per_week=gap if gap > 0 else 20,
                reason=f"Auto-generated: Available Teacher Rate {available_teacher_rate:.1f}% < 20%",
                status=HeadcountRequestStatus.OPEN,
                requested_by="system",
            )
            db.add(new_request)
    
    # Check gap > 10 hours/week for 3 consecutive weeks
    # (Simplified: check current gap)
    if gap > 10:
        print(f"ALERT: Centre {centre_id} - Gap {gap:.1f} hours > 10 for week {week_start}")


def get_forecast_periods(centre_id: int, db: Session) -> List[Dict]:
    """Get all forecast periods for a centre."""
    periods = db.query(ForecastPeriod).filter(
        ForecastPeriod.centre_id == centre_id
    ).order_by(ForecastPeriod.week_start).all()
    
    return [
        {
            "id": p.id,
            "centre_id": p.centre_id,
            "week_start": p.week_start,
            "week_end": p.week_end,
            "projected_demand_hours": p.projected_demand_hours,
            "available_ft_hours": p.available_ft_hours,
            "available_pt_hours": p.available_pt_hours,
            "unassigned_ft_rate": p.unassigned_ft_rate,
            "available_teacher_rate": p.available_teacher_rate,
            "notes": p.notes,
        }
        for p in periods
    ]