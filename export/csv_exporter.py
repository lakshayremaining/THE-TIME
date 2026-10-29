"""
export/csv_exporter.py
Exports timetable assignments to standard CSV formats with explicit Time Slots
and footer credit: "Creation of Lakshay Indoriya".
"""

import csv
import io
from typing import Dict
from core.models import TimetableProblem, SlotAssignment


def export_timetable_to_csv_string(
    problem: TimetableProblem, assignment: Dict[str, SlotAssignment]
) -> str:
    """Generates a master schedule CSV as a string with explicit Time Slots."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Title & Creator Metadata
    writer.writerow([f"# Academic Timetable - {problem.name}"])
    writer.writerow(["# Creation of Lakshay Indoriya"])
    writer.writerow([])

    # Table Header with Time Slot
    writer.writerow([
        "Class", "Subject Code", "Subject Name", "Faculty",
        "Day", "Period", "Time Slot", "Room", "Type"
    ])

    var_dict = {v.var_id: v for v in problem.variables}
    day_order = {day: i for i, day in enumerate(problem.time_structure.days)}

    sorted_entries = sorted(
        assignment.items(),
        key=lambda item: (
            day_order.get(item[1].day, 99),
            item[1].period,
            var_dict[item[0]].class_name
        )
    )

    for var_id, slot in sorted_entries:
        var = var_dict.get(var_id)
        if not var:
            continue
        subj = problem.subjects.get(var.subject_code)
        subj_name = subj.name if subj else var.subject_code
        session_type = "Lab" if var.is_lab else "Theory"

        time_slot_str = (
            problem.time_structure.period_times[slot.period - 1]
            if problem.time_structure.period_times and slot.period - 1 < len(problem.time_structure.period_times)
            else f"Period {slot.period}"
        )

        writer.writerow([
            var.class_name,
            var.subject_code,
            subj_name,
            var.teacher_name,
            slot.day,
            slot.period,
            time_slot_str,
            slot.room_name,
            session_type
        ])

    writer.writerow([])
    writer.writerow(["# End of Schedule - Creation of Lakshay Indoriya"])
    return output.getvalue()


def export_class_grid_to_csv_string(
    problem: TimetableProblem, assignment: Dict[str, SlotAssignment], class_name: str
) -> str:
    """Generates a Day x Period grid CSV with explicit Time Slot headers."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([f"# Timetable for Class: {class_name}"])
    writer.writerow(["# Creation of Lakshay Indoriya"])
    writer.writerow([])

    days = problem.time_structure.days
    periods = list(range(1, problem.time_structure.periods_per_day + 1))
    c_batch = problem.classes.get(class_name)
    lunch_p = c_batch.lunch_break_period if c_batch else -1

    def get_header(p: int) -> str:
        if problem.time_structure.period_times and p - 1 < len(problem.time_structure.period_times):
            return f"P{p} ({problem.time_structure.period_times[p - 1]})"
        return f"Period {p}"

    header = ["Day"] + [get_header(p) for p in periods]
    writer.writerow(header)

    var_dict = {v.var_id: v for v in problem.variables}
    grid = {}
    for var_id, slot in assignment.items():
        var = var_dict.get(var_id)
        if var and var.class_name == class_name:
            grid[(slot.day, slot.period)] = f"{var.subject_code} ({var.teacher_name}, {slot.room_name})"

    for day in days:
        row = [day]
        for p in periods:
            if p == lunch_p:
                row.append("LUNCH BREAK")
            else:
                row.append(grid.get((day, p), "---"))
        writer.writerow(row)

    writer.writerow([])
    writer.writerow(["# Creation of Lakshay Indoriya"])
    return output.getvalue()
