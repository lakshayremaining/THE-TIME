"""
export/xml_exporter.py
Exports timetable assignments to structured XML format with explicit time slots
and creator credit: "Creation of Lakshay Indoriya".
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict
from core.models import TimetableProblem, SlotAssignment


def export_timetable_to_xml_string(
    problem: TimetableProblem, assignment: Dict[str, SlotAssignment]
) -> str:
    """Generates a well-formatted XML document with explicit time slots and creator signature."""
    var_dict = {v.var_id: v for v in problem.variables}
    days = problem.time_structure.days
    day_order = {day: i for i, day in enumerate(days)}

    root = ET.Element(
        "academic_timetable",
        attrib={
            "institute": "Indian Institute of Information Technology Kota",
            "department": "Department of Artificial Intelligence & Data Engineering",
            "academic_session": "July-Dec 2026",
            "problem_name": problem.name
        }
    )

    # 1. Metadata Block
    meta = ET.SubElement(root, "metadata")
    ET.SubElement(meta, "creator").text = "Creation of Lakshay Indoriya"
    ET.SubElement(meta, "total_scheduled_sessions").text = str(len(assignment))
    ET.SubElement(meta, "total_classes").text = str(len(problem.classes))
    ET.SubElement(meta, "total_teachers").text = str(len(problem.teachers))
    ET.SubElement(meta, "total_rooms").text = str(len(problem.rooms))

    # 2. Daily Time Structure with Explicit Time Slots
    time_struct_elem = ET.SubElement(root, "time_structure")
    for p in range(1, problem.time_structure.periods_per_day + 1):
        slot_label = (
            problem.time_structure.period_times[p - 1]
            if problem.time_structure.period_times and p - 1 < len(problem.time_structure.period_times)
            else f"Period {p}"
        )
        is_break = p in problem.time_structure.break_periods
        ET.SubElement(
            time_struct_elem,
            "period_slot",
            attrib={
                "period_number": str(p),
                "time_slot": slot_label,
                "is_break": "true" if is_break else "false"
            }
        )

    # 3. Scheduled Sessions
    sessions_elem = ET.SubElement(root, "scheduled_sessions")

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

        time_slot_str = (
            problem.time_structure.period_times[slot.period - 1]
            if problem.time_structure.period_times and slot.period - 1 < len(problem.time_structure.period_times)
            else f"Period {slot.period}"
        )

        sess_elem = ET.SubElement(sessions_elem, "session", attrib={"var_id": var.var_id})
        ET.SubElement(sess_elem, "class_batch").text = var.class_name
        ET.SubElement(sess_elem, "subject_code").text = var.subject_code
        ET.SubElement(sess_elem, "subject_name").text = subj_name
        ET.SubElement(sess_elem, "faculty").text = var.teacher_name
        ET.SubElement(sess_elem, "day").text = slot.day
        ET.SubElement(sess_elem, "period").text = str(slot.period)
        ET.SubElement(sess_elem, "time_slot").text = time_slot_str
        ET.SubElement(sess_elem, "room").text = slot.room_name
        ET.SubElement(sess_elem, "type").text = "Laboratory" if var.is_lab else "Theory"

    # 4. Footer Credit
    ET.SubElement(root, "footer_signature").text = "Creation of Lakshay Indoriya"

    # Pretty-print XML
    raw_str = ET.tostring(root, encoding="utf-8")
    parsed = minidom.parseString(raw_str)
    return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
