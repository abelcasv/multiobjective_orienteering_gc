from typing import List, Optional
import random
import numpy as np
from ..core.problem import OrienteeringProblem, Individual
from .genetic_algorithm import crossover, mutate, _repair_chromosome


class EpsilonConstraintGA:
    """Línea base por método de ε-restricción: maximiza puntuación sujeta a T(R) <= ε."""

    def __init__(
        self,
        problem: OrienteeringProblem,
        pop_size: int = 30,
        generations: int = 66,
        epsilons: Optional[List[float]] = None,
    ):
        self.problem = problem
        self.pop_size = pop_size
        self.generations = generations
        if epsilons is None:
            min_eps = min(60.0, float(problem.t_max))
            self.epsilons = [float(x) for x in np.linspace(min_eps, float(problem.t_max), 10)]
        else:
            self.epsilons = [float(x) for x in epsilons]
        self.candidates = problem.available_nodes()
        self.evaluations: int = 0

    def _effective_limit(self, epsilon: float) -> float:
        return min(float(epsilon), float(self.problem.t_max))

    def _fitness(self, ind: Individual, epsilon: float) -> float:
        limit = self._effective_limit(epsilon)
        violation_eps = max(0.0, ind.total_time - limit)
        if violation_eps > 0:
            return -1e5 - violation_eps * 100.0
        # Pequeño término secundario para romper empates de puntuación hacia menor tiempo
        return ind.score - 1e-4 * (ind.total_time / max(1.0, float(self.problem.t_max)))

    def _create_initial_individual(self) -> Individual:
        max_k = min(7, len(self.candidates))
        min_k = min(2, max_k)
        size = random.randint(min_k, max_k) if max_k > 0 else 0
        genes = random.sample(self.candidates, size)
        return Individual(_repair_chromosome(genes, self.problem))

    def _evaluate(self, ind: Individual) -> None:
        ind.evaluate(self.problem)
        self.evaluations += 1

    def _tournament(self, population: List[Individual], epsilon: float) -> Individual:
        a, b = random.sample(population, 2)
        return a if self._fitness(a, epsilon) >= self._fitness(b, epsilon) else b

    def _generate_offspring(self, population: List[Individual], epsilon: float) -> List[Individual]:
        offspring: List[Individual] = []
        while len(offspring) < self.pop_size:
            p1 = self._tournament(population, epsilon)
            p2 = self._tournament(population, epsilon)
            raw_c1, raw_c2 = crossover(p1, p2)
            c1 = Individual(_repair_chromosome(raw_c1.genes, self.problem))
            c2 = Individual(_repair_chromosome(raw_c2.genes, self.problem))
            c1 = mutate(c1, self.candidates, self.problem)
            c2 = mutate(c2, self.candidates, self.problem)
            for child in (c1, c2):
                if len(offspring) < self.pop_size:
                    self._evaluate(child)
                    offspring.append(child)
        return offspring

    def _solve_for_epsilon(self, epsilon: float) -> Optional[Individual]:
        population = [self._create_initial_individual() for _ in range(self.pop_size)]
        for ind in population:
            self._evaluate(ind)

        for _ in range(self.generations):
            offspring = self._generate_offspring(population, epsilon)
            combined = population + offspring
            combined.sort(key=lambda ind: self._fitness(ind, epsilon), reverse=True)
            population = combined[: self.pop_size]

        limit = self._effective_limit(epsilon)
        feasible = [
            ind for ind in population
            if ind.total_time <= limit and ind.violation == 0 and ind.genes
        ]
        return max(feasible, key=lambda ind: self._fitness(ind, epsilon)) if feasible else None

    def run(self) -> List[Individual]:
        self.evaluations = 0
        if not self.candidates:
            return []
        solutions: List[Individual] = []
        for eps in self.epsilons:
            best = self._solve_for_epsilon(eps)
            if best and not any(
                round(p.score, 2) == round(best.score, 2)
                and round(p.total_time, 2) == round(best.total_time, 2)
                for p in solutions
            ):
                solutions.append(best)
        solutions.sort(key=lambda ind: ind.total_time)
        return self._filter_pareto(solutions)

    def _filter_pareto(self, individuals: List[Individual]) -> List[Individual]:
        return [c for c in individuals if not any(o.dominates(c) for o in individuals)]
