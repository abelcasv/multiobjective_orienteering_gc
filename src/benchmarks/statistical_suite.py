import json
import time
from pathlib import Path
from typing import Dict, List, Any
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    from ..core.problem import OrienteeringProblem, GAConfig
    from ..core.metrics import (
        calcular_hipervolumen,
        calcular_spread,
        test_wilcoxon,
        resumen_estadistico,
    )
    from ..algorithms.genetic_algorithm import NSGA2Orienteering
    from ..algorithms.greedy_algorithm import GreedyOrienteering
    from ..algorithms.random_search import RandomSearchOrienteering
    from ..algorithms.weighted_sum import WeightedSumGA
    from ..pipeline import load_distance_matrix, create_problem_instance
except (ImportError, ValueError):
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    from src.core.problem import OrienteeringProblem, GAConfig
    from src.core.metrics import (
        calcular_hipervolumen,
        calcular_spread,
        test_wilcoxon,
        resumen_estadistico,
    )
    from src.algorithms.genetic_algorithm import NSGA2Orienteering
    from src.algorithms.greedy_algorithm import GreedyOrienteering
    from src.algorithms.random_search import RandomSearchOrienteering
    from src.algorithms.weighted_sum import WeightedSumGA
    from src.pipeline import load_distance_matrix, create_problem_instance

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / "output"


def _evaluate_algorithm_run(
    algo_name: str,
    problem: OrienteeringProblem,
) -> Tuple[List[Tuple[float, float]], float]:
    t0 = time.time()
    if algo_name == "NSGA-II":
        algo = NSGA2Orienteering(problem, GAConfig(population_size=100, generations=200))
        front = algo.evolve()
        pts = [(ind.total_time, ind.score) for ind in front]
    elif algo_name == "Greedy":
        front_greedy = GreedyOrienteering(problem).generate_greedy_front(step_minutes=15.0)
        pts = [(s["total_time"], s["score"]) for s in front_greedy]
    elif algo_name == "Random Search":
        front_rs = RandomSearchOrienteering(problem, total_evaluations=20100).run()
        pts = [(ind.total_time, ind.score) for ind in front_rs]
    else:
        front_ws = WeightedSumGA(problem, pop_size=50, generations=39).run()
        pts = [(ind.total_time, ind.score) for ind in front_ws]
    return pts, time.time() - t0


def _build_summary_report(
    algorithms: List[str],
    results: Dict[str, Dict[str, List[float]]],
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"algoritmos": {}}
    hv_ref = results["NSGA-II"]["hipervolumen"]
    for algo in algorithms:
        summary["algoritmos"][algo] = {
            "hipervolumen": resumen_estadistico(results[algo]["hipervolumen"]),
            "spread": resumen_estadistico(results[algo]["spread"]),
            "tiempo_segundos": resumen_estadistico(results[algo]["tiempo_segundos"]),
            "test_wilcoxon_vs_nsga2": test_wilcoxon(hv_ref, results[algo]["hipervolumen"]) if algo != "NSGA-II" else None,
        }
    return summary


def run_statistical_benchmark(
    seeds: List[int],
    problem: OrienteeringProblem,
) -> Dict[str, Any]:
    algorithms = ["NSGA-II", "Greedy", "Random Search", "Weighted Sum"]
    results: Dict[str, Dict[str, List[float]]] = {
        algo: {"hipervolumen": [], "spread": [], "tiempo_segundos": []} for algo in algorithms
    }
    raw_records: List[Dict[str, Any]] = []

    print(f"--> Iniciando batería estadística con {len(seeds)} semillas independientes...")
    for seed in seeds:
        print(f"    * Ejecutando semilla {seed}...")
        random.seed(seed)
        np.random.seed(seed)
        for algo in algorithms:
            pts, elapsed = _evaluate_algorithm_run(algo, problem)
            hv = calcular_hipervolumen(pts, ref_point=(problem.t_max, 0.0))
            sp = calcular_spread(pts)
            results[algo]["hipervolumen"].append(hv)
            results[algo]["spread"].append(sp)
            results[algo]["tiempo_segundos"].append(elapsed)
            raw_records.append({"semilla": seed, "algoritmo": algo, "hipervolumen": hv, "spread": sp, "tiempo_s": elapsed})

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(raw_records).to_csv(OUTPUT_DIR / "resultados_estadisticos_semillas.csv", index=False)
    summary_report = _build_summary_report(algorithms, results)
    with open(OUTPUT_DIR / "resumen_estadistico.json", "w", encoding="utf-8") as f:
        json.dump(summary_report, f, ensure_ascii=False, indent=2)

    _plot_boxplots(results, OUTPUT_DIR / "boxplot_hipervolumen.png")
    return summary_report


def _plot_boxplots(results: Dict[str, Dict[str, List[float]]], output_path: Path) -> None:
    plt.figure(figsize=(9, 5))
    algos = list(results.keys())
    data = [results[a]["hipervolumen"] for a in algos]

    bp = plt.boxplot(data, tick_labels=algos, patch_artist=True)
    colors = ["#2980b9", "#8e44ad", "#e67e22", "#27ae60"]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    plt.title("Distribución de Hipervolumen (15 Semillas Independientes)", fontsize=12, fontweight="bold")
    plt.ylabel("Hipervolumen (HV)", fontsize=11)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def main() -> None:
    matrix, names = load_distance_matrix("matriz_tiempos.csv")
    problem = create_problem_instance(matrix, names, depot_name="Vegueta (Las Palmas)", t_max=480.0)
    seeds = [42, 101, 203, 314, 456, 578, 619, 723, 831, 954, 1024, 1234, 2048, 3072, 4096]

    summary = run_statistical_benchmark(seeds, problem)

    print("\n" + "=" * 80)
    print("  RESULTADOS DE LA BATERÍA ESTADÍSTICA (15 SEMILLAS)")
    print("=" * 80)
    print(f"{'Algoritmo':<18} | {'HV (Media ± Std)':<22} | {'Spread (Media)':<15} | {'p-valor vs NSGA-II':<18}")
    print("-" * 80)

    for algo, vals in summary["algoritmos"].items():
        hv_str = f"{vals['hipervolumen']['mean']:.1f} ± {vals['hipervolumen']['std']:.1f}"
        sp_str = f"{vals['spread']['mean']:.3f}"
        w = vals.get("test_wilcoxon_vs_nsga2")
        pval_str = f"{w['p_value']:.4e} *" if w and w["significant_at_005"] else ("N/A (Ref)" if algo == "NSGA-II" else f"{w['p_value']:.4e}")
        print(f"{algo:<18} | {hv_str:<22} | {sp_str:<15} | {pval_str:<18}")

    print("=" * 80)
    print("  * Diferencia estadísticamente significativa (p < 0.05)")
    print(f"  Ficheros guardados en '{OUTPUT_DIR.name}/'\n")


if __name__ == "__main__":
    main()
