# Project Report: AI-Based Timetable Scheduler

**Course**: Artificial Intelligence | **Class**: B.Tech, Second Year  
**Team Size**: 3 Students | **Marks**: 18 (+ 12 Bonus Marks = 30 Marks)  
**Submission Deliverable**: GitHub Code, Project Report, Working Demo  

---

## 1. Problem Formulation

The academic timetable scheduling problem is modeled as a **Constraint Satisfaction Problem (CSP)** supplemented with an optimization objective over soft preferences.

### 1.1 Variables ($X$)
Every atomic lecture or laboratory session required by a student batch is modeled as a distinct decision variable:
$$X_i = \langle C_i, S_i, T_i, k_i, \tau_i \rangle$$
Where:
- $C_i \in \mathcal{C}$: Class or student batch (e.g., `Class_A`, `Class_1`).
- $S_i \in \mathcal{S}$: Subject course code (e.g., `MATH`, `AI_LAB`).
- $T_i \in \mathcal{T}$: Instructor assigned to teach the course.
- $k_i \in \{1, \dots, \text{WeeklyHours}(S_i)\}$: The $k$-th weekly session index.
- $\tau_i \in \{\text{Theory}, \text{Lab}\}$: Session type.

For the **Small Dataset**, $N = 47$ discrete session variables are defined across 3 classes. For the **Large Dataset**, $N = 132$ session variables are defined across 8 classes.

### 1.2 Domain ($D$)
The domain of each variable $X_i$ is the Cartesian product of available working days, time periods, and physical rooms:
$$D(X_i) = \{ (d, p, r) \mid d \in \text{Days}, \, p \in \{1, \dots, P\}, \, r \in \mathcal{R} \}$$
To prune the state space prior to search, unary filtering is applied:
1. **Room Type Match**: If $\tau_i = \text{Lab}$, $r \in \mathcal{R}_{\text{lab}}$; if $\tau_i = \text{Theory}$, $r \in \mathcal{R}_{\text{classroom}}$.
2. **Room Capacity**: $\text{Capacity}(r) \ge \text{Strength}(C_i)$.
3. **Class Lunch Break**: $p \neq \text{LunchPeriod}(C_i)$.
4. **Instructor Availability**: $(d, p) \notin \text{UnavailableSlots}(T_i)$.

### 1.3 Constraints Specification

#### Hard Constraints ($H_1 - H_9$, Must Never Be Violated)
1. **$H_1$ (Instructor Collision)**: An instructor cannot teach two sessions simultaneously:
   $$\forall X_i \neq X_j: (T_i = T_j \land d_i = d_j \land p_i = p_j) \implies \text{Violation}$$
2. **$H_2$ (Class Collision)**: A class batch cannot attend two sessions simultaneously:
   $$\forall X_i \neq X_j: (C_i = C_j \land d_i = d_j \land p_i = p_j) \implies \text{Violation}$$
3. **$H_3$ (Room Collision)**: A room cannot host two sessions simultaneously:
   $$\forall X_i \neq X_j: (r_i = r_j \land d_i = d_j \land p_i = p_j) \implies \text{Violation}$$
4. **$H_4$ (Room Capacity)**: $\text{Capacity}(r_i) \ge \text{Strength}(C_i)$.
5. **$H_5$ (Room Type Compatibility)**: $\tau_i = \text{Type}(r_i)$.
6. **$H_6$ (Instructor Availability)**: $(d_i, p_i) \notin \text{UnavailableSlots}(T_i)$.
7. **$H_7$ (Weekly Load Fulfillment)**: Every course gets exactly its prescribed weekly contact hours.
8. **$H_8$ (Instructor Max Load)**: $|\{X_i \mid T_i = t\}| \le \text{MaxWeeklyLoad}(t)$.
9. **$H_9$ (Lunch Break Protection)**: $p_i \neq \text{LunchPeriod}(C_i)$.

#### Soft Constraints ($S_1 - S_5$, Implemented and Optimized)
1. **$S_1$ (Minimize Idle Periods)**: Minimizes free gap periods between scheduled sessions for a class on any day. (Weight $w_1 = 15$)
2. **$S_2$ (Subject Day-Spread)**: Avoids clustering multiple theory sessions of the same subject on the same day. (Weight $w_2 = 10$)
3. **$S_3$ (Consecutive Laboratory Periods)**: Laboratory sessions must occupy adjacent periods in the same room. (Weight $w_3 = 25$)
4. **$S_4$ (Instructor Preferences)**: Schedules instructors in their declared preferred periods. (Weight $w_4 = 5$)
5. **$S_5$ (Instructor Fatigue Prevention)**: Penalizes scheduling more than two consecutive teaching periods for an instructor. (Weight $w_5 = 20$)

---

## 2. Cost Function Definition

