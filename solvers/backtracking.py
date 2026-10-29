"""
solvers/backtracking.py
Systematic Backtracking CSP Solvers:
1. Plain Backtracking (Baseline)
2. Backtracking with Heuristics (MRV, Degree Heuristic, Forward Checking, LCV)
"""

import time
from typing import Dict, List, Optional, Set, Tuple
from core.models import TimetableProblem, SessionVariable, SlotAssignment
from core.constraints import ConstraintChecker
from solvers.base import BaseSolver, SolverResult


class PlainBacktrackingSolver(BaseSolver):
    """
    Baseline CSP Backtracking:
    - Static sequential variable ordering.
    - Arbitrary static domain ordering.
    - Consistency check against already assigned variables.
    - No forward checking or heuristics.
    """

    def __init__(self, problem: TimetableProblem, timeout_seconds: float = 20.0, **kwargs):
        super().__init__(problem, **kwargs)
        self.checker = ConstraintChecker(problem)
        self.timeout_seconds = timeout_seconds
        self.nodes_expanded = 0
        self.start_time = 0.0

    def solve(self) -> SolverResult:
        self.nodes_expanded = 0
        self.start_time = time.perf_counter()

        variables = [v for v in self.problem.variables if v.var_id not in self.fixed_assignments]
        initial_domains = self.get_domains()

        assignment: Dict[str, SlotAssignment] = dict(self.fixed_assignments)
        if any(not initial_domains.get(var_id) for var_id in self.fixed_assignments):
            success = False
        else:
            success = True
        if success:
            success = self._backtrack(0, variables, initial_domains, assignment)
        elapsed = time.perf_counter() - self.start_time

        total_cost, hard_viol, soft_pen = self.checker.calculate_total_cost(assignment)
        _, conflicts = self.checker.count_hard_violations(assignment)

        return SolverResult(
            algorithm_name="Backtracking (Baseline)",
            assignment=assignment,
            time_taken=elapsed,
            nodes_expanded=self.nodes_expanded,
            iterations=self.nodes_expanded,
            hard_violations=hard_viol,
            soft_penalty=soft_pen,
            total_cost=total_cost,
            success=success and hard_viol == 0 and len(assignment) == len(self.problem.variables),
            conflict_messages=conflicts,
            metadata={"timed_out": elapsed >= self.timeout_seconds}
        )

    def _backtrack(
        self,
        index: int,
        variables: List[SessionVariable],
        domains: Dict[str, List[SlotAssignment]],
        assignment: Dict[str, SlotAssignment]
    ) -> bool:
        if time.perf_counter() - self.start_time > self.timeout_seconds:
            return False

        if index == len(variables):
            return True

        var = variables[index]
        self.nodes_expanded += 1

        for slot in domains[var.var_id]:
            if self.checker.is_consistent_assignment(var.var_id, slot, assignment):
                assignment[var.var_id] = slot
                if self._backtrack(index + 1, variables, domains, assignment):
                    return True
                del assignment[var.var_id]

        return False


