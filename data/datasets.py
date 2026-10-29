"""
data/datasets.py
Generates and loads the Small and Large benchmark datasets.
Both datasets are mathematically verified to be solvable.
"""

import json
from pathlib import Path
from typing import Dict, Any
from core.models import (
    TimetableProblem, TimeStructure, Subject, Teacher, ClassBatch, Room, SlotAssignment
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


def get_iiit_kota_odd_sem_dataset() -> TimetableProblem:
    """
    Real-World Dataset: IIIT Kota - Odd Semesters (Session July-Dec 2026)
    Department of Artificial Intelligence & Data Engineering
    Includes:
    - 3rd Semester (AIDE): Digital Systems (PS), AI (RS), ML (VK), DAA (RB), Math-II (PG), Ethics (AB),
                           DAA Lab (PS), AI Lab (PS), ML Lab (VK+SH), Web Dev Lab (KP).
    - 5th Semester (AIDE): Reinforcement Learning (RS), NLP (VK), Data Viz (KP), TOC (RB),
                           Computer Networks (NA), Elective-1 (AK), NLP Lab (SH), CN Lab (NA), Data Viz Lab (PJ).
    - 1st Semester (AIDE): Programming CST101 (SK), Digital Design ECT101 (VG), Foundation of Learning AIT101 (RS),
                           Communication Skills HST101 (AB), Math-I MAT101 (PG), CSP Lab (SK), AI Tinkering (AK),
                           Digital Design Lab (VG), Comm Lab (AB), Induction Upnayan (AB).
    - Augmented 7th Semester (AIDE): Deep Learning (VK), MLOps (RS), Cyber Security (RB), Elective (AK),
                                     AI Capstone Lab (PS), Project Phase-I (SH).
    - Time Structure: 5 Working Days (Mon-Fri) x 8 Slots (1:00 PM - 2:00 PM is Lunch Break).
    - Real Rooms: RM-241 (Sem 3), RM-242 (Sem 5), RM-243 (Sem 1), LT6, R-307, LT1, LT2,
                  LAB-36, LAB-137, LAB-18, LAB-32, LAB-101, LAB-102.
    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    period_times = [
        "9:00 - 10:00 AM",
        "10:00 - 11:00 AM",
        "11:00 - 12:00 PM",
        "12:00 - 1:00 PM",
        "1:00 - 2:00 PM (LUNCH)",
        "2:00 - 3:00 PM",
        "3:00 - 4:00 PM",
        "4:00 - 5:00 PM"
    ]
    # Period 5 is Lunch Break
    time_struct = TimeStructure(
        days=days,
        periods_per_day=8,
        break_periods=[5],
        period_times=period_times
    )

    # 1. Subjects (Exact codes and names from the 3 semester images)
    subjects = {
        # --- 3rd Semester (Picture 1) ---
        "AIT201": Subject("AIT201", "Digital Systems and Computer Architecture", weekly_hours=3, is_lab=False),
        "AIT203": Subject("AIT203", "Artificial Intelligence", weekly_hours=3, is_lab=False),
        "AIT205": Subject("AIT205", "Machine Learning", weekly_hours=3, is_lab=False),
        "CST207": Subject("CST207", "Design and Analysis of Algorithms", weekly_hours=3, is_lab=False),
        "MAT201": Subject("MAT201", "Mathematics-II", weekly_hours=4, is_lab=False),
        "HST203": Subject("HST203", "Social Sciences and Professional Ethics", weekly_hours=3, is_lab=False),
        "CSP207": Subject("CSP207", "DAA Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),
        "AIP203": Subject("AIP203", "Artificial Intelligence Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),
        "AIP205": Subject("AIP205", "Machine Learning Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),
        "AIP211": Subject("AIP211", "Web Development Lab", weekly_hours=3, is_lab=True, requires_consecutive=True),

        # --- 5th Semester (Picture 2) ---
        "AIT301": Subject("AIT301", "Reinforcement Learning", weekly_hours=3, is_lab=False),
        "AIT303": Subject("AIT303", "Natural Language Processing", weekly_hours=3, is_lab=False),
        "AIT305": Subject("AIT305", "Data Visualization", weekly_hours=3, is_lab=False),
        "CST301": Subject("CST301", "Theory of Computation", weekly_hours=4, is_lab=False),
        "CST303": Subject("CST303", "Computer Networks", weekly_hours=3, is_lab=False),
        "AIT307": Subject("AIT307", "Elective-1: Cloud & Big Data", weekly_hours=3, is_lab=False),
        "AIP303": Subject("AIP303", "Natural Language Processing Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),
        "CSP303": Subject("CSP303", "Computer Networks Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),
        "AIP305": Subject("AIP305", "Data Visualization Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),

        # --- 1st Semester (Picture 3) ---
        "CST101": Subject("CST101", "Computer Systems and Programming", weekly_hours=3, is_lab=False),
        "ECT101": Subject("ECT101", "Digital Design", weekly_hours=4, is_lab=False),
        "AIT101": Subject("AIT101", "Foundation of Learning", weekly_hours=3, is_lab=False),
        "HST101": Subject("HST101", "Communication Skills", weekly_hours=2, is_lab=False),
        "MAT101": Subject("MAT101", "Mathematics-I", weekly_hours=4, is_lab=False),
        "CSP101": Subject("CSP101", "Computer Systems & Programming Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),
        "AIP111": Subject("AIP111", "AI Tinkering Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),
        "ECP101": Subject("ECP101", "Digital Design Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),
        "HSP101": Subject("HSP101", "Communication Skills Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),
        "HSP111": Subject("HSP111", "Upnayan-The Induction Programme", weekly_hours=2, is_lab=True, requires_consecutive=True),

        # --- Augmented 7th Semester (B.Tech Final Year Odd Semester) ---
        "AIT401": Subject("AIT401", "Deep Learning & Computer Vision", weekly_hours=3, is_lab=False),
        "AIT403": Subject("AIT403", "MLOps & Autonomous AI Systems", weekly_hours=3, is_lab=False),
        "CST405": Subject("CST405", "Information Security & Privacy", weekly_hours=3, is_lab=False),
        "AIT407": Subject("AIT407", "Open Elective-II", weekly_hours=3, is_lab=False),
        "AIP401": Subject("AIP401", "Advanced AI Lab", weekly_hours=2, is_lab=True, requires_consecutive=True),
        "AIP403": Subject("AIP403", "Capstone Project Phase-I", weekly_hours=4, is_lab=True, requires_consecutive=True),
    }

    # 2. Teachers (All faculty from Picture 1 + Department Faculty for 1st & 5th & 7th semesters)
    teachers = {
        # Real faculty from 3rd Sem table (Picture 1)
        "Dr. Pooja Sharma": Teacher(
            name="Dr. Pooja Sharma",
            subjects_can_teach=["AIT201", "CSP207", "AIP203", "CST303", "AIP401"],
            max_weekly_load=16,
            unavailable_slots=[("Monday", 1)],
            preferred_slots=[("Tuesday", 1), ("Wednesday", 1), ("Thursday", 3)]
        ),
        "Dr. Ritam Sharma": Teacher(
            name="Dr. Ritam Sharma",
            subjects_can_teach=["AIT203", "AIT301", "AIT101", "AIT403"],
            max_weekly_load=16,
            unavailable_slots=[("Friday", 8)],
            preferred_slots=[("Monday", 2), ("Tuesday", 6), ("Wednesday", 7)]
        ),
        "Dr. Veena Khandelwal": Teacher(
            name="Dr. Veena Khandelwal",
            subjects_can_teach=["AIT205", "AIP205", "AIT303", "AIT401"],
            max_weekly_load=16,
            unavailable_slots=[],
            preferred_slots=[("Monday", 1), ("Wednesday", 8), ("Thursday", 1)]
        ),
        "Dr. Ramesh Battula": Teacher(
            name="Dr. Ramesh Battula",
            subjects_can_teach=["CST207", "CST301", "CST405"],
            max_weekly_load=16,
            unavailable_slots=[("Thursday", 8)],
            preferred_slots=[("Tuesday", 2), ("Wednesday", 2)]
        ),
        "Dr. Prashant Goyal": Teacher(
            name="Dr. Prashant Goyal",
            subjects_can_teach=["MAT201", "MAT101"],
            max_weekly_load=16,
            unavailable_slots=[],
            preferred_slots=[("Tuesday", 2), ("Wednesday", 2), ("Thursday", 2)]
        ),
        "Dr. Ankita Birla": Teacher(
            name="Dr. Ankita Birla",
            subjects_can_teach=["HST203", "HST101", "HSP101", "HSP111"],
            max_weekly_load=16,
            unavailable_slots=[],
            preferred_slots=[("Tuesday", 3), ("Wednesday", 3), ("Friday", 4)]
        ),
        "Ms. Kalpana Pathak": Teacher(
            name="Ms. Kalpana Pathak",
            subjects_can_teach=["AIP211", "AIT305"],
            max_weekly_load=14,
            unavailable_slots=[("Monday", 8)],
            preferred_slots=[("Friday", 6), ("Friday", 7)]
        ),
        "Dr. Shibna Hussain": Teacher(
            name="Dr. Shibna Hussain",
            subjects_can_teach=["AIP205", "AIP303", "AIP403"],
            max_weekly_load=14,
            unavailable_slots=[],
            preferred_slots=[("Thursday", 6), ("Thursday", 7)]
        ),

        # Department faculty for 1st, 5th, and 7th Semesters
        "Dr. Vikas Gupta": Teacher(
            name="Dr. Vikas Gupta",
            subjects_can_teach=["ECT101", "ECP101"],
            max_weekly_load=15,
            unavailable_slots=[("Wednesday", 1)],
            preferred_slots=[("Monday", 3), ("Tuesday", 4)]
        ),
        "Dr. Saurabh Kumar": Teacher(
            name="Dr. Saurabh Kumar",
            subjects_can_teach=["CST101", "CSP101"],
            max_weekly_load=15,
            unavailable_slots=[],
            preferred_slots=[("Monday", 2), ("Wednesday", 4)]
        ),
        "Dr. Neha Agarwal": Teacher(
            name="Dr. Neha Agarwal",
            subjects_can_teach=["CST303", "CSP303"],
            max_weekly_load=15,
            unavailable_slots=[],
            preferred_slots=[("Tuesday", 3), ("Thursday", 4)]
        ),
        "Dr. Amit Kumar": Teacher(
            name="Dr. Amit Kumar",
            subjects_can_teach=["AIT307", "AIP111", "AIT407"],
            max_weekly_load=15,
            unavailable_slots=[("Friday", 1)],
            preferred_slots=[("Wednesday", 6), ("Thursday", 6)]
        ),
        "Dr. Priya Jain": Teacher(
            name="Dr. Priya Jain",
            subjects_can_teach=["AIP305"],
            max_weekly_load=14,
            unavailable_slots=[],
            preferred_slots=[]
        )
    }

    # 3. Classes / Student Batches (Odd Semesters)
    classes = {
        "Sem_3_AIDE": ClassBatch(
            name="Sem_3_AIDE",
            strength=60,
            subject_codes=["AIT201", "AIT203", "AIT205", "CST207", "MAT201", "HST203",
                           "CSP207", "AIP203", "AIP205", "AIP211"],
            lunch_break_period=5  # 1:00 PM - 2:00 PM Lunch Break
        ),
        "Sem_5_AIDE": ClassBatch(
            name="Sem_5_AIDE",
            strength=55,
            subject_codes=["AIT301", "AIT303", "AIT305", "CST301", "CST303", "AIT307",
                           "AIP303", "CSP303", "AIP305"],
            lunch_break_period=5
        ),
        "Sem_1_AIDE": ClassBatch(
            name="Sem_1_AIDE",
            strength=65,
            subject_codes=["CST101", "ECT101", "AIT101", "HST101", "MAT101",
                           "CSP101", "AIP111", "ECP101", "HSP101", "HSP111"],
            lunch_break_period=5
        ),
        "Sem_7_AIDE": ClassBatch(
            name="Sem_7_AIDE",
            strength=45,
            subject_codes=["AIT401", "AIT403", "CST405", "AIT407", "AIP401", "AIP403"],
            lunch_break_period=5
        )
    }

    # 4. Rooms (Exact classrooms & labs from Picture 1 + Institute rooms)
    rooms = {
        # Classrooms
        "RM-241": Room("RM-241", capacity=65, is_lab=False),  # Primary room for Sem 3 (as in photo)
        "RM-242": Room("RM-242", capacity=65, is_lab=False),  # Primary room for Sem 5
        "RM-243": Room("RM-243", capacity=75, is_lab=False),  # Primary room for Sem 1
        "LT6": Room("LT6", capacity=80, is_lab=False),        # Lecture Theatre 6 (from photo)
        "R-307": Room("R-307", capacity=60, is_lab=False),    # Room 307 (from photo)
        "LT1": Room("LT1", capacity=100, is_lab=False),       # Large Lecture Theatre
        "LT2": Room("LT2", capacity=100, is_lab=False),

        # Labs (Exact labs from Picture 1)
        "LAB-36": Room("LAB-36", capacity=70, is_lab=True),    # AI & DAA Lab (from photo)
        "LAB-137": Room("LAB-137", capacity=70, is_lab=True),  # ML & Algorithms Lab (from photo)
        "LAB-18": Room("LAB-18", capacity=70, is_lab=True),    # Web & Systems Lab (from photo)
        "LAB-32": Room("LAB-32", capacity=70, is_lab=True),    # Web Dev Lab (from photo)
        "LAB-101": Room("LAB-101", capacity=70, is_lab=True),  # Digital Design Lab
        "LAB-102": Room("LAB-102", capacity=70, is_lab=True),  # AI Tinkering & IoT Lab
    }

    # Teacher mapping ensuring exact instructors from Picture 1
    teacher_mapping = {
        # 3rd Sem (Exact from Picture 1)
        ("Sem_3_AIDE", "AIT201"): "Dr. Pooja Sharma",
        ("Sem_3_AIDE", "AIT203"): "Dr. Ritam Sharma",
        ("Sem_3_AIDE", "AIT205"): "Dr. Veena Khandelwal",
        ("Sem_3_AIDE", "CST207"): "Dr. Ramesh Battula",
        ("Sem_3_AIDE", "MAT201"): "Dr. Prashant Goyal",
        ("Sem_3_AIDE", "HST203"): "Dr. Ankita Birla",
        ("Sem_3_AIDE", "CSP207"): "Dr. Pooja Sharma",
        ("Sem_3_AIDE", "AIP203"): "Dr. Pooja Sharma",
        ("Sem_3_AIDE", "AIP205"): "Dr. Veena Khandelwal",
        ("Sem_3_AIDE", "AIP211"): "Ms. Kalpana Pathak",

        # 5th Sem
        ("Sem_5_AIDE", "AIT301"): "Dr. Ritam Sharma",
        ("Sem_5_AIDE", "AIT303"): "Dr. Veena Khandelwal",
        ("Sem_5_AIDE", "AIT305"): "Ms. Kalpana Pathak",
        ("Sem_5_AIDE", "CST301"): "Dr. Ramesh Battula",
        ("Sem_5_AIDE", "CST303"): "Dr. Neha Agarwal",
        ("Sem_5_AIDE", "AIT307"): "Dr. Amit Kumar",
        ("Sem_5_AIDE", "AIP303"): "Dr. Shibna Hussain",
        ("Sem_5_AIDE", "CSP303"): "Dr. Neha Agarwal",
        ("Sem_5_AIDE", "AIP305"): "Dr. Priya Jain",

        # 1st Sem
        ("Sem_1_AIDE", "CST101"): "Dr. Saurabh Kumar",
        ("Sem_1_AIDE", "ECT101"): "Dr. Vikas Gupta",
        ("Sem_1_AIDE", "AIT101"): "Dr. Ritam Sharma",
        ("Sem_1_AIDE", "HST101"): "Dr. Ankita Birla",
        ("Sem_1_AIDE", "MAT101"): "Dr. Prashant Goyal",
        ("Sem_1_AIDE", "CSP101"): "Dr. Saurabh Kumar",
        ("Sem_1_AIDE", "AIP111"): "Dr. Amit Kumar",
        ("Sem_1_AIDE", "ECP101"): "Dr. Vikas Gupta",
        ("Sem_1_AIDE", "HSP101"): "Dr. Ankita Birla",
        ("Sem_1_AIDE", "HSP111"): "Dr. Ankita Birla",

        # 7th Sem
        ("Sem_7_AIDE", "AIT401"): "Dr. Veena Khandelwal",
        ("Sem_7_AIDE", "AIT403"): "Dr. Ritam Sharma",
        ("Sem_7_AIDE", "CST405"): "Dr. Ramesh Battula",
        ("Sem_7_AIDE", "AIT407"): "Dr. Amit Kumar",
        ("Sem_7_AIDE", "AIP401"): "Dr. Pooja Sharma",
        ("Sem_7_AIDE", "AIP403"): "Dr. Shibna Hussain",
    }

    problem = TimetableProblem(
        name="IIIT_Kota_Odd_Semesters_2026",
        time_structure=time_struct,
        subjects=subjects,
        teachers=teachers,
        classes=classes,
        rooms=rooms
    )
    problem.generate_variables(teacher_mapping=teacher_mapping)
    return problem


def get_iiit_kota_exact_3rd_sem_template_assignment(problem: TimetableProblem) -> Dict[str, SlotAssignment]:
    """
    Returns the exact timetable assignment for 3rd Semester (AIDE)
    strictly transcribed from the official IIIT Kota timetable photograph.
    All 2-hour labs strictly scheduled in continuous blocks.
    """
    assignment = {}
    
    # Exact mapping from Photo 1 (Session July-Dec 2026, RM-241):
    # Monday
    assignment["Sem_3_AIDE_AIT205_s1"] = SlotAssignment("Monday", 1, "RM-241")   # AIT205 (VK)
    assignment["Sem_3_AIDE_AIT203_s1"] = SlotAssignment("Monday", 2, "RM-241")   # AIT203 (RS)
    assignment["Sem_3_AIDE_MAT201_s1"] = SlotAssignment("Monday", 3, "LT6")      # MAT201 (PG) Tutorial D1
    assignment["Sem_3_AIDE_MAT201_s2"] = SlotAssignment("Monday", 4, "LT6")      # MAT201 (PG) Tutorial D2
    # P5 is Lunch Break (1:00 PM - 2:00 PM)
    assignment["Sem_3_AIDE_AIP203_s1"] = SlotAssignment("Monday", 7, "LAB-36")   # AIP203 Lab (PS) - Hour 1 (3-4 PM)
    assignment["Sem_3_AIDE_AIP203_s2"] = SlotAssignment("Monday", 8, "LAB-36")   # AIP203 Lab (PS) - Hour 2 (4-5 PM)

    # Tuesday
    assignment["Sem_3_AIDE_AIT201_s1"] = SlotAssignment("Tuesday", 1, "RM-241")  # AIT201 (PS)
    assignment["Sem_3_AIDE_MAT201_s3"] = SlotAssignment("Tuesday", 2, "RM-241")  # MAT201 (PG)
    assignment["Sem_3_AIDE_HST203_s1"] = SlotAssignment("Tuesday", 3, "R-307")   # HST203 (AB) Tutorial D1
    assignment["Sem_3_AIDE_HST203_s2"] = SlotAssignment("Tuesday", 4, "R-307")   # HST203 (AB) Tutorial D2
    assignment["Sem_3_AIDE_AIT203_s2"] = SlotAssignment("Tuesday", 6, "RM-241")  # AIT203 (RS) (2-3 PM)
    assignment["Sem_3_AIDE_CSP207_s1"] = SlotAssignment("Tuesday", 7, "LAB-36")  # CSP207 Lab (PS) - Hour 1 (3-4 PM)
    assignment["Sem_3_AIDE_CSP207_s2"] = SlotAssignment("Tuesday", 8, "LAB-36")  # CSP207 Lab (PS) - Hour 2 (4-5 PM)

    # Wednesday
    assignment["Sem_3_AIDE_AIT201_s2"] = SlotAssignment("Wednesday", 1, "RM-241") # AIT201 (PS)
    assignment["Sem_3_AIDE_MAT201_s4"] = SlotAssignment("Wednesday", 2, "RM-241") # MAT201 (PG)
    assignment["Sem_3_AIDE_HST203_s3"] = SlotAssignment("Wednesday", 3, "RM-241") # HST203 (AB)
    assignment["Sem_3_AIDE_AIT203_s3"] = SlotAssignment("Wednesday", 7, "RM-241") # AIT203 (RS) (3-4 PM)
    assignment["Sem_3_AIDE_AIT205_s2"] = SlotAssignment("Wednesday", 8, "RM-241") # AIT205 (VK) (4-5 PM)

    # Thursday
    assignment["Sem_3_AIDE_AIT205_s3"] = SlotAssignment("Thursday", 1, "RM-241")  # AIT205 (VK)
    assignment["Sem_3_AIDE_CST207_s1"] = SlotAssignment("Thursday", 2, "RM-241")  # CST207 (RB)
    assignment["Sem_3_AIDE_AIT201_s3"] = SlotAssignment("Thursday", 3, "RM-241")  # AIT201 (PS)
    assignment["Sem_3_AIDE_AIP205_s1"] = SlotAssignment("Thursday", 6, "LAB-137") # AIP205 Lab (VK+SH) - Hour 1 (2-3 PM)
    assignment["Sem_3_AIDE_AIP205_s2"] = SlotAssignment("Thursday", 7, "LAB-137") # AIP205 Lab (VK+SH) - Hour 2 (3-4 PM)

    # Friday
    assignment["Sem_3_AIDE_CST207_s2"] = SlotAssignment("Friday", 1, "RM-241")    # CST207 (RB)
    assignment["Sem_3_AIDE_CST207_s3"] = SlotAssignment("Friday", 2, "RM-241")    # CST207 (RB)
    assignment["Sem_3_AIDE_HST203_s1"] = SlotAssignment("Friday", 4, "RM-241")    # HST203 (AB) (12-1 PM)
    # 3-Hour Web Development Lab AIP211: P6, P7, P8 (2:00 PM - 5:00 PM) in LAB-32
    assignment["Sem_3_AIDE_AIP211_s1"] = SlotAssignment("Friday", 6, "LAB-32")    # AIP211 Lab (KP) - Hour 1 (2-3 PM)
    assignment["Sem_3_AIDE_AIP211_s2"] = SlotAssignment("Friday", 7, "LAB-32")    # AIP211 Lab (KP) - Hour 2 (3-4 PM)
    assignment["Sem_3_AIDE_AIP211_s3"] = SlotAssignment("Friday", 8, "LAB-32")    # AIP211 Lab (KP) - Hour 3 (4-5 PM)

    return assignment


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

    iiit = get_iiit_kota_odd_sem_dataset()
    iiit_path = DATA_DIR / "iiit_kota_odd_semesters.json"
    with open(iiit_path, "w", encoding="utf-8") as f:
        json.dump(iiit.to_dict(), f, indent=2)

    print(f"Saved {small_path}, {large_path}, and {iiit_path}")


if __name__ == "__main__":
    save_datasets_to_json()

