# Active Context: JTWMS

## Current Phase
Phase 1 – Core Data & Scheduling Engine (Weeks 1–8 as per proposal).  
Items 1.1–1.4 and 1.7 completed. Items 1.5, 1.6, 1.8 pending.

## Recent Decisions
- FastAPI backend with Vite+React+MUI frontend scaffolded.
- Docker Compose set up with PostgreSQL 15.
- All core data models implemented: Teacher, Centre, Room, Class, TeacherAvailability, Leave, TimetableSlot, HeadcountRequest, ForecastPeriod.
- Alembic migration created (manual) covering all 9 tables with enum types.
- Seed script creates 2 centres, 5 teachers, 3 rooms, availability, 3 classes.
- Teacher Registry backend: full CRUD + availability bulk set + leave management with role-based salary masking.
- Class & Room backend: CRUD with centre filtering, class status workflow with validated transitions (Planned → Approved → Timetabled → Open → Completed / Cancelled), room booking conflict detection endpoint.
- Frontend: Teacher list (MUI DataGrid with filters), Teacher detail/edit form, weekly availability editor (checkboxes for 7 days × 3 time slots), Room manager (table + dialog), Class list (filterable by centre/status), Class create/edit form.
- Role-based access implemented via `?role=` query parameter (HR sees salary fields; Academic Managers do not).

## Open Questions
- Exact visual timetable component selection (DHTMLX vs FullCalendar) – deferred to Phase 2.
- Handling async scheduling tasks on Vercel – to be decided after performance testing.
- Scheduling engine algorithm design (two-phase FT-first) – deferred to item 1.5.