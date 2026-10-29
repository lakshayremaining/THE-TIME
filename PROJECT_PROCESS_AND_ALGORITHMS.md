# AI-Based Timetable Scheduler

## Project purpose

This project creates a weekly timetable for academic classes. It assigns every required lecture or lab session to a day, period, and room while avoiding clashes between classes, teachers, and rooms. It can also compare scheduling algorithms and display or export the resulting timetable.

The application is built in Python. The scheduling interface uses Streamlit; the scheduling data and constraints are in `core/`; algorithms are in `solvers/`; sample problems are in `data/`; and CSV/Excel output is in `export/`.

## What the application can do

- Load the IIIT Kota odd-semester timetable problem or upload a custom JSON problem. Small/large generators remain for internal tests and benchmarks, but are no longer offered in the app's dataset selector.
- Validate input information such as room availability, class strength, teacher qualifications, and teaching load.
- Generate a timetable with one of six algorithms.
- Show the result by class, teacher, all teachers, or room.
- Report hard conflicts and soft-constraint penalties.
- Move a session manually, pin its chosen day, period, and room, then rerun the selected algorithm to schedule the other sessions around it.
- Keep the old timetable visible if the selected algorithm cannot find a complete conflict-free schedule with the requested manual slot.
- Export a schedule as CSV or a styled Excel workbook.
- Plot solver cost history and view benchmark comparisons in the Analytics tab.

## Timetable problem: what is being scheduled?

Each required weekly meeting is represented as a session variable. For example, if a class needs four weekly MATH lectures, the model creates four distinct MATH session variables. A solver assigns each variable a `SlotAssignment`:

```text
(day, period, room)
```

For example:

```text
Class_A / MATH / Prof_Smith / session 1 -> Tuesday, Period 2, Room_101
```

The available domain for a session is filtered before or during search. A candidate slot must use a room with enough capacity and the correct type, avoid the class lunch period, and avoid the teacher's unavailable periods. Multi-period labs also need consecutive periods in the same room.

### Hard constraints

These constraints define whether a timetable is valid. A valid final timetable should have zero hard violations.

1. **Teacher clash:** a teacher cannot teach two sessions at the same time.
2. **Class clash:** a class cannot attend two sessions at the same time.
3. **Room clash:** a room cannot host two sessions at the same time.
4. **Room capacity:** the room must fit the class.
5. **Room type:** labs use lab rooms; theory sessions use classrooms.
6. **Teacher availability:** sessions avoid a teacher's unavailable slots.
7. **Weekly requirements:** each subject's required sessions are represented in the problem and scheduled.
8. **Teacher load:** a teacher cannot exceed their maximum weekly load.
9. **Lunch:** a session cannot occupy the class's lunch period.
10. **Lab block integrity:** linked periods in a multi-hour lab must stay consecutive, on the same day, and in the same room.

The implementation checks the lab-block rule as an additional hard check alongside the named H1-H9 rules.

### Soft constraints

Soft constraints measure schedule quality. A timetable may be valid while still receiving a soft penalty.

| Goal | What the score discourages | Weight in the implementation |
|---|---|---:|
| Reduce class gaps | Empty periods between a class's first and last session in a day | 15 per gap |
| Spread theory subjects | Multiple lectures of the same subject clustered on one day | 10 per excess lecture |
| Keep labs together | Linked lab sessions separated or put in different rooms | 25 |
| Respect teacher preferences | Assigning a teacher outside their listed preferred periods | 5 per preference miss |
| Reduce teacher fatigue | More than two consecutive teaching periods | 20 per excess consecutive period |

The general evaluation is:

```text
total cost = 1000 × hard-violation count + soft-penalty score
```

This makes hard conflicts much more expensive than soft preferences. Search algorithms use this cost differently: CSP solvers reject conflicts while building a schedule, while local-search algorithms compare candidate schedules by their cost.

## The scheduling process, from input to timetable

1. **Choose the problem.** Select the IIIT Kota dataset or upload a custom JSON problem.
2. **Validate the input.** The app checks basic feasibility and shows the number of sessions to schedule.
3. **Choose an algorithm.** Select a solver and adjust its available parameters in the sidebar.
4. **Build candidate slots.** For each session, generate day-period-room choices that meet unary rules such as room type, capacity, availability, and lunch.
5. **Search or improve.** The selected algorithm creates a complete timetable, resolves conflicts, or tries to reduce its cost.
6. **Evaluate the result.** The app calculates hard violations, soft penalty, run time, and solver steps.
7. **Review the timetable.** Open Timetable Views and choose the class, teacher, or room view.
8. **Refine if needed.** In Manual Editor, pin a session to a new slot and rerun the selected algorithm. The other sessions are allowed to move around the pinned slot.
9. **Export or analyze.** Download CSV/Excel or inspect the cost curve and benchmark data.

