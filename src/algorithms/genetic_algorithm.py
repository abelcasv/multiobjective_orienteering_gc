from typing import List, Tuple, Optional, Callable
import random
from ..core.problem import OrienteeringProblem, GAConfig, Individual
from ..core.metrics import calcular_hipervolumen


def _insert_random_node(genes: List[int], candidates: List[int]) -> List[int]:
    unvisited = [node for node in candidates if node not in genes]
    if not unvisited:
        return genes
    copy_genes = list(genes)
    copy_genes.insert(random.randint(0, len(copy_genes)), random.choice(unvisited))
    return copy_genes


def _remove_random_node(genes: List[int]) -> List[int]:
    if len(genes) <= 1:
        return genes
    copy_genes = list(genes)
    copy_genes.pop(random.randint(0, len(copy_genes) - 1))
    return copy_genes


def _swap_random_nodes(genes: List[int]) -> List[int]:
    if len(genes) < 2:
        return genes
    copy_genes = list(genes)
    i, j = random.sample(range(len(copy_genes)), 2)
    copy_genes[i], copy_genes[j] = copy_genes[j], copy_genes[i]
    return copy_genes


def _invert_random_segment(genes: List[int]) -> List[int]:
    if len(genes) < 3:
        return genes
    copy_genes = list(genes)
    i, j = sorted(random.sample(range(len(copy_genes)), 2))
    copy_genes[i : j + 1] = reversed(copy_genes[i : j + 1])
    return copy_genes


def mutate(ind: Individual, candidates: List[int]) -> Individual:
    operators = [
        _insert_random_node,
        _remove_random_node,
        _swap_random_nodes,
        _invert_random_segment,
    ]
    weights = [0.4, 0.3, 0.2, 0.1]
    chosen_op = random.choices(operators, weights=weights, k=1)[0]
    if chosen_op == _insert_random_node:
        new_genes = _insert_random_node(ind.genes, candidates)
    else:
        new_genes = chosen_op(ind.genes)
    return Individual(new_genes)


def _build_child_genes(base: List[int], donor: List[int], max_len: int) -> List[int]:
    cut_point = random.randint(1, max(1, len(base) - 1))
    segment = base[:cut_point]
    remainder = [gene for gene in donor if gene not in segment]
    child_genes = segment + remainder
    return child_genes[:max_len]


def crossover(p1: Individual, p2: Individual, max_len: int = 12) -> Tuple[Individual, Individual]:
    if not p1.genes or not p2.genes:
        return Individual(list(p1.genes)), Individual(list(p2.genes))
    child1_genes = _build_child_genes(p1.genes, p2.genes, max_len)
    child2_genes = _build_child_genes(p2.genes, p1.genes, max_len)
    return Individual(child1_genes), Individual(child2_genes)


def binary_tournament(first: Individual, second: Individual) -> Individual:
    if first.rank != second.rank:
        return first if first.rank < second.rank else second
    return first if first.crowding_distance > second.crowding_distance else second


def fast_non_dominated_sort(population: List[Individual]) -> List[List[Individual]]:
    dominated_by = {ind: 0 for ind in population}
    dominates_list = {ind: [] for ind in population}
    first_front: List[Individual] = []

    for p in population:
        for q in population:
            if p.dominates(q):
                dominates_list[p].append(q)
            elif q.dominates(p):
                dominated_by[p] += 1
        if dominated_by[p] == 0:
            p.rank = 0
            first_front.append(p)

    fronts = [first_front]
    i = 0
    while fronts[i]:
        next_front: List[Individual] = []
        for p in fronts[i]:
            for q in dominates_list[p]:
                dominated_by[q] -= 1
                if dominated_by[q] == 0:
                    q.rank = i + 1
                    next_front.append(q)
        i += 1
        fronts.append(next_front)

    fronts.pop()
    return fronts


def _apply_metric_crowding(front: List[Individual], key_func: Callable[[Individual], float]) -> None:
    front.sort(key=key_func)
    front[0].crowding_distance = float("inf")
    front[-1].crowding_distance = float("inf")
    value_range = key_func(front[-1]) - key_func(front[0])
    if value_range <= 0:
        return
    for i in range(1, len(front) - 1):
        delta = key_func(front[i + 1]) - key_func(front[i - 1])
        front[i].crowding_distance += delta / value_range


def calculate_crowding_distance(front: List[Individual]) -> None:
    if not front:
        return
    for ind in front:
        ind.crowding_distance = 0.0
    if len(front) <= 2:
        for ind in front:
            ind.crowding_distance = float("inf")
        return
    _apply_metric_crowding(front, lambda ind: ind.score)
    _apply_metric_crowding(front, lambda ind: ind.total_time)


