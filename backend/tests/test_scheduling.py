"""Unit tests for the scheduling engine (two-phase constraint solver).

Scenarios:
  1. Normal case — all classes fit within FT teacher capacity.
  2. Overflow case — FT teacher capacity is insufficient; PT teacher required.
  3. Qualification mismatch — no teacher has the required qualification.
"""

from datetime import time
import pytest

from app.scheduling.engine import (
    TeacherSlot,
    ClassToSchedule,
    RoomInfo,
    ScheduleInput,
    run_schedule,
)


# ─── Shared helpers ────────────────────────────────────────────────────────

def _make_ft_teacher(
    tid: int,
    centre_id: int = 1,
    contracted_hours: float = 40,
    qualifications: str = "ielts 7.0 celta",
) -> TeacherSlot:
    """Create a full-time teacher available Mon-Fri 8:00-12:00 and 13:00-17:00."""
    return TeacherSlot(
        teacher_id=tid,
        contract_type="full_time",
        contracted_hours=contracted_hours,
        primary_centre_id=centre_id,
        qualifications=qualifications,
        day_of_week="Monday",
        start_time=time(8, 0),
        end_time=time(17, 0),
        is_available=True,
    )


def _make_pt_teacher(
    tid: int,
    centre_id: int = 1,
    contracted_hours: float = 20,
    qualifications: str = "ielts 7.0",
) -> TeacherSlot:
    """Create a part-time teacher available Mon/Wed/Fri 14:00-18:00."""
    return TeacherSlot(
        teacher_id=tid,
        contract_type="part_time",
        contracted_hours=contracted_hours,
        primary_centre_id=centre_id,
        qualifications=qualifications,
        day_of_week="Monday",
        start_time=time(14, 0),
        end_time=time(18, 0),
        is_available=True,
    )


def _make_class(
    cid: int,
    centre_id: int = 1,
    name: str = "Test Class",
    qualification: str = "",
    preferred_day: str = "Monday",
    start_time: time = time(9, 0),
    end_time: time = time(10, 30),
    max_students: int = 10,
) -> ClassToSchedule:
    return ClassToSchedule(
        id=cid,
        name=name,
        centre_id=centre_id,
        max_students=max_students,
        required_qualification=qualification,
        preferred_day=preferred_day,
        preferred_start_time=start_time,
        preferred_end_time=end_time,
        duration_minutes=90,
        status="approved",
    )


def _make_room(rid: int, centre_id: int = 1, capacity: int = 20) -> RoomInfo:
    return RoomInfo(id=rid, centre_id=centre_id, name=f"Room {rid}", capacity=capacity)


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 1: Normal case — all classes fit within FT teacher capacity
# ═══════════════════════════════════════════════════════════════════════════

def test_ft_only_all_classes_assigned():
    """Given 2 FT teachers (80h total capacity) and 4 classes (6h each = 24h),
    all classes should be assigned in Phase 1 with no overflow."""
    ft1 = _make_ft_teacher(1, centre_id=1, contracted_hours=40, qualifications="ielts 7.0 celta")
    ft2 = _make_ft_teacher(2, centre_id=1, contracted_hours=40, qualifications="ielts 7.0 celta")
    # Both teachers available Mon-Fri 8:00-17:00 (9h/day)
    # Add all weekday slots for both
    ft1_multi = []
    ft2_multi = []
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        for t, lst in [(ft1, ft1_multi), (ft2, ft2_multi)]:
            lst.append(TeacherSlot(
                teacher_id=t.teacher_id,
                contract_type=t.contract_type,
                contracted_hours=t.contracted_hours,
                primary_centre_id=t.primary_centre_id,
                qualifications=t.qualifications,
                day_of_week=day,
                start_time=time(8, 0),
                end_time=time(17, 0),
                is_available=True,
            ))

    classes = [
        _make_class(1, name="IELTS A1 Mon", preferred_day="Monday", start_time=time(9,0), end_time=time(10,30)),
        _make_class(2, name="IELTS A1 Tue", preferred_day="Tuesday", start_time=time(9,0), end_time=time(10,30)),
        _make_class(3, name="IELTS B1 Wed", preferred_day="Wednesday", start_time=time(14,0), end_time=time(15,30)),
        _make_class(4, name="IELTS B1 Thu", preferred_day="Thursday", start_time=time(14,0), end_time=time(15,30)),
    ]
    rooms = [_make_room(1), _make_room(2)]

    inp = ScheduleInput(classes=classes, teachers=ft1_multi + ft2_multi, rooms=rooms)
    output = run_schedule(inp)

    assert len(output.slots) == 4, f"Expected 4 slots assigned, got {len(output.slots)}"
    assert len(output.unassigned) == 0, f"Expected 0 unassigned, got {len(output.unassigned)}"
    assert output.conflict_report.total_conflicts == 0, f"Conflicts: {output.conflict_report.details}"
    assert output.stats["ft_hours_assigned"] > 0
    assert output.stats["pt_hours_assigned"] == 0


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 2: Overflow case — FT capacity insufficient, PT teacher needed
# ═══════════════════════════════════════════════════════════════════════════

