from pathlib import Path
from typing import Callable, Dict, List, Tuple
import random
import numpy as np
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / "output"


def _h_zdt1(f1: float, g: float) -> float:
    return 1.0 - np.sqrt(f1 / g)


def _h_zdt2(f1: float, g: float) -> float:
    return 1.0 - (f1 / g) ** 2


def _h_zdt3(f1: float, g: float) -> float:
    return 1.0 - np.sqrt(f1 / g) - (f1 / g) * np.sin(10.0 * np.pi * f1)


_ZDT_H_FUNCTIONS: Dict[str, Callable[[float, float], float]] = {
    "ZDT1": _h_zdt1,
    "ZDT2": _h_zdt2,
    "ZDT3": _h_zdt3,
}


class ZDTIndividual:
    def __init__(self, x: np.ndarray, problem_name: str = "ZDT1"):
        if problem_name not in _ZDT_H_FUNCTIONS:
            raise ValueError(f"Unknown ZDT problem '{problem_name}'. Valid: {list(_ZDT_H_FUNCTIONS)}")
        self.problem_name = problem_name
        self.x = np.clip(x, 0.0, 1.0)
        self.f1: float = 0.0
        self.f2: float = 0.0
        self.rank: int = 0
        self.crowding_distance: float = 0.0
        self.evaluate()

    def evaluate(self) -> None:
        self.f1 = float(self.x[0])
        g = 1.0 + 9.0 * float(np.sum(self.x[1:])) / (len(self.x) - 1)
        h = float(_ZDT_H_FUNCTIONS[self.problem_name](self.f1, g))
        self.f2 = float(g * h)

    def dominates(self, other: "ZDTIndividual") -> bool:
        better_equal = (self.f1 <= other.f1) and (self.f2 <= other.f2)
        strictly_better = (self.f1 < other.f1) or (self.f2 < other.f2)
        return better_equal and strictly_better


class ZDT1Individual(ZDTIndividual):
    def __init__(self, x: np.ndarray):
        super().__init__(x, problem_name="ZDT1")


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


def fast_sort_zdt(population: List[ZDTIndividual]) -> List[List[ZDTIndividual]]:
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


def crowding_distance_zdt(front: List[ZDTIndividual]) -> None:
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


def _tournament_selection(population: List[ZDTIndividual]) -> ZDTIndividual:
    p1, p2 = random.sample(population, 2)
    if p1.rank != p2.rank:
        return p1 if p1.rank < p2.rank else p2
    return p1 if p1.crowding_distance >= p2.crowding_distance else p2


def _reproduce_zdt_pair(
    population: List[ZDTIndividual],
    num_vars: int,
    problem_name: str,
) -> Tuple[ZDTIndividual, ZDTIndividual]:
    p = _tournament_selection(population)
    q = _tournament_selection(population)
    c1_x, c2_x = _sbx_crossover(p.x, q.x)
    c1_x = _polynomial_mutation(c1_x, pm=1.0 / num_vars)
    c2_x = _polynomial_mutation(c2_x, pm=1.0 / num_vars)
    return ZDTIndividual(c1_x, problem_name), ZDTIndividual(c2_x, problem_name)


def _generate_zdt_offspring(
    population: List[ZDTIndividual],
    pop_size: int,
    num_vars: int,
    problem_name: str,
) -> List[ZDTIndividual]:
    offspring: List[ZDTIndividual] = []
    while len(offspring) < pop_size:
        c1, c2 = _reproduce_zdt_pair(population, num_vars, problem_name)
        offspring.extend([c1, c2])
    return offspring[:pop_size]


def _select_next_generation_zdt(population: List[ZDTIndividual], pop_size: int) -> List[ZDTIndividual]:
    fronts = fast_sort_zdt(population)
    selected: List[ZDTIndividual] = []
    for front in fronts:
        crowding_distance_zdt(front)
        if len(selected) + len(front) <= pop_size:
            selected.extend(front)
        else:
            front.sort(key=lambda ind: ind.crowding_distance, reverse=True)
            selected.extend(front[: pop_size - len(selected)])
            break
    return selected


def true_pareto_front(problem_name: str, n_points: int = 500) -> np.ndarray:
    """Devuelve puntos (f1, f2) sobre el frente de Pareto teórico exacto con g(x)=1."""
    if problem_name == "ZDT1":
        true_f1 = np.linspace(0.0, 1.0, n_points)
        true_f2 = 1.0 - np.sqrt(true_f1)
        return np.column_stack([true_f1, true_f2])
    if problem_name == "ZDT2":
        true_f1 = np.linspace(0.0, 1.0, n_points)
        true_f2 = 1.0 - true_f1 ** 2
        return np.column_stack([true_f1, true_f2])
    if problem_name == "ZDT3":
        f1_grid = np.linspace(0.0, 1.0, 5000)
        f2_grid = 1.0 - np.sqrt(f1_grid) - f1_grid * np.sin(10.0 * np.pi * f1_grid)
        pts = []
        best_f2 = float("inf")
        for f1, f2 in zip(f1_grid, f2_grid):
            if f2 < best_f2:
                pts.append((f1, f2))
                best_f2 = float(f2)
        arr = np.array(pts)
        indices = np.linspace(0, len(arr) - 1, min(n_points, len(arr)), dtype=int)
        return arr[indices]
    raise ValueError(f"Unknown ZDT problem '{problem_name}'.")


