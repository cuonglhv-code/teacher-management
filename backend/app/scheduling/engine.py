"""
JTWMS Scheduling Engine — Two-phase constraint solver.

Phase 1:  Assign only FULL-TIME teachers, maximise utilisation up to contracted hours.
Phase 2:  Assign PART-TIME teachers to remaining (overflow) classes.

Hard constraints (all phases):
  1. No double-booking — a teacher cannot be in two places at the same day+time.
  2. No double-booking — a room cannot host two classes at the same day+time.
  3. Room capacity >= class max_students.
  4. Teacher qualification matches class required_teacher_qualification.
  5. Teacher is available (day_of_week / time window), not on leave.
  6. FT teacher must not exceed contracted_hours (hard ceiling).

Soft constraints (weighted scoring):
  +500  FT utilisation (fill an FT hour)
  +200  Teacher's primary centre matches class centre
  +100  Preferred day matches
   -50  Per hour of remaining contracted capacity (encourage filling earlier)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import time, date
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Data classes for the scheduler input / output ─────────────────────────

@dataclass
class TeacherSlot:
    """A teacher's availability window for a given day."""
    teacher_id: int
    contract_type: str            # "full_time" | "part_time"
    contracted_hours: float
    primary_centre_id: int
    qualifications: str           # comma-separated or space-separated tokens
    day_of_week: str              # "Monday" .. "Sunday"
    start_time: time
    end_time: time
    is_available: bool
    # Running total of hours already scheduled for this teacher in this run
    scheduled_hours: float = 0.0


@dataclass
class ClassToSchedule:
    id: int
    name: str
    centre_id: int
    max_students: int
    required_qualification: str
    preferred_day: Optional[str]
    preferred_start_time: Optional[time]
    preferred_end_time: Optional[time]
    duration_minutes: int
    status: str                     # should be "approved" for scheduling


@dataclass
class RoomInfo:
    id: int
    centre_id: int
    name: str
    capacity: int


@dataclass
class ScheduleInput:
    classes: list[ClassToSchedule]
    teachers: list[TeacherSlot]
    rooms: list[RoomInfo]


# ─── Output data classes ───────────────────────────────────────────────────

@dataclass
class ScheduledSlot:
    """One assigned timetable slot (result)."""
    class_id: int
    teacher_id: int
    room_id: int
    day_of_week: str
    start_time: time
    end_time: time
    is_draft: bool = True


@dataclass
class UnassignedClass:
    class_id: int
    reason: str


@dataclass
class ConflictReport:
    total_conflicts: int
    details: list[str]


@dataclass
class ScheduleOutput:
    slots: list[ScheduledSlot]
    unassigned: list[UnassignedClass]
    conflict_report: ConflictReport
    stats: dict = field(default_factory=dict)


# ─── Helper: tokenise qualification string ─────────────────────────────────

def _qual_tokens(q: Optional[str]) -> set[str]:
    if not q:
        return set()
    return {t.strip().lower() for t in q.replace(",", " ").split() if t.strip()}


def _teacher_qualifies(teacher_qual: str, class_required: str) -> bool:
    """Return True if teacher qualification covers the class requirement."""
    if not class_required:
        return True  # no requirement means anyone can teach
    tq = _qual_tokens(teacher_qual)
    rq = _qual_tokens(class_required)
    # The teacher must have ALL required tokens
    return rq.issubset(tq)


# ─── Helper: time overlap ──────────────────────────────────────────────────

def _times_overlap(
    s1: time, e1: time,
    s2: time, e2: time,
) -> bool:
    return s1 < e2 and s2 < e1


def _duration_hours(start: time, end: time) -> float:
    """Return duration in hours between two time objects (assume same day)."""
    secs = (end.hour * 3600 + end.minute * 60) - (start.hour * 3600 + start.minute * 60)
    return max(0, secs / 3600.0)


# ─── Core state for the solver ─────────────────────────────────────────────

