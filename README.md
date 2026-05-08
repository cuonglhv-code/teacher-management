# JTWMS – Teacher Workforce Management System

A full-stack web application for centralising teacher data, automating scheduling, tracking utilisation, and providing workforce forecasting across **10 English language centres**.

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Alembic, PostgreSQL
- **Frontend**: React 18, Material UI (MUI), Vite, React Router
- **Deployment**: Docker Compose (development), Vercel (production target)

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/routes/       # FastAPI route modules
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── db/               # Database connection & session
│   │   ├── main.py           # FastAPI application entry point
│   │   └── seed.py           # Development seed script
│   ├── alembic/              # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/              # API client modules
│   │   ├── components/       # Reusable React components
│   │   ├── pages/            # Page-level components
│   │   ├── App.jsx           # Root component with routing
│   │   └── main.jsx          # Vite entry point
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── README.md
```

## Quick Start (Development)

### Prerequisites

- Docker & Docker Compose
- Node.js 18+

### 1. Start Backend & Database

```bash
docker compose up --build
```

This starts:
- **PostgreSQL 15** on port `5432`
- **FastAPI** on port `8000` with auto-reload

### 2. Run Migrations (first time only)

```bash
cd backend
alembic upgrade head
```

### 3. Seed Sample Data (optional)

```bash
cd backend
python -m app.seed
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` with API proxy to `http://localhost:8000`.

## API Endpoints

| Prefix | Description |
|---|---|
| `/api/v1/teachers` | Teacher CRUD + Availability + Leave |
| `/api/v1/centres` | Centre CRUD |
| `/api/v1/rooms` | Room CRUD (per centre) |
| `/api/v1/classes` | Class CRUD + status workflow + room booking validation |
| `/health` | Health check |

### Role-Based Access

Pass `?role=hr` or `?role=academic_manager` as a query parameter to relevant endpoints. HR role can see salary fields; Academic Managers cannot.

## Key Business Rules

- **Full-time teachers** are paid fixed salary → scheduling fills FT teachers before assigning PT teachers.
- **Part-time teachers** are paid hourly → used only after FT capacity is exhausted.
- **Human approval gate** — all auto-generated timetable slots require explicit manager publish action.
- **Salary data is HR-only** — enforced at the API layer.

## Vercel Deployment (Production with Neon PostgreSQL)

### Prerequisites
- Neon account with a project created
- Vercel account
- GitHub repository with your code pushed

### Step 1: Get Neon Connection String
1. Go to [Neon Dashboard](https://console.neon.tech)
2. Select your project → "Connection Details"
3. Copy the connection string
4. **Important**: Ensure `?sslmode=require` is appended at the end
   - Example: `postgresql://user:pass@ep-xxx.neon.tech/jtwms?sslmode=require`

### Step 2: Push Code to GitHub
```bash
git add .
git commit -m "Ready for Vercel deployment with Neon"
git push origin main
```

### Step 3: Import Project to Vercel
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"New Project"**
3. Import your GitHub repository
4. Configure project settings:
   - **Root Directory**: `backend`
   - **Build Command**: Leave empty (Vercel uses `vercel.json`)
   - **Output Directory**: Leave empty

### Step 4: Set Environment Variables
In Vercel project settings → **Environment Variables**, add:

| Name | Value | Notes |
|------|-------|-------|
| `DATABASE_URL` | Your Neon connection string with `?sslmode=require` | Required |
| `SECRET_KEY` | Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` | Required |
| `ENVIRONMENT` | `production` | Recommended |
| `GOOGLE_CLIENT_ID` | (optional) | For Google Calendar integration |
| `GOOGLE_CLIENT_SECRET` | (optional) | For Google Calendar integration |
| `SENDGRID_API_KEY` | (optional) | For email notifications |
| `VERCEL_URL` | `https://your-project.vercel.app` | Set after first deployment |

### Step 5: Deploy
- Click **"Deploy"** button
- Wait for deployment to complete (usually 1-2 minutes)
- Note your deployment URL: `https://your-project.vercel.app`

### Step 6: Run Database Migrations
After first deployment, run Alembic migrations against Neon:

**Option A: Using Vercel CLI**
```bash
# Pull environment variables
vercel env pull .env.production

# Run migrations
cd backend
python run_migration_prod.py
```

**Option B: One-time Vercel Function**
```bash
# Create a temporary endpoint in api/index.py for migration
# Then call it once: https://your-project.vercel.app/migrate
# Remove after use
```

### Step 7: Verify Deployment
1. **Check Swagger UI**: Visit `https://your-project.vercel.app/docs`
   - Should load FastAPI Swagger interface
   - Test endpoints directly from the UI

2. **Test Health Check**: `https://your-project.vercel.app/health`
   - Should return: `{"status": "ok"}`

3. **Test Database Connection**:
   - In Swagger UI, try `GET /api/v1/teachers`
   - Should return teacher data from Neon database

4. **Check Function Logs**:
   - Vercel Dashboard → Deployments → View Function Logs
   - Monitor for any errors

### Common Issues

**Issue**: `sslmode` not set
- **Solution**: Ensure `DATABASE_URL` ends with `?sslmode=require`

**Issue**: Alembic can't find `alembic.ini`
- **Solution**: Set working directory or use absolute paths in `run_migration_prod.py`

**Issue**: Import errors in Vercel
- **Solution**: Verify `backend/api/index.py` has correct Python path setup

### Frontend Deployment

1. **Configure API URL**:
   - Create `frontend/.env`:
     ```
     VITE_API_BASE_URL=https://your-backend.vercel.app
     ```

2. **Build the frontend**:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

3. **Deploy**:
   - Option A: Deploy static build (`dist/` folder) to Vercel as a separate project
   - Option B: Use Vercel CLI:
     ```bash
     cd frontend
     vercel --prod
     ```

### PWA Features

The frontend is configured as a Progressive Web App (PWA):
- **Manifest**: `frontend/public/manifest.json`
- **Service Worker**: `frontend/public/service-worker.js` caches teacher schedules for offline viewing
- **Install Prompt**: Users can "Install" the app on mobile devices

### Mobile-First Design

The timetable view automatically switches between:
- **Mobile (<960px)**: Simple list grouped by day
- **Desktop (≥960px)**: Full table grid with rooms and time slots

### Teacher Features

- **Submit Availability**: Teachers can tap "Submit Weekly Availability" from the home screen
- **View Schedule**: Mobile-friendly schedule view
- **Offline Access**: Schedule cached for offline viewing

## License

Proprietary — Jaxtina Education
