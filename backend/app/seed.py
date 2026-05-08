"""Seed script — populates the database with initial data for development."""

import sys
import os
from datetime import time

# Ensure the app module is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal, engine, Base
from app.models.teacher import (
    ContractType, TeacherStatus, Teacher, Centre, Room,
    TeacherAvailability, Class, ClassStatus,
)


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # ── Centres ───────────────────────────────────────────────────
        centre_a = Centre(name="Jaxtina Trần Quốc Hoàn", code="JTH", is_active=True)
        centre_b = Centre(name="Jaxtina Lê Văn Lương", code="JLL", is_active=True)
        db.add_all([centre_a, centre_b])
        db.flush()

        # ── Teachers ───────────────────────────────────────────────────
        teachers = [
            Teacher(
                first_name="Nguyen", last_name="Van Anh",
                email="anh.nv@jaxtina.edu.vn", phone="0901000001",
                contract_type=ContractType.FULL_TIME,
                contracted_hours=40, salary=15000000,
                primary_centre_id=centre_a.id, status=TeacherStatus.ACTIVE,
                qualifications="IELTS 8.0, CELTA",
            ),
            Teacher(
                first_name="Tran", last_name="Thi Binh",
                email="binh.tt@jaxtina.edu.vn", phone="0901000002",
                contract_type=ContractType.FULL_TIME,
                contracted_hours=40, salary=15000000,
                primary_centre_id=centre_a.id, status=TeacherStatus.ACTIVE,
                qualifications="IELTS 7.5, TESOL",
            ),
            Teacher(
                first_name="Le", last_name="Van Cuong",
                email="cuong.lv@jaxtina.edu.vn", phone="0901000003",
                contract_type=ContractType.PART_TIME,
                contracted_hours=20, hourly_rate=200000,
                primary_centre_id=centre_a.id, status=TeacherStatus.ACTIVE,
                qualifications="IELTS 7.0",
            ),
            Teacher(
                first_name="Pham", last_name="Thi Dung",
                email="dung.pt@jaxtina.edu.vn", phone="0901000004",
                contract_type=ContractType.PART_TIME,
                contracted_hours=15, hourly_rate=180000,
                primary_centre_id=centre_b.id, status=TeacherStatus.ACTIVE,
                qualifications="IELTS 7.5, CELTA",
            ),
            Teacher(
                first_name="Hoang", last_name="Van Em",
                email="em.hv@jaxtina.edu.vn", phone="0901000005",
                contract_type=ContractType.FULL_TIME,
                contracted_hours=40, salary=16000000,
                primary_centre_id=centre_b.id, status=TeacherStatus.ACTIVE,
                qualifications="IELTS 8.5, DELTA",
            ),
        ]
        db.add_all(teachers)
        db.flush()

        # ── Rooms ─────────────────────────────────────────────────────
        rooms = [
            Room(centre_id=centre_a.id, name="Room 101", capacity=20, has_projector=True),
            Room(centre_id=centre_a.id, name="Room 102", capacity=15),
            Room(centre_id=centre_b.id, name="Room A", capacity=25, has_projector=True, has_whiteboard=True),
        ]
        db.add_all(rooms)
        db.flush()

        # ── Availability (for teacher 1 & 3 as examples) ──────────────
        availabilities = [
            # Teacher 1: Mon-Fri 8:00-12:00, 13:00-17:00
            TeacherAvailability(teacher_id=teachers[0].id, day_of_week="Monday",    start_time=time(8,0),  end_time=time(12,0)),
            TeacherAvailability(teacher_id=teachers[0].id, day_of_week="Monday",    start_time=time(13,0), end_time=time(17,0)),
            TeacherAvailability(teacher_id=teachers[0].id, day_of_week="Tuesday",   start_time=time(8,0),  end_time=time(12,0)),
            TeacherAvailability(teacher_id=teachers[0].id, day_of_week="Tuesday",   start_time=time(13,0), end_time=time(17,0)),
            TeacherAvailability(teacher_id=teachers[0].id, day_of_week="Wednesday", start_time=time(8,0),  end_time=time(12,0)),
            TeacherAvailability(teacher_id=teachers[0].id, day_of_week="Wednesday", start_time=time(13,0), end_time=time(17,0)),
            TeacherAvailability(teacher_id=teachers[0].id, day_of_week="Thursday",  start_time=time(8,0),  end_time=time(12,0)),
            TeacherAvailability(teacher_id=teachers[0].id, day_of_week="Thursday",  start_time=time(13,0), end_time=time(17,0)),
            TeacherAvailability(teacher_id=teachers[0].id, day_of_week="Friday",    start_time=time(8,0),  end_time=time(12,0)),
            TeacherAvailability(teacher_id=teachers[0].id, day_of_week="Friday",    start_time=time(13,0), end_time=time(17,0)),
            # Teacher 3 (PT): Mon/Wed/Fri 14:00-18:00
            TeacherAvailability(teacher_id=teachers[2].id, day_of_week="Monday",    start_time=time(14,0), end_time=time(18,0)),
            TeacherAvailability(teacher_id=teachers[2].id, day_of_week="Wednesday", start_time=time(14,0), end_time=time(18,0)),
            TeacherAvailability(teacher_id=teachers[2].id, day_of_week="Friday",    start_time=time(14,0), end_time=time(18,0)),
        ]
        db.add_all(availabilities)

        # ── Classes (sample) ──────────────────────────────────────────
        classes = [
            Class(centre_id=centre_a.id, name="IELTS Foundation A1", level="A1",
                  required_teacher_qualification="IELTS 7.0",
                  preferred_day="Monday", preferred_start_time=time(9,0),
                  preferred_end_time=time(10,30), duration_minutes=90,
                  max_students=15, status=ClassStatus.PLANNED),
            Class(centre_id=centre_a.id, name="IELTS Intermediate B1", level="B1",
                  required_teacher_qualification="IELTS 7.5",
                  preferred_day="Wednesday", preferred_start_time=time(9,0),
                  preferred_end_time=time(11,0), duration_minutes=120,
                  max_students=12, status=ClassStatus.PLANNED),
            Class(centre_id=centre_b.id, name="Business English", level="B2",
                  required_teacher_qualification="IELTS 7.5",
                  preferred_day="Tuesday", preferred_start_time=time(14,0),
                  preferred_end_time=time(16,0), duration_minutes=120,
                  max_students=10, status=ClassStatus.PLANNED),
        ]
        db.add_all(classes)

        db.commit()
        print("✅ Seed completed: 2 centres, 5 teachers, 3 rooms, availability, 3 classes.")
    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()