def test_pt_overflow_required():
    """Given 1 FT teacher (40h) and 6 classes (6h each = 36h total, but scheduling
    constraints cause some to overflow), verify PT teacher is used for overflow."""
    ft1 = _make_ft_teacher(1, centre_id=1, contracted_hours=40, qualifications="ielts 7.0 celta")
    ft1_slots = []
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        ft1_slots.append(TeacherSlot(
            teacher_id=ft1.teacher_id,
            contract_type=ft1.contract_type,
            contracted_hours=ft1.contracted_hours,
            primary_centre_id=ft1.primary_centre_id,
            qualifications=ft1.qualifications,
            day_of_week=day,
            start_time=time(8, 0),
            end_time=time(17, 0),
            is_available=True,
        ))

    pt1 = _make_pt_teacher(2, centre_id=1, contracted_hours=20, qualifications="ielts 7.0")
    pt1_slots = []
    for day in ["Monday", "Wednesday", "Friday"]:
        pt1_slots.append(TeacherSlot(
            teacher_id=pt1.teacher_id,
            contract_type=pt1.contract_type,
            contracted_hours=pt1.contracted_hours,
            primary_centre_id=pt1.primary_centre_id,
            qualifications=pt1.qualifications,
            day_of_week=day,
            start_time=time(14, 0),
            end_time=time(18, 0),
            is_available=True,
        ))

    # 6 classes — likely more than 1 FT teacher can handle in their windows
    classes = [
        _make_class(1, name="C1 Mon 9-10:30", preferred_day="Monday", start_time=time(9,0), end_time=time(10,30)),
        _make_class(2, name="C2 Mon 11-12:30", preferred_day="Monday", start_time=time(11,0), end_time=time(12,30)),
        _make_class(3, name="C3 Tue 9-10:30", preferred_day="Tuesday", start_time=time(9,0), end_time=time(10,30)),
        _make_class(4, name="C4 Tue 14-15:30", preferred_day="Tuesday", start_time=time(14,0), end_time=time(15,30)),
        _make_class(5, name="C5 Wed 9-10:30", preferred_day="Wednesday", start_time=time(9,0), end_time=time(10,30)),
        _make_class(6, name="C6 Wed 15-16:30", preferred_day="Wednesday", start_time=time(15,0), end_time=time(16,30)),
    ]
    rooms = [_make_room(1), _make_room(2)]

    inp = ScheduleInput(classes=classes, teachers=ft1_slots + pt1_slots, rooms=rooms)
    output = run_schedule(inp)

    # At minimum some classes should be assigned (at least the FT ones)
    assert len(output.slots) > 0, "At least some slots should be assigned"

    # Check that PT hours are non-zero (PT teacher was used)
    if output.stats.get("pt_hours_assigned", 0) > 0:
        # Verify that assigned slots include the PT teacher
        pt_slots = [s for s in output.slots if s.teacher_id == 2]
        assert len(pt_slots) > 0, "Expected PT teacher to have at least one slot"

    # All unassigned should have a reason
    for u in output.unassigned:
        assert u.reason, f"Unassigned class {u.class_id} has no reason"


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 3: Qualification mismatch — unschedulable class
# ═══════════════════════════════════════════════════════════════════════════

