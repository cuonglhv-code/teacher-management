# Tech Context: JTWMS

## Development Environment
- VS Code with Cline extension.
- AI model: DeepSeek V4 Flash (with option to use DeepSeek V4 Pro for complex algorithms).
- AI provider API: DeepSeek (base URL: https://api.deepseek.com).

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy ORM, Alembic for migrations, Pydantic for validation.
- **Frontend**: React 18, Material UI (MUI), React Router, Axios, `@dhtmlx/scheduler` or `@fullcalendar/resource-timeline` for visual timetable (Phase 2/3).
- **Database**: PostgreSQL (local dev via Docker, production via Neon or Vercel Postgres).
- **Testing**: Pytest for backend, Jest + React Testing Library for frontend.
- **Deployment**: Vercel (frontend + serverless FastAPI), Vercel‑managed PostgreSQL.

## Constraints
- Serverless timeout limit (10s Hobby, 60s Pro): scheduling algorithm must be efficient; for long‑running tasks consider queue.
- No local file persistence; use database for all state.
- API key management via Vercel environment variables.