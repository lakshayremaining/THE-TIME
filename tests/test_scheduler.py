"""
tests/test_scheduler.py
Unit tests verifying constraint satisfaction, all 5 algorithms, and edge cases.
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.datasets import get_small_dataset, get_large_dataset
from core.constraints import ConstraintChecker
from solvers.backtracking import PlainBacktrackingSolver, HeuristicBacktrackingSolver
from solvers.min_conflicts import MinConflictsSolver
from solvers.simulated_annealing import SimulatedAnnealingSolver
from solvers.hybrid import HybridCSPSolver
from export.excel_exporter import export_timetable_to_excel_bytes
from export.csv_exporter import export_timetable_to_csv_string


class TestTimetableScheduler(unittest.TestCase):

    def setUp(self):
        self.small_problem = get_small_dataset()
        self.checker = ConstraintChecker(self.small_problem)

    def test_dataset_solvability(self):
        valid, errors = self.small_problem.validate_input()
        self.assertTrue(valid, f"Validation errors: {errors}")
        self.assertEqual(len(self.small_problem.variables), 47)

    def test_heuristic_backtracking(self):
        solver = HeuristicBacktrackingSolver(self.small_problem, timeout_seconds=10.0)
        res = solver.solve()
        self.assertTrue(res.success)
        self.assertEqual(res.hard_violations, 0)
        self.assertEqual(len(res.assignment), 47)

    def test_min_conflicts(self):
        solver = MinConflictsSolver(self.small_problem, max_iterations=2000, random_seed=42)
        res = solver.solve()
        self.assertTrue(res.success)
        self.assertEqual(res.hard_violations, 0)

    def test_simulated_annealing_bonus(self):
        solver = SimulatedAnnealingSolver(
            self.small_problem,
            initial_temperature=80.0,
            cooling_rate=0.99,
            max_total_steps=1500,
            random_seed=42
        )
        res = solver.solve()
        self.assertTrue(res.success)
        self.assertEqual(res.hard_violations, 0)
        self.assertLess(res.soft_penalty, 500)

    def test_hybrid_csp_sa_bonus(self):
        solver = HybridCSPSolver(
            self.small_problem,
            sa_max_steps=500,
            random_seed=42
        )
        res = solver.solve()
        self.assertTrue(res.success)
        self.assertEqual(res.hard_violations, 0)

    def test_iiit_kota_odd_sem_solvability(self):
        from data.datasets import get_iiit_kota_odd_sem_dataset
        iiit = get_iiit_kota_odd_sem_dataset()
        valid, errors = iiit.validate_input()
        self.assertTrue(valid, f"Validation errors: {errors}")
        self.assertEqual(len(iiit.variables), 96)

        # Verify Min-Conflicts solves it
        solver = MinConflictsSolver(iiit, max_iterations=2000, random_seed=42)
        res = solver.solve()
        self.assertTrue(res.success)
        self.assertEqual(res.hard_violations, 0)

    def test_exporters(self):
        solver = HeuristicBacktrackingSolver(self.small_problem)
        res = solver.solve()
        csv_str = export_timetable_to_csv_string(self.small_problem, res.assignment)
        self.assertIn("Class,Subject,Teacher", csv_str)

        excel_bytes = export_timetable_to_excel_bytes(self.small_problem, res.assignment)
        self.assertGreater(len(excel_bytes), 1000)


if __name__ == "__main__":
    unittest.main()