## How each algorithm builds or improves a timetable

The mini examples below use a made-up schedule with two classes (`Class_A`, `Class_B`), two teachers (`T1`, `T2`), two rooms (`R1`, `R2`), and a few periods. They illustrate the algorithm steps; the exact slot chosen in a real run depends on the selected dataset, domain order, parameters, and random choices.

### 1. Backtracking (Baseline)

**Approach:** depth-first constraint satisfaction search. It visits sessions in their stored order and tries each available slot in domain order. If a slot conflicts with a session already assigned, it skips that slot. If a later session has no legal slot, it goes back to the previous session and tries another choice.

**Example walk-through:**

| Step | Decision | Result |
|---:|---|---|
| 1 | Place `A-MATH-1` with T1 at Mon P1 in R1 | Valid so far |
| 2 | Try `B-PHY-1` with T1 at Mon P1 in R2 | Rejected: T1 is already teaching at Mon P1 |
| 3 | Try `B-PHY-1` with T1 at Mon P2 in R2 | Accepted |
| 4 | Try `A-CS-1` with T2 at Mon P1 in R1 | Rejected if R1 is still occupied; try another room or period |
| 5 | A later session has no legal option | Backtrack and change an earlier assignment, then continue |

The search stops when all variables are assigned consistently, or when its timeout is reached. This method is easy to understand and gives a systematic search, but it can spend time exploring branches that later fail.

### 2. Backtracking with heuristics (MRV, Degree, Forward Checking, LCV)

This is still backtracking, but it uses four ways to choose better search steps:

- **MRV (Minimum Remaining Values):** schedule the unassigned session with the fewest legal slots first. This exposes a dead end early.
- **Degree tie-breaker:** if multiple sessions have the same smallest domain, prefer the one connected to more other sessions, such as sessions sharing a teacher or class.
- **Forward checking:** after assigning a session, remove incompatible day-period-room choices from affected unassigned sessions. If any domain becomes empty, immediately abandon that branch.
- **LCV (Least Constraining Value):** among a session's choices, try a slot that removes fewer options from neighboring sessions first.

**Example walk-through:**

Suppose `A-LAB-1` has only two legal choices, while `B-MATH-1` has twelve. MRV places `A-LAB-1` first. Its linked lab period is reserved in the same room and on the next period. Forward checking then removes those periods from the domains of sessions that share the class, teacher, or room. If that leaves `B-PHY-1` with zero choices, the solver undoes the lab choice immediately instead of scheduling many other sessions first. If two legal lab starts remain, LCV tries the one that blocks fewer neighboring options.

This solver is a good choice when finding a consistent schedule is the priority and the search needs stronger pruning than the baseline.

### 3. Min-Conflicts Local Search

**Approach:** begin with a complete assignment, usually a random choice from each session's unary-valid domain. The initial timetable can contain clashes. Then repeatedly choose a session involved in a hard conflict and move it to a slot that creates the fewest hard conflicts. Ties are broken randomly. A random-walk probability and restarts help the search escape plateaus.

**Example walk-through:**

| Iteration | Current problem | Move |
|---:|---|---|
| 0 | `A-MATH-1` and `B-PHY-1` both use T1 at Tue P2 | Initial timetable has a teacher clash |
| 1 | Pick one of the conflicted sessions | Consider all its allowed slots |
| 2 | Score those slots by conflicts with the other scheduled sessions | Mon P1 creates 2 clashes; Wed P3 creates 0 |
| 3 | Move that session to Wed P3 | Clash count falls |
| 4 | Repeat for any remaining conflicted session | Stop once hard violations reach zero, or when iteration/restart limits are reached |

When the code finds a zero-hard-conflict schedule, it can return immediately; this algorithm focuses on feasibility rather than extended soft-score optimization.

### 4. Simulated Annealing

**Approach:** first construct a complete zero-hard-conflict schedule with Min-Conflicts, using heuristic backtracking if needed. Then repeatedly generate a neighboring schedule. A neighbor can move one session, swap two sessions, or move a linked lab pair together. Infeasible neighbors are rejected. Always accept a lower-soft-penalty schedule; sometimes accept a higher one with probability `exp(-change / temperature)`. The temperature decreases over time, so exploration is more likely early and less likely later. The best feasible schedule seen is returned.

**Example walk-through:**

1. Construct a feasible starting timetable with soft penalty 180.
2. Move `A-MATH-1` from Tue P2 to Wed P3; discard this neighbor if it creates a hard conflict.
3. If it is feasible and has a lower soft penalty, accept it. If its penalty is higher, accept it only if the random acceptance test passes at the current temperature.
4. Try another neighbor, such as swapping two sessions or moving a lab pair together.
5. Cool the temperature and repeat until the step budget or temperature threshold is reached.
6. Return the best-cost state encountered.

If no feasible starting schedule can be built within the configured limit, Simulated Annealing reports the failure rather than presenting an incomplete schedule as successful.

