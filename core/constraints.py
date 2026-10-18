"""
core/constraints.py
Comprehensive constraint checking and violation detection for Timetable CSP.
Supports Hard Constraints (H1-H9), Soft Constraints (S1-S5), and detailed diagnostic reporting.
"""

from typing import Dict, List, Tuple, Set, Optional, Any
from collections import defaultdict
from core.models import TimetableProblem, SessionVariable, SlotAssignment


class ConstraintChecker:
    """
    Evaluates timetable assignments against all Hard (H1-H9) and Soft (S1-S5) constraints.
    Reused across CSP backtracking, Min-Conflicts, Simulated Annealing, and the UI manual editor.
    """

    def __init__(self, problem: TimetableProblem):
        self.problem = problem
        self.var_map: Dict[str, SessionVariable] = {v.var_id: v for v in self.problem.variables}
        self.subject_map = self.problem.subjects
        self.class_map = self.problem.classes
        self.teacher_map = self.problem.teachers
        self.room_map = self.problem.rooms
        self.time_structure = self.problem.time_structure

    def count_hard_violations(
        self, assignment: Dict[str, SlotAssignment]
    ) -> Tuple[int, List[str]]:
        """
        Evaluates Hard Constraints H1-H9 on a complete or partial assignment.
        Returns:
            (violations_count, list_of_human_readable_conflict_strings)
        """
        conflicts = []
        violations_count = 0

        # Data structures for conflict tracking
        # (day, period, teacher) -> list of var_ids
        teacher_slots = defaultdict(list)
        # (day, period, class) -> list of var_ids
        class_slots = defaultdict(list)
        # (day, period, room) -> list of var_ids
        room_slots = defaultdict(list)
        # teacher -> count of sessions assigned
        teacher_hours = defaultdict(int)

        for var_id, slot in assignment.items():
            var = self.var_map.get(var_id)
            if not var:
                continue

            day = slot.day
            period = slot.period
            room_name = slot.room_name
            room = self.room_map.get(room_name)
            c_batch = self.class_map.get(var.class_name)
            teacher = self.teacher_map.get(var.teacher_name)

            # --- H4: Room Capacity ---
            if room and c_batch:
                if room.capacity < c_batch.strength:
                    violations_count += 1
                    conflicts.append(
                        f"[H4 - Room Capacity] Room '{room_name}' (cap: {room.capacity}) "
                        f"is too small for class '{c_batch.name}' (strength: {c_batch.strength}) "
                        f"in session '{var.subject_code}' on {day} P{period}."
                    )

            # --- H5: Room Type (Lab vs Theory) ---
            if room:
                if var.is_lab and not room.is_lab:
                    violations_count += 1
                    conflicts.append(
                        f"[H5 - Room Type] Lab session '{var.subject_code}' of class '{var.class_name}' "
                        f"scheduled in classroom '{room_name}' on {day} P{period}."
                    )
                elif not var.is_lab and room.is_lab:
                    violations_count += 1
                    conflicts.append(
                        f"[H5 - Room Type] Theory session '{var.subject_code}' of class '{var.class_name}' "
                        f"scheduled in lab room '{room_name}' on {day} P{period}."
                    )

            # --- H6: Teacher Availability ---
            if teacher:
                if (day, period) in teacher.unavailable_slots:
                    violations_count += 1
                    conflicts.append(
                        f"[H6 - Teacher Unavailable] Teacher '{teacher.name}' is unavailable on "
                        f"{day} Period {period} (assigned {var.subject_code} for {var.class_name})."
                    )

            # --- H9: Lunch Break Conflict ---
            if c_batch and period == c_batch.lunch_break_period:
                violations_count += 1
                conflicts.append(
                    f"[H9 - Lunch Break] Class '{var.class_name}' has lunch break during Period {period}, "
                    f"but session '{var.subject_code}' is scheduled on {day}."
                )

            # Record slot occupancy for overlap checks
            teacher_slots[(day, period, var.teacher_name)].append(var_id)
            class_slots[(day, period, var.class_name)].append(var_id)
            room_slots[(day, period, room_name)].append(var_id)
            teacher_hours[var.teacher_name] += 1

        # --- H1: Teacher Overlaps (teacher in 2 places at once) ---
        for (day, period, teacher_name), vars_in_slot in teacher_slots.items():
            if len(vars_in_slot) > 1:
                overlap_count = len(vars_in_slot) - 1
                violations_count += overlap_count
                clashing_details = ", ".join(
                    f"{self.var_map[vid].class_name} ({self.var_map[vid].subject_code})"
                    for vid in vars_in_slot
                )
                conflicts.append(
                    f"[H1 - Teacher Clash] Teacher '{teacher_name}' double-booked on {day} Period {period}: {clashing_details}."
                )

        # --- H2: Class Overlaps (class has 2 sessions at once) ---
        for (day, period, class_name), vars_in_slot in class_slots.items():
            if len(vars_in_slot) > 1:
                overlap_count = len(vars_in_slot) - 1
                violations_count += overlap_count
                clashing_subjects = ", ".join(self.var_map[vid].subject_code for vid in vars_in_slot)
                conflicts.append(
                    f"[H2 - Class Clash] Class '{class_name}' has multiple sessions on {day} Period {period}: {clashing_subjects}."
                )

        # --- H3: Room Overlaps (room hosting 2 sessions at once) ---
        for (day, period, room_name), vars_in_slot in room_slots.items():
            if len(vars_in_slot) > 1:
                overlap_count = len(vars_in_slot) - 1
                violations_count += overlap_count
                clashing_sessions = ", ".join(
                    f"{self.var_map[vid].class_name}-{self.var_map[vid].subject_code}"
                    for vid in vars_in_slot
                )
                conflicts.append(
                    f"[H3 - Room Clash] Room '{room_name}' has multiple sessions on {day} Period {period}: {clashing_sessions}."
                )

        # --- H8: Teacher Maximum Weekly Load ---
        for teacher_name, assigned_load in teacher_hours.items():
            teacher = self.teacher_map.get(teacher_name)
            if teacher and assigned_load > teacher.max_weekly_load:
                excess = assigned_load - teacher.max_weekly_load
                violations_count += excess
                conflicts.append(
                    f"[H8 - Teacher Overload] Teacher '{teacher_name}' assigned {assigned_load} hours, "
                    f"exceeding max load of {teacher.max_weekly_load}."
                )

        # --- Strict 2-Hour Lab Block Constraint (Consecutive Periods) ---
        checked_pairs = set()
        for var_id, var in self.var_map.items():
            if var.is_lab and var.consecutive_with and var_id in assignment and var.consecutive_with in assignment:
                pair_key = tuple(sorted([var_id, var.consecutive_with]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)

                s1 = assignment[var_id]
                s2 = assignment[var.consecutive_with]
                c_batch = self.class_map.get(var.class_name)
                lunch_p = c_batch.lunch_break_period if c_batch else -1

                is_consecutive_block = (
                    s1.day == s2.day
                    and s1.room_name == s2.room_name
                    and abs(s1.period - s2.period) == 1
                    and s1.period != lunch_p
                    and s2.period != lunch_p
                )
                if not is_consecutive_block:
                    violations_count += 1
                    conflicts.append(
                        f"[H-Lab - 2-Hour Block Clashed] Lab '{var.subject_code}' for '{var.class_name}' "
                        f"must be consecutive in same lab room, but is split ({s1.day} P{s1.period} in {s1.room_name} vs {s2.day} P{s2.period} in {s2.room_name})."
                    )

        return violations_count, conflicts

    def count_soft_violations(
        self, assignment: Dict[str, SlotAssignment]
    ) -> Tuple[int, Dict[str, int], List[str]]:
        """
        Evaluates Soft Constraints S1-S5.
        Returns:
            (total_penalty_score, breakdown_dict, descriptions)
        """
        breakdown = {
            "S1_gaps": 0,
            "S2_subject_spread": 0,
            "S3_consecutive_labs": 0,
            "S4_teacher_preferences": 0,
            "S5_consecutive_teaching": 0
        }
        descriptions = []

        # Weights for soft constraints
        W1_GAP = 15
        W2_SPREAD = 10
        W3_LAB = 25
        W4_TEACHER_PREF = 5
        W5_FATIGUE = 20

        # Organize by (class, day) -> list of periods
        class_day_periods = defaultdict(lambda: defaultdict(list))
        # Organize by (class, subject, day) -> count of theory sessions
        class_subj_day = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        # Organize by (teacher, day) -> sorted list of periods
        teacher_day_periods = defaultdict(lambda: defaultdict(list))
        # Assigned slots map
        var_to_slot = assignment

        for var_id, slot in assignment.items():
            var = self.var_map.get(var_id)
            if not var:
                continue
            c_batch = self.class_map.get(var.class_name)
            lunch_p = c_batch.lunch_break_period if c_batch else -1

            class_day_periods[var.class_name][slot.day].append((slot.period, lunch_p))
            if not var.is_lab:
                class_subj_day[var.class_name][var.subject_code][slot.day] += 1
            teacher_day_periods[var.teacher_name][slot.day].append(slot.period)

            # --- S4: Teacher Preferences ---
            teacher = self.teacher_map.get(var.teacher_name)
            if teacher and teacher.preferred_slots:
                # If teacher has specified preferred slots, check if this slot is among them
                if (slot.day, slot.period) not in teacher.preferred_slots:
                    breakdown["S4_teacher_preferences"] += W4_TEACHER_PREF
                    descriptions.append(
                        f"[S4 - Teacher Preference] Teacher '{teacher.name}' scheduled on {slot.day} P{slot.period} "
                        f"(not in preferred slots)."
                    )

        # --- S1: Minimize free periods (gaps) in a class's day ---
        for class_name, days in class_day_periods.items():
            for day, period_info in days.items():
                if len(period_info) <= 1:
                    continue
                periods = sorted([p for p, _ in period_info])
                lunch_p = period_info[0][1]
                min_p, max_p = periods[0], periods[-1]
                
                # Count gaps between min_p and max_p (excluding lunch break)
                scheduled_set = set(periods)
                for p in range(min_p, max_p + 1):
                    if p not in scheduled_set and p != lunch_p:
                        breakdown["S1_gaps"] += W1_GAP
                        descriptions.append(
                            f"[S1 - Free Period Gap] Class '{class_name}' has an idle gap on {day} at Period {p}."
                        )

        # --- S2: Spread a subject's lectures across different days ---
        for class_name, subjs in class_subj_day.items():
            for subj_code, days in subjs.items():
                for day, count in days.items():
                    if count > 1:
                        excess = count - 1
                        penalty = excess * W2_SPREAD
                        breakdown["S2_subject_spread"] += penalty
                        descriptions.append(
                            f"[S2 - Subject Clustering] Class '{class_name}' has {count} sessions of '{subj_code}' "
                            f"on {day} (should be spread across days)."
                        )

        # --- S3: Lab sessions should occupy consecutive periods ---
        # Check variables that have consecutive_with
        checked_pairs = set()
        for var_id, var in self.var_map.items():
            if var.is_lab and var.consecutive_with and var_id in var_to_slot and var.consecutive_with in var_to_slot:
                pair_key = tuple(sorted([var_id, var.consecutive_with]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)

                slot1 = var_to_slot[var_id]
                slot2 = var_to_slot[var.consecutive_with]

                is_consecutive = (
                    slot1.day == slot2.day
                    and slot1.room_name == slot2.room_name
                    and abs(slot1.period - slot2.period) == 1
                )
                if not is_consecutive:
                    breakdown["S3_consecutive_labs"] += W3_LAB
                    descriptions.append(
                        f"[S3 - Non-consecutive Lab] Lab pair '{var.subject_code}' for '{var.class_name}' "
                        f"is split ({slot1.day} P{slot1.period} in {slot1.room_name} vs {slot2.day} P{slot2.period} in {slot2.room_name})."
                    )

        # --- S5: Avoid more than 2 consecutive lectures for a teacher ---
        for teacher_name, days in teacher_day_periods.items():
            for day, periods in days.items():
                if len(periods) <= 2:
                    continue
                sorted_periods = sorted(periods)
                consecutive_streak = 1
                for i in range(1, len(sorted_periods)):
                    if sorted_periods[i] == sorted_periods[i - 1] + 1:
                        consecutive_streak += 1
                        if consecutive_streak > 2:
                            breakdown["S5_consecutive_teaching"] += W5_FATIGUE
                            descriptions.append(
                                f"[S5 - Teacher Fatigue] Teacher '{teacher_name}' has {consecutive_streak} "
                                f"consecutive periods on {day} ending at Period {sorted_periods[i]}."
                            )
                    else:
                        consecutive_streak = 1

        total_soft_penalty = sum(breakdown.values())
        return total_soft_penalty, breakdown, descriptions

    def calculate_total_cost(
        self, assignment: Dict[str, SlotAssignment]
    ) -> Tuple[float, int, int]:
        """
        Total Cost = 1000 * (hard violations) + (soft penalties)
        Returns: (total_cost, hard_violations, soft_penalties)
        """
        hard_count, _ = self.count_hard_violations(assignment)
        soft_count, _, _ = self.count_soft_violations(assignment)
        total_cost = 1000.0 * hard_count + soft_count
        return total_cost, hard_count, soft_count

    def is_consistent_assignment(
        self, var_id: str, slot: SlotAssignment, current_assignment: Dict[str, SlotAssignment]
    ) -> bool:
        """
        Fast incremental consistency check for CSP backtracking:
        Checks whether adding (var_id -> slot) violates any hard constraint
        with already assigned variables.
        """
        var = self.var_map[var_id]
        c_batch = self.class_map[var.class_name]
        teacher = self.teacher_map[var.teacher_name]
        room = self.room_map[slot.room_name]

        # 1. Room capacity check
        if room.capacity < c_batch.strength:
            return False

        # 2. Room type check (Lab vs Classroom)
        if var.is_lab != room.is_lab:
            return False

        # 3. Lunch break check
        if slot.period == c_batch.lunch_break_period:
            return False

        # 4. Teacher unavailable slot check
        if (slot.day, slot.period) in teacher.unavailable_slots:
            return False

        # 5. Check pairwise binary conflicts with already assigned variables
        for other_id, other_slot in current_assignment.items():
            if other_slot.day == slot.day and other_slot.period == slot.period:
                other_var = self.var_map[other_id]
                # Same teacher at same time
                if other_var.teacher_name == var.teacher_name:
                    return False
                # Same class at same time
                if other_var.class_name == var.class_name:
                    return False
                # Same room at same time
                if other_slot.room_name == slot.room_name:
                    return False

        # 6. Consecutive 2-Hour Lab Block check
        if var.is_lab and var.consecutive_with:
            if var.consecutive_with in current_assignment:
                partner_slot = current_assignment[var.consecutive_with]
                # Must be on the same day, same lab room, and adjacent period
                if partner_slot.day != slot.day or partner_slot.room_name != slot.room_name:
                    return False
                if abs(partner_slot.period - slot.period) != 1:
                    return False
            else:
                # Ensure slot has at least one valid adjacent period not hitting lunch or boundary
                adjacent_possible = False
                for adj_p in [slot.period - 1, slot.period + 1]:
                    if 1 <= adj_p <= self.time_structure.periods_per_day:
                        if adj_p != c_batch.lunch_break_period:
                            if (slot.day, adj_p) not in teacher.unavailable_slots:
                                adjacent_possible = True
                                break
                if not adjacent_possible:
                    return False

        return True
