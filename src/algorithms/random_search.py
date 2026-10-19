from typing import List, Tuple
import random
from ..core.problem import OrienteeringProblem, Individual


class RandomSearchOrienteering:
    def __init__(self, problem: OrienteeringProblem, total_evaluations: int = 20000):
        self.problem = problem
        self.total_evaluations = total_evaluations
        self.candidates = problem.available_nodes()

    def run(self) -> List[Individual]:
        all_feasible: List[Individual] = []

        for _ in range(self.total_evaluations):
            size = random.randint(2, min(10, len(self.candidates)))
            genes = random.sample(self.candidates, size)
            ind = Individual(genes)
            ind.evaluate(self.problem)

            if ind.violation == 0 and ind.genes:
                all_feasible.append(ind)

        return self._filter_pareto(all_feasible)

    def _filter_pareto(self, individuals: List[Individual]) -> List[Individual]:
        pareto: List[Individual] = []
        for cand in individuals:
            is_dominated = False
            for other in individuals:
                if other.dominates(cand):
                    is_dominated = True
                    break
            if not is_dominated:
                if not any(p.score == cand.score and p.total_time == cand.total_time for p in pareto):
                    pareto.append(cand)

        pareto.sort(key=lambda ind: ind.total_time)
        return pareto
