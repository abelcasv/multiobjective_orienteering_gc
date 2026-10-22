from typing import List, Tuple, Optional
import random
import numpy as np
from ..core.problem import OrienteeringProblem, Individual
from .genetic_algorithm import crossover, mutate


class WeightedSumGA:
    def __init__(
        self,
        problem: OrienteeringProblem,
        pop_size: int = 50,
        generations: int = 39,
        weights: Optional[List[float]] = None,
    ):
        self.problem = problem
        self.pop_size = pop_size
        self.generations = generations
        self.weights = weights or [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
        self.candidates = problem.available_nodes()
        self.max_theoretical_score = max(1.0, float(np.sum(problem.scores)))

    def _fitness(self, ind: Individual, weight_score: float) -> float:
        if ind.violation > 0:
            return -1e5 - ind.violation * 100.0
        norm_score = ind.score / self.max_theoretical_score
        norm_time = ind.total_time / self.problem.t_max
        return weight_score * norm_score - (1.0 - weight_score) * norm_time

    def _generate_offspring(self, population: List[Individual], weight: float) -> List[Individual]:
        offspring: List[Individual] = []
        while len(offspring) < self.pop_size:
            p1 = self._tournament(population, weight)
            p2 = self._tournament(population, weight)
            c1, c2 = crossover(p1, p2)
            c1 = mutate(c1, self.candidates)
            c2 = mutate(c2, self.candidates)
            c1.evaluate(self.problem)
            c2.evaluate(self.problem)
            offspring.extend([c1, c2])
        return offspring

    def _solve_for_weight(self, weight_score: float) -> Optional[Individual]:
        population = [
            Individual(random.sample(self.candidates, random.randint(2, 7)))
            for _ in range(self.pop_size)
        ]
        for ind in population:
            ind.evaluate(self.problem)

        for _ in range(self.generations):
            offspring = self._generate_offspring(population, weight_score)
            combined = population + offspring
            combined.sort(key=lambda ind: self._fitness(ind, weight_score), reverse=True)
            population = combined[: self.pop_size]

        feasible = [ind for ind in population if ind.violation == 0 and ind.genes]
        return max(feasible, key=lambda ind: self._fitness(ind, weight_score)) if feasible else None

    def _tournament(self, population: List[Individual], weight: float) -> Individual:
        a, b = random.sample(population, 2)
        return a if self._fitness(a, weight) >= self._fitness(b, weight) else b

    def run(self) -> List[Individual]:
        solutions: List[Individual] = []
        for w in self.weights:
            best = self._solve_for_weight(w)
            if best and not any(p.score == best.score and p.total_time == best.total_time for p in solutions):
                solutions.append(best)
        solutions.sort(key=lambda ind: ind.total_time)
        return self._filter_pareto(solutions)

    def _filter_pareto(self, individuals: List[Individual]) -> List[Individual]:
        return [c for c in individuals if not any(o.dominates(c) for o in individuals)]
