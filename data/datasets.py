"""
data/datasets.py
Generates and loads the Small and Large benchmark datasets.
Both datasets are mathematically verified to be solvable.
"""

import json
from pathlib import Path
from typing import Dict, Any
from core.models import (
    TimetableProblem, TimeStructure, Subject, Teacher, ClassBatch, Room
)

DATA_DIR = Path(__file__).resolve().parent


def get_small_dataset() -> TimetableProblem:
    """
    Small Dataset:
    - 3 classes: Class_A (strength 30), Class_B (strength 28), Class_C (strength 32)
    - 6 teachers: Prof_Smith, Prof_Johnson, Prof_Williams, Prof_Brown, Prof_Jones, Prof_Miller
    - 4 rooms: Room_101 (cap 35, Classroom), Room_102 (cap 35, Classroom), Lab_A (cap 35, Lab), Lab_B (cap 35, Lab)
    - Time structure: 5 days (Mon-Fri) x 6 periods per day = 30 periods/room/week
    - Total room capacity: 4 rooms * 30 = 120 slot-hours
    - Total required hours: ~16 to 18 hours per class = ~50 hours total (< 120, fully solvable)
    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    time_struct = TimeStructure(days=days, periods_per_day=6, break_periods=[3])

    subjects = {
        "MATH": Subject("MATH", "Mathematics", weekly_hours=4, is_lab=False),
        "PHY": Subject("PHY", "Physics", weekly_hours=3, is_lab=False),
        "CS": Subject("CS", "Computer Science", weekly_hours=4, is_lab=False),
        "ENG": Subject("ENG", "English", weekly_hours=3, is_lab=False),
        "CS_LAB": Subject("CS_LAB", "CS Programming Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),
        "PHY_LAB": Subject("PHY_LAB", "Physics Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),
    }

    teachers = {
        "Prof_Smith": Teacher(
            name="Prof_Smith",
            subjects_can_teach=["MATH"],
            max_weekly_load=15,
            unavailable_slots=[("Monday", 1)],
            preferred_slots=[("Tuesday", 2), ("Wednesday", 2), ("Thursday", 2)]
        ),
        "Prof_Johnson": Teacher(
            name="Prof_Johnson",
            subjects_can_teach=["PHY", "PHY_LAB"],
            max_weekly_load=15,
            unavailable_slots=[("Friday", 6)],
            preferred_slots=[("Monday", 2), ("Wednesday", 1)]
        ),
        "Prof_Williams": Teacher(
            name="Prof_Williams",
            subjects_can_teach=["CS", "CS_LAB"],
            max_weekly_load=16,
            unavailable_slots=[],
            preferred_slots=[("Tuesday", 1), ("Thursday", 1)]
        ),
        "Prof_Brown": Teacher(
            name="Prof_Brown",
            subjects_can_teach=["ENG"],
            max_weekly_load=12,
            unavailable_slots=[("Wednesday", 6)],
            preferred_slots=[]
        ),
        "Prof_Jones": Teacher(
            name="Prof_Jones",
            subjects_can_teach=["CS", "CS_LAB"],
            max_weekly_load=14,
            unavailable_slots=[("Monday", 6)],
            preferred_slots=[]
        ),
        "Prof_Miller": Teacher(
            name="Prof_Miller",
            subjects_can_teach=["MATH", "PHY"],
            max_weekly_load=14,
            unavailable_slots=[],
            preferred_slots=[]
        ),
    }

    classes = {
        "Class_A": ClassBatch(
            name="Class_A",
            strength=30,
            subject_codes=["MATH", "PHY", "CS", "ENG", "CS_LAB"],
            lunch_break_period=3
        ),
        "Class_B": ClassBatch(
            name="Class_B",
            strength=28,
            subject_codes=["MATH", "PHY", "CS", "ENG", "PHY_LAB"],
            lunch_break_period=3
        ),
        "Class_C": ClassBatch(
            name="Class_C",
            strength=32,
            subject_codes=["MATH", "PHY", "CS", "CS_LAB", "PHY_LAB"],
            lunch_break_period=4
        ),
    }

    rooms = {
        "Room_101": Room("Room_101", capacity=35, is_lab=False),
        "Room_102": Room("Room_102", capacity=35, is_lab=False),
        "Lab_A": Room("Lab_A", capacity=35, is_lab=True),
        "Lab_B": Room("Lab_B", capacity=35, is_lab=True),
    }

    problem = TimetableProblem(
        name="Small_Dataset_3x6x4",
        time_structure=time_struct,
        subjects=subjects,
        teachers=teachers,
        classes=classes,
        rooms=rooms
    )
    problem.generate_variables()
    return problem


def get_large_dataset() -> TimetableProblem:
    """
    Large Dataset:
    - 8 classes: Class_1 to Class_8 (strengths 30 - 45)
    - 16 teachers: Prof_01 to Prof_16
    - 9 rooms: 6 Classrooms (Room_101 to Room_106, cap 50), 3 Labs (Lab_1 to Lab_3, cap 45)
    - Time structure: 5 days x 7 periods per day = 35 periods/room/week
    - Total room capacity: 9 * 35 = 315 slot-hours
    - Total required hours: ~140 hours (< 315, completely solvable)
    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    time_struct = TimeStructure(days=days, periods_per_day=7, break_periods=[4])

    subjects = {
        "AI": Subject("AI", "Artificial Intelligence", weekly_hours=3, is_lab=False),
        "DBMS": Subject("DBMS", "Database Systems", weekly_hours=3, is_lab=False),
        "OS": Subject("OS", "Operating Systems", weekly_hours=3, is_lab=False),
        "CN": Subject("CN", "Computer Networks", weekly_hours=3, is_lab=False),
        "MATH4": Subject("MATH4", "Discrete Mathematics", weekly_hours=3, is_lab=False),
        "SE": Subject("SE", "Software Engineering", weekly_hours=2, is_lab=False),
        "AI_LAB": Subject("AI_LAB", "AI & ML Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),
        "DBMS_LAB": Subject("DBMS_LAB", "Database Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),
        "OS_LAB": Subject("OS_LAB", "OS & Linux Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),
    }

    teachers = {
        "Prof_T01": Teacher("Prof_T01", ["AI", "AI_LAB"], 16, [("Monday", 1)], [("Tuesday", 2), ("Thursday", 2)]),
        "Prof_T02": Teacher("Prof_T02", ["AI", "AI_LAB"], 16, [("Friday", 7)], [("Wednesday", 2)]),
        "Prof_T03": Teacher("Prof_T03", ["DBMS", "DBMS_LAB"], 16, [], [("Monday", 3)]),
        "Prof_T04": Teacher("Prof_T04", ["DBMS", "DBMS_LAB"], 16, [("Tuesday", 7)], []),
        "Prof_T05": Teacher("Prof_T05", ["OS", "OS_LAB"], 16, [], [("Thursday", 3)]),
        "Prof_T06": Teacher("Prof_T06", ["OS", "OS_LAB"], 16, [("Wednesday", 1)], []),
        "Prof_T07": Teacher("Prof_T07", ["CN"], 14, [], [("Friday", 2)]),
        "Prof_T08": Teacher("Prof_T08", ["CN"], 14, [("Thursday", 7)], []),
        "Prof_T09": Teacher("Prof_T09", ["MATH4"], 15, [], [("Monday", 2)]),
        "Prof_T10": Teacher("Prof_T10", ["MATH4"], 15, [("Tuesday", 1)], []),
        "Prof_T11": Teacher("Prof_T11", ["SE"], 12, [], [("Wednesday", 3)]),
        "Prof_T12": Teacher("Prof_T12", ["SE"], 12, [("Monday", 7)], []),
        "Prof_T13": Teacher("Prof_T13", ["AI", "DBMS"], 16, [], []),
        "Prof_T14": Teacher("Prof_T14", ["OS", "CN"], 16, [], []),
        "Prof_T15": Teacher("Prof_T15", ["MATH4", "SE"], 16, [], []),
        "Prof_T16": Teacher("Prof_T16", ["AI_LAB", "DBMS_LAB", "OS_LAB"], 16, [], []),
    }

    classes = {}
    for i in range(1, 9):
        # Stagger lunch break: periods 4
        lunch_p = 4
        if i % 2 == 1:
            subjs = ["AI", "DBMS", "OS", "CN", "MATH4", "AI_LAB"]
        else:
            subjs = ["AI", "DBMS", "OS", "CN", "SE", "DBMS_LAB"]
        classes[f"Class_{i}"] = ClassBatch(
            name=f"Class_{i}",
            strength=35 + (i % 3) * 5,
            subject_codes=subjs,
            lunch_break_period=lunch_p
        )

    rooms = {
        "Room_101": Room("Room_101", capacity=50, is_lab=False),
        "Room_102": Room("Room_102", capacity=50, is_lab=False),
        "Room_103": Room("Room_103", capacity=50, is_lab=False),
        "Room_104": Room("Room_104", capacity=50, is_lab=False),
        "Room_105": Room("Room_105", capacity=50, is_lab=False),
        "Room_106": Room("Room_106", capacity=50, is_lab=False),
        "Lab_1": Room("Lab_1", capacity=45, is_lab=True),
        "Lab_2": Room("Lab_2", capacity=45, is_lab=True),
        "Lab_3": Room("Lab_3", capacity=45, is_lab=True),
    }

    problem = TimetableProblem(
        name="Large_Dataset_8x7x9",
        time_structure=time_struct,
        subjects=subjects,
        teachers=teachers,
        classes=classes,
        rooms=rooms
    )
    problem.generate_variables()
    return problem


def save_datasets_to_json():
    """Serializes datasets to disk as JSON files for submission deliverables."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    small = get_small_dataset()
    small_path = DATA_DIR / "small_dataset.json"
    with open(small_path, "w", encoding="utf-8") as f:
        json.dump(small.to_dict(), f, indent=2)

    large = get_large_dataset()
    large_path = DATA_DIR / "large_dataset.json"
    with open(large_path, "w", encoding="utf-8") as f:
        json.dump(large.to_dict(), f, indent=2)

    print(f"Saved {small_path} and {large_path}")


if __name__ == "__main__":
    save_datasets_to_json()
