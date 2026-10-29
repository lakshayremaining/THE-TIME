"""Helpers for constructing a complete, hard-constraint-feasible starting state."""

from typing import Dict, Optional, Tuple

from core.models import SlotAssignment, TimetableProblem
from solvers.base import SolverResult


def find_feasible_initial_assignment(
    problem: TimetableProblem,
    fixed_assignments: Optional[Dict[str, SlotAssignment]] = None,
    timeout_seconds: float = 15.0,
    random_seed: Optional[int] = 42,
) -> Tuple[Optional[Dict[str, SlotAssignment]], str, list[str]]:
    """Try Min-Conflicts first, then heuristic CSP, returning only complete valid states."""
    from core.constraints import ConstraintChecker
    from solvers.backtracking import HeuristicBacktrackingSolver
    from solvers.min_conflicts import MinConflictsSolver

    fixed = fixed_assignments or {}
    variable_ids = {v.var_id for v in problem.variables}
    unknown_ids = sorted(set(fixed) - variable_ids)
    if unknown_ids:
        return None, "input validation", [f"Unknown fixed session ID(s): {', '.join(unknown_ids)}"]

    domains = {v.var_id: problem.get_domain_for_variable(v) for v in problem.variables}
    invalid_fixed = [
        var_id for var_id, slot in fixed.items()
        if slot not in domains.get(var_id, [])
    ]
    if invalid_fixed:
        return None, "input validation", [
            f"The fixed slot for '{var_id}' violates room, capacity, availability, lunch, or lab-block domain rules."
            for var_id in invalid_fixed
        ]

    empty_domains = [var_id for var_id, domain in domains.items() if not domain]
    if empty_domains:
        return None, "input validation", [
            f"No valid day, period, and room are available for: {', '.join(empty_domains[:8])}"
        ]

    checker = ConstraintChecker(problem)
    mc_result = MinConflictsSolver(
        problem,
        max_iterations=1000,
        random_walk_prob=0.10,
        max_restarts=2,
        restart_patience=250,
        random_seed=random_seed,
        fixed_assignments=fixed,
    ).solve()
    if (
        mc_result.success
        and len(mc_result.assignment) == len(problem.variables)
        and checker.count_hard_violations(mc_result.assignment)[0] == 0
        and all(mc_result.assignment.get(var_id) == slot for var_id, slot in fixed.items())
    ):
        return mc_result.assignment, "Min-Conflicts", []

    csp_result = HeuristicBacktrackingSolver(
        problem,
        use_mrv=True,
        use_degree=True,
        use_forward_checking=True,
        use_lcv=True,
        timeout_seconds=timeout_seconds,
        fixed_assignments=fixed,
    ).solve()
    if (
        csp_result.success
        and len(csp_result.assignment) == len(problem.variables)
        and checker.count_hard_violations(csp_result.assignment)[0] == 0
        and all(csp_result.assignment.get(var_id) == slot for var_id, slot in fixed.items())
    ):
        return csp_result.assignment, "Heuristic Backtracking", []

    messages = list(csp_result.conflict_messages)
    if csp_result.metadata.get("timed_out"):
        messages.insert(0, f"Feasible timetable search exceeded the {timeout_seconds:g}-second limit.")
    if not messages:
        messages.append("Could not construct a complete timetable that satisfies all hard constraints.")
    return None, "feasibility search", messages


def failed_initialization_result(
    algorithm_name: str,
    messages: list[str],
    elapsed_seconds: float = 0.0,
) -> SolverResult:
    return SolverResult(
        algorithm_name=algorithm_name,
        assignment={},
        time_taken=elapsed_seconds,
        hard_violations=0,
        success=False,
        conflict_messages=messages,
        metadata={"initialization_failed": True},
    )
