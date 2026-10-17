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

    @abstractmethod
    def solve(self) -> SolverResult:
        """Executes the scheduling algorithm and returns a SolverResult."""
        pass