class HeuristicBacktrackingSolver(BaseSolver):
    """
    Advanced CSP Backtracking incorporating:
    1. MRV (Minimum Remaining Values) variable ordering.
    2. Degree Heuristic as tie-breaker.
    3. Forward Checking (FC) for early domain pruning and dead-end detection.
    4. LCV (Least Constraining Value) ordering.
    """

    def __init__(
        self,
        problem: TimetableProblem,
        use_mrv: bool = True,
        use_degree: bool = True,
        use_forward_checking: bool = True,
        use_lcv: bool = True,
        timeout_seconds: float = 30.0,
        **kwargs
    ):
        super().__init__(problem, **kwargs)
        self.checker = ConstraintChecker(problem)
        self.use_mrv = use_mrv
        self.use_degree = use_degree
        self.use_forward_checking = use_forward_checking
        self.use_lcv = use_lcv
        self.timeout_seconds = timeout_seconds
        self.nodes_expanded = 0
        self.start_time = 0.0

        # Precompute static degree (count of other variables sharing teacher, class, or room)
        self.degree_map: Dict[str, int] = {}
        self._compute_degree_heuristic()

    def _compute_degree_heuristic(self):
        neighbors = {v.var_id: set() for v in self.problem.variables}
        occupancy = {}
        for var in self.problem.variables:
            for slot in self.problem.get_domain_for_variable(var):
                occupancy.setdefault((slot.day, slot.period, slot.room_name), []).append(var.var_id)

        for var_ids in occupancy.values():
            unique_ids = set(var_ids)
            for var_id in unique_ids:
                neighbors[var_id].update(unique_ids - {var_id})

        for index, first in enumerate(self.problem.variables):
            for second in self.problem.variables[index + 1:]:
                if first.class_name == second.class_name or first.teacher_name == second.teacher_name:
                    neighbors[first.var_id].add(second.var_id)
                    neighbors[second.var_id].add(first.var_id)

        self.degree_map = {var_id: len(adjacent) for var_id, adjacent in neighbors.items()}

    def solve(self) -> SolverResult:
        self.nodes_expanded = 0
        self.start_time = time.perf_counter()

        # Initialize domains with unary filtering
        domains = self.get_domains()
        assignment: Dict[str, SlotAssignment] = dict(self.fixed_assignments)
        success = not any(not domains.get(var_id) for var_id in self.fixed_assignments)
        if success:
            success = self._backtrack(domains, assignment)
        elapsed = time.perf_counter() - self.start_time

        total_cost, hard_viol, soft_pen = self.checker.calculate_total_cost(assignment)
        _, conflicts = self.checker.count_hard_violations(assignment)

        return SolverResult(
            algorithm_name="Backtracking (+ Heuristics: MRV, Degree, FC, LCV)",
            assignment=assignment,
            time_taken=elapsed,
            nodes_expanded=self.nodes_expanded,
            iterations=self.nodes_expanded,
            hard_violations=hard_viol,
            soft_penalty=soft_pen,
            total_cost=total_cost,
            success=success and hard_viol == 0 and len(assignment) == len(self.problem.variables),
            conflict_messages=conflicts,
            metadata={"timed_out": elapsed >= self.timeout_seconds}
        )

    def _select_unassigned_variable(
        self, domains: Dict[str, List[SlotAssignment]], assignment: Dict[str, SlotAssignment]
    ) -> Optional[SessionVariable]:
        """
        Selects next variable using MRV with Degree Heuristic tie-breaker.
        """
        unassigned = [v for v in self.problem.variables if v.var_id not in assignment]
        if not unassigned:
            return None

        if not self.use_mrv:
            return unassigned[0]

        # MRV: minimum remaining domain size
        min_domain_len = min(len(domains[v.var_id]) for v in unassigned)
        candidates = [v for v in unassigned if len(domains[v.var_id]) == min_domain_len]

        if len(candidates) == 1 or not self.use_degree:
            return candidates[0]

        # Degree Heuristic tie-breaker: maximum degree
        candidates.sort(key=lambda v: self.degree_map.get(v.var_id, 0), reverse=True)
        return candidates[0]

    def _order_domain_values(
        self,
        var: SessionVariable,
        domains: Dict[str, List[SlotAssignment]],
        assignment: Dict[str, SlotAssignment]
    ) -> List[SlotAssignment]:
        """
        Orders domain values using LCV (Least Constraining Value) or domain order.
        """
        val_list = domains[var.var_id]
        if not self.use_lcv or len(val_list) <= 1:
            return val_list

        # Count eliminated choices in neighbors
        unassigned = [v for v in self.problem.variables if v.var_id not in assignment and v.var_id != var.var_id]

        def count_conflicts(slot: SlotAssignment) -> int:
            eliminated = 0
            for u in unassigned:
                shares_teacher = u.teacher_name == var.teacher_name
                shares_class = u.class_name == var.class_name
                for u_slot in domains[u.var_id]:
                    if u_slot.day == slot.day and u_slot.period == slot.period:
                        if shares_teacher or shares_class or u_slot.room_name == slot.room_name:
                            eliminated += 1
            return eliminated

        return sorted(val_list, key=count_conflicts)

    def _forward_check(
        self,
        assigned_var: SessionVariable,
        slot: SlotAssignment,
        domains: Dict[str, List[SlotAssignment]],
        assignment: Dict[str, SlotAssignment]
    ) -> Tuple[bool, Dict[str, List[SlotAssignment]]]:
        """
        Prunes incompatible domain values for unassigned variables.
        Returns: (is_valid, pruned_domain_map)
        If any unassigned variable's domain is reduced to empty, returns False.
        """
        pruned_domains: Dict[str, List[SlotAssignment]] = {}

        for u in self.problem.variables:
            if u.var_id in assignment:
                continue

            # Check if u shares teacher, class, or could share room
            shares_teacher = (u.teacher_name == assigned_var.teacher_name)
            shares_class = (u.class_name == assigned_var.class_name)

            new_domain = []
            for u_slot in domains[u.var_id]:
                # Conflict if same day, same period, and (same teacher, same class, or same room)
                if u_slot.day == slot.day and u_slot.period == slot.period:
                    if shares_teacher or shares_class or (u_slot.room_name == slot.room_name):
                        continue  # Pruned!
                new_domain.append(u_slot)

            if len(new_domain) == 0:
                # Dead-end detected!
                return False, {}

            pruned_domains[u.var_id] = new_domain

        return True, pruned_domains

    def _backtrack(
        self,
        domains: Dict[str, List[SlotAssignment]],
        assignment: Dict[str, SlotAssignment]
    ) -> bool:
        if time.perf_counter() - self.start_time > self.timeout_seconds:
            return False

        if len(assignment) == len(self.problem.variables):
            return True

        var = self._select_unassigned_variable(domains, assignment)
        if not var:
            return True

        self.nodes_expanded += 1
        ordered_values = self._order_domain_values(var, domains, assignment)

        for slot in ordered_values:
            if self.checker.is_consistent_assignment(var.var_id, slot, assignment):
                assignment[var.var_id] = slot

                if self.use_forward_checking:
                    valid, new_domains = self._forward_check(var, slot, domains, assignment)
                    if valid:
                        saved_domains = domains
                        # Update with pruned domains
                        merged_domains = dict(domains)
                        merged_domains.update(new_domains)
                        if self._backtrack(merged_domains, assignment):
                            return True
                else:
                    if self._backtrack(domains, assignment):
                        return True

                del assignment[var.var_id]

        return False
