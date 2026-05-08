"""JTWMS – FastAPI application entry point."""

from fastapi import FastAPI

from app.db.database import engine, Base
from app.api.routes.teachers import router as teachers_router
from app.api.routes.centres import router as centres_router
from app.api.routes.rooms import router as rooms_router
from app.api.routes.classes import router as classes_router
from app.api.routes.timetable import router as timetable_router
from app.api.routes.forecasts import router as forecasts_router
from app.api.routes.hr import router as hr_router
from app.api.routes.reports import router as reports_router
from app.scheduler import start_scheduler, shutdown_scheduler

# Create all tables on startup (for development; use Alembic in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="JTWMS – Teacher Workforce Management System",
    description="Backend API for managing teacher scheduling across 10 English centres.",
    version="0.1.0",
)

app.include_router(teachers_router, prefix="/api/v1/teachers", tags=["teachers"])
app.include_router(centres_router, prefix="/api/v1/centres", tags=["centres"])
app.include_router(rooms_router, prefix="/api/v1/rooms", tags=["rooms"])
app.include_router(classes_router, prefix="/api/v1/classes", tags=["classes"])
app.include_router(timetable_router, prefix="/api/v1/timetable", tags=["timetable"])
app.include_router(forecasts_router, prefix="/api/v1/forecasts", tags=["forecasts"])
app.include_router(hr_router, prefix="/api/v1/hr", tags=["hr"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    shutdown_scheduler()