class _SchedulingState:
    """Tracks assignments and remaining capacity during the solve."""

    def __init__(self, inp: ScheduleInput):
        self.input = inp
        self.slots: list[ScheduledSlot] = []
        self.unassigned: list[UnassignedClass] = []

        # Build lookup structures
        self.teacher_avail: dict[int, list[TeacherSlot]] = {}
        self.teacher_contract_type: dict[int, str] = {}
        self.teacher_contracted_hours: dict[int, float] = {}
        self.teacher_scheduled_hours: dict[int, float] = {}
        self.teacher_primary_centre: dict[int, int] = {}
        self.teacher_qualifications: dict[int, str] = {}
        for t in inp.teachers:
            self.teacher_avail.setdefault(t.teacher_id, []).append(t)
            self.teacher_contract_type[t.teacher_id] = t.contract_type
            self.teacher_contracted_hours[t.teacher_id] = t.contracted_hours
            self.teacher_scheduled_hours[t.teacher_id] = t.scheduled_hours
            self.teacher_primary_centre[t.teacher_id] = t.primary_centre_id
            self.teacher_qualifications[t.teacher_id] = t.qualifications

        self.rooms_by_centre: dict[int, list[RoomInfo]] = {}
        for r in inp.rooms:
            self.rooms_by_centre.setdefault(r.centre_id, []).append(r)

        # Booked time ranges per teacher: teacher_id -> [(day, start, end)]
        self.teacher_booked: dict[int, list[tuple[str, time, time]]] = {}
        # Booked time ranges per room: room_id -> [(day, start, end)]
        self.room_booked: dict[int, list[tuple[str, time, time]]] = {}

    def teacher_is_available(self, tid: int, day: str, start: time, end: time) -> bool:
        """Check if teacher has an availability window covering this slot."""
        for av in self.teacher_avail.get(tid, []):
            if av.day_of_week == day and av.is_available and \
               av.start_time <= start and av.end_time >= end:
                return True
        return False

    def teacher_has_hours_remaining(self, tid: int, additional_hours: float) -> bool:
        ct = self.teacher_contract_type.get(tid)
        if ct == "full_time":
            cap = self.teacher_contracted_hours.get(tid, 0)
            used = self.teacher_scheduled_hours.get(tid, 0)
            return (used + additional_hours) <= cap + 0.001  # small tolerance
        # PT: no hard ceiling, but we respect their confirmed availability
        return True

    def can_assign(self, tid: int, rid: int, day: str, start: time, end: time) -> Optional[str]:
        """Check hard constraints. Return None if OK, or a conflict reason string."""
        hours = _duration_hours(start, end)

        # 1. Teacher availability
        if not self.teacher_is_available(tid, day, start, end):
            return f"Teacher {tid} not available on {day} {start}-{end}"

        # 2. Teacher double-booking
        for b_day, b_start, b_end in self.teacher_booked.get(tid, []):
            if b_day == day and _times_overlap(start, end, b_start, b_end):
                return f"Teacher {tid} already booked on {day} {b_start}-{b_end}"

        # 3. Room double-booking
        for b_day, b_start, b_end in self.room_booked.get(rid, []):
            if b_day == day and _times_overlap(start, end, b_start, b_end):
                return f"Room {rid} already booked on {day} {b_start}-{b_end}"

        # 4. Contracted hours ceiling (FT only)
        if not self.teacher_has_hours_remaining(tid, hours):
            ct = self.teacher_contract_type.get(tid, "?")
            if ct == "full_time":
                return f"Teacher {tid} FT contracted hours would be exceeded"

        return None

    def book(self, slot: ScheduledSlot):
        """Record a booking in the state."""
        self.slots.append(slot)
        hours = _duration_hours(slot.start_time, slot.end_time)
        self.teacher_scheduled_hours[slot.teacher_id] = \
            self.teacher_scheduled_hours.get(slot.teacher_id, 0) + hours
        self.teacher_booked.setdefault(slot.teacher_id, []).append(
            (slot.day_of_week, slot.start_time, slot.end_time))
        self.room_booked.setdefault(slot.room_id, []).append(
            (slot.day_of_week, slot.start_time, slot.end_time))


# ─── Phase 1: FT-only scheduling ───────────────────────────────────────────

def _phase1(state: _SchedulingState) -> list[int]:
    """Assign approved classes using only FT teachers.

    Returns a list of class_ids that could NOT be placed (overflow).
    """
    ft_teachers = [
        t for t in state.input.teachers
        if t.contract_type == "full_time"
    ]
    ft_ids = {t.teacher_id for t in ft_teachers}
    return _greedy_assign(state, ft_ids, phase=1)


# ─── Phase 2: PT overflow scheduling ───────────────────────────────────────

def _phase2(state: _SchedulingState, overflow_class_ids: list[int]) -> list[int]:
    """Assign overflow classes using PT teachers.

    Returns list of class_ids that remain unassigned.
    """
    pt_teachers = [
        t for t in state.input.teachers
        if t.contract_type == "part_time"
    ]
    pt_ids = {t.teacher_id for t in pt_teachers}
    return _greedy_assign(state, pt_ids, phase=2, only_ids=overflow_class_ids)