def _calculate_zdt_igd(front: List[ZDTIndividual], problem_name: str) -> float:
    true_pareto = true_pareto_front(problem_name, n_points=500)
    obtained = np.array([[ind.f1, ind.f2] for ind in front])
    return float(np.mean([np.min(np.linalg.norm(obtained - pt, axis=1)) for pt in true_pareto]))


def run_zdt_validation(
    problem_name: str = "ZDT1",
    num_variables: int = 30,
    pop_size: int = 100,
    generations: int = 250,
    seed: int = 42,
) -> Tuple[List[ZDTIndividual], float]:
    random.seed(seed)
    np.random.seed(seed)
    population = [ZDTIndividual(np.random.rand(num_variables), problem_name) for _ in range(pop_size)]
    for front in fast_sort_zdt(population):
        crowding_distance_zdt(front)

    for _ in range(generations):
        offspring = _generate_zdt_offspring(population, pop_size, num_variables, problem_name)
        population = _select_next_generation_zdt(population + offspring, pop_size)

    f1_front = fast_sort_zdt(population)[0]
    crowding_distance_zdt(f1_front)
    return f1_front, _calculate_zdt_igd(f1_front, problem_name)


def run_zdt1_validation(
    num_variables: int = 30,
    pop_size: int = 100,
    generations: int = 250,
    seed: int = 42,
) -> Tuple[List[ZDTIndividual], float]:
    return run_zdt_validation("ZDT1", num_variables=num_variables, pop_size=pop_size, generations=generations, seed=seed)


def _plot_single_zdt(ax: plt.Axes, problem_name: str, front: List[ZDTIndividual], igd: float) -> None:
    pareto_pts = true_pareto_front(problem_name, n_points=300)
    f1_curve = pareto_pts[:, 0].copy()
    f2_curve = pareto_pts[:, 1].copy()
    if problem_name == "ZDT3":
        # Separar visualmente los 5 tramos discontinuos del frente de ZDT3
        diffs = np.diff(f1_curve, prepend=f1_curve[0])
        jumps = np.where(diffs > 0.02)[0]
        for idx in reversed(jumps):
            f1_curve = np.insert(f1_curve, idx, np.nan)
            f2_curve = np.insert(f2_curve, idx, np.nan)

    ax.plot(f1_curve, f2_curve, "r-", linewidth=2.0, label="Frente Teórico")
    ax.scatter(
        [ind.f1 for ind in front],
        [ind.f2 for ind in front],
        color="#2980b9",
        s=32,
        alpha=0.8,
        edgecolors="black",
        label=f"NSGA-II (IGD = {igd:.4f})",
    )
    ax.set_xlabel("$f_1(x)$ (Minimizar)", fontsize=10)
    ax.set_ylabel("$f_2(x)$ (Minimizar)", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9)


def plot_zdt1_benchmark(f1_front: List[ZDTIndividual], igd: float, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    _plot_single_zdt(ax, "ZDT1", f1_front, igd)
    ax.set_title("Validación de NSGA-II en Benchmark Analítico Estándar: ZDT1", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_zdt_family(results: Dict[str, Tuple[List[ZDTIndividual], float]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    titles = {
        "ZDT1": "ZDT1 (Frente Convexo)",
        "ZDT2": "ZDT2 (Frente Cóncavo)",
        "ZDT3": "ZDT3 (Frente Discontinuo)",
    }
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, name in zip(axes, ("ZDT1", "ZDT2", "ZDT3")):
        front, igd = results[name]
        _plot_single_zdt(ax, name, front, igd)
        ax.set_title(titles[name], fontsize=11, fontweight="bold")
    fig.suptitle("Validación Analítica de NSGA-II en la Familia ZDT", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def main() -> None:
    print("--> Ejecutando validación analítica de NSGA-II en ZDT1, ZDT2 y ZDT3...")
    results: Dict[str, Tuple[List[ZDTIndividual], float]] = {}
    for name in ("ZDT1", "ZDT2", "ZDT3"):
        front, igd = run_zdt_validation(name)
        results[name] = (front, igd)
        print(f"    - {name}: F1={len(front)} soluciones | IGD = {igd:.4f}")

    fig_zdt1 = OUTPUT_DIR / "validacion_zdt1.png"
    plot_zdt1_benchmark(results["ZDT1"][0], results["ZDT1"][1], fig_zdt1)
    fig_family = OUTPUT_DIR / "validacion_zdt_familia.png"
    plot_zdt_family(results, fig_family)
    print(f"--> [OK] Gráficas guardadas en '{fig_zdt1}' y '{fig_family}'")


if __name__ == "__main__":
    main()
