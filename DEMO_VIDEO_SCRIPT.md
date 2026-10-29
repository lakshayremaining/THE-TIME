# AI Timetable Scheduler: Official 6-to-8 Minute Demo Video Script

**Format**: Screen recording with Voiceover & Live Walkthrough  
**Tone**: Technical, Professional, Academic, and Logical  
**Target Duration**: ~6 to 8 minutes  

---

## 🎬 Video Overview & Timestamp Breakdown

| Timestamp | Segment Title | Primary Focus & Features Covered |
| :--- | :--- | :--- |
| **00:00 - 01:00** | **1. Introduction & Problem Modeling** | NP-hard Timetabling, Hard ($H_1-H_9$) & Soft ($S_1-S_5$) Constraints |
| **01:00 - 02:00** | **2. Dataset Configuration & Data Input** | IIIT Kota Odd Semester benchmark, Custom JSON, Real-world scale |
| **02:00 - 04:00** | **3. AI Solver Engine & Algorithm Suite** | Backtracking (MRV+Degree+FC+LCV), Min-Conflicts, Simulated Annealing, Hybrid CSP+SA |
| **04:00 - 05:15** | **4. Multi-View Schedule Explorer & Export** | Class Grid, Teacher View, Room Utilization, Excel & CSV Exporter |
| **05:15 - 06:30** | **5. Interactive Conflict Detection Studio** | Live Human-in-the-Loop Drag/Move, Instant Hard-Constraint Collision Flagger |
| **06:30 - 07:30** | **6. Analytics, Convergence & Benchmark** | Cost vs. Iteration trajectory, Algorithm speed/violation comparison |
| **07:30 - 08:00** | **7. Summary & Architectural Conclusion** | Summary of findings, Feasible manifold guarantee, Outro |

---

## 🎙️ Detailed Script: Section by Section

---

### [00:00 - 01:00] Segment 1: Introduction & Problem Formulation
**On Screen:**
- Display Streamlit App Home page: Title banner *"AI Timetable Scheduler - IIIT Kota"*.
- Scroll down slightly or show presentation slide illustrating Hard vs. Soft constraints.

**Voiceover (Spoken):**
> "Hello everyone, and welcome to this demonstration of our **AI-Based Automated Timetable Scheduler**.
>
> University timetabling is a notoriously NP-hard combinatorial optimization problem. When scheduling dozens of student batches, faculty members, and physical rooms, the search space grows exponentially—often exceeding $10^{60}$ potential configurations.
>
> In this project, we formulate timetabling strictly as a **Constraint Satisfaction Problem (CSP)** coupled with **Metaheuristic Local Search**.
>
> Our engine formally evaluates two constraint categories:
> 1. **Hard Constraints ($H_1$ to $H_9$)**: These are non-negotiable. They mandate zero teacher conflicts, zero class batch overlaps, zero room collisions, strict adherence to room capacities, dedicated laboratory room matching, teacher unavailability windows, weekly workload caps, and dedicated lunch intervals.
> 2. **Soft Constraints ($S_1$ to $S_5$)**: These represent timetable quality—minimizing idle gaps for students, spreading courses uniformly across weekdays, enforcing consecutive lab blocks, and honoring faculty preferences to avoid fatigue.
>
> Let's look at how the application operates."

---

### [01:00 - 02:00] Segment 2: Dataset Configuration & Data Input
**On Screen:**
- Mouse navigates to the left Sidebar under **"Configuration & Data"**.
- Expand the dataset selection dropdown. Show the loaded **IIIT Kota Odd Semester (3rd, 5th, 7th Semesters)**.
- Highlight the metrics summary: Number of Classes, Faculty members, Available Classrooms/Labs, and Weekly Time Slots ($5 \text{ days} \times 8 \text{ periods}$).
- Briefly show the *"Upload Custom JSON"* expander to demonstrate extensibility.

**Voiceover (Spoken):**
> "On the left sidebar, we have our data ingestion interface. 
> 
> By default, the system loads the authentic **IIIT Kota Odd Semester dataset**, covering 3rd, 5th, and 7th semester batches across Computer Science and Electronics branches. 
> 
> This benchmark contains over 100 lecture and laboratory sessions, assigned across multiple specialized hardware labs, computer centres, and lecture halls.
> 
> Users can also upload custom university JSON structures or adjust problem parameters dynamically. The problem model parses every entity into explicit variables: a 4-tuple consisting of the *Class Batch, Subject, Teacher,* and *Room Type*. The solver's goal is to bind each variable to an optimal domain slot of `(Day, Period, Room)`."

