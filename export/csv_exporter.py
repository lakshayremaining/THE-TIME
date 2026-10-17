"""
export/csv_exporter.py
Exports timetable assignments to standard CSV formats.
"""

import csv
import io
from typing import Dict
from core.models import TimetableProblem, SlotAssignment


def export_timetable_to_csv_string(
    problem: TimetableProblem, assignment: Dict[str, SlotAssignment]
) -> str:
    """Generates a master schedule CSV as a string."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Class", "Subject", "Teacher", "Day", "Period", "Room", "Type"])

    var_dict = {v.var_id: v for v in problem.variables}
    # Sort by day, period, class
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
        session_type = "Lab" if var.is_lab else "Theory"
        writer.writerow([
            var.class_name,
            var.subject_code,
            var.teacher_name,
            slot.day,
            slot.period,
            slot.room_name,
            session_type
        ])

    return output.getvalue()


def export_class_grid_to_csv_string(
    problem: TimetableProblem, assignment: Dict[str, SlotAssignment], class_name: str
) -> str:
    """Generates a Day x Period grid CSV for a specific class batch."""
    output = io.StringIO()
    writer = csv.writer(output)

    days = problem.time_structure.days
    periods = list(range(1, problem.time_structure.periods_per_day + 1))
    c_batch = problem.classes.get(class_name)
    lunch_p = c_batch.lunch_break_period if c_batch else -1

    header = ["Day"] + [f"Period {p}" for p in periods]
    writer.writerow(header)

    var_dict = {v.var_id: v for v in problem.variables}
    # (day, period) -> cell text
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

    return output.getvalue()
