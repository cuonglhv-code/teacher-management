"""API route modules."""

from app.api.routes.teachers import router as teachers_router
from app.api.routes.classes import router as classes_router
from app.api.routes.rooms import router as rooms_router
from app.api.routes.centres import router as centres_router
from app.api.routes.timetable import router as timetable_router

__all__ = ["teachers_router", "classes_router", "rooms_router", "centres_router", "timetable_router"]