# ─── Greedy assignment core ────────────────────────────────────────────────

def _greedy_assign(
    state: _SchedulingState,
    allowed_teacher_ids: set[int],
    phase: int,
    only_ids: Optional[list[int]] = None,
) -> list[int]:
    """Greedily assign classes to allowed teachers.

    Sort classes by fewest feasible teachers (most constrained first).
    For each class, try each feasible teacher+room+time, pick the highest-scoring
    assignment that satisfies all hard constraints.

    Returns list of class_ids that remain unassigned.
    """
    # Determine which classes to process
    if only_ids is not None:
        classes_to_schedule = [c for c in state.input.classes if c.id in only_ids]
    else:
        classes_to_schedule = [c for c in state.input.classes]

    # Pre-filter: only classes with approved status
    classes_to_schedule = [c for c in classes_to_schedule if c.status == "approved"]

    # Build feasible teacher list for each class (for ranking)
    def _feasible_teachers(cls: ClassToSchedule) -> list[int]:
        """Return sorted list of teacher ids that could potentially teach this class."""
        feasible = []
        for tid in allowed_teacher_ids:
            qual = state.teacher_qualifications.get(tid, "")
            if not _teacher_qualifies(qual, cls.required_qualification):
                continue
            feasible.append(tid)
        return feasible

    # Sort classes: fewest feasible teachers first (most constrained)
    ranked = []
    for cls in classes_to_schedule:
        feas = _feasible_teachers(cls)
        ranked.append((len(feas), cls, feas))
    ranked.sort(key=lambda x: x[0])  # asc by count

    unassigned_ids: list[int] = []

    for cnt, cls, feasible_tids in ranked:
        if cnt == 0:
            unassigned_ids.append(cls.id)
            state.unassigned.append(UnassignedClass(
                class_id=cls.id,
                reason=f"No teacher available with required qualification '{cls.required_qualification}'",
            ))
            continue

        best_score = -1e9
        best_slot: Optional[ScheduledSlot] = None

        # Determine eligible rooms (same centre)
        rooms = state.rooms_by_centre.get(cls.centre_id, [])
        suitable_rooms = [r for r in rooms if r.capacity >= cls.max_students]

        for tid in feasible_tids:
            teacher_primary = state.teacher_primary_centre.get(tid)
            ct = state.teacher_contract_type.get(tid, "")

            # Determine time windows to try: use preferred time, or whole day
            day_candidates = []
            if cls.preferred_day:
                day_candidates.append(cls.preferred_day)
            else:
                # Try all weekdays if no preference
                for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
                    day_candidates.append(d)

            for day in day_candidates:
                # Determine time range for this day
                if cls.preferred_start_time and cls.preferred_end_time:
                    time_windows = [(cls.preferred_start_time, cls.preferred_end_time)]
                else:
                    # Default window: 8:00 - 12:00, 13:00 - 17:00, 17:00 - 21:00
                    time_windows = [
                        (time(8, 0), time(12, 0)),
                        (time(13, 0), time(17, 0)),
                        (time(17, 0), time(21, 0)),
                    ]

                for start, end in time_windows:
                    actual_end = end
                    actual_start = start
                    if cls.duration_minutes:
                        # If duration is specified, compute end from start
                        mins = cls.duration_minutes
                        h = start.hour + (start.minute + mins) // 60
                        m = (start.minute + mins) % 60
                        if h < 24:
                            actual_end = time(h, m)

                    if actual_end <= actual_start:
                        continue

                    for room in suitable_rooms:
                        conflict = state.can_assign(tid, room.id, day, actual_start, actual_end)
                        if conflict:
                            continue

                        # Scoring
                        score = 0
                        # +500 for FT fill (phase 1 only conceptually; we still score for both)
                        if ct == "full_time":
                            score += 500
                        # +200 centre match
                        if teacher_primary == cls.centre_id:
                            score += 200
                        # +100 preferred day match
                        if cls.preferred_day and cls.preferred_day == day:
                            score += 100
                        # -50 per remaining contracted hour (encourage packing)
                        remaining = state.teacher_contracted_hours.get(tid, 0) - \
                            state.teacher_scheduled_hours.get(tid, 0)
                        score -= 50 * max(0, remaining)

                        if score > best_score:
                            best_score = score
                            best_slot = ScheduledSlot(
                                class_id=cls.id,
                                teacher_id=tid,
                                room_id=room.id,
                                day_of_week=day,
                                start_time=actual_start,
                                end_time=actual_end,
                                is_draft=True,
                            )

        if best_slot is not None:
            state.book(best_slot)
        else:
            unassigned_ids.append(cls.id)
            state.unassigned.append(UnassignedClass(
                class_id=cls.id,
                reason="No feasible (teacher, room, time) combination found",
            ))

    return unassigned_ids