---

### [02:00 - 04:00] Segment 3: The AI Solver Suite (Core Algorithms in Action)
**On Screen:**
- Navigate to the **"Algorithm Selection"** section in the sidebar.
- Show the dropdown containing:
  1. Plain Backtracking (Baseline)
  2. Heuristic CSP (MRV + Degree + FC + LCV)
  3. Min-Conflicts Local Search
  4. Simulated Annealing
  5. Hybrid CSP + Simulated Annealing
  6. Hill Climbing
- Select **Hybrid CSP + SA**, adjust parameters (Max Iterations, Initial Temp), and click **"Generate Timetable"**.
- Watch the progress bar execute and display the final performance card: Execution Time (seconds), Hard Violations (`0`), and Soft Penalty Cost.

**Voiceover (Spoken):**
> "Now let us examine the engine's core: our algorithmic search suite. Rather than offering a single black-box method, we implemented and benchmarked five distinct AI paradigms:
>
> First, **Backtracking CSP**: We start with classical depth-first chronological backtracking as our baseline. Alongside it, we built **Heuristic CSP**, which integrates four powerful pruning heuristics:
> - **MRV (Minimum Remaining Values)** selects the most constrained variable first.
> - **Degree Heuristic** breaks ties by choosing the variable with the highest degree of constraint constraints on others.
> - **Forward Checking** prunes invalid domain values ahead of time to eliminate dead branches early.
> - **LCV (Least Constraining Value)** orders domain values to leave maximum flexibility for unassigned sessions.
>
> Second, **Min-Conflicts Local Search**: This starts with an initial state and iteratively repairs conflicting variables using a randomized min-conflict heuristic with random-walk restarts to escape local plateaus.
>
> Third, **Simulated Annealing**: Utilizing a geometric cooling schedule $T_{k+1} = \alpha T_k$ and the Metropolis acceptance criterion $P = e^{-\Delta C / T}$, allowing uphill moves early in search to escape local minima.
>
> And finally, our premier algorithm: the **Hybrid Two-Phase CSP + SA**. 
> - **Phase 1** uses constraint satisfaction to establish a mathematically guaranteed conflict-free baseline (Zero hard violations).
> - **Phase 2** activates Simulated Annealing restricted solely to the feasible manifold—swapping compatible slots to minimize idle gaps and maximize teacher spread without ever reintroducing a hard conflict.
>
> Let's run the **Hybrid Solver** right now... Within just a few seconds, the solver converges: Hard Violations: exactly **Zero**, with an optimized soft cost penalty."

---

### [04:00 - 05:15] Segment 4: Multi-View Timetable Grids & One-Click Export
**On Screen:**
- Scroll to the main viewing area.
- Switch between the tabs:
  1. **"By Class Batch"**: Select `3rd Sem CSE`, observe consecutive 2-hour lab slots and cleanly distributed lectures.
  2. **"By Teacher"**: Select a specific professor, showing their daily schedule, max load limit respected, and lunch buffer.
  3. **"By Room"**: Select a Lab/Classroom, showing zero overlapping bookings.
- Scroll down to the export buttons and click **"Export to Excel (.xlsx)"** and **"Export to CSV"**. Show the downloaded multi-sheet Excel file.

**Voiceover (Spoken):**
> "Once the schedule is generated, the interface renders a responsive, multi-dimensional view of the solution.
>
> 1. In the **Class Batch View**, academic coordinators can verify that each student group has a balanced day. Notice how laboratory sessions are placed in consecutive two-period blocks, and mandatory lunch intervals remain free.
> 2. Switching to the **Teacher View**, individual faculty members can inspect their personal schedules. The engine guarantees that no professor is double-booked across different rooms or assigned beyond their maximum weekly workload.
> 3. The **Room View** provides infrastructure management, verifying room capacities and equipment compatibility.
>
> For administrative deployment, the platform includes a **One-Click Exporter**. We can export the entire institutional schedule directly into CSV format or an automated, multi-tab styled Excel workbook where each class batch and faculty member has their own dedicated worksheet."

