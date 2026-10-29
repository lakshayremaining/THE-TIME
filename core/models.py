"""
core/models.py
Data models and structure definitions for AI Timetable Scheduler.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Set
import json


@dataclass
class Subject:
    code: str
    name: str
    weekly_hours: int
    is_lab: bool = False  # False = theory, True = lab
    requires_consecutive: bool = False  # True for multi-hour labs


@dataclass
class Teacher:
    name: str
    subjects_can_teach: List[str]
    max_weekly_load: int
    unavailable_slots: List[Tuple[str, int]] = field(default_factory=list)  # (day, period)
    preferred_slots: List[Tuple[str, int]] = field(default_factory=list)  # (day, period)


@dataclass
class ClassBatch:
    name: str
    strength: int
    subject_codes: List[str]
    lunch_break_period: int  # 1-indexed period number for lunch (e.g. period 4)


@dataclass
class Room:
    name: str
    capacity: int
    is_lab: bool = False  # False = classroom, True = lab


@dataclass
class TimeStructure:
    days: List[str]  # e.g., ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    periods_per_day: int  # e.g., 6 or 7
    break_periods: List[int] = field(default_factory=list)  # Periods marked as global breaks if any
    period_times: List[str] = field(default_factory=list)  # e.g., ["9:00-10:00 AM", ...]


@dataclass
class SessionVariable:
    """
    Represents an atomic variable in the CSP:
    One lecture or lab period session to be scheduled.
    """
    var_id: str
    class_name: str
    subject_code: str
    teacher_name: str
    session_index: int  # 1 to weekly_hours
    is_lab: bool = False
    consecutive_with: Optional[str] = None  # ID of linked consecutive session
    block_vars: List[str] = field(default_factory=list)  # All variable IDs in this continuous block (e.g. 2hr, 3hr)
    block_offset: int = 0  # 0 for 1st hour, 1 for 2nd hour, 2 for 3rd hour


@dataclass
class SlotAssignment:
    """
    Value assigned to a SessionVariable in the domain:
    (day, period, room_name)
    """
    day: str
    period: int
    room_name: str

    def to_tuple(self) -> Tuple[str, int, str]:
        return (self.day, self.period, self.room_name)


@dataclass
class TimetableProblem:
    """
    Encapsulates the complete scheduling problem specification.
    """
    name: str
    time_structure: TimeStructure
    subjects: Dict[str, Subject]
    teachers: Dict[str, Teacher]
    classes: Dict[str, ClassBatch]
    rooms: Dict[str, Room]
    variables: List[SessionVariable] = field(default_factory=list)

    def validate_input(self) -> Tuple[bool, List[str]]:
        """
        Validate inputs for basic feasibility:
        - Room capacity vs Class strength
        - Total required hours vs available room slots
        - Teacher qualifications and maximum loads
        """
        errors = []
        total_slots_per_room = len(self.time_structure.days) * self.time_structure.periods_per_day
        total_room_slots = total_slots_per_room * len(self.rooms)

        total_required_hours = sum(
            self.subjects[s_code].weekly_hours
            for c in self.classes.values()
            for s_code in c.subject_codes
            if s_code in self.subjects
        )

        if total_required_hours > total_room_slots:
            errors.append(
                f"Infeasible: Total required session hours ({total_required_hours}) "
                f"exceed total room-slot capacity ({total_room_slots})."
            )

        # Check classrooms and lab rooms exist
        lab_rooms = [r for r in self.rooms.values() if r.is_lab]
        theory_rooms = [r for r in self.rooms.values() if not r.is_lab]

        if not theory_rooms:
            errors.append("Infeasible: No classrooms defined for theory sessions.")

        has_labs = any(s.is_lab for s in self.subjects.values())
        if has_labs and not lab_rooms:
            errors.append("Infeasible: Lab subjects exist but no lab rooms are defined.")

        # Check teacher assignments & load
        teacher_subject_map = {t.name: set(t.subjects_can_teach) for t in self.teachers.values()}
        teacher_assigned_hours: Dict[str, int] = {t.name: 0 for t in self.teachers.values()}

        for c in self.classes.values():
            for s_code in c.subject_codes:
                if s_code not in self.subjects:
                    errors.append(f"Subject '{s_code}' required by class '{c.name}' is not defined.")
                    continue
                subj = self.subjects[s_code]
                qualified_teachers = [
                    t_name for t_name, subjs in teacher_subject_map.items() if s_code in subjs
                ]
                if not qualified_teachers:
                    errors.append(f"No teacher qualified to teach subject '{s_code}' for class '{c.name}'.")

                eligible_rooms = [
                    r for r in self.rooms.values()
                    if r.capacity >= c.strength and r.is_lab == subj.is_lab
                ]
                if not eligible_rooms:
                    room_type = "Lab" if subj.is_lab else "Classroom"
                    errors.append(
                        f"No suitable {room_type} found with capacity >= {c.strength} for class '{c.name}' taking '{s_code}'."
                    )

        return len(errors) == 0, errors

    def generate_variables(self, teacher_mapping: Optional[Dict[Tuple[str, str], str]] = None) -> List[SessionVariable]:
        """
        Decomposes class subject requirements into atomic SessionVariables.
        If teacher_mapping is provided: (class_name, subject_code) -> teacher_name.
        Otherwise, assigns the first available qualified teacher.
        """
        variables = []
        teacher_loads: Dict[str, int] = {t: 0 for t in self.teachers}

        # Build qualified map
        qualified_for_subj: Dict[str, List[Teacher]] = {}
        for s_code in self.subjects:
            qualified_for_subj[s_code] = [
                t for t in self.teachers.values() if s_code in t.subjects_can_teach
            ]

        for c_name, c_batch in self.classes.items():
            for s_code in c_batch.subject_codes:
                subj = self.subjects[s_code]
                
                # Determine teacher
                teacher_name = None
                if teacher_mapping and (c_name, s_code) in teacher_mapping:
                    teacher_name = teacher_mapping[(c_name, s_code)]
                else:
                    # Pick qualified teacher with lowest current load
                    candidates = qualified_for_subj.get(s_code, [])
                    if candidates:
                        candidates_sorted = sorted(candidates, key=lambda t: teacher_loads[t.name])
                        teacher_name = candidates_sorted[0].name

                if not teacher_name:
                    continue

                hours = subj.weekly_hours
                teacher_loads[teacher_name] += hours

                # If it's a lab with consecutive requirement (e.g. 2 hours or 3 hours)
                if subj.is_lab and subj.requires_consecutive and hours >= 2:
                    block_sizes = [2, 2] if hours == 4 else [hours]
                    sess_counter = 1
                    for b_size in block_sizes:
                        b_ids = [f"{c_name}_{s_code}_s{sess_counter + k}" for k in range(b_size)]
                        for k in range(b_size):
                            v_id = b_ids[k]
                            v = SessionVariable(
                                var_id=v_id,
                                class_name=c_name,
                                subject_code=s_code,
                                teacher_name=teacher_name,
                                session_index=sess_counter + k,
                                is_lab=True,
                                consecutive_with=b_ids[k + 1] if k + 1 < b_size else (b_ids[k - 1] if k > 0 else None),
                                block_vars=b_ids,
                                block_offset=k
                            )
                            variables.append(v)
                        sess_counter += b_size
                else:
                    for session_idx in range(1, hours + 1):
                        v_id = f"{c_name}_{s_code}_s{session_idx}"
                        variables.append(
                            SessionVariable(
                                var_id=v_id,
                                class_name=c_name,
                                subject_code=s_code,
                                teacher_name=teacher_name,
                                session_index=session_idx,
                                is_lab=subj.is_lab,
                                block_vars=[v_id],
                                block_offset=0
                            )
                        )

        self.variables = variables
        return variables

    def get_domain_for_variable(self, var: SessionVariable) -> List[SlotAssignment]:
        """
        Returns all valid (day, period, room) triples satisfying unary constraints:
        - Room capacity >= class strength
        - Room type matches session type (lab vs classroom)
        - Class lunch break is avoided (and entire multi-hour block does not cross lunch)
        - Teacher unavailable slots are avoided
        """
        c_batch = self.classes[var.class_name]
        teacher = self.teachers[var.teacher_name]
        unavailable_set = set(teacher.unavailable_slots)

        valid_rooms = [
            r for r in self.rooms.values()
            if r.capacity >= c_batch.strength and r.is_lab == var.is_lab
        ]

        block_len = len(var.block_vars) if var.block_vars else 1
        k_offset = var.block_offset

        domain = []
        for day in self.time_structure.days:
            for p in range(1, self.time_structure.periods_per_day + 1):
                p_start = p - k_offset
                p_end = p_start + block_len - 1

                # Entire block must fit inside working hours
                if p_start < 1 or p_end > self.time_structure.periods_per_day:
                    continue

                # Entire block must avoid lunch break
                block_periods = list(range(p_start, p_end + 1))
                if c_batch.lunch_break_period in block_periods:
                    continue

                # Entire block must avoid teacher unavailable slots
                if any((day, bp) in unavailable_set for bp in block_periods):
                    continue

                for room in valid_rooms:
                    domain.append(SlotAssignment(day=day, period=p, room_name=room.name))

        return domain

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "time_structure": {
                "days": self.time_structure.days,
                "periods_per_day": self.time_structure.periods_per_day,
                "break_periods": self.time_structure.break_periods,
                "period_times": self.time_structure.period_times
            },
            "subjects": {k: v.__dict__ for k, v in self.subjects.items()},
            "teachers": {
                k: {
                    "name": v.name,
                    "subjects_can_teach": v.subjects_can_teach,
                    "max_weekly_load": v.max_weekly_load,
                    "unavailable_slots": v.unavailable_slots,
                    "preferred_slots": v.preferred_slots
                }
                for k, v in self.teachers.items()
            },
            "classes": {k: v.__dict__ for k, v in self.classes.items()},
            "rooms": {k: v.__dict__ for k, v in self.rooms.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimetableProblem":
        time_struct = TimeStructure(
            days=data["time_structure"]["days"],
            periods_per_day=data["time_structure"]["periods_per_day"],
            break_periods=data["time_structure"].get("break_periods", []),
            period_times=data["time_structure"].get("period_times", [])
        )
        subjects = {
            k: Subject(**v) for k, v in data["subjects"].items()
        }
        teachers = {}
        for k, v in data["teachers"].items():
            unavail = [tuple(x) for x in v.get("unavailable_slots", [])]
            pref = [tuple(x) for x in v.get("preferred_slots", [])]
            teachers[k] = Teacher(
                name=v["name"],
                subjects_can_teach=v["subjects_can_teach"],
                max_weekly_load=v["max_weekly_load"],
                unavailable_slots=unavail,
                preferred_slots=pref
            )
        classes = {
            k: ClassBatch(**v) for k, v in data["classes"].items()
        }
        rooms = {
            k: Room(**v) for k, v in data["rooms"].items()
        }
        problem = cls(
            name=data.get("name", "TimetableProblem"),
            time_structure=time_struct,
            subjects=subjects,
            teachers=teachers,
            classes=classes,
            rooms=rooms
        )
        problem.generate_variables()
        return problem
