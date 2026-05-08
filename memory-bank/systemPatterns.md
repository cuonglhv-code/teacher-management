# System Patterns: JTWMS

## Architecture
- **Frontend**: React (with Material UI) – single‑page application.
- **Backend**: FastAPI (Python) providing RESTful API.
- **Database**: PostgreSQL.
- **Scheduling Engine**: Python custom constraint solver, two‑phase (FT‑first, then PT overflow) using greedy assignment with soft constraints.
- **Forecast Module**: Python, recomputed weekly, simulates assignment to estimate teacher utilisation.

## Key Design Decisions
1. **Two‑phase scheduling** to enforce the business rule “fill FT hours before using PT”. Soft constraint with high weight.
2. **Human‑in‑the‑loop**: every timetable draft must be explicitly published by an Academic Manager.
3. **Role‑based access**: HR role vs Academic Manager role – enforced at API level.
4. **12‑week rolling forecast** with both gap analysis and idle‑capacity health metrics.
5. **Vercel‑compatible serverless deployment**: backend functions kept within timeout limits; long scheduling runs may be offloaded to an async task system later.

## Data Relationships
See proposal Section 4. Core: Teacher (with contract type, hourly_rate for PT), Centre, Room, Class, TimetableSlot, Availability, Leave, HeadcountRequest, ForecastPeriod.