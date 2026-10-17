"""
solvers/min_conflicts.py
Min-Conflicts Local Search Solver with Random Walk & Restarts for Plateau Escape.
"""

import time
import random
from typing import Dict, List, Optional, Set, Tuple
from core.models import TimetableProblem, SessionVariable, SlotAssignment
from core.constraints import ConstraintChecker
from solvers.base import BaseSolver, SolverResult


class MinConflictsSolver(BaseSolver):
    """
    Min-Conflicts Local Search:
    - Starts with a complete (unary-feasible) random assignment.
    - Iteratively selects a conflicted variable and moves it to the slot minimizing conflicts.
    - Plateau escaping via Random Walk (probability p) and Random Restarts.
    - Captures iteration-by-iteration cost trajectory for plotting.
    """

    def __init__(
        self,
        problem: TimetableProblem,
        max_iterations: int = 3000,
        random_walk_prob: float = 0.10,
        max_restarts: int = 5,
        restart_patience: int = 300,
        random_seed: Optional[int] = 42,
        **kwargs
    ):
        super().__init__(problem, **kwargs)
        self.checker = ConstraintChecker(problem)
        self.max_iterations = max_iterations
        self.random_walk_prob = random_walk_prob
        self.max_restarts = max_restarts
        self.restart_patience = restart_patience
        self.random_seed = random_seed
        self.domains: Dict[str, List[SlotAssignment]] = {
            v.var_id: self.problem.get_domain_for_variable(v) for v in self.problem.variables
        }

    def _generate_initial_assignment(self) -> Dict[str, SlotAssignment]:
        """
        Creates a complete assignment by choosing a random valid slot (unary-filtered)
        for every variable.
        """
        assignment = {}
        for var in self.problem.variables:
            valid_slots = self.domains[var.var_id]
            assignment[var.var_id] = random.choice(valid_slots)
        return assignment

    def _get_conflicted_variables(
        self, assignment: Dict[str, SlotAssignment]
    ) -> List[str]:
        """
        Returns the list of var_ids currently involved in at least one hard clash.
        """
        # (day, period, teacher) -> list of var_ids
        teacher_map = {}
        class_map = {}
        room_map = {}
        conflicted_set: Set[str] = set()

        for var_id, slot in assignment.items():
            var = self.problem.variables_dict[var_id]
            t_key = (slot.day, slot.period, var.teacher_name)
            c_key = (slot.day, slot.period, var.class_name)
            r_key = (slot.day, slot.period, slot.room_name)

            if t_key in teacher_map:
                conflicted_set.add(var_id)
                conflicted_set.add(teacher_map[t_key])
            else:
                teacher_map[t_key] = var_id

            if c_key in class_map:
                conflicted_set.add(var_id)
                conflicted_set.add(class_map[c_key])
            else:
                class_map[c_key] = var_id

            if r_key in room_map:
                conflicted_set.add(var_id)
                conflicted_set.add(room_map[r_key])
            else:
                room_map[r_key] = var_id

        return list(conflicted_set)

    def _count_var_conflicts(
        self, var_id: str, slot: SlotAssignment, assignment: Dict[str, SlotAssignment]
    ) -> int:
        """
        Calculates how many conflicts variable `var_id` would have if assigned to `slot`.
        """
        var = self.problem.variables_dict[var_id]
        conflicts = 0

        for other_id, other_slot in assignment.items():
            if other_id == var_id:
                continue
            if other_slot.day == slot.day and other_slot.period == slot.period:
                other_var = self.problem.variables_dict[other_id]
                if other_var.teacher_name == var.teacher_name:
                    conflicts += 1
                if other_var.class_name == var.class_name:
                    conflicts += 1
                if other_slot.room_name == slot.room_name:
                    conflicts += 1

        return conflicts

    def solve(self) -> SolverResult:
        if self.random_seed is not None:
            random.seed(self.random_seed)

        start_time = time.perf_counter()
        self.problem.variables_dict = {v.var_id: v for v in self.problem.variables}

        best_assignment: Optional[Dict[str, SlotAssignment]] = None
        best_cost = float("inf")
        best_hard_viol = 999999
        cost_history: List[float] = []

        total_iterations = 0

        for restart_idx in range(self.max_restarts):
            assignment = self._generate_initial_assignment()
            stagnation_counter = 0

            for it in range(self.max_iterations):
                total_iterations += 1
                conflicted_vars = self._get_conflicted_variables(assignment)

                hard_count = len(conflicted_vars)
                # Compute cost periodically or every step
                cost, h_viol, s_pen = self.checker.calculate_total_cost(assignment)
                cost_history.append(cost)

                if cost < best_cost:
                    best_cost = cost
                    best_hard_viol = h_viol
                    best_assignment = dict(assignment)
                    stagnation_counter = 0

                if h_viol == 0:
                    # Solved perfectly!
                    elapsed = time.perf_counter() - start_time
                    _, conflicts = self.checker.count_hard_violations(assignment)
                    return SolverResult(
                        algorithm_name="Min-Conflicts Local Search",
                        assignment=assignment,
                        time_taken=elapsed,
                        nodes_expanded=total_iterations,
                        iterations=total_iterations,
                        hard_violations=0,
                        soft_penalty=s_pen,
                        total_cost=cost,
                        success=True,
                        cost_history=cost_history,
                        conflict_messages=conflicts,
                        metadata={"restarts": restart_idx}
                    )

                stagnation_counter += 1
                if stagnation_counter >= self.restart_patience:
                    # Escape deep plateau with random restart
                    break

                # Pick a random conflicted variable
                chosen_var_id = random.choice(conflicted_vars)
                candidate_slots = self.domains[chosen_var_id]

                # Random walk with probability p to escape local optima
                if random.random() < self.random_walk_prob:
                    assignment[chosen_var_id] = random.choice(candidate_slots)
                    continue

                # Otherwise, find the slot minimizing conflicts
                min_conf = float("inf")
                best_candidates = []

                for slot in candidate_slots:
                    c = self._count_var_conflicts(chosen_var_id, slot, assignment)
                    if c < min_conf:
                        min_conf = c
                        best_candidates = [slot]
                    elif c == min_conf:
                        best_candidates.append(slot)

                # Tie-breaking: choose uniformly among best
                assignment[chosen_var_id] = random.choice(best_candidates)

        elapsed = time.perf_counter() - start_time
        final_assignment = best_assignment if best_assignment is not None else assignment
        total_cost, final_hard, final_soft = self.checker.calculate_total_cost(final_assignment)
        _, conflicts = self.checker.count_hard_violations(final_assignment)

        return SolverResult(
            algorithm_name="Min-Conflicts Local Search",
            assignment=final_assignment,
            time_taken=elapsed,
            nodes_expanded=total_iterations,
            iterations=total_iterations,
            hard_violations=final_hard,
            soft_penalty=final_soft,
            total_cost=total_cost,
            success=final_hard == 0,
            cost_history=cost_history,
            conflict_messages=conflicts,
            metadata={"restarts": self.max_restarts}
        )
