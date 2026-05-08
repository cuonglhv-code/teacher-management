"""APScheduler setup for scheduled tasks."""

from datetime import datetime, timedelta
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, engine
from app.forecasting.forecast import compute_12_week_forecast
from app.models.teacher import Centre, ForecastPeriod

scheduler = BackgroundScheduler()

def run_weekly_forecast():
    """Weekly task to recompute forecast for all active centres."""
    print(f"Running weekly forecast computation at {datetime.utcnow()}")
    
    # Create a new session
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Get all active centres
        centres = db.query(Centre).filter(Centre.is_active == True).all()
        today = datetime.utcnow().date()
        
        for centre in centres:
            # Compute forecast starting from next week
            start_date = today + timedelta(days=(7 - today.weekday()))  # Next Sunday
            compute_12_week_forecast(centre.id, start_date, db)
            print(f"Forecast computed for centre {centre.id} ({centre.name})")
        
        db.commit()
    except Exception as e:
        print(f"Error in weekly forecast: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Start the scheduler with weekly forecast task."""
    # Schedule for every Sunday at 23:00
    scheduler.add_job(
        run_weekly_forecast,
        CronTrigger(day_of_week='sun', hour=23, minute=0),
        id='weekly_forecast',
        name='Compute 12-week forecast for all centres',
        replace_existing=True
    )
    scheduler.start()
    print("Scheduler started - weekly forecast will run every Sunday at 23:00")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    scheduler.shutdown()
    print("Scheduler shutdown")