To guide local search and metaheuristics, we formulate a scalar evaluation function:
$$\text{Cost}(S) = 1000 \cdot \mathcal{H}(S) + \sum_{k=1}^5 w_k \cdot \mathcal{S}_k(S)$$
Where:
- $\mathcal{H}(S) = \sum_{m=1}^9 \text{violations}(H_m)$ is the total count of hard constraint breaches.
- $\mathcal{S}_k(S)$ is the count of soft constraint violations of type $k$.
- The multiplier $1000$ strictly prioritizes hard constraint satisfaction over soft preferences. A schedule is mathematically **feasible** if and only if $\mathcal{H}(S) = 0$.

---

## 3. Algorithm Descriptions and Design Choices

### 3.1 Algorithm 1: Systematic Backtracking CSP

#### Baseline Backtracking
- **Search Tree**: Explores variables in static sequential order.
- **Value Ordering**: Arbitrary domain order.
- **Inference**: None; consistency is validated incrementally at each node.
- **Limitation**: Suffers from thrashing and catastrophic backtracking on densely constrained instances.

#### Backtracking with Advanced Heuristics
1. **MRV (Minimum Remaining Values)**: Selects the unassigned variable $X_i$ with the smallest remaining domain $|D(X_i)|$, triggering early pruning ("fail-first" principle).
2. **Degree Heuristic**: Breaks ties in MRV by selecting the variable involved in the greatest number of constraints with other unassigned variables.
3. **Forward Checking (FC)**: When $X_i$ is assigned $(d, p, r)$, all incompatible choices in neighboring unassigned variables (sharing teacher, class, or room) are removed. If any domain is emptied, the branch is pruned immediately.
4. **LCV (Least Constraining Value)**: Orders candidate values to minimize the number of options eliminated from neighboring domains.

