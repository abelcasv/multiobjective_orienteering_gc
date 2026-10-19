from dataclasses import dataclass
from typing import List
import numpy as np


@dataclass(frozen=True)
class OrienteeringProblem:
    time_matrix: np.ndarray
    scores: np.ndarray
    visit_times: np.ndarray
    depot_idx: int
    t_max: float

    @property
    def node_count(self) -> int:
        return self.time_matrix.shape[0]

    def available_nodes(self) -> List[int]:
        return [i for i in range(self.node_count) if i != self.depot_idx]

    def driving_time(self, origin: int, destination: int) -> float:
        return float(self.time_matrix[origin, destination])


@dataclass(frozen=True)
class GAConfig:
    population_size: int = 100
    generations: int = 200
    crossover_rate: float = 0.85
    mutation_rate: float = 0.35
    min_init_nodes: int = 3
    max_init_nodes: int = 7


class Individual:
    def __init__(self, genes: List[int]):
        self.genes: List[int] = genes
        self.score: float = 0.0
        self.driving_time: float = 0.0
        self.visiting_time: float = 0.0
        self.total_time: float = 0.0
        self.violation: float = 0.0
        self.rank: int = 0
        self.crowding_distance: float = 0.0

    def evaluate(self, problem: OrienteeringProblem) -> None:
        if not self.genes:
            self._reset_metrics()
            return
        self.score = float(np.sum(problem.scores[self.genes]))
        self.visiting_time = float(np.sum(problem.visit_times[self.genes]))
        self.driving_time = self._compute_driving_time(problem)
        self.total_time = self.driving_time + self.visiting_time
        self.violation = max(0.0, self.total_time - problem.t_max)

    def _reset_metrics(self) -> None:
        self.score = 0.0
        self.driving_time = 0.0
        self.visiting_time = 0.0
        self.total_time = 0.0
        self.violation = 0.0

    def _compute_driving_time(self, problem: OrienteeringProblem) -> float:
        route = [problem.depot_idx] + self.genes + [problem.depot_idx]
        return sum(
            problem.driving_time(route[i], route[i + 1])
            for i in range(len(route) - 1)
        )

    def dominates(self, other: "Individual") -> bool:
        if self.violation == 0 and other.violation > 0:
            return True
        if self.violation > 0 and other.violation == 0:
            return False
        if self.violation > 0 and other.violation > 0:
            return self.violation < other.violation
        return self._pareto_dominates(other)

    def _pareto_dominates(self, other: "Individual") -> bool:
        better_equal = (self.score >= other.score) and (self.total_time <= other.total_time)
        strictly_better = (self.score > other.score) or (self.total_time < other.total_time)
        return better_equal and strictly_better
