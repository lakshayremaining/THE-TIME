"""
solvers/hill_climbing.py
Hill Climbing Local Search Solver (Extra comparison baseline).
Iteratively moves to the neighbor that provides the steepest cost reduction until reaching a local minimum or plateau.
"""

import time
import random
from typing import Dict, List, Optional, Tuple
from core.models import TimetableProblem, SessionVariable, SlotAssignment
from core.constraints import ConstraintChecker
from solvers.base import BaseSolver, SolverResult
from solvers.initialization import find_feasible_initial_assignment, failed_initialization_result


class HillClimbingSolver(BaseSolver):
    """
    Feasible-seeded steepest-descent Hill Climbing.
    Candidate moves include single-session moves, compatible swaps, and whole lab-block moves.
    Only complete zero-hard-conflict neighbors are eligible for acceptance.
    """

    def __init__(
        self,
        problem: TimetableProblem,
        max_iterations: int = 1500,
        sample_neighborhood_size: int = 40,
        random_seed: Optional[int] = 42,
        initialization_timeout: float = 15.0,
        **kwargs
    ):
        super().__init__(problem, **kwargs)
        self.checker = ConstraintChecker(problem)
        self.max_iterations = max_iterations
        self.sample_neighborhood_size = sample_neighborhood_size
        self.random_seed = random_seed
        self.initialization_timeout = initialization_timeout
        self.domains = self.get_domains()
        self.variables = [v for v in self.problem.variables if v.var_id not in self.fixed_assignments]
        var_map = {v.var_id: v for v in self.problem.variables}
        self.lab_blocks = []
        seen_blocks = set()
        for var in self.problem.variables:
            block_key = tuple(var.block_vars)
            if var.is_lab and len(block_key) > 1 and block_key not in seen_blocks:
                seen_blocks.add(block_key)
                self.lab_blocks.append([var_map[member_id] for member_id in block_key])

    def _sample_neighbor(self, state: Dict[str, SlotAssignment]) -> Dict[str, SlotAssignment]:
        """Propose one legal-domain move, a compatible swap, or a whole lab-block move."""
        neighbor = dict(state)
        if not self.variables:
            return neighbor

        move_kind = random.random()
        if move_kind < 0.55 or len(self.variables) < 2:
            var = random.choice(self.variables)
            choices = [slot for slot in self.domains[var.var_id] if slot != state[var.var_id]]
            if choices:
                neighbor[var.var_id] = random.choice(choices)
            return neighbor

        if move_kind < 0.82:
            first, second = random.sample(self.variables, 2)
            first_slot = state[first.var_id]
            second_slot = state[second.var_id]
            if second_slot in self.domains[first.var_id] and first_slot in self.domains[second.var_id]:
                neighbor[first.var_id] = second_slot
                neighbor[second.var_id] = first_slot
            return neighbor

        movable_blocks = [
            block for block in self.lab_blocks
            if all(var.var_id not in self.fixed_assignments for var in block)
        ]
        if not movable_blocks:
            return neighbor

        block = random.choice(movable_blocks)
        block.sort(key=lambda var: var.block_offset)
        block_len = len(block)
        max_start = self.problem.time_structure.periods_per_day - block_len + 1
        if max_start < 1:
            return neighbor

        candidates = []
        for day in self.problem.time_structure.days:
            for start_period in range(1, max_start + 1):
                for room in self.problem.rooms.values():
                    proposed = {
                        var.var_id: SlotAssignment(day, start_period + var.block_offset, room.name)
                        for var in block
                    }
                    if all(proposed[var.var_id] in self.domains[var.var_id] for var in block):
                        if any(state[var.var_id] != proposed[var.var_id] for var in block):
                            candidates.append(proposed)
        if candidates:
            neighbor.update(random.choice(candidates))
        return neighbor

    def solve(self) -> SolverResult:
        if self.random_seed is not None:
            random.seed(self.random_seed)

        start_time = time.perf_counter()

        current_state, initializer, init_messages = find_feasible_initial_assignment(
            self.problem,
            fixed_assignments=self.fixed_assignments,
            timeout_seconds=self.initialization_timeout,
            random_seed=self.random_seed,
        )
        if current_state is None:
            return failed_initialization_result(
                "Hill Climbing (feasible initialization failed)",
                init_messages,
                time.perf_counter() - start_time,
            )

        _, current_hard, current_soft = self.checker.calculate_total_cost(current_state)
        current_cost = current_soft
        cost_history: List[float] = [float(current_soft)]

        step = 0
        for step in range(1, self.max_iterations + 1):
            if not self.variables:
                break
            if current_soft == 0:
                break

            best_neighbor = None
            best_neighbor_cost = current_soft
            best_n_soft = current_soft

            # Sample a subset of neighborhood moves
            for _ in range(self.sample_neighborhood_size):
                neighbor = self._sample_neighbor(current_state)
                if neighbor == current_state:
                    continue
                n_hard, _ = self.checker.count_hard_violations(neighbor)
                if n_hard:
                    continue
                n_soft, _, _ = self.checker.count_soft_violations(neighbor)
                if n_soft < best_neighbor_cost:
                    best_neighbor = neighbor
                    best_neighbor_cost = n_soft
                    best_n_soft = n_soft

            if best_neighbor is None or best_neighbor_cost >= current_soft:
                # Reached local optimum / stuck on plateau!
                break

            current_state = best_neighbor
            current_cost = best_neighbor_cost
            current_hard = 0
            current_soft = best_n_soft
            cost_history.append(current_cost)

        elapsed = time.perf_counter() - start_time
        _, conflicts = self.checker.count_hard_violations(current_state)

        return SolverResult(
            algorithm_name="Hill Climbing (Feasible-Seeded Local Search)",
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
            metadata={
                "stuck_at_local_optimum": current_soft > 0,
                "feasible_initializer": initializer,
                "feasible_start": True,
            }
        )