class NSGA2Orienteering:
    def __init__(self, problem: OrienteeringProblem, config: Optional[GAConfig] = None):
        self.problem = problem
        self.config = config or GAConfig()
        self.candidates = problem.available_nodes()
        self.history_best_score: List[float] = []
        self.history_hypervolume: List[float] = []

    def _create_random_individual(self) -> Individual:
        size = random.randint(self.config.min_init_nodes, self.config.max_init_nodes)
        return Individual(random.sample(self.candidates, size))

    def _evaluate_all(self, individuals: List[Individual]) -> None:
        for ind in individuals:
            ind.evaluate(self.problem)

    def _create_offspring(self, population: List[Individual]) -> List[Individual]:
        offspring: List[Individual] = []
        while len(offspring) < self.config.population_size:
            p1 = binary_tournament(random.choice(population), random.choice(population))
            p2 = binary_tournament(random.choice(population), random.choice(population))

            if random.random() < self.config.crossover_rate:
                c1, c2 = crossover(p1, p2)
            else:
                c1, c2 = Individual(list(p1.genes)), Individual(list(p2.genes))

            if random.random() < self.config.mutation_rate:
                c1 = mutate(c1, self.candidates)
            if random.random() < self.config.mutation_rate:
                c2 = mutate(c2, self.candidates)

            self._evaluate_all([c1, c2])
            offspring.extend([c1, c2])

        return offspring[: self.config.population_size]

    def _environmental_selection(self, combined: List[Individual]) -> List[Individual]:
        fronts = fast_non_dominated_sort(combined)
        selected: List[Individual] = []
        for front in fronts:
            calculate_crowding_distance(front)
            if len(selected) + len(front) <= self.config.population_size:
                selected.extend(front)
            else:
                front.sort(key=lambda ind: ind.crowding_distance, reverse=True)
                needed = self.config.population_size - len(selected)
                selected.extend(front[:needed])
                break
        return selected

    def _record_generation_metrics(self, population: List[Individual]) -> None:
        feasible = [ind for ind in population if ind.violation == 0 and ind.genes]
        if not feasible:
            self.history_best_score.append(0.0)
            self.history_hypervolume.append(0.0)
            return

        self.history_best_score.append(max(ind.score for ind in feasible))
        f1_front = fast_non_dominated_sort(feasible)[0]
        points = [(ind.total_time, ind.score) for ind in f1_front]
        self.history_hypervolume.append(
            calcular_hipervolumen(points, ref_point=(self.problem.t_max, 0.0))
        )

    def evolve(self) -> List[Individual]:
        population = [
            self._create_random_individual()
            for _ in range(self.config.population_size)
        ]
        self._evaluate_all(population)

        for _ in range(self.config.generations):
            offspring = self._create_offspring(population)
            population = self._environmental_selection(population + offspring)
            self._record_generation_metrics(population)

        return self._extract_unique_feasible_pareto(population)

    def _extract_unique_feasible_pareto(self, population: List[Individual]) -> List[Individual]:
        f1 = fast_non_dominated_sort(population)[0]
        feasible = [ind for ind in f1 if ind.violation == 0 and ind.genes]
        unique_solutions: dict[Tuple[float, float], Individual] = {}
        for ind in feasible:
            key = (round(ind.score, 2), round(ind.total_time, 2))
            if key not in unique_solutions:
                unique_solutions[key] = ind
        return list(unique_solutions.values())


def _find_knee_point(front: List[Individual]) -> Individual:
    min_t = min(ind.total_time for ind in front)
    max_t = max(ind.total_time for ind in front)
    min_s = min(ind.score for ind in front)
    max_s = max(ind.score for ind in front)
    delta_t = max(1.0, max_t - min_t)
    delta_s = max(1.0, max_s - min_s)

    def distance_to_ideal(ind: Individual) -> float:
        norm_t = (ind.total_time - min_t) / delta_t
        norm_s = (ind.score - min_s) / delta_s
        return (norm_t ** 2 + (1.0 - norm_s) ** 2) ** 0.5

    return min(front, key=distance_to_ideal)


def seleccionar_3_opciones_turisticas(
    frente: List[Individual],
) -> Tuple[Optional[Individual], Optional[Individual], Optional[Individual]]:
    if not frente:
        return None, None, None
    sorted_front = sorted(frente, key=lambda ind: ind.total_time)
    express = max(sorted_front, key=lambda ind: ind.score / max(1.0, ind.total_time))
    exhaustive = max(sorted_front, key=lambda ind: ind.score)
    balanced = _find_knee_point(sorted_front)
    return express, balanced, exhaustive
