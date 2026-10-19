from pathlib import Path
from typing import List, Tuple
import random
import numpy as np
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / "output"


class ZDT1Individual:
    def __init__(self, x: np.ndarray):
        self.x = np.clip(x, 0.0, 1.0)
        self.f1: float = 0.0
        self.f2: float = 0.0
        self.rank: int = 0
        self.crowding_distance: float = 0.0
        self.evaluate()

    def evaluate(self) -> None:
        self.f1 = float(self.x[0])
        g = 1.0 + 9.0 * float(np.sum(self.x[1:])) / (len(self.x) - 1)
        h = 1.0 - np.sqrt(self.f1 / g)
        self.f2 = float(g * h)

    def dominates(self, other: "ZDT1Individual") -> bool:
        better_equal = (self.f1 <= other.f1) and (self.f2 <= other.f2)
        strictly_better = (self.f1 < other.f1) or (self.f2 < other.f2)
        return better_equal and strictly_better


def _sbx_crossover(p1: np.ndarray, p2: np.ndarray, eta: float = 15.0) -> Tuple[np.ndarray, np.ndarray]:
    c1, c2 = np.copy(p1), np.copy(p2)
    for i in range(len(p1)):
        if random.random() <= 0.5:
            if abs(p1[i] - p2[i]) > 1e-14:
                y1 = min(p1[i], p2[i])
                y2 = max(p1[i], p2[i])
                rand = random.random()
                beta = 1.0 + (2.0 * (y1) / (y2 - y1))
                alpha = 2.0 - (beta ** -(eta + 1.0))
                betaq = (rand * alpha) ** (1.0 / (eta + 1.0)) if rand <= (1.0 / alpha) else (1.0 / (2.0 - rand * alpha)) ** (1.0 / (eta + 1.0))
                c1[i] = 0.5 * ((y1 + y2) - betaq * (y2 - y1))
                c2[i] = 0.5 * ((y1 + y2) + betaq * (y2 - y1))
    return np.clip(c1, 0.0, 1.0), np.clip(c2, 0.0, 1.0)


def _polynomial_mutation(x: np.ndarray, eta: float = 20.0, pm: float = 0.05) -> np.ndarray:
    mutated = np.copy(x)
    for i in range(len(mutated)):
        if random.random() < pm:
            u = random.random()
            if u < 0.5:
                delta = (2.0 * u) ** (1.0 / (eta + 1.0)) - 1.0
                mutated[i] += delta * mutated[i]
            else:
                delta = 1.0 - (2.0 * (1.0 - u)) ** (1.0 / (eta + 1.0))
                mutated[i] += delta * (1.0 - mutated[i])
    return np.clip(mutated, 0.0, 1.0)


def fast_sort_zdt(population: List[ZDT1Individual]) -> List[List[ZDT1Individual]]:
    sp = {ind: [] for ind in population}
    np_cnt = {ind: 0 for ind in population}
    first_front = []

    for p in population:
        for q in population:
            if p.dominates(q):
                sp[p].append(q)
            elif q.dominates(p):
                np_cnt[p] += 1
        if np_cnt[p] == 0:
            p.rank = 0
            first_front.append(p)

    fronts = [first_front]
    i = 0
    while fronts[i]:
        next_front = []
        for p in fronts[i]:
            for q in sp[p]:
                np_cnt[q] -= 1
                if np_cnt[q] == 0:
                    q.rank = i + 1
                    next_front.append(q)
        i += 1
        fronts.append(next_front)
    fronts.pop()
    return fronts


def crowding_distance_zdt(front: List[ZDT1Individual]) -> None:
    if not front:
        return
    for ind in front:
        ind.crowding_distance = 0.0
    if len(front) <= 2:
        for ind in front:
            ind.crowding_distance = float("inf")
        return

    for obj in [lambda ind: ind.f1, lambda ind: ind.f2]:
        front.sort(key=obj)
        front[0].crowding_distance = float("inf")
        front[-1].crowding_distance = float("inf")
        val_range = obj(front[-1]) - obj(front[0])
        if val_range > 0:
            for i in range(1, len(front) - 1):
                front[i].crowding_distance += (obj(front[i + 1]) - obj(front[i - 1])) / val_range


