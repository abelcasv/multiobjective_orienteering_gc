import random
import unittest
import numpy as np

from src.core.problem import OrienteeringProblem, GAConfig, Individual
from src.algorithms.genetic_algorithm import (
    _repair_chromosome,
    mutate,
    NSGA2Orienteering,
)
from src.algorithms.weighted_sum import WeightedSumGA
from src.algorithms.epsilon_constraint import EpsilonConstraintGA


def _build_synthetic_problem(
    mandatory_node=None,
    forbidden_nodes=None,
    t_max: float = 200.0,
) -> OrienteeringProblem:
    n = 10
    rng = np.random.default_rng(42)
    time_matrix = rng.uniform(5.0, 20.0, size=(n, n))
    np.fill_diagonal(time_matrix, 0.0)
    scores = np.array([0.0, 8.0, 7.5, 9.0, 6.5, 8.5, 7.0, 9.5, 6.0, 8.0])
    visit_times = np.array([0.0, 30.0, 25.0, 40.0, 20.0, 35.0, 30.0, 45.0, 20.0, 30.0])
    return OrienteeringProblem(
        time_matrix=time_matrix,
        scores=scores,
        visit_times=visit_times,
        depot_idx=0,
        t_max=t_max,
        mandatory_node=mandatory_node,
        forbidden_nodes=forbidden_nodes,
    )


class TestHardConstraints(unittest.TestCase):
    def setUp(self) -> None:
        random.seed(42)

    def test_available_nodes_excludes_depot_and_forbidden(self) -> None:
        problem = _build_synthetic_problem(forbidden_nodes=[2, 5, 8])
        available = problem.available_nodes()
        self.assertNotIn(0, available)
        for node in (2, 5, 8):
            self.assertNotIn(node, available)
        self.assertEqual(available, [1, 3, 4, 6, 7, 9])

    def test_problem_validation_rejects_contradictory_constraints(self) -> None:
        with self.assertRaises(ValueError):
            _build_synthetic_problem(mandatory_node=3, forbidden_nodes=[1, 3, 5])

        with self.assertRaises(ValueError):
            _build_synthetic_problem(mandatory_node=0)

        with self.assertRaises(ValueError):
            _build_synthetic_problem(mandatory_node=99)

        with self.assertRaises(ValueError):
            _build_synthetic_problem(mandatory_node=-1)

    def test_repair_chromosome_enforces_constraints_and_order(self) -> None:
        problem = _build_synthetic_problem(mandatory_node=4, forbidden_nodes=[2, 7])
        repaired = _repair_chromosome([1, 2, 3, 1, 7, 5, 3], problem)

        self.assertIn(4, repaired)
        self.assertNotIn(2, repaired)
        self.assertNotIn(7, repaired)
        self.assertEqual(len(repaired), len(set(repaired)))
        non_mandatory = [g for g in repaired if g != 4]
        self.assertEqual(non_mandatory, [1, 3, 5])

    def test_mutate_preserves_mandatory_and_excludes_forbidden(self) -> None:
        problem = _build_synthetic_problem(mandatory_node=3, forbidden_nodes=[2, 6])
        candidates = problem.available_nodes()

        single_ind = Individual([3])
        for _ in range(100):
            mutated = mutate(single_ind, candidates, problem)
            self.assertIn(3, mutated.genes)
            self.assertNotIn(2, mutated.genes)
            self.assertNotIn(6, mutated.genes)

        multi_ind = Individual([1, 3, 5, 8])
        for _ in range(100):
            mutated = mutate(multi_ind, candidates, problem)
            self.assertIn(3, mutated.genes)
            self.assertNotIn(2, mutated.genes)
            self.assertNotIn(6, mutated.genes)
            self.assertEqual(len(mutated.genes), len(set(mutated.genes)))

    def test_nsga2_evolve_respects_mandatory_and_forbidden(self) -> None:
        problem = _build_synthetic_problem(
            mandatory_node=3,
            forbidden_nodes=[2, 5, 8],
            t_max=220.0,
        )
        config = GAConfig(population_size=40, generations=50)
        nsga2 = NSGA2Orienteering(problem, config)
        front = nsga2.evolve()

        self.assertGreater(len(front), 0)
        for ind in front:
            self.assertIn(3, ind.genes)
            for forbidden in (2, 5, 8):
                self.assertNotIn(forbidden, ind.genes)
            self.assertEqual(ind.violation, 0.0)
            self.assertLessEqual(ind.total_time, problem.t_max)

    def test_nsga2_returns_empty_front_when_mandatory_exceeds_tmax(self) -> None:
        problem = _build_synthetic_problem(
            mandatory_node=7,
            forbidden_nodes=[1, 2],
            t_max=20.0,
        )
        config = GAConfig(population_size=30, generations=30)
        nsga2 = NSGA2Orienteering(problem, config)
        front = nsga2.evolve()
        self.assertEqual(front, [])

    def test_weighted_sum_runs_with_constraints(self) -> None:
        problem = _build_synthetic_problem(
            mandatory_node=4,
            forbidden_nodes=[1, 6],
            t_max=220.0,
        )
        ws = WeightedSumGA(problem, pop_size=20, generations=25, weights=[0.3, 0.7])
        solutions = ws.run()
        self.assertGreater(len(solutions), 0)
        for ind in solutions:
            self.assertIn(4, ind.genes)
            self.assertNotIn(1, ind.genes)
            self.assertNotIn(6, ind.genes)
            self.assertEqual(ind.violation, 0.0)

    def test_epsilon_constraint_respects_constraints_and_pareto(self) -> None:
        problem = _build_synthetic_problem(
            mandatory_node=4,
            forbidden_nodes=[1, 6],
            t_max=220.0,
        )
        ec = EpsilonConstraintGA(problem, pop_size=20, generations=25)
        solutions = ec.run()
        self.assertGreater(len(solutions), 0)
        self.assertEqual(ec.evaluations, len(ec.epsilons) * 20 * (1 + 25))
        for ind in solutions:
            self.assertIn(4, ind.genes)
            self.assertNotIn(1, ind.genes)
            self.assertNotIn(6, ind.genes)
            self.assertEqual(ind.violation, 0.0)
            self.assertLessEqual(ind.total_time, problem.t_max)

        # Ninguna solución devuelta debe estar dominada por otra
        for i, ind in enumerate(solutions):
            for j, other in enumerate(solutions):
                if i != j:
                    self.assertFalse(other.dominates(ind))

    def test_epsilon_constraint_default_budget_is_20100(self) -> None:
        problem = _build_synthetic_problem(t_max=480.0)
        ec = EpsilonConstraintGA(problem)
        self.assertEqual(len(ec.epsilons), 10)
        self.assertEqual(ec.epsilons[0], 60.0)
        self.assertEqual(ec.epsilons[-1], 480.0)
        ec.run()
        self.assertEqual(ec.evaluations, 20100)


if __name__ == "__main__":
    unittest.main()