# ─── Conflict detection (post-hoc) ─────────────────────────────────────────

def _detect_conflicts(state: _SchedulingState) -> ConflictReport:
    """Re-check all assigned slots for any violations and return a report."""
    details: list[str] = []
    # Teacher double-booking
    teacher_slots: dict[int, list[ScheduledSlot]] = {}
    for s in state.slots:
        teacher_slots.setdefault(s.teacher_id, []).append(s)
    for tid, slots in teacher_slots.items():
        for i, a in enumerate(slots):
            for b in slots[i + 1:]:
                if a.day_of_week == b.day_of_week and \
                   _times_overlap(a.start_time, a.end_time, b.start_time, b.end_time):
                    details.append(
                        f"CONFLICT: Teacher {tid} double-booked on {a.day_of_week} "
                        f"(Class {a.class_id} {a.start_time}-{a.end_time} vs "
                        f"Class {b.class_id} {b.start_time}-{b.end_time})"
                    )
    # Room double-booking
    room_slots: dict[int, list[ScheduledSlot]] = {}
    for s in state.slots:
        room_slots.setdefault(s.room_id, []).append(s)
    for rid, slots in room_slots.items():
        for i, a in enumerate(slots):
            for b in slots[i + 1:]:
                if a.day_of_week == b.day_of_week and \
                   _times_overlap(a.start_time, a.end_time, b.start_time, b.end_time):
                    details.append(
                        f"CONFLICT: Room {rid} double-booked on {a.day_of_week} "
                        f"(Class {a.class_id} vs Class {b.class_id})"
                    )
    # FT hour ceiling check
    ft_hours: dict[int, float] = {}
    for s in state.slots:
        tid = s.teacher_id
        if state.teacher_contract_type.get(tid) == "full_time":
            ft_hours[tid] = ft_hours.get(tid, 0) + _duration_hours(s.start_time, s.end_time)
    for tid, hrs in ft_hours.items():
        cap = state.teacher_contracted_hours.get(tid, 0)
        if hrs > cap + 0.01:
            details.append(
                f"CONFLICT: FT Teacher {tid} scheduled {hrs:.1f}h vs contracted {cap}h"
            )

    return ConflictReport(total_conflicts=len(details), details=details)


# ─── Public API ────────────────────────────────────────────────────────────

def run_schedule(inp: ScheduleInput) -> ScheduleOutput:
    """Execute the two-phase scheduling algorithm and return results.

    Args:
        inp: All input data (classes, teachers with availability, rooms).

    Returns:
        ScheduleOutput with assigned slots, unassigned list, and conflict report.
    """
    state = _SchedulingState(inp)

    logger.info("Phase 1: Scheduling FT teachers...")
    overflow = _phase1(state)
    logger.info(f"Phase 1 complete: {len(state.slots)} slots assigned, "
                f"{len(overflow)} classes to overflow")

    if overflow:
        logger.info("Phase 2: Scheduling PT teachers for overflow classes...")
        still_unassigned = _phase2(state, overflow)
        logger.info(f"Phase 2 complete: {len(overflow) - len(still_unassigned)} "
                    f"overflow classes assigned, {len(still_unassigned)} still unassigned")

    conflicts = _detect_conflicts(state)

    # Collect stats
    ft_hours_assigned = sum(
        _duration_hours(s.start_time, s.end_time)
        for s in state.slots
        if state.teacher_contract_type.get(s.teacher_id) == "full_time"
    )
    pt_hours_assigned = sum(
        _duration_hours(s.start_time, s.end_time)
        for s in state.slots
        if state.teacher_contract_type.get(s.teacher_id) == "part_time"
    )

    return ScheduleOutput(
        slots=state.slots,
        unassigned=state.unassigned,
        conflict_report=conflicts,
        stats={
            "total_slots_assigned": len(state.slots),
            "total_unassigned": len(state.unassigned),
            "ft_hours_assigned": round(ft_hours_assigned, 1),
            "pt_hours_assigned": round(pt_hours_assigned, 1),
            "total_conflicts": conflicts.total_conflicts,
        },
    )