### 5. Hybrid CSP + Simulated Annealing

**Approach:** combine feasibility search with timetable-quality improvement.

**Phase 1 — find a feasible schedule:** use heuristic backtracking to find a complete schedule with zero hard violations. If this phase does not succeed, the implementation falls back to feasible initialization and standalone Simulated Annealing.

**Phase 2 — improve quality:** start from the feasible schedule and try moving sessions. A candidate with hard conflicts receives a very large penalty. The search accepts feasible changes according to the annealing rule and keeps the best soft score found.

**Example walk-through:**

| Phase | Schedule state | Action |
|---|---|---|
| 1 | Some sessions are unassigned | MRV/forward checking fills all sessions with no teacher, class, or room clash |
| 2, start | Complete feasible timetable, soft penalty 180 | Save it as the current best |
| 2, step 1 | Move a lecture and produce soft penalty 165, hard violations 0 | Accept as an improvement; update best |
| 2, step 2 | Try a slot that clashes with another class | Large hard-conflict penalty makes the move unattractive; keep exploring feasible options |
| End | Best feasible state seen, for example soft penalty 140 | Return it for the views and exports |

This is useful when the goal is both a conflict-free schedule and better soft-constraint quality. As with any configured search, check the displayed success and hard-violation metrics.

### 6. Hill Climbing (Comparison Baseline)

**Approach:** first build a complete feasible timetable using Min-Conflicts, then heuristic backtracking if needed. Sample neighboring schedules and move to the best conflict-free neighbor only when its soft penalty is strictly lower. Moves include changing one session, swapping compatible sessions, and moving a whole lab block. Stop when no sampled neighbor improves the current score or the iteration limit is reached.

**Example walk-through:**

| Iteration | Current cost | Sampled alternatives | Decision |
|---:|---:|---|---|
| 0 | 180 soft penalty, 0 hard conflicts | Move MATH: 165; swap PHY/CS: 140; move lab pair: 190 | Choose the swap (lowest feasible sampled penalty) |
| 1 | 140 soft penalty, 0 hard conflicts | Best sampled neighbor: 140; others are higher or infeasible | Stop: no strict feasible improvement |

The search is simple and fast, but it can stop at a local minimum. The feasible initializer and acceptance rule keep the result conflict-free when initialization succeeds. Hill Climbing improves the best schedule it finds; it does not prove a global soft-constraint optimum.

## Manual editing and pinned-slot rescheduling

Manual editing is intended for a user who wants one session to stay at a chosen time and room while the rest of the timetable is recomputed.

1. Generate a timetable.
2. Open **Manual Editor & Conflict Flagger**.
3. Choose a session, then choose its new day, period, and room.
4. Click **Apply Move & Re-schedule**.
5. The selected slot is added to the fixed assignments and passed to the selected solver. Other sessions remain movable.
6. If a complete zero-hard-conflict assignment is found with the manual slot preserved, the app replaces the current schedule with that result.
7. Open **Timetable Views** to see the latest assignment by class, teacher, or room.
8. If the solver cannot find a valid schedule, the app reports that and keeps the previous schedule visible.

If multiple manual slots have been fixed, later rescheduling keeps those slots fixed too. Reloading or changing the dataset clears the manual pins.

## Reading the result

- **Execution Time:** wall-clock time spent in the solver.
- **Nodes / Steps:** search nodes or local-search iterations, depending on the algorithm.
- **Hard Violations:** the number of rule breaches. A conflict-free result should show `0`.
- **Soft Penalty:** weighted schedule-quality score. Lower is better, but compare this only after checking that hard violations are zero.
- **Cost curve:** the Analytics tab can show the recorded cost history for algorithms that provide it.

## Project layout

```text
app.py                         Streamlit interface and user workflow
core/models.py                 Data classes and candidate-slot generation
core/constraints.py            Hard/soft constraint checks and cost calculation
data/datasets.py               Built-in demonstration problem generators
data/*.json                    Problem data files
solvers/base.py                Shared solver result structure and fixed-slot support
solvers/backtracking.py        Baseline and heuristic CSP search
solvers/min_conflicts.py       Min-Conflicts local search
solvers/simulated_annealing.py Simulated Annealing local search
solvers/hybrid.py              CSP followed by Simulated Annealing
solvers/hill_climbing.py       Hill Climbing comparison solver
export/csv_exporter.py         CSV timetable output
export/excel_exporter.py       Excel timetable output
experiments/benchmark.py       Benchmark runner
tests/test_scheduler.py        Automated test suite
```

## Running the application

From the project folder, run:

```bash
python -m streamlit run app.py
```

Then open the local URL printed in the terminal (normally `http://localhost:8501`). The project dependencies listed in the README include Streamlit, pandas, NumPy, Matplotlib, Plotly, and openpyxl.

