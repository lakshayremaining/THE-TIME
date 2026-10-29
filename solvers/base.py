"""
solvers/base.py
Base Solver interface and execution result data structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from core.models import TimetableProblem, SlotAssignment


@dataclass
class SolverResult:
    algorithm_name: str
    assignment: Dict[str, SlotAssignment]
    time_taken: float  # seconds
    nodes_expanded: int = 0
    iterations: int = 0
    hard_violations: int = 0
    soft_penalty: int = 0
    total_cost: float = 0.0
    success: bool = False
    cost_history: List[float] = field(default_factory=list)  # (iteration -> cost) for plotting
    conflict_messages: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseSolver(ABC):
    def __init__(self, problem: TimetableProblem, **kwargs):
        self.problem = problem
        self.kwargs = kwargs
        self.fixed_assignments: Dict[str, SlotAssignment] = kwargs.get("fixed_assignments", {}) or {}

    def get_domains(self) -> Dict[str, List[SlotAssignment]]:
        """Build unary-feasible domains, restricting manually pinned sessions."""
        domains = {
            v.var_id: self.problem.get_domain_for_variable(v)
            for v in self.problem.variables
        }
        for var_id, slot in self.fixed_assignments.items():
            if var_id in domains:
                domains[var_id] = [slot] if slot in domains[var_id] else []
        return domains

    @abstractmethod
    def solve(self) -> SolverResult:
        """Executes the scheduling algorithm and returns a SolverResult."""
        pass