### 3.2 Algorithm 2: Min-Conflicts Local Search
- **Initial Assignment**: Complete assignment initialized randomly across unary-filtered domains.
- **Step Dynamics**:
  1. Identifies all conflicted variables participating in $\ge 1$ hard clash.
  2. Selects a conflicted variable $X_{\text{conf}}$ uniformly at random.
  3. Reassigns $X_{\text{conf}}$ to the domain slot $(d', p', r')$ that minimizes total conflicts.
  4. **Tie-Breaking**: Random selection among tied minimum-conflict slots.
- **Plateau & Local Optima Escaping**:
  - **Random Walk**: With probability $p = 0.10$, selects a random domain value rather than the greedy argmin.
  - **Random Restart**: If no improvement is achieved for 300 iterations, the assignment is re-initialized with a new random seed.

### 3.3 Algorithm 3: Simulated Annealing (+6 Bonus Marks)
- **Feasible Initialization**: Builds a complete conflict-free seed with Min-Conflicts and falls back to heuristic CSP if needed. Infeasible neighbors are rejected so optimization stays on the feasible search space.
- **Neighborhood Operators**:
  1. *Move*: Reassign a single session to a random valid slot (70% probability).
  2. *Swap*: Exchange the time/room assignments of two sessions (20% probability).
  3. *Block Move*: Move consecutive lab sessions together (10% probability).
- **Metropolis Criterion**: Downhill moves ($\Delta E < 0$) are always accepted. Uphill moves ($\Delta E \ge 0$) are accepted with probability:
  $$P(\text{accept}) = \exp\left(-\frac{\Delta E}{T}\right)$$
- **Cooling Schedule**: Geometric temperature reduction $T_{k+1} = \alpha T_k$ with $T_0 = 100.0$, $\alpha = 0.995$, terminating when $T < 0.05$ or max steps reached.

### 3.4 Algorithm 4: Hybrid CSP + Simulated Annealing (+6 Bonus Marks)
- **Two-Phase Architecture**:
  - **Phase 1 (CSP Feasibility Engine)**: Employs Backtracking with MRV and Forward Checking to rapidly locate a 100% collision-free schedule ($\mathcal{H} = 0$).
  - **Phase 2 (Feasible-Manifold Optimization)**: Initializes Simulated Annealing using Phase 1's feasible state. Hard violations are assigned an infinite penalty ($10^5$), compelling the annealing process to strictly explore the feasible sub-space while optimizing soft constraints ($S_1 - S_5$).
- **Advantage**: Combines the mathematical guarantee of exact CSP search with the quality optimization of metaheuristics.

### 3.5 Algorithm 5: Hill Climbing (Baseline Local Search)
- Builds a complete feasible seed with Min-Conflicts, then heuristic CSP if needed. Samples single-session moves, compatible swaps, and whole lab-block moves; accepts only conflict-free moves that strictly improve the soft penalty. Terminates at a local optimum or iteration limit. It does not guarantee a global soft-score optimum.

---

## 4. Experimental Results and Comparative Analysis

> The benchmark figures below are historical results from the earlier solver behavior. The current app hides the Small/Large datasets from its selector, and feasible initialization and local-search neighborhoods have changed. Rerun the benchmark before presenting these values as current measurements.

### 4.1 Benchmark Evaluation Table (10 Runs Average)

#### Small Dataset (3 Classes, 6 Teachers, 4 Rooms, 47 Sessions)
| Metric | Backtracking (Baseline) | Backtracking (+ Heuristics) | Min-Conflicts | Simulated Annealing (+6) | Hybrid CSP+SA (+6) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Time taken (s)** | 0.0051 | 0.0353 | 0.0092 | 0.8041 | 0.1998 |
| **Nodes / Iterations** | 47 | 47 | 21.5 | 3500.0 | 666.0 |
| **Hard violations** | 0 | 0 | 0.0 | 0.0 | 0.0 |
| **Soft penalty score** | 525 | 470 | 465.0 | **161.5** | **280.5** |
| **Success rate** | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |

#### Large Dataset (8 Classes, 16 Teachers, 9 Rooms, 132 Sessions)
| Metric | Backtracking (Baseline) | Backtracking (+ Heuristics) | Min-Conflicts | Simulated Annealing (+6) | Hybrid CSP+SA (+6) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Time taken (s)** | 0.0516 | 1.1845 | 0.1749 | 3.0988 | 1.6207 |
| **Nodes / Iterations** | 132 | 132 | 62.7 | 5000.0 | 666.0 |
| **Hard violations** | 0 | 0 | 0.0 | 0.0 | 0.0 |
| **Soft penalty score** | 1555 | 1400 | 1489.0 | **493.5** | **994.0** |
| **Success rate** | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |

---

### 4.2 Analytical Questions Addressed

#### 1. Which method was faster?
- On the Small Dataset, Baseline Backtracking and Min-Conflicts solved the problem in under $0.01$ seconds.
- On the Large Dataset, **Min-Conflicts** found a valid schedule fastest (average $0.1749$ seconds in 62.7 iterations), followed by Heuristic Backtracking ($1.184$ seconds).
- Simulated Annealing took longer ($3.09$ seconds) because its objective is not merely finding feasibility, but performing thousands of temperature cooling steps to optimize soft constraints.

#### 2. Which gave better soft-constraint quality?
- **Simulated Annealing and Hybrid CSP+SA delivered vastly superior soft-constraint quality**.
- Pure Backtracking and Min-Conflicts focus on reaching $\mathcal{H} = 0$ and terminate as soon as hard constraints are met, leaving high soft penalties ($1400 - 1555$ on Large).
- In contrast, Simulated Annealing slashed the soft penalty score from $1555$ down to **$493.5$** (a **68.2% reduction in student gaps, teacher fatigue, and subject clustering**). Hybrid CSP+SA achieved an initial feasibility state in $1.18$s and then optimized soft penalty down to **$994.0$**.

#### 3. What happens as the problem grows?
- **Search Space Explosion**: As variables increase from 47 to 132, the raw state space grows from $|D|^{47}$ to $|D|^{132}$.
- Without Forward Checking, unguided backtracking is prone to deep recursive thrashing when constraints become tight.
- Min-Conflicts scales effectively in time complexity ($O(N \cdot k)$), but requires random walk mechanics to escape dense plateaus.
- Simulated Annealing scales predictably with its cooling schedule budget ($O(\text{steps})$).

#### 4. When would you use each method?
- **Backtracking with Heuristics (MRV + FC)**: Ideal when an absolute mathematical proof of feasibility or unsatisfiability is required.
- **Min-Conflicts**: Best suited for rapid feasibility generation in interactive applications where immediate clash-free scheduling is needed.
- **Simulated Annealing / Hybrid CSP+SA**: The gold standard for real-world academic institutions where student satisfaction (minimal gaps, balanced days) and faculty preferences are paramount.

---

## 5. Software Architecture & Usability Features

1. **Modular Engine**: Complete decoupling of core constraint logic (`core/constraints.py`), solver algorithms (`solvers/`), and the presentation tier (`app.py`).
2. **Interactive Manual Editor**: Live conflict detection flags hard clashes (with specific teacher, class, and room details) when the user modifies a schedule.
3. **Multi-View Grids**: Instant rendering of timetables by Class, by Teacher, and by Room.
4. **Export Engine**: One-click generation of CSVs and multi-tab, color-formatted Excel workbooks (`.xlsx`).

---

## 6. Limitations and Future Work

1. **Elective Subject Grouping**: Currently, subjects are assigned per entire class batch. Future versions can support elective splits (students within the same batch choosing different subjects).
2. **Dynamic Room Distances**: Incorporating physical building walking times between consecutive lectures for teachers and students.
3. **Genetic Algorithm Comparison**: Adding Evolutionary Algorithms as an additional metaheuristic comparison point.

---

## 7. Team Member Contributions

| Member | Primary Responsibilities |
| :--- | :--- |
| **Member 1** | Mathematical CSP modeling, Hard (H1-H9) and Soft (S1-S5) constraint evaluators, dataset validation. |
| **Member 2** | Backtracking CSP implementation (MRV, Degree, Forward Checking, LCV), Min-Conflicts local search. |
| **Member 3** | Simulated Annealing (+6 Bonus), Hybrid CSP+SA (+6 Bonus), Streamlit UI, Excel exporter, and benchmark analysis. |