---

### [05:15 - 06:30] Segment 5: Real-Time Manual Editing & Conflict Flagger
**On Screen:**
- Navigate to the **"Interactive Schedule Editor"** section.
- Select a session (e.g., *Data Structures Lecture for 3rd Sem CSE*).
- Attempt to move it to a slot where the teacher is already teaching another batch or where the room is occupied.
- Watch the **Red Conflict Alert Box** immediately appear with explicit human-readable reasons (e.g., *"Hard Constraint H1 Violated: Teacher Dr. X is already booked on Tuesday Period 3 in Room 102"*).
- Now, move the session to a valid, open slot. The box turns **Green** (*"Valid Move: 0 Conflicts"*).

**Voiceover (Spoken):**
> "Real-world academic environments require agility—professors may request emergency swaps or rooms might undergo maintenance. To address this, we developed a **Real-Time Human-in-the-Loop Conflict Detection Studio**.
>
> Let's demonstrate this live. Suppose an administrator wants to manually shift a Tuesday lecture to Wednesday morning.
>
> If we pick an occupied slot, our real-time constraint evaluator immediately intercepts the move and triggers a diagnostic alert. It doesn't just show an error; it explains the exact mathematical constraint breached—for instance: *'Teacher Overlap: Faculty already assigned to 5th Sem CSE in Lab 2'*.
>
> When we instead move the lecture to an open, valid slot, the validator confirms the transition with zero hard conflicts and dynamically updates the timetable grid. This ensures administrative flexibility without corrupting schedule integrity."

---

### [06:30 - 07:30] Segment 6: Analytics Studio, Convergence Curves & Benchmarks
**On Screen:**
- Scroll down to the **"Analytics & Convergence Studio"**.
- Point to the interactive **Plotly Convergence Curve** (*Cost vs. Iterations*).
- Hover over the curve to show the temperature cooldown and cost reduction trajectory.
- Show the **Automated Benchmark Comparison Table** comparing Backtracking vs. Heuristic CSP vs. Min-Conflicts vs. Simulated Annealing on metrics: Execution Time, Hard Violations, and Final Quality Cost.

**Voiceover (Spoken):**
> "To validate our algorithms scientifically, the platform integrates an **Analytics & Convergence Studio**.
>
> Here we see the interactive convergence plot generated using Plotly. For Simulated Annealing and Min-Conflicts, it tracks the cost trajectory across iterations. Notice how early iterations show exploratory peaks—characteristic of the Metropolis acceptance criteria escaping local plateaus—before steadily cooling and converging toward the global optimum.
>
> Furthermore, our pre-compiled **Benchmark Comparison Matrix** aggregates results across multiple random-seed trials:
> - Plain Backtracking often hits worst-case exponential time limits on dense datasets.
> - Heuristic CSP with MRV and Forward Checking reduces backtrack states by more than 85%.
> - And our Hybrid CSP+SA consistently produces the highest quality soft-penalty scores while strictly maintaining zero hard violations."

---

### [07:30 - 08:00] Segment 7: Conclusion & Wrap-Up
**On Screen:**
- Return to the top of the app showing the clean timetable schedule.
- Show your name, repository URL (`github.com/lakshayremaining/THE-TIME`), and live Streamlit link.

**Voiceover (Spoken):**
> "In conclusion, this project provides a complete, mathematically sound, and user-friendly AI solution to university timetable scheduling. By synthesizing deterministic CSP pruning with stochastic metaheuristics, we achieve both absolute constraint satisfaction and high pedagogical timetable quality.
>
> The entire project is open-source, fully tested with unit tests, and live on Streamlit Cloud.
>
> Thank you for watching!"

---

## 💡 Tips for Recording Your Demo Video

1. **Resolution & Scaling**: Record at `1920x1080` (Full HD). In your browser, set zoom to `100%` or `110%` so typography is crisp and legible.
2. **Smooth Cursor Movements**: Move your cursor deliberately; pause for half a second on elements (like metrics and conflict boxes) before clicking.
3. **Pacing**: Speak at an even, confident pace. The estimated reading time of this script is **6 minutes 45 seconds**, leaving ideal breathing room for 7 to 8 minutes of total video time.