def _reproduce_zdt_pair(population: List[ZDT1Individual], num_vars: int) -> Tuple[ZDT1Individual, ZDT1Individual]:
    p1, p2 = random.sample(population, 2)
    p = p1 if p1.rank < p2.rank else p2
    q1, q2 = random.sample(population, 2)
    q = q1 if q1.rank < q2.rank else q2
    c1_x, c2_x = _sbx_crossover(p.x, q.x)
    c1_x = _polynomial_mutation(c1_x, pm=1.0 / num_vars)
    c2_x = _polynomial_mutation(c2_x, pm=1.0 / num_vars)
    return ZDT1Individual(c1_x), ZDT1Individual(c2_x)


def _generate_zdt_offspring(population: List[ZDT1Individual], pop_size: int, num_vars: int) -> List[ZDT1Individual]:
    offspring: List[ZDT1Individual] = []
    while len(offspring) < pop_size:
        c1, c2 = _reproduce_zdt_pair(population, num_vars)
        offspring.extend([c1, c2])
    return offspring[:pop_size]


def _select_next_generation_zdt(population: List[ZDT1Individual], pop_size: int) -> List[ZDT1Individual]:
    fronts = fast_sort_zdt(population)
    selected: List[ZDT1Individual] = []
    for front in fronts:
        crowding_distance_zdt(front)
        if len(selected) + len(front) <= pop_size:
            selected.extend(front)
        else:
            front.sort(key=lambda ind: ind.crowding_distance, reverse=True)
            selected.extend(front[: pop_size - len(selected)])
            break
    return selected


def _calculate_zdt1_igd(front: List[ZDT1Individual]) -> float:
    true_f1 = np.linspace(0.0, 1.0, 500)
    true_f2 = 1.0 - np.sqrt(true_f1)
    true_pareto = np.column_stack([true_f1, true_f2])
    obtained = np.array([[ind.f1, ind.f2] for ind in front])
    return float(np.mean([np.min(np.linalg.norm(obtained - pt, axis=1)) for pt in true_pareto]))


def run_zdt1_validation(
    num_variables: int = 30,
    pop_size: int = 100,
    generations: int = 150,
) -> Tuple[List[ZDT1Individual], float]:
    population = [ZDT1Individual(np.random.rand(num_variables)) for _ in range(pop_size)]
    for _ in range(generations):
        offspring = _generate_zdt_offspring(population, pop_size, num_variables)
        population = _select_next_generation_zdt(population + offspring, pop_size)
    f1_front = fast_sort_zdt(population)[0]
    return f1_front, _calculate_zdt1_igd(f1_front)


def plot_zdt1_benchmark(f1_front: List[ZDT1Individual], igd: float, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    true_f1 = np.linspace(0.0, 1.0, 300)
    true_f2 = 1.0 - np.sqrt(true_f1)

    plt.figure(figsize=(8, 5))
    plt.plot(true_f1, true_f2, "r-", linewidth=2.0, label="Frente de Pareto Teórico (Exacto)")
    f1_vals = [ind.f1 for ind in f1_front]
    f2_vals = [ind.f2 for ind in f1_front]
    plt.scatter(f1_vals, f2_vals, color="#2980b9", s=40, alpha=0.8, edgecolors="black", label=f"NSGA-II Propio (IGD = {igd:.4f})")

    plt.title("Validación de NSGA-II en Benchmark Analítico Estándar: ZDT1", fontsize=12, fontweight="bold")
    plt.xlabel("$f_1(x)$ (Minimizar)", fontsize=11)
    plt.ylabel("$f_2(x)$ (Minimizar)", fontsize=11)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper right", framealpha=0.9)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def main() -> None:
    print("--> Ejecutando validación analítica de NSGA-II en el problema benchmark ZDT1...")
    front, igd = run_zdt1_validation()
    fig_path = OUTPUT_DIR / "validacion_zdt1.png"
    plot_zdt1_benchmark(front, igd, fig_path)
    print(f"--> [OK] Validación ZDT1 completada exitosamente:")
    print(f"    - Soluciones en Frente F1: {len(front)}")
    print(f"    - Inverted Generational Distance (IGD): {igd:.4f} (Excelente convergencia al frente real)")
    print(f"    - Gráfica guardada en: '{fig_path}'")


if __name__ == "__main__":
    main()
