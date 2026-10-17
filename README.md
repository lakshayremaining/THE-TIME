# AI-Based Timetable Scheduler

An intelligent, constraint-satisfaction and local-search automated timetable scheduling engine built in Python and Streamlit.

Includes implementations of **Plain Backtracking CSP (Baseline)**, **Heuristic CSP (MRV + Degree + Forward Checking + LCV)**, **Min-Conflicts Local Search**, **Simulated Annealing (+6 Bonus)**, and **Hybrid CSP + SA (+6 Bonus)**.

---

## 🌟 Key Features

- **Mathematical Problem Modeling**:
  - Full implementation of all **Hard Constraints ($H_1 - H_9$)**: no teacher overlaps, no class overlaps, no room overlaps, room capacity, room type (labs vs. classrooms), teacher availability, teacher max weekly load, and lunch breaks.
  - Full implementation of all **Soft Constraints ($S_1 - S_5$)**: class idle gap minimization, subject spread across days, consecutive lab periods, teacher preferences, and teacher fatigue prevention.
- **AI Search Algorithms**:
  - **Backtracking CSP (Baseline)**: Classical recursive tree search with incremental consistency checks.
  - **Backtracking CSP (+ Heuristics)**: Minimum Remaining Values (MRV) + Degree Heuristic tie-breaker + Forward Checking domain pruning + Least Constraining Value (LCV) ordering.
  - **Min-Conflicts Local Search**: Conflicted variable heuristic with random walk and random restart plateau escapes.
  - **Simulated Annealing (+6 Bonus Marks)**: Multi-operator neighborhood exploration with geometric cooling schedule ($T_{k+1} = \alpha T_k$) and Metropolis acceptance criterion.
  - **Hybrid CSP + SA (+6 Bonus Marks)**: Two-phase pipeline where Phase 1 guarantees 0 hard conflicts via CSP, and Phase 2 strictly navigates the feasible manifold using SA to maximize soft-constraint timetable quality.
  - **Hill Climbing**: Deterministic steepest-descent local search baseline.
- **Interactive Streamlit Web UI**:
  - **Multi-View Timetable Grids**: View by Class Batch, by Teacher, and by Room.
  - **Real-Time Manual Editing & Conflict Flagger**: Move any session; conflicts are immediately identified and explained in human-readable terms.
  - **Export Capabilities**: Instant download as formatted CSV and multi-sheet styled Excel workbook (`.xlsx`).
  - **Analytics Studio**: Interactive Plotly convergence graphs (Cost vs. Iterations) and automated benchmark comparison.

---

## 📋 Project Structure

```
timetable_project/
├── app.py                      # Interactive Streamlit Web Application
├── README.md                   # Setup guide and usage instructions
├── PROJECT_REPORT.md           # Full academic report (6-10 pages equivalent)
├── core/
│   ├── models.py               # Data models: Subject, Teacher, ClassBatch, Room, TimetableProblem
│   └── constraints.py          # Unified Hard (H1-H9) & Soft (S1-S5) constraint evaluators
├── solvers/
│   ├── base.py                 # Abstract BaseSolver and SolverResult
│   ├── backtracking.py         # Plain & Heuristic Backtracking (MRV, Degree, FC, LCV)
│   ├── min_conflicts.py        # Min-Conflicts Local Search with Plateau Escape
│   ├── simulated_annealing.py  # Simulated Annealing (+6 Bonus)
│   ├── hybrid.py               # Hybrid CSP + Simulated Annealing (+6 Bonus)
│   └── hill_climbing.py        # Hill Climbing baseline
├── data/
│   ├── datasets.py             # Solvable Small & Large dataset generators
│   ├── small_dataset.json      # 3 classes, 6 teachers, 4 rooms, 5x6 periods (47 sessions)
│   └── large_dataset.json      # 8 classes, 16 teachers, 9 rooms, 5x7 periods (132 sessions)
├── export/
│   ├── excel_exporter.py       # Multi-tab styled Excel (.xlsx) generator
│   └── csv_exporter.py         # CSV schedule exporter
├── experiments/
│   ├── benchmark.py            # Automated 10-trial runner across both datasets
│   ├── benchmark_results.json  # Raw benchmark trial data
│   └── cost_vs_iterations.png  # Generated convergence plot
└── tests/
    └── test_scheduler.py       # Comprehensive unit test suite
```

---

## 🚀 Quickstart & Installation

### 1. Requirements
- Python 3.10+ (tested on Python 3.12)
- Dependencies: `streamlit`, `pandas`, `numpy`, `matplotlib`, `plotly`, `openpyxl`

### 2. Setup
Clone the repository and install the dependencies:
```bash
git clone <your-repo-link>
cd pooja
pip install streamlit pandas numpy matplotlib plotly openpyxl
```

### 3. Launch the Application
Run the Streamlit application:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 4. Run Unit Tests
```bash
python -m unittest tests/test_scheduler.py
```

### 5. Run 10-Trial Benchmark Evaluation
To reproduce the experimental comparison table and convergence curves:
```bash
python -m experiments.benchmark
```

---

## 📊 Experimental Results (10 Runs Summary)

### Small Dataset (3 Classes, 6 Teachers, 4 Rooms — 47 Sessions)
| Metric | Backtracking (Baseline) | Backtracking (+ Heuristics) | Min-Conflicts | Simulated Annealing (+6) | Hybrid CSP+SA (+6) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Time taken (s)** | 0.0051 | 0.0353 | 0.0092 | 0.8041 | 0.1998 |
| **Nodes / Iterations** | 47 | 47 | 21.5 | 3500.0 | 666.0 |
| **Hard violations** | 0 | 0 | 0.0 | 0.0 | 0.0 |
| **Soft penalty score** | 525 | 470 | 465.0 | **161.5** | **280.5** |
| **Success rate** | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |

### Large Dataset (8 Classes, 16 Teachers, 9 Rooms — 132 Sessions)
| Metric | Backtracking (Baseline) | Backtracking (+ Heuristics) | Min-Conflicts | Simulated Annealing (+6) | Hybrid CSP+SA (+6) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Time taken (s)** | 0.0516 | 1.1845 | 0.1749 | 3.0988 | 1.6207 |
| **Nodes / Iterations** | 132 | 132 | 62.7 | 5000.0 | 666.0 |
| **Hard violations** | 0 | 0 | 0.0 | 0.0 | 0.0 |
| **Soft penalty score** | 1555 | 1400 | 1489.0 | **493.5** | **994.0** |
| **Success rate** | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |

---

## 🎯 Demo Walkthrough (8-10 Minutes Guide)

1. **Overview (1 min)**: Explain CSP formulation (Variables = sessions, Domains = (Day, Period, Room), Constraints = H1-H9 and S1-S5).
2. **Dataset Selection (1 min)**: Show Small vs. Large datasets with automated solvability validation.
3. **Algorithm Execution (3 min)**:
   - Run Plain Backtracking vs. Backtracking with Heuristics (show speed & zero backtracks).
   - Run Min-Conflicts (show rapid convergence in ~20 iterations).
   - Run **Simulated Annealing** and **Hybrid CSP+SA** (show dramatic reduction in soft penalty score from 1555 down to 493).
4. **Timetable Visualization & Exports (2 min)**:
   - Switch between Class, Teacher, and Room views.
   - Download multi-sheet Excel file (`.xlsx`) and CSV.
5. **Real-time Conflict Detection (2 min)**:
   - Open Manual Editor, intentionally move a lecture to conflict with a teacher or lunch break.
   - Show instant red alert detailing the exact clash.
