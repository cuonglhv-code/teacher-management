"""Forecast API routes — 12-week forecast and reporting."""

from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.forecasting.forecast import compute_12_week_forecast, get_forecast_periods

router = APIRouter()


@router.post("/{centre_id}/compute")
async def compute_forecast(
    centre_id: int,
    start_date: date,
    db: Session = Depends(get_db),
):
    """Trigger 12-week forecast computation for a centre."""
    # Verify centre exists
    from app.models.teacher import Centre
    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    
    results = compute_12_week_forecast(centre_id, start_date, db)
    
    return {
        "message": f"12-week forecast computed for centre {centre_id}",
        "periods_computed": len(results),
        "start_date": start_date,
    }


@router.get("/{centre_id}")
async def get_forecast(
    centre_id: int,
    db: Session = Depends(get_db),
):
    """Get all forecast periods for a centre."""
    from app.models.teacher import Centre
    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    
    periods = get_forecast_periods(centre_id, db)
    
    return {
        "centre_id": centre_id,
        "centre_name": centre.name,
        "periods": periods,
    }