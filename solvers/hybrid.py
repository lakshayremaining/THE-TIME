"""
solvers/hybrid.py
Hybrid CSP + Simulated Annealing Solver (+6 Bonus Marks).
Phase 1: Heuristic CSP Backtracking guarantees a clash-free feasible schedule (0 hard violations).
Phase 2: Feasibility-preserving Simulated Annealing optimizes soft constraints (S1-S5).
"""

import time
import math
import random
from typing import Dict, List, Optional, Tuple
from core.models import TimetableProblem, SessionVariable, SlotAssignment
from core.constraints import ConstraintChecker
from solvers.base import BaseSolver, SolverResult
from solvers.backtracking import HeuristicBacktrackingSolver
from solvers.simulated_annealing import SimulatedAnnealingSolver


class HybridCSPSolver(BaseSolver):
    """
    Two-Stage Hybrid Solver:
    - Stage 1 (CSP): MRV + Forward Checking to find a feasible solution (0 hard violations).
    - Stage 2 (SA): Annealing that stays strictly within the feasible space or heavily penalizes
      any hard violations, specifically targeting soft-constraint quality maximization.
    """

    def __init__(
        self,
        problem: TimetableProblem,
        sa_cooling_rate: float = 0.99,
        sa_initial_temp: float = 50.0,
        sa_max_steps: int = 1500,
        csp_timeout_seconds: float = 25.0,
        random_seed: Optional[int] = 42,
        **kwargs
    ):
        super().__init__(problem, **kwargs)
        self.checker = ConstraintChecker(problem)
        self.sa_cooling_rate = sa_cooling_rate
        self.sa_initial_temp = sa_initial_temp
        self.sa_max_steps = sa_max_steps
        self.csp_timeout_seconds = csp_timeout_seconds
        self.random_seed = random_seed

    def solve(self) -> SolverResult:
        if self.random_seed is not None:
            random.seed(self.random_seed)

        start_time = time.perf_counter()

        # --- Stage 1: CSP Heuristic Backtracking ---
        csp_solver = HeuristicBacktrackingSolver(
            self.problem,
            use_mrv=True,
            use_degree=True,
            use_forward_checking=True,
            timeout_seconds=self.csp_timeout_seconds,
            fixed_assignments=self.fixed_assignments
        )
        csp_res = csp_solver.solve()

        if not csp_res.success or csp_res.hard_violations > 0:
            # If pure CSP timed out or failed, fallback to standard SA
            sa_fallback = SimulatedAnnealingSolver(
                self.problem,
                initial_temperature=self.sa_initial_temp,
                cooling_rate=self.sa_cooling_rate,
                max_total_steps=self.sa_max_steps,
                random_seed=self.random_seed,
                fixed_assignments=self.fixed_assignments
            )
            fallback_result = sa_fallback.solve()
            fallback_result.algorithm_name = "Hybrid CSP + SA (feasible-start fallback)"
            fallback_result.metadata["csp_fallback"] = True
            return fallback_result

        phase1_assignment = csp_res.assignment
        phase1_time = csp_res.time_taken
        phase1_cost, _, phase1_soft = self.checker.calculate_total_cost(phase1_assignment)

        # --- Stage 2: Feasible-Manifold Simulated Annealing ---
        current_state = dict(phase1_assignment)
        current_cost = phase1_cost
        best_state = dict(phase1_assignment)
        best_cost = phase1_cost
        best_soft = phase1_soft

        domains = self.get_domains()
        variables = [v for v in self.problem.variables if v.var_id not in self.fixed_assignments]

        temperature = self.sa_initial_temp
        cost_history: List[float] = [phase1_cost]
        steps = 0

        while variables and temperature > 0.05 and steps < self.sa_max_steps:
            steps += 1

            # Candidate move: swap or slot move
            var = random.choice(variables)
            candidate_slots = domains[var.var_id]
            new_slot = random.choice(candidate_slots)

            neighbor_state = dict(current_state)
            neighbor_state[var.var_id] = new_slot

            # Calculate cost with severe penalty on any hard violation
            hard_viol, _ = self.checker.count_hard_violations(neighbor_state)
            soft_pen, _, _ = self.checker.count_soft_violations(neighbor_state)

            if hard_viol > 0:
                # Disallow moves that break feasibility
                neighbor_cost = 100000.0 * hard_viol + soft_pen
            else:
                neighbor_cost = soft_pen  # Zero hard violations!

            delta = neighbor_cost - current_cost

            accept = False
            if delta < 0:
                accept = True
            elif hard_viol == 0:  # Only allow uphill moves if hard constraints remain 0
                prob = math.exp(-delta / max(temperature, 1e-5))
                if random.random() < prob:
                    accept = True

            if accept:
                current_state = neighbor_state
                current_cost = neighbor_cost
                if hard_viol == 0 and soft_pen < best_soft:
                    best_soft = soft_pen
                    best_cost = soft_pen
                    best_state = dict(current_state)

            cost_history.append(best_cost)
            temperature *= self.sa_cooling_rate

        total_time = time.perf_counter() - start_time
        final_hard, conflicts = self.checker.count_hard_violations(best_state)
        final_soft, _, _ = self.checker.count_soft_violations(best_state)

        return SolverResult(
            algorithm_name="Hybrid CSP + Simulated Annealing (+6 Bonus)",
            assignment=best_state,
            time_taken=total_time,
            nodes_expanded=csp_res.nodes_expanded + steps,
            iterations=steps,
            hard_violations=final_hard,
            soft_penalty=final_soft,
            total_cost=float(final_soft),
            success=final_hard == 0,
            cost_history=cost_history,
            conflict_messages=conflicts,
            metadata={
                "csp_nodes": csp_res.nodes_expanded,
                "csp_time": phase1_time,
                "sa_steps": steps,
                "initial_soft_penalty": phase1_soft,
                "optimized_soft_penalty": final_soft,
                "soft_improvement_pct": round(
                    ((phase1_soft - final_soft) / max(phase1_soft, 1)) * 100, 2
                )
            }
        )
