"""
app.py
Streamlit Web Application for AI-Based Timetable Scheduler.
Includes:
1. Data Input (Predefined Small/Large, JSON upload, or interactive forms) with basic validation.
2. Algorithm Selector (Backtracking Baseline, Heuristic CSP, Min-Conflicts, Simulated Annealing, Hybrid CSP+SA, Hill Climbing).
3. Generate button with live metrics (Time, Violations, Cost).
4. Timetable Grid Views (By Class, By Teacher, By Room).
5. One-Click Export to CSV and styled multi-sheet Excel (.xlsx).
6. Interactive Manual Editing with real-time hard-constraint conflict detection.
7. Analytics & Convergence Studio (Cost vs. Iterations plot & benchmark results).
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import time
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Optional, List

from core.models import TimetableProblem, SlotAssignment, SessionVariable
from core.constraints import ConstraintChecker
from data.datasets import (
    get_small_dataset, get_large_dataset, get_iiit_kota_odd_sem_dataset,
    get_iiit_kota_exact_3rd_sem_template_assignment
)
from solvers.backtracking import PlainBacktrackingSolver, HeuristicBacktrackingSolver
from solvers.min_conflicts import MinConflictsSolver
from solvers.simulated_annealing import SimulatedAnnealingSolver
from solvers.hybrid import HybridCSPSolver
from solvers.hill_climbing import HillClimbingSolver
from export.excel_exporter import export_timetable_to_excel_bytes
from export.csv_exporter import export_timetable_to_csv_string

# Page config
st.set_page_config(
    page_title="AI Timetable Scheduler - IIIT Kota",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .inst-badge {
        background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: 600;
        margin-bottom: 15px;
        display: inline-block;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .conflict-alert {
        background-color: #FEE2E2;
        border-left: 5px solid #EF4444;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
        color: #991B1B;
    }
    .success-alert {
        background-color: #DCFCE7;
        border-left: 5px solid #22C55E;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
        color: #166534;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if "problem" not in st.session_state:
        st.session_state.problem = get_iiit_kota_odd_sem_dataset()
    if "assignment" not in st.session_state:
        st.session_state.assignment = None
    if "solver_result" not in st.session_state:
        st.session_state.solver_result = None
    if "manual_history" not in st.session_state:
        st.session_state.manual_history = []


init_session_state()

# ----------------- SIDEBAR -----------------
st.sidebar.image("https://img.icons8.com/color/96/calendar--v1.png", width=64)
st.sidebar.title("Configuration & Data")

# Dataset Selection
dataset_choice = st.sidebar.selectbox(
    "Choose Dataset",
    [
        "IIIT Kota - Odd Semesters (Sem 1, 3, 5, 7 - Real Timetable)",
        "Small Dataset (3 Classes, 6 Teachers, 4 Rooms, 5x6)",
        "Large Dataset (8 Classes, 16 Teachers, 9 Rooms, 5x7)",
        "Upload Custom JSON Dataset"
    ],
    index=0
)

if dataset_choice.startswith("IIIT Kota"):
    if st.sidebar.button("🔄 Reload IIIT Kota Odd Semesters") or st.session_state.problem.name != "IIIT_Kota_Odd_Semesters_2026":
        st.session_state.problem = get_iiit_kota_odd_sem_dataset()
        st.session_state.assignment = None
        st.session_state.solver_result = None
        st.rerun()
elif dataset_choice.startswith("Small"):
    if st.sidebar.button("🔄 Reload Small Dataset") or st.session_state.problem.name != "Small_Dataset_3x6x4":
        st.session_state.problem = get_small_dataset()
        st.session_state.assignment = None
        st.session_state.solver_result = None
        st.rerun()
elif dataset_choice.startswith("Large"):
    if st.sidebar.button("🔄 Load Large Dataset") or st.session_state.problem.name != "Large_Dataset_8x7x9":
        st.session_state.problem = get_large_dataset()
        st.session_state.assignment = None
        st.session_state.solver_result = None
        st.rerun()
else:
    uploaded_file = st.sidebar.file_uploader("Upload JSON problem file", type=["json"])
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            st.session_state.problem = TimetableProblem.from_dict(data)
            st.session_state.assignment = None
            st.sidebar.success(f"Loaded '{st.session_state.problem.name}' successfully!")
        except Exception as e:
            st.sidebar.error(f"Error loading JSON: {e}")

problem: TimetableProblem = st.session_state.problem

# Validation indicator
is_valid, validation_errors = problem.validate_input()
if is_valid:
    st.sidebar.success(f"✓ Solvability Validated ({len(problem.variables)} sessions)")
else:
    for err in validation_errors:
        st.sidebar.error(f"❌ {err}")

st.sidebar.markdown("---")
st.sidebar.subheader("Algorithm Selector")

algo_choice = st.sidebar.selectbox(
    "Select AI Algorithm",
    [
        "Backtracking (Baseline)",
        "Backtracking (+ Heuristics: MRV, Degree, FC, LCV)",
        "Min-Conflicts Local Search",
        "Simulated Annealing (+6 Bonus)",
        "Hybrid CSP + Simulated Annealing (+6 Bonus)",
        "Hill Climbing (Comparison Baseline)"
    ],
    index=1
)

# Hyperparameter Controls
with st.sidebar.expander("⚙️ Algorithm Hyperparameters", expanded=False):
    timeout_sec = st.slider("CSP Timeout (seconds)", 5, 60, 25)
    max_iters = st.slider("Max Iterations (Local Search)", 500, 6000, 3000, step=250)
    random_walk_p = st.slider("Min-Conflicts Random Walk Prob", 0.0, 0.3, 0.10, step=0.02)
    init_temp = st.slider("SA Initial Temperature", 10.0, 200.0, 100.0, step=10.0)
    cooling_rate = st.slider("SA Cooling Rate (alpha)", 0.95, 0.999, 0.995, step=0.001)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Bonus Included:**\n- Simulated Annealing (+6)\n- Hybrid CSP+SA (+6)\n- Real-time Conflict Detector\n- Multi-tab Excel Export")

# ----------------- MAIN CONTENT -----------------
st.markdown('<div class="main-header">📅 AI-Based Timetable Scheduler</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Automated College Scheduling using Constraint Satisfaction (CSP), '
    'Min-Conflicts, Simulated Annealing, and Hybrid Metaheuristics</div>',
    unsafe_allow_html=True
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚀 Schedule Generator",
    "📊 Timetable Views (Class / Teacher / Room)",
    "✏️ Manual Editor & Conflict Flagger",
    "📈 Analytics & Cost Curves",
    "📁 Dataset Overview"
])

# ----------------- TAB 1: GENERATOR -----------------
with tab1:
    col_ctrl, col_stats = st.columns([1, 2])

    with col_ctrl:
        st.subheader("Run Solver")
        st.write(f"**Dataset**: `{problem.name}`")
        st.write(f"**Total Classes**: {len(problem.classes)} | **Teachers**: {len(problem.teachers)}")
        st.write(f"**Rooms**: {len(problem.rooms)} | **Sessions to Schedule**: {len(problem.variables)}")

        generate_btn = st.button("⚡ Generate AI Optimal Timetable", type="primary", use_container_width=True)

        load_exact_btn = False
        if "IIIT_Kota" in problem.name:
            load_exact_btn = st.button("📋 Load Published 3rd Sem Timetable (Photo 1)", use_container_width=True)

    if load_exact_btn:
        exact_assignment = get_iiit_kota_exact_3rd_sem_template_assignment(problem)
        checker = ConstraintChecker(problem)
        h_viol, conflicts = checker.count_hard_violations(exact_assignment)
        s_pen, _, _ = checker.count_soft_violations(exact_assignment)
        from solvers.base import SolverResult

        st.session_state.assignment = exact_assignment
        st.session_state.solver_result = SolverResult(
            algorithm_name="Official Published Timetable (Photo 1 - 3rd Sem)",
            assignment=exact_assignment,
            time_taken=0.001,
            nodes_expanded=len(exact_assignment),
            iterations=len(exact_assignment),
            hard_violations=h_viol,
            soft_penalty=s_pen,
            total_cost=float(s_pen),
            success=h_viol == 0,
            conflict_messages=conflicts
        )
        st.rerun()

    if generate_btn:
        checker = ConstraintChecker(problem)
        with st.spinner(f"Running {algo_choice}..."):
            start_t = time.perf_counter()

            if algo_choice == "Backtracking (Baseline)":
                solver = PlainBacktrackingSolver(problem, timeout_seconds=timeout_sec)
            elif algo_choice.startswith("Backtracking (+ Heuristics"):
                solver = HeuristicBacktrackingSolver(
                    problem,
                    use_mrv=True,
                    use_degree=True,
                    use_forward_checking=True,
                    use_lcv=True,
                    timeout_seconds=timeout_sec
                )
            elif algo_choice.startswith("Min-Conflicts"):
                solver = MinConflictsSolver(
                    problem,
                    max_iterations=max_iters,
                    random_walk_prob=random_walk_p
                )
            elif algo_choice.startswith("Simulated Annealing"):
                solver = SimulatedAnnealingSolver(
                    problem,
                    initial_temperature=init_temp,
                    cooling_rate=cooling_rate,
                    max_total_steps=max_iters
                )
            elif algo_choice.startswith("Hybrid CSP"):
                solver = HybridCSPSolver(
                    problem,
                    sa_cooling_rate=cooling_rate,
                    sa_initial_temp=init_temp / 2.0,
                    sa_max_steps=max_iters // 2
                )
            else:  # Hill Climbing
                solver = HillClimbingSolver(problem, max_iterations=max_iters)

            result = solver.solve()
            st.session_state.solver_result = result
            st.session_state.assignment = result.assignment

    res = st.session_state.solver_result
    assignment = st.session_state.assignment

    if res is not None and assignment is not None:
        with col_stats:
            st.subheader("Performance Metrics")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Execution Time", f"{res.time_taken:.3f} s")
            m2.metric("Nodes / Steps", f"{res.nodes_expanded}")
            m3.metric("Hard Violations", f"{res.hard_violations}", delta=None if res.hard_violations == 0 else "Clash!", delta_color="inverse")
            m4.metric("Soft Penalty", f"{res.soft_penalty}")

            if res.hard_violations == 0:
                st.markdown(
                    f'<div class="success-alert">✅ <b>Feasible Timetable Generated!</b> '
                    f'All {len(problem.variables)} sessions scheduled with 0 hard conflicts. '
                    f'Soft penalty score: <b>{res.soft_penalty}</b>.</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="conflict-alert">⚠️ <b>Incomplete / Conflicts Present:</b> '
                    f'{res.hard_violations} hard constraint violation(s) detected.</div>',
                    unsafe_allow_html=True
                )

        st.markdown("---")
        st.subheader("📥 Export Schedule")
        e_col1, e_col2, _ = st.columns([1, 1, 2])

        # CSV Download
        csv_str = export_timetable_to_csv_string(problem, assignment)
        e_col1.download_button(
            label="📄 Download CSV",
            data=csv_str,
            file_name=f"timetable_{problem.name.lower()}.csv",
            mime="text/csv",
            use_container_width=True
        )

        # Excel Download
        excel_bytes = export_timetable_to_excel_bytes(problem, assignment)
        e_col2.download_button(
            label="📊 Download Excel (.xlsx)",
            data=excel_bytes,
            file_name=f"timetable_{problem.name.lower()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# ----------------- TAB 2: TIMETABLE VIEWS -----------------
with tab2:
    if assignment is None:
        st.info("👉 Please generate a timetable in the **Schedule Generator** tab first!")
    else:
        view_mode = st.radio("Select View Mode", ["By Class Batch", "By Teacher", "By Room"], horizontal=True)

        var_dict = {v.var_id: v for v in problem.variables}
        days = problem.time_structure.days
        periods = list(range(1, problem.time_structure.periods_per_day + 1))

        def get_p_name(p: int) -> str:
            if problem.time_structure.period_times and p - 1 < len(problem.time_structure.period_times):
                return f"P{p} ({problem.time_structure.period_times[p - 1]})"
            return f"Period {p}"

        if view_mode == "By Class Batch":
            selected_class = st.selectbox("Select Class Batch", list(problem.classes.keys()))
            c_batch = problem.classes[selected_class]

            # Room hint
            room_hint = {
                "Sem_3_AIDE": "RM-241 (Primary Lecture Hall, capacity: 65)",
                "Sem_5_AIDE": "RM-242 (Lecture Hall, capacity: 65)",
                "Sem_1_AIDE": "RM-243 (Lecture Hall, capacity: 75)",
                "Sem_7_AIDE": "R-307 / LT2 (capacity: 60-100)"
            }.get(selected_class, "Designated Classrooms & Labs")
            st.caption(f"🏫 **Assigned Classroom/Locus**: `{room_hint}` | **Strength**: {c_batch.strength} students")

            # Build grid
            grid_data = {get_p_name(p): [] for p in periods}
            for day in days:
                for p in periods:
                    col_key = get_p_name(p)
                    if p == c_batch.lunch_break_period:
                        grid_data[col_key].append("🍱 LUNCH BREAK")
                    else:
                        # Find session
                        matched = [
                            f"{var_dict[vid].subject_code}\n({var_dict[vid].teacher_name}, {slot.room_name})"
                            for vid, slot in assignment.items()
                            if var_dict[vid].class_name == selected_class and slot.day == day and slot.period == p
                        ]
                        grid_data[col_key].append("\n".join(matched) if matched else "—")

            df = pd.DataFrame(grid_data, index=days)
            st.dataframe(df, use_container_width=True, height=290)

        elif view_mode == "By Teacher":
            selected_teacher = st.selectbox("Select Teacher", list(problem.teachers.keys()))
            t_obj = problem.teachers[selected_teacher]
            st.caption(f"👨‍🏫 **Faculty**: {t_obj.name} | **Max Weekly Load**: {t_obj.max_weekly_load} hrs | **Teaches**: {', '.join(t_obj.subjects_can_teach)}")

            grid_data = {get_p_name(p): [] for p in periods}
            for day in days:
                for p in periods:
                    col_key = get_p_name(p)
                    if (day, p) in t_obj.unavailable_slots:
                        grid_data[col_key].append("⛔ Unavailable")
                    else:
                        matched = [
                            f"{var_dict[vid].class_name}: {var_dict[vid].subject_code} ({slot.room_name})"
                            for vid, slot in assignment.items()
                            if var_dict[vid].teacher_name == selected_teacher and slot.day == day and slot.period == p
                        ]
                        grid_data[col_key].append("\n".join(matched) if matched else "—")

            df = pd.DataFrame(grid_data, index=days)
            st.dataframe(df, use_container_width=True, height=290)

        else:  # By Room
            selected_room = st.selectbox("Select Room", list(problem.rooms.keys()))
            r_obj = problem.rooms[selected_room]
            st.caption(f"🏫 **Room**: {r_obj.name} | **Capacity**: {r_obj.capacity} | **Type**: {'Lab Room' if r_obj.is_lab else 'Theory Classroom'}")

            grid_data = {get_p_name(p): [] for p in periods}
            for day in days:
                for p in periods:
                    col_key = get_p_name(p)
                    matched = [
                        f"{var_dict[vid].class_name} - {var_dict[vid].subject_code} ({var_dict[vid].teacher_name})"
                        for vid, slot in assignment.items()
                        if slot.room_name == selected_room and slot.day == day and slot.period == p
                    ]
                    grid_data[col_key].append("\n".join(matched) if matched else "—")

            df = pd.DataFrame(grid_data, index=days)
            st.dataframe(df, use_container_width=True, height=290)

# ----------------- TAB 3: MANUAL EDITING & CONFLICT FLAGGER -----------------
with tab3:
    st.subheader("✏️ Interactive Manual Editing & Conflict Flagger")
    st.markdown(
        "Move any session to another time slot or room. The application immediately evaluates "
        "all **Hard Constraints (H1-H9)** and flags any conflict in real time."
    )

    if assignment is None:
        st.info("👉 Please generate a timetable first to enable manual editing.")
    else:
        var_dict = {v.var_id: v for v in problem.variables}
        session_options = [
            f"{vid} | {var_dict[vid].class_name} - {var_dict[vid].subject_code} ({var_dict[vid].teacher_name}) -> Currently: {slot.day} P{slot.period} in {slot.room_name}"
            for vid, slot in sorted(assignment.items())
        ]

        col_sel, col_move = st.columns([1, 1])

        with col_sel:
            selected_session_str = st.selectbox("Select Session to Move", session_options)
            chosen_var_id = selected_session_str.split(" | ")[0]
            current_slot = assignment[chosen_var_id]

        with col_move:
            st.write(f"**Target New Slot for `{chosen_var_id}`:**")
            m_day = st.selectbox("New Day", problem.time_structure.days, index=problem.time_structure.days.index(current_slot.day))
            m_period = st.selectbox("New Period", list(range(1, problem.time_structure.periods_per_day + 1)), index=current_slot.period - 1)
            m_room = st.selectbox("New Room", list(problem.rooms.keys()), index=list(problem.rooms.keys()).index(current_slot.room_name))

        if st.button("🚀 Apply Move & Check Conflicts", type="primary"):
            new_slot = SlotAssignment(day=m_day, period=m_period, room_name=m_room)
            st.session_state.assignment[chosen_var_id] = new_slot
            st.session_state.manual_history.append((chosen_var_id, current_slot, new_slot))

        # Check constraints immediately
        checker = ConstraintChecker(problem)
        h_viol, conflicts = checker.count_hard_violations(st.session_state.assignment)
        s_pen, s_breakdown, soft_descs = checker.count_soft_violations(st.session_state.assignment)

        if h_viol == 0:
            st.markdown(
                f'<div class="success-alert">✅ <b>No Hard Conflicts!</b> '
                f'The modified schedule satisfies all hard constraints (Soft Penalty: {s_pen}).</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="conflict-alert">🚨 <b>CONFLICT DETECTED! ({h_viol} violation(s))</b><br>'
                + "<br>".join(f"• {c}" for c in conflicts)
                + '</div>',
                unsafe_allow_html=True
            )

        if soft_descs:
            with st.expander("ℹ️ Soft Constraint Feedback", expanded=False):
                st.write(f"Total Soft Penalty: **{s_pen}**")
                for s in soft_descs[:8]:
                    st.caption(f"• {s}")

# ----------------- TAB 4: ANALYTICS & COST CURVES -----------------
with tab4:
    st.subheader("📈 Convergence & Algorithm Comparison")

    if res is not None and res.cost_history:
        st.write(f"### Cost vs. Iterations Curve: `{res.algorithm_name}`")
        fig = px.line(
            x=list(range(len(res.cost_history))),
            y=res.cost_history,
            labels={"x": "Iteration / Step", "y": "Total Cost (1000*Hard + Soft)"},
            title=f"Convergence Trajectory for {res.algorithm_name}"
        )
        fig.update_traces(line_color="#2563EB", line_width=2.5)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Run a local search algorithm (Min-Conflicts, Simulated Annealing, Hybrid) to view its iteration-by-iteration convergence graph.")

    # Display Benchmark Table
    benchmark_json_path = "experiments/benchmark_results.json"
    try:
        with open(benchmark_json_path, "r", encoding="utf-8") as f:
            b_data = json.load(f)

        st.markdown("### 🏆 10-Trial Experimental Results Table")
        for dataset_k, algo_metrics in b_data.items():
            st.write(f"#### {dataset_k}")
            b_df = pd.DataFrame(algo_metrics).T
            st.dataframe(b_df, use_container_width=True)
    except Exception:
        st.info("💡 Run `python -m experiments.benchmark` from your terminal to compute and populate the full 10-run comparison table!")

# ----------------- TAB 5: DATASET OVERVIEW -----------------
with tab5:
    st.subheader(f"Dataset Details: {problem.name}")
    col_a, col_b = st.columns(2)

    with col_a:
        st.write("#### 👥 Classes")
        classes_data = [
            {"Class": c.name, "Strength": c.strength, "Subjects": ", ".join(c.subject_codes), "Lunch Break": f"Period {c.lunch_break_period}"}
            for c in problem.classes.values()
        ]
        st.dataframe(pd.DataFrame(classes_data), use_container_width=True)

        st.write("#### 🏫 Rooms")
        rooms_data = [
            {"Room": r.name, "Capacity": r.capacity, "Type": "Lab" if r.is_lab else "Classroom"}
            for r in problem.rooms.values()
        ]
        st.dataframe(pd.DataFrame(rooms_data), use_container_width=True)

    with col_b:
        st.write("#### 👨‍🏫 Teachers")
        teachers_data = [
            {"Teacher": t.name, "Max Load": t.max_weekly_load, "Can Teach": ", ".join(t.subjects_can_teach), "Unavailable": str(t.unavailable_slots)}
            for t in problem.teachers.values()
        ]
        st.dataframe(pd.DataFrame(teachers_data), use_container_width=True)

        st.write("#### 📚 Subjects")
        subjs_data = [
            {"Code": s.code, "Name": s.name, "Hours/Week": s.weekly_hours, "Type": "Lab" if s.is_lab else "Theory"}
            for s in problem.subjects.values()
        ]
        st.dataframe(pd.DataFrame(subjs_data), use_container_width=True)
