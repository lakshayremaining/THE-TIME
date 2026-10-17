"""
solvers/hill_climbing.py
Hill Climbing Local Search Solver (Extra comparison baseline).
Iteratively moves to the neighbor that provides the steepest cost reduction until reaching a local minimum or plateau.
"""

import time
import random
from typing import Dict, List, Optional
from core.models import TimetableProblem, SlotAssignment
from core.constraints import ConstraintChecker
from solvers.base import BaseSolver, SolverResult


class HillClimbingSolver(BaseSolver):
    """
    Steepest-Descent Hill Climbing:
    Evaluates neighborhood candidates and greedily picks the best improving move.
    Terminates when no neighbor improves the cost (local optimum or plateau reached).
    """

    def __init__(
        self,
        problem: TimetableProblem,
        max_iterations: int = 1500,
        sample_neighborhood_size: int = 40,
        random_seed: Optional[int] = 42,
        **kwargs
    ):
        super().__init__(problem, **kwargs)
        self.checker = ConstraintChecker(problem)
        self.max_iterations = max_iterations
        self.sample_neighborhood_size = sample_neighborhood_size
        self.random_seed = random_seed
        self.domains = {v.var_id: self.problem.get_domain_for_variable(v) for v in self.problem.variables}
        self.variables = list(self.problem.variables)

    def solve(self) -> SolverResult:
        if self.random_seed is not None:
            random.seed(self.random_seed)

        start_time = time.perf_counter()

        # Random complete initial assignment
        current_state: Dict[str, SlotAssignment] = {}
        for var in self.variables:
            current_state[var.var_id] = random.choice(self.domains[var.var_id])

        current_cost, current_hard, current_soft = self.checker.calculate_total_cost(current_state)
        cost_history: List[float] = [current_cost]

        step = 0
        for step in range(1, self.max_iterations + 1):
            if current_hard == 0 and current_soft == 0:
                break

            best_neighbor = None
            best_neighbor_cost = current_cost
            best_n_hard = current_hard
            best_n_soft = current_soft

            # Sample a subset of neighborhood moves
            for _ in range(self.sample_neighborhood_size):
                var = random.choice(self.variables)
                new_slot = random.choice(self.domains[var.var_id])

                neighbor = dict(current_state)
                neighbor[var.var_id] = new_slot

                n_cost, n_hard, n_soft = self.checker.calculate_total_cost(neighbor)
                if n_cost < best_neighbor_cost:
                    best_neighbor = neighbor
                    best_neighbor_cost = n_cost
                    best_n_hard = n_hard
                    best_n_soft = n_soft

            if best_neighbor is None or best_neighbor_cost >= current_cost:
                # Reached local optimum / stuck on plateau!
                break

            current_state = best_neighbor
            current_cost = best_neighbor_cost
            current_hard = best_n_hard
            current_soft = best_n_soft
            cost_history.append(current_cost)

        elapsed = time.perf_counter() - start_time
        _, conflicts = self.checker.count_hard_violations(current_state)

        return SolverResult(
            algorithm_name="Hill Climbing (Local Search Baseline)",
            assignment=current_state,
            time_taken=elapsed,
            nodes_expanded=step,
            iterations=step,
            hard_violations=current_hard,
            soft_penalty=current_soft,
            total_cost=current_cost,
            success=current_hard == 0,
            cost_history=cost_history,
            conflict_messages=conflicts,
            metadata={"stuck_at_local_optimum": current_hard > 0}
        )
