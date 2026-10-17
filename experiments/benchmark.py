"""
experiments/benchmark.py
Automated experimental evaluation runner (10 runs per randomized method on Small & Large datasets).
Generates benchmark comparison tables and convergence graphs (Cost vs. Iterations).
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from data.datasets import get_small_dataset, get_large_dataset
from solvers.backtracking import PlainBacktrackingSolver, HeuristicBacktrackingSolver
from solvers.min_conflicts import MinConflictsSolver
from solvers.simulated_annealing import SimulatedAnnealingSolver
from solvers.hybrid import HybridCSPSolver
from solvers.hill_climbing import HillClimbingSolver

OUTPUT_DIR = Path(__file__).resolve().parent


def run_benchmark(num_trials: int = 10, timeout_baseline: float = 15.0) -> Dict[str, Any]:
    print("=" * 70)
    print("STARTING EXPERIMENTAL BENCHMARK EVALUATION (10 TRIALS)")
    print("=" * 70)

    datasets = {
        "Small Dataset": get_small_dataset(),
        "Large Dataset": get_large_dataset()
    }

    results_table = {}
    curves_to_plot = {}

    for d_name, problem in datasets.items():
        print(f"\n>>> Evaluating on: {d_name} ({len(problem.variables)} variables) <<<")
        results_table[d_name] = {}

        # 1. Backtracking (Baseline) - Deterministic
        print("Running Plain Backtracking (Baseline)...")
        plain_solver = PlainBacktrackingSolver(problem, timeout_seconds=timeout_baseline)
        plain_res = plain_solver.solve()
        results_table[d_name]["Backtracking (Baseline)"] = {
            "time_taken": round(plain_res.time_taken, 4),
            "nodes_or_iters": plain_res.nodes_expanded,
            "hard_violations": plain_res.hard_violations,
            "soft_penalty": plain_res.soft_penalty,
            "success_rate": "10/10" if plain_res.success else "0/10 (Timeout)"
        }

        # 2. Backtracking (+ Heuristics) - Deterministic
        print("Running Backtracking (+ Heuristics: MRV, Degree, FC, LCV)...")
        heur_solver = HeuristicBacktrackingSolver(problem, timeout_seconds=30.0)
        heur_res = heur_solver.solve()
        results_table[d_name]["Backtracking (+ Heuristics)"] = {
            "time_taken": round(heur_res.time_taken, 4),
            "nodes_or_iters": heur_res.nodes_expanded,
            "hard_violations": heur_res.hard_violations,
            "soft_penalty": heur_res.soft_penalty,
            "success_rate": "10/10" if heur_res.success else "0/10"
        }

        # 3. Min-Conflicts (10 runs)
        print(f"Running Min-Conflicts ({num_trials} runs)...")
        mc_times, mc_iters, mc_hard, mc_soft, mc_success = [], [], [], [], []
        sample_mc_curve = []

        for trial in range(num_trials):
            mc_solver = MinConflictsSolver(
                problem,
                max_iterations=3000 if d_name == "Small Dataset" else 4000,
                random_walk_prob=0.10,
                random_seed=100 + trial
            )
            res = mc_solver.solve()
            mc_times.append(res.time_taken)
            mc_iters.append(res.iterations)
            mc_hard.append(res.hard_violations)
            mc_soft.append(res.soft_penalty)
            mc_success.append(1 if res.success else 0)
            if trial == 0 and res.cost_history:
                sample_mc_curve = res.cost_history

        results_table[d_name]["Min-Conflicts"] = {
            "time_taken": round(float(np.mean(mc_times)), 4),
            "nodes_or_iters": round(float(np.mean(mc_iters)), 1),
            "hard_violations": round(float(np.mean(mc_hard)), 2),
            "soft_penalty": round(float(np.mean(mc_soft)), 1),
            "success_rate": f"{sum(mc_success)}/{num_trials}"
        }
        curves_to_plot[f"{d_name} - Min-Conflicts"] = sample_mc_curve

        # 4. Simulated Annealing (+6 Bonus) (10 runs)
        print(f"Running Simulated Annealing ({num_trials} runs)...")
        sa_times, sa_iters, sa_hard, sa_soft, sa_success = [], [], [], [], []
        sample_sa_curve = []

        for trial in range(num_trials):
            sa_solver = SimulatedAnnealingSolver(
                problem,
                initial_temperature=100.0,
                cooling_rate=0.995,
                max_total_steps=3500 if d_name == "Small Dataset" else 5000,
                random_seed=200 + trial
            )
            res = sa_solver.solve()
            sa_times.append(res.time_taken)
            sa_iters.append(res.iterations)
            sa_hard.append(res.hard_violations)
            sa_soft.append(res.soft_penalty)
            sa_success.append(1 if res.success else 0)
            if trial == 0 and res.cost_history:
                sample_sa_curve = res.cost_history

        results_table[d_name]["Simulated Annealing (+6 Bonus)"] = {
            "time_taken": round(float(np.mean(sa_times)), 4),
            "nodes_or_iters": round(float(np.mean(sa_iters)), 1),
            "hard_violations": round(float(np.mean(sa_hard)), 2),
            "soft_penalty": round(float(np.mean(sa_soft)), 1),
            "success_rate": f"{sum(sa_success)}/{num_trials}"
        }
        curves_to_plot[f"{d_name} - Simulated Annealing"] = sample_sa_curve

        # 5. Hybrid CSP + SA (+6 Bonus) (10 runs)
        print(f"Running Hybrid CSP + SA ({num_trials} runs)...")
        hy_times, hy_iters, hy_hard, hy_soft, hy_success = [], [], [], [], []
        sample_hy_curve = []

        for trial in range(num_trials):
            hy_solver = HybridCSPSolver(
                problem,
                sa_cooling_rate=0.99,
                sa_initial_temp=40.0,
                sa_max_steps=1200,
                random_seed=300 + trial
            )
            res = hy_solver.solve()
            hy_times.append(res.time_taken)
            hy_iters.append(res.iterations)
            hy_hard.append(res.hard_violations)
            hy_soft.append(res.soft_penalty)
            hy_success.append(1 if res.success else 0)
            if trial == 0 and res.cost_history:
                sample_hy_curve = res.cost_history

        results_table[d_name]["Hybrid CSP + SA (+6 Bonus)"] = {
            "time_taken": round(float(np.mean(hy_times)), 4),
            "nodes_or_iters": round(float(np.mean(hy_iters)), 1),
            "hard_violations": round(float(np.mean(hy_hard)), 2),
            "soft_penalty": round(float(np.mean(hy_soft)), 1),
            "success_rate": f"{sum(hy_success)}/{num_trials}"
        }
        curves_to_plot[f"{d_name} - Hybrid CSP+SA"] = sample_hy_curve

    # Save benchmark table as JSON
    with open(OUTPUT_DIR / "benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results_table, f, indent=2)

    # Plot Cost vs. Iterations graph
    plt.figure(figsize=(12, 7))
    for label, curve in curves_to_plot.items():
        if curve:
            # Subsample if too long
            xs = list(range(len(curve)))
            if len(curve) > 500:
                step = len(curve) // 300
                xs = xs[::step]
                curve = curve[::step]
            plt.plot(xs, curve, label=label, linewidth=1.8)

    plt.xlabel("Iteration", fontsize=12)
    plt.ylabel("Total Cost (1000 * Hard + Soft)", fontsize=12)
    plt.title("Cost vs. Iterations Convergence Comparison", fontsize=14, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(fontsize=10)
    plot_file = OUTPUT_DIR / "cost_vs_iterations.png"
    plt.tight_layout()
    plt.savefig(plot_file, dpi=200)
    plt.close()
    print(f"\nSaved convergence plot to {plot_file}")

    # Print formatted markdown table
    print("\n" + "=" * 70)
    print("EXPERIMENTAL RESULTS COMPARISON TABLE (SECTION 6)")
    print("=" * 70)
    for d_name, algos in results_table.items():
        print(f"\n### {d_name}\n")
        print("| Metric | Backtracking (Baseline) | Backtracking (+ Heuristics) | Min-Conflicts | Simulated Annealing (+6) | Hybrid CSP+SA (+6) |")
        print("| :--- | :--- | :--- | :--- | :--- | :--- |")
        
        metrics = [
            ("Time taken (seconds)", "time_taken"),
            ("Nodes / Iterations", "nodes_or_iters"),
            ("Hard violations", "hard_violations"),
            ("Soft penalty score", "soft_penalty"),
            ("Success rate (10 runs)", "success_rate")
        ]
        for m_label, m_key in metrics:
            row = [f"**{m_label}**"]
            for a_name in ["Backtracking (Baseline)", "Backtracking (+ Heuristics)", "Min-Conflicts", "Simulated Annealing (+6 Bonus)", "Hybrid CSP + SA (+6 Bonus)"]:
                row.append(str(algos[a_name][m_key]))
            print("| " + " | ".join(row) + " |")

    return results_table


if __name__ == "__main__":
    run_benchmark(num_trials=10)