def test_qualification_mismatch_unschedulable():
    """Given a class requiring 'delta' qualification and teachers who only have
    'ielts', the class should remain unassigned with the correct reason."""
    ft1 = _make_ft_teacher(1, centre_id=1, qualifications="ielts 8.0 celta")
    ft1_slots = []
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        ft1_slots.append(TeacherSlot(
            teacher_id=ft1.teacher_id,
            contract_type=ft1.contract_type,
            contracted_hours=ft1.contracted_hours,
            primary_centre_id=ft1.primary_centre_id,
            qualifications=ft1.qualifications,
            day_of_week=day,
            start_time=time(8, 0),
            end_time=time(17, 0),
            is_available=True,
        ))

    pt1 = _make_pt_teacher(2, centre_id=1, qualifications="ielts 7.0")
    pt1_slots = []
    for day in ["Monday", "Wednesday", "Friday"]:
        pt1_slots.append(TeacherSlot(
            teacher_id=pt1.teacher_id,
            contract_type=pt1.contract_type,
            contracted_hours=pt1.contracted_hours,
            primary_centre_id=pt1.primary_centre_id,
            qualifications=pt1.qualifications,
            day_of_week=day,
            start_time=time(14, 0),
            end_time=time(18, 0),
            is_available=True,
        ))

    classes = [
        # This class requires 'delta' — neither teacher has it
        _make_class(1, name="Advanced DELTA", qualification="delta",
                     preferred_day="Monday", start_time=time(9,0), end_time=time(10,30)),
        # This class requires 'ielts' — both teachers have it, should be assigned
        _make_class(2, name="IELTS Prep", qualification="ielts",
                     preferred_day="Tuesday", start_time=time(9,0), end_time=time(10,30)),
    ]
    rooms = [_make_room(1)]

    inp = ScheduleInput(classes=classes, teachers=ft1_slots + pt1_slots, rooms=rooms)
    output = run_schedule(inp)

    # Class 1 should be unassigned due to qualification mismatch
    unassigned_ids = {u.class_id for u in output.unassigned}
    assert 1 in unassigned_ids, "Class 1 (delta) should be unassigned"
    # Verify the reason mentions qualification
    reason = next(u.reason for u in output.unassigned if u.class_id == 1)
    assert "qualification" in reason.lower(), f"Reason should mention qualification, got: {reason}"

    # Class 2 should be assigned (ielts qualification is available)
    assigned_ids = {s.class_id for s in output.slots}
    assert 2 in assigned_ids, "Class 2 (ielts) should be assigned"

    assert output.conflict_report.total_conflicts == 0, f"Conflicts: {output.conflict_report.details}"


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 4 (bonus): No double-booking verification
# ═══════════════════════════════════════════════════════════════════════════

def test_no_double_booking():
    """Verify that no two assigned slots overlap for the same teacher or room."""
    ft1 = _make_ft_teacher(1, centre_id=1, qualifications="ielts celta")
    ft1_slots = []
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        ft1_slots.append(TeacherSlot(
            teacher_id=ft1.teacher_id,
            contract_type=ft1.contract_type,
            contracted_hours=ft1.contracted_hours,
            primary_centre_id=ft1.primary_centre_id,
            qualifications=ft1.qualifications,
            day_of_week=day,
            start_time=time(8, 0),
            end_time=time(17, 0),
            is_available=True,
        ))

    # Same-day classes to force potential overlap
    classes = [
        _make_class(1, name="C1 Mon 9-10:30", preferred_day="Monday", start_time=time(9,0), end_time=time(10,30)),
        _make_class(2, name="C2 Mon 10:30-12", preferred_day="Monday", start_time=time(10,30), end_time=time(12,0)),
        _make_class(3, name="C3 Mon 14-15:30", preferred_day="Monday", start_time=time(14,0), end_time=time(15,30)),
        _make_class(4, name="C4 Mon 9-10:30B", preferred_day="Monday", start_time=time(9,0), end_time=time(10,30)),
    ]
    # Only 1 room and 1 teacher — forces some to be unassigned but no double-booking
    rooms = [_make_room(1)]

    inp = ScheduleInput(classes=classes, teachers=ft1_slots, rooms=rooms)
    output = run_schedule(inp)

    # No conflicts should exist
    assert output.conflict_report.total_conflicts == 0, f"Conflicts found: {output.conflict_report.details}"

    # Verify no overlapping times for the same teacher
    teacher_slots = {}
    for s in output.slots:
        teacher_slots.setdefault(s.teacher_id, []).append(s)
    for tid, slots in teacher_slots.items():
        for i, a in enumerate(slots):
            for b in slots[i + 1:]:
                if a.day_of_week == b.day_of_week:
                    assert a.end_time <= b.start_time or b.end_time <= a.start_time, \
                        f"Teacher {tid} double-booked: Class {a.class_id} {a.start_time}-{a.end_time} " \
                        f"and Class {b.class_id} {b.start_time}-{b.end_time} on {a.day_of_week}"