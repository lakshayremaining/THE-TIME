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
from solvers.initialization import find_feasible_initial_assignment, failed_initialization_result


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
        initialization_timeout: float = 15.0,
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
        self.initialization_timeout = initialization_timeout
        self.domains: Dict[str, List[SlotAssignment]] = self.get_domains()
        self.variables = [v for v in self.problem.variables if v.var_id not in self.fixed_assignments]
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
            # Operator 3: Move a whole lab block while preserving its period offsets.
            var_map = self.var_dict
            seen_blocks = set()
            blocks = []
            for var in self.problem.variables:
                block_key = tuple(var.block_vars)
                if var.is_lab and len(block_key) > 1 and block_key not in seen_blocks:
                    seen_blocks.add(block_key)
                    block = [var_map[member_id] for member_id in block_key]
                    if all(member.var_id not in self.fixed_assignments for member in block):
                        blocks.append(sorted(block, key=lambda member: member.block_offset))
            if blocks:
                block = random.choice(blocks)
                max_start = self.problem.time_structure.periods_per_day - len(block) + 1
                candidates = []
                for day in self.problem.time_structure.days:
                    for start_period in range(1, max_start + 1):
                        for room in self.problem.rooms.values():
                            proposed = {
                                member.var_id: SlotAssignment(
                                    day, start_period + member.block_offset, room.name
                                )
                                for member in block
                            }
                            if all(proposed[member.var_id] in self.domains[member.var_id] for member in block):
                                candidates.append(proposed)
                if candidates:
                    new_state.update(random.choice(candidates))
                    desc = f"Move lab block {', '.join(v.var_id for v in block)}"
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

        current_state = None
        initializer = "provided initial assignment"
        if self.provided_initial is not None:
            candidate = dict(self.provided_initial)
            candidate.update(self.fixed_assignments)
            _, candidate_hard, _ = self.checker.calculate_total_cost(candidate)
            if (
                candidate_hard == 0
                and len(candidate) == len(self.problem.variables)
                and all(candidate.get(var_id) == slot for var_id, slot in self.fixed_assignments.items())
            ):
                current_state = candidate

        if current_state is None:
            current_state, initializer, init_messages = find_feasible_initial_assignment(
                self.problem,
                fixed_assignments=self.fixed_assignments,
                timeout_seconds=self.initialization_timeout,
                random_seed=self.random_seed,
            )
            if current_state is None:
                return failed_initialization_result(
                    "Simulated Annealing (feasible initialization failed)",
                    init_messages,
                    time.perf_counter() - start_time,
                )

        current_cost, current_hard, current_soft = self.checker.calculate_total_cost(current_state)
        best_state = dict(current_state)
        best_cost = current_cost
        best_hard = current_hard
        best_soft = current_soft

        temperature = self.initial_temperature
        cost_history: List[float] = [current_cost]
        total_steps = 0

        while self.variables and temperature > self.min_temperature and total_steps < self.max_total_steps:
            for _ in range(self.max_steps_per_temp):
                total_steps += 1
                neighbor_state, _ = self._generate_neighbor(current_state)
                n_hard, _ = self.checker.count_hard_violations(neighbor_state)

                # Start from a feasible schedule and keep the annealing walk on
                # the feasible portion of the search space.
                if n_hard > 0:
                    cost_history.append(current_cost)
                    continue

                n_soft, _, _ = self.checker.count_soft_violations(neighbor_state)
                neighbor_cost = float(n_soft)

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
            metadata={
                "final_temp": temperature,
                "cooling_rate": self.cooling_rate,
                "feasible_initializer": initializer,
                "feasible_start": True,
            }
        )
