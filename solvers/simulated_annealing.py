"""
solvers/simulated_annealing.py
Simulated Annealing Solver for Timetable Scheduling (+6 Bonus Marks).
Implements configurable neighborhood moves, geometric cooling, and Metropolis acceptance.
"""

import time
import math
import random
from typing import Dict, List, Optional, Tuple
from core.models import TimetableProblem, SessionVariable, SlotAssignment
from core.constraints import ConstraintChecker
from solvers.base import BaseSolver, SolverResult


class SimulatedAnnealingSolver(BaseSolver):
    """
    Simulated Annealing:
    - State: Complete timetable assignment.
    - Cost: 1000 * hard_violations + soft_penalties.
    - Moves:
        1. Single session move to a valid slot.
        2. Pair session swap.
        3. Class-specific slot exchange.
    - Cooling: Geometric schedule T_{k+1} = alpha * T_k.
    - Acceptance: exp(-delta / T) for uphill moves.
    """

    def __init__(
        self,
        problem: TimetableProblem,
        initial_temperature: float = 100.0,
        cooling_rate: float = 0.995,
        min_temperature: float = 0.05,
        max_steps_per_temp: int = 5,
        max_total_steps: int = 4000,
        initial_assignment: Optional[Dict[str, SlotAssignment]] = None,
        random_seed: Optional[int] = 42,
        **kwargs
    ):
        super().__init__(problem, **kwargs)
        self.checker = ConstraintChecker(problem)
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.min_temperature = min_temperature
        self.max_steps_per_temp = max_steps_per_temp
        self.max_total_steps = max_total_steps
        self.provided_initial = initial_assignment
        self.random_seed = random_seed
        self.domains: Dict[str, List[SlotAssignment]] = {
            v.var_id: self.problem.get_domain_for_variable(v) for v in self.problem.variables
        }
        self.variables = list(self.problem.variables)
        self.var_dict = {v.var_id: v for v in self.problem.variables}

    def _random_initial_state(self) -> Dict[str, SlotAssignment]:
        state = {}
        for var in self.variables:
            state[var.var_id] = random.choice(self.domains[var.var_id])
        return state

    def _generate_neighbor(
        self, current_state: Dict[str, SlotAssignment]
    ) -> Tuple[Dict[str, SlotAssignment], str]:
        """
        Generates a neighbor state using one of three neighborhood operators:
        1. Move a session to a new valid slot (70% probability)
        2. Swap two sessions (20% probability)
        3. Move a consecutive lab pair together (10% probability)
        """
        new_state = dict(current_state)
        move_type = random.random()

        if move_type < 0.70 or len(self.variables) < 2:
            # Operator 1: Move single session
            var = random.choice(self.variables)
            candidate_slots = self.domains[var.var_id]
            new_slot = random.choice(candidate_slots)
            new_state[var.var_id] = new_slot
            desc = f"Move {var.var_id} -> {new_slot.day} P{new_slot.period}"

        elif move_type < 0.90:
            # Operator 2: Swap two sessions of the same class or room type
            v1, v2 = random.sample(self.variables, 2)
            # Check if slots are valid for each other's unary constraints
            s1 = current_state[v1.var_id]
            s2 = current_state[v2.var_id]

            v1_valid = s2 in self.domains[v1.var_id]
            v2_valid = s1 in self.domains[v2.var_id]

            if v1_valid and v2_valid:
                new_state[v1.var_id] = s2
                new_state[v2.var_id] = s1
                desc = f"Swap {v1.var_id} <-> {v2.var_id}"
            else:
                # Fallback to single move
                new_slot = random.choice(self.domains[v1.var_id])
                new_state[v1.var_id] = new_slot
                desc = f"Move {v1.var_id}"
        else:
            # Operator 3: Move lab pair consecutively
            lab_vars = [v for v in self.variables if v.is_lab and v.consecutive_with]
            if lab_vars:
                v1 = random.choice(lab_vars)
                v2_id = v1.consecutive_with
                if v2_id in new_state:
                    # Pick random day and period 1 to periods_per_day - 1
                    day = random.choice(self.problem.time_structure.days)
                    max_p = self.problem.time_structure.periods_per_day
                    p = random.randint(1, max_p - 1)
                    # Find a lab room
                    lab_rooms = [r for r in self.problem.rooms.values() if r.is_lab]
                    if lab_rooms:
                        room = random.choice(lab_rooms)
                        slot1 = SlotAssignment(day=day, period=p, room_name=room.name)
                        slot2 = SlotAssignment(day=day, period=p + 1, room_name=room.name)
                        if slot1 in self.domains[v1.var_id] and slot2 in self.domains[v2_id]:
                            new_state[v1.var_id] = slot1
                            new_state[v2_id] = slot2
                            desc = f"Move lab pair {v1.var_id},{v2_id} -> {day} P{p}-{p+1}"
                        else:
                            desc = "No-op"
                    else:
                        desc = "No-op"
                else:
                    desc = "No-op"
            else:
                var = random.choice(self.variables)
                new_state[var.var_id] = random.choice(self.domains[var.var_id])
                desc = f"Move {var.var_id}"

        return new_state, desc

    def solve(self) -> SolverResult:
        if self.random_seed is not None:
            random.seed(self.random_seed)

        start_time = time.perf_counter()

        current_state = (
            dict(self.provided_initial)
            if self.provided_initial is not None
            else self._random_initial_state()
        )

        current_cost, current_hard, current_soft = self.checker.calculate_total_cost(current_state)
        best_state = dict(current_state)
        best_cost = current_cost
        best_hard = current_hard
        best_soft = current_soft

        temperature = self.initial_temperature
        cost_history: List[float] = [current_cost]
        total_steps = 0

        while temperature > self.min_temperature and total_steps < self.max_total_steps:
            for _ in range(self.max_steps_per_temp):
                total_steps += 1
                neighbor_state, _ = self._generate_neighbor(current_state)
                neighbor_cost, n_hard, n_soft = self.checker.calculate_total_cost(neighbor_state)

                delta = neighbor_cost - current_cost

                # Metropolis acceptance criterion
                accept = False
                if delta < 0:
                    accept = True
                else:
                    # Prevent overflow in exp
                    exponent = -delta / max(temperature, 1e-6)
                    prob = math.exp(min(exponent, 20.0))
                    if random.random() < prob:
                        accept = True

                if accept:
                    current_state = neighbor_state
                    current_cost = neighbor_cost
                    current_hard = n_hard
                    current_soft = n_soft

                    if current_cost < best_cost:
                        best_cost = current_cost
                        best_hard = current_hard
                        best_soft = current_soft
                        best_state = dict(current_state)

                cost_history.append(current_cost)

                # Early stopping if perfect 0 hard violations and very low soft penalty
                if current_hard == 0 and current_soft == 0:
                    break

            # Geometric cooling schedule
            temperature *= self.cooling_rate

            if best_hard == 0 and best_soft == 0:
                break

        elapsed = time.perf_counter() - start_time
        _, conflicts = self.checker.count_hard_violations(best_state)

        return SolverResult(
            algorithm_name="Simulated Annealing (+6 Bonus)",
            assignment=best_state,
            time_taken=elapsed,
            nodes_expanded=total_steps,
            iterations=total_steps,
            hard_violations=best_hard,
            soft_penalty=best_soft,
            total_cost=best_cost,
            success=best_hard == 0,
            cost_history=cost_history,
            conflict_messages=conflicts,
            metadata={"final_temp": temperature, "cooling_rate": self.cooling_rate}
        )
