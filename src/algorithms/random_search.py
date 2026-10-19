from typing import List, Tuple
import random
from ..core.problem import OrienteeringProblem, Individual


class RandomSearchOrienteering:
    def __init__(self, problem: OrienteeringProblem, total_evaluations: int = 20000):
        self.problem = problem
        self.total_evaluations = total_evaluations
        self.candidates = problem.available_nodes()

    def _sample_individual(self) -> Individual:
        size = random.randint(2, min(10, len(self.candidates)))
        genes = random.sample(self.candidates, size)
        ind = Individual(genes)
        ind.evaluate(self.problem)
        return ind

    def run(self) -> List[Individual]:
        all_feasible: List[Individual] = []
        for _ in range(self.total_evaluations):
            ind = self._sample_individual()
            if ind.violation == 0 and ind.genes:
                all_feasible.append(ind)
        return self._filter_pareto(all_feasible)

    def _filter_pareto(self, individuals: List[Individual]) -> List[Individual]:
        pareto = [c for c in individuals if not any(o.dominates(c) for o in individuals)]
        unique: List[Individual] = []
        for ind in pareto:
            if not any(p.score == ind.score and p.total_time == ind.total_time for p in unique):
                unique.append(ind)
        unique.sort(key=lambda ind: ind.total_time)
        return unique
