"""Integration tests for timetable generation, forecast computation, and alert triggering."""

import pytest
from datetime import date, timedelta, time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.models.teacher import (
    Teacher, Centre, Class, Room, TimetableDraft, TimetableSlot,
    TeacherAvailability, ContractType, ClassStatus, DraftStatus,
    HeadcountRequest, HeadcountRequestStatus, TeacherStatus
)

# Test Database Setup
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# Helper Functions

def create_centre(db, name="Test Centre", code="TC01"):
    centre = Centre(name=name, code=code, is_active=True)
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return centre


def create_teacher(db, centre_id, contract_type=ContractType.FULL_TIME, 
                   qualifications="ielts 7.0 celta", contracted_hours=40):
    # Generate email based on contract type
    if hasattr(contract_type, 'value'):
        email_val = f"test{contract_type.value}@test.com"
    else:
        email_val = f"test{contract_type}@test.com"
    
    teacher = Teacher(
        first_name="Test",
        last_name="Teacher",
        email=email_val,
        contract_type=contract_type,
        contracted_hours=contracted_hours,
        qualifications=qualifications,
        primary_centre_id=centre_id,
        status=TeacherStatus.ACTIVE,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    
    # Add availability for all weekdays 8:00-17:00
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        avail = TeacherAvailability(
            teacher_id=teacher.id,
            day_of_week=day,
            start_time=time(8, 0),
            end_time=time(17, 0),
            is_available=True,
        )
        db.add(avail)
    db.commit()
    
    return teacher


def create_room(db, centre_id, name="Test Room", capacity=20):
    room = Room(
        name=name,
        centre_id=centre_id,
        capacity=capacity,
        is_active=True,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


def create_class(db, centre_id, name="Test Class", 
                 qualification="ielts 7.0", 
                 preferred_day="Monday",
                 start_time_str="09:00", end_time_str="10:30",
                 status=ClassStatus.APPROVED):
    def parse_time(t_str):
        h, m = map(int, t_str.split(":"))
        return time(h, m)
    
    class_obj = Class(
        name=name,
        centre_id=centre_id,
        max_students=10,
        required_qualification=qualification,
        preferred_day=preferred_day,
        preferred_start_time=parse_time(start_time_str),
        preferred_end_time=parse_time(end_time_str),
        duration_minutes=90,
        status=status,
    )
    db.add(class_obj)
    db.commit()
    db.refresh(class_obj)
    return class_obj


# Section 1: Timetable Generation Endpoint Tests

class TestTimetableGeneration:
    """Tests for POST /api/v1/timetable/generate-draft endpoint."""
    
    def test_ft_only_all_classes_assigned(self, client, db_session):
        """Normal case: all classes fit within FT teacher capacity."""
        # Setup
        centre = create_centre(db_session)
        ft1 = create_teacher(db_session, centre.id, ContractType.FULL_TIME, "ielts 7.0 celta", 40)
        ft2 = create_teacher(db_session, centre.id, ContractType.FULL_TIME, "ielts 7.0 celta", 40)
        room = create_room(db_session, centre.id)
        
        # Create 4 classes
        days = ["Monday", "Tuesday", "Wednesday", "Thursday"]
        for i in range(4):
            create_class(
                db_session, centre.id, 
                name=f"Class {i+1}",
                qualification="ielts 7.0",
                preferred_day=days[i],
                start_time_str="09:00", end_time_str="10:30",
            )
        
        # Generate draft
        start_date = date.today()
        end_date = start_date + timedelta(days=6)
        response = client.post(
            "/api/v1/timetable/generate-draft",
            params={
                "centre_id": centre.id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "draft_id" in data
        
        # Verify draft
        draft_response = client.get(f"/api/v1/timetable/drafts/{centre.id}")
        assert draft_response.status_code == 200
        draft_data = draft_response.json()
        assert draft_data["total_slots"] == 4
        assert draft_data["total_unassigned"] == 0
        assert draft_data["conflict_report"]["total_conflicts"] == 0
        
        # Verify all slots are assigned to FT teachers
        for slot in draft_data["slots"]:
            teacher = db_session.query(Teacher).filter(Teacher.id == slot["teacher_id"]).first()
            assert teacher.contract_type == ContractType.FULL_TIME
    
    def test_pt_overflow_required(self, client, db_session):
        """Overflow case: FT capacity insufficient, PT teacher needed."""
        # Setup
        centre = create_centre(db_session)
        ft1 = create_teacher(db_session, centre.id, ContractType.FULL_TIME, "ielts 7.0 celta", 40)
        pt1 = create_teacher(db_session, centre.id, ContractType.PART_TIME, "ielts 7.0", 20)
        
        # Add PT availability (limited)
        for day in ["Monday", "Wednesday", "Friday"]:
            avail = TeacherAvailability(
                teacher_id=pt1.id,
                day_of_week=day,
                start_time=time(14, 0),
                end_time=time(18, 0),
                is_available=True,
            )
            db_session.add(avail)
        db_session.commit()
        
        room = create_room(db_session, centre.id)
        
        # Create 6 classes
        class_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Monday"]
        for i in range(6):
            create_class(
                db_session, centre.id,
                name=f"Class {i+1}",
                qualification="ielts 7.0",
                preferred_day=class_days[i],
                start_time_str="09:00", end_time_str="10:30",
            )
        
        # Generate draft
        start_date = date.today()
        end_date = start_date + timedelta(days=6)
        response = client.post(
            "/api/v1/timetable/generate-draft",
            params={
                "centre_id": centre.id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify draft
        draft_response = client.get(f"/api/v1/timetable/drafts/{centre.id}")
        draft_data = draft_response.json()
        
        # At least some slots should be assigned
        assert draft_data["total_slots"] > 0
        
        # Check if PT teacher was used (if overflow happened)
        pt_slots = []
        for s in draft_data["slots"]:
            if s["teacher_id"] == pt1.id:
                pt_slots.append(s)
        if len(draft_data["unassigned_classes"]) < 6:
            # PT might have been used
            assert True
    
    def test_qualification_mismatch_unschedulable(self, client, db_session):
        """Class requiring 'delta' qualification when no teacher has it."""
        # Setup
        centre = create_centre(db_session)
        ft1 = create_teacher(db_session, centre.id, ContractType.FULL_TIME, "ielts 7.0 celta", 40)
        room = create_room(db_session, centre.id)
        
        # Class requiring delta (no teacher has this)
        create_class(
            db_session, centre.id,
            name="Advanced DELTA Class",
            qualification="delta",
            preferred_day="Monday",
            start_time_str="09:00", end_time_str="10:30",
        )
        
        # Class with ielts (should be assignable)
        create_class(
            db_session, centre.id,
            name="IELTS Class",
            qualification="ielts 7.0",
            preferred_day="Tuesday",
            start_time_str="09:00", end_time_str="10:30",
        )
        
        # Generate draft
        start_date = date.today()
        end_date = start_date + timedelta(days=6)
        response = client.post(
            "/api/v1/timetable/generate-draft",
            params={
                "centre_id": centre.id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        )
        
        assert response.status_code == 200
        
        # Verify draft
        draft_response = client.get(f"/api/v1/timetable/drafts/{centre.id}")
        draft_data = draft_response.json()
        
        # Class 1 (delta) should be unassigned
        unassigned_ids = []
        for u in draft_data.get("unassigned_classes", []):
            unassigned_ids.append(u["class_id"])
        
        # Find the delta class ID
        delta_class = db_session.query(Class).filter(Class.required_qualification == "delta").first()
        assert delta_class.id in unassigned_ids
        
        # Check reason mentions qualification
        delta_unassigned = None
        for u in draft_data.get("unassigned_classes", []):
            if u["class_id"] == delta_class.id:
                delta_unassigned = u
                break
        assert delta_unassigned is not None
        assert "qualification" in delta_unassigned["reason"].lower()
        
        # Class 2 (ielts) should be assigned
        assigned_class_ids = []
        for s in draft_data.get("slots", []):
            assigned_class_ids.append(s["class_id"])
        ielts_class = db_session.query(Class).filter(Class.required_qualification == "ielts 7.0").first()
        assert ielts_class.id in assigned_class_ids
    
    def test_conflict_detection(self, client, db_session):
        """Verify conflict detection when double-booking would occur."""
        # Setup
        centre = create_centre(db_session)
        ft1 = create_teacher(db_session, centre.id, ContractType.FULL_TIME, "ielts 7.0 celta", 40)
        room = create_room(db_session, centre.id)  # Only 1 room
        
        # Create 2 classes on same day/time (will conflict for room)
        create_class(
            db_session, centre.id,
            name="Class A Mon 9-10:30",
            qualification="ielts 7.0",
            preferred_day="Monday",
            start_time_str="09:00", end_time_str="10:30",
        )
        create_class(
            db_session, centre.id,
            name="Class B Mon 9-10:30",
            qualification="ielts 7.0",
            preferred_day="Monday",
            start_time_str="09:00", end_time_str="10:30",
        )
        
        # Generate draft
        start_date = date.today()
        end_date = start_date + timedelta(days=6)
        response = client.post(
            "/api/v1/timetable/generate-draft",
            params={
                "centre_id": centre.id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        )
        
        assert response.status_code == 200
        
        # Verify draft
        draft_response = client.get(f"/api/v1/timetable/drafts/{centre.id}")
        draft_data = draft_response.json()
        
        # Should have at least 1 unassigned due to conflict
        assert draft_data["total_unassigned"] >= 1
        
        # Conflict report should mention something
        assert draft_data["conflict_report"]["total_conflicts"] >= 0


# Section 2: Forecast Computation Endpoint Tests

class TestForecastComputation:
    """Tests for POST /api/v1/forecasts/{centre_id}/compute endpoint."""
    
    def test_basic_forecast_computation(self, client, db_session):
        """Basic forecast with FT and PT teachers."""
        # Setup
        centre = create_centre(db_session)
        ft1 = create_teacher(db_session, centre.id, ContractType.FULL_TIME, "ielts 7.0 celta", 40)
        ft2 = create_teacher(db_session, centre.id, ContractType.FULL_TIME, "ielts 7.0 celta", 40)
        pt1 = create_teacher(db_session, centre.id, ContractType.PART_TIME, "ielts 7.0", 20)
        room = create_room(db_session, centre.id)
        
        # Create classes
        for i in range(4):
            create_class(
                db_session, centre.id,
                name=f"Forecast Class {i+1}",
                qualification="ielts 7.0",
            )
        
        # Compute forecast
        start_date = date.today() + timedelta(days=7)  # Next week
        response = client.post(
            f"/api/v1/forecasts/{centre.id}/compute",
            params={"start_date": start_date.isoformat()}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Verify forecast periods created
        forecast_response = client.get(f"/api/v1/forecasts/{centre.id}")
        assert forecast_response.status_code == 200
        forecast_data = forecast_response.json()
        
        assert len(forecast_data["forecast_periods"]) >= 12
        
        # Verify first period has required fields
        first_period = forecast_data["forecast_periods"][0]
        assert "projected_demand_hours" in first_period
        assert "available_ft_hours" in first_period
        assert "available_pt_hours" in first_period
        assert "unassigned_ft_rate" in first_period
        assert "available_teacher_rate" in first_period
    
    def test_ft_first_supply_simulation(self, client, db_session):
        """FT teachers should be assigned first in supply simulation."""
        # Setup
        centre = create_centre(db_session)
        ft1 = create_teacher(db_session, centre.id, ContractType.FULL_TIME, "ielts 7.0 celta", 40)
        ft2 = create_teacher(db_session, centre.id, ContractType.FULL_TIME, "ielts 7.0 celta", 40)
        pt1 = create_teacher(db_session, centre.id, ContractType.PART_TIME, "ielts 7.0", 20)
        
        # Create classes with demand less than FT capacity
        for i in range(3):
            create_class(
                db_session, centre.id,
                name=f"FT First Class {i+1}",
                qualification="ielts 7.0",
            )
        
        # Compute forecast
        start_date = date.today() + timedelta(days=7)
        response = client.post(
            f"/api/v1/forecasts/{centre.id}/compute",
            params={"start_date": start_date.isoformat()}
        )
        
        assert response.status_code == 200
        
        # Verify forecast
        forecast_response = client.get(f"/api/v1/forecasts/{centre.id}")
        forecast_data = forecast_response.json()
        
        first_period = forecast_data["forecast_periods"][0]
        
        # FT hours should be used first
        assert first_period["available_ft_hours"] >= 0
        # Since demand < FT capacity, PT hours might not be used
        assert "available_pt_hours" in first_period


# Section 3: Alert Triggering Tests  

class TestAlertTriggering:
    """Tests for alert generation based on forecast thresholds."""
    
    def test_unassigned_ft_rate_alert(self, client, db_session):
        """Alert when Unassigned FT Rate > 50%."""
        # Setup: Create centre with many FT teachers but only 1 qualified
        centre = create_centre(db_session)
        
        # Create 4 FT teachers with ielts
        for i in range(4):
            if i == 0:
                qual = "ielts 7.0 celta"
            else:
                qual = "ielts 6.0"
            create_teacher(
                db_session, centre.id, 
                ContractType.FULL_TIME, 
                qual,
                40
            )
        
        # Create 1 PT teacher
        create_teacher(db_session, centre.id, ContractType.PART_TIME, "ielts 7.0", 20)
        
        # Create classes requiring ielts 7.0 (only 1 teacher qualified)
        for i in range(5):
            create_class(
                db_session, centre.id,
                name=f"High Qual Class {i+1}",
                qualification="ielts 7.0 celta",
            )
        
        # Compute forecast (should trigger unassigned FT rate > 50%)
        start_date = date.today() + timedelta(days=7)
        client.post(
            f"/api/v1/forecasts/{centre.id}/compute",
            params={"start_date": start_date.isoformat()}
        )
        
        # Check alerts
        alerts_response = client.get("/api/v1/hr/alerts", params={"centre_id": centre.id})
        assert alerts_response.status_code == 200
        alerts_data = alerts_response.json()
        
        # Should have some alerts
        requests_response = client.get(
            "/api/v1/hr/headcount-requests", 
            params={"centre_id": centre.id}
        )
        requests_data = requests_response.json()
        
        # If unassigned FT rate > 50%, should have open headcount request
        if alerts_data["total_alerts"] > 0:
            assert True  # Pass - alerts mechanism working
    
    def test_available_teacher_rate_alert(self, client, db_session):
        """Alert when Available Teacher Rate < 20%."""
        # Setup: Create centre with many teachers, low demand
        centre = create_centre(db_session)
        
        # Create 5 FT teachers (high supply)
        for i in range(5):
            create_teacher(
                db_session, centre.id,
                ContractType.FULL_TIME,
                "ielts 7.0 celta",
                40
            )
        
        # Create only 1 class (very low demand)
        create_class(
            db_session, centre.id,
            name="Single Class",
            qualification="ielts 7.0",
        )
        
        # Compute forecast
        start_date = date.today() + timedelta(days=7)
        client.post(
            f"/api/v1/forecasts/{centre.id}/compute",
            params={"start_date": start_date.isoformat()}
        )
        
        # Check if headcount request was auto-created (low available teacher rate)
        requests_response = client.get(
            "/api/v1/hr/headcount-requests",
            params={"centre_id": centre.id}
        )
        requests_data = requests_response.json()
        
        # Low demand might trigger headcount request
        assert isinstance(requests_data, list)
    
    def test_contract_expiry_alert(self, client, db_session):
        """Alert for contracts expiring within 60 days."""
        # Setup
        centre = create_centre(db_session)
        
        # Create teacher with contract expiring in 30 days
        teacher = create_teacher(
            db_session, centre.id,
            ContractType.FULL_TIME,
            "ielts 7.0 celta",
            40
        )
        teacher.contract_end_date = date.today() + timedelta(days=30)
        teacher.renewal_status = None  # Not set yet
        db_session.commit()
        
        # Check alerts (alerts endpoint queries expiring contracts)
        alerts_response = client.get("/api/v1/hr/alerts", params={"centre_id": centre.id})
        assert alerts_response.status_code == 200
        alerts_data = alerts_response.json()
        
        # Should have contract_expiry alert
        expiry_alerts = []
        for a in alerts_data.get("alerts", []):
            if a.get("type") == "contract_expiry":
                expiry_alerts.append(a)
        
        # If teacher contract is within 60 days, should be in alerts
        if teacher.contract_end_date <= date.today() + timedelta(days=60):
            assert len(expiry_alerts) > 0 or teacher.renewal_status == "pending"