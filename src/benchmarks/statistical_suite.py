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


def run_statistical_benchmark(
    seeds: List[int],
    problem: OrienteeringProblem,
) -> Dict[str, Any]:
    algorithms = ["NSGA-II", "Greedy", "Random Search", "Weighted Sum"]
    results: Dict[str, Dict[str, List[float]]] = {
        algo: {"hipervolumen": [], "spread": [], "tiempo_segundos": []}
        for algo in algorithms
    }
    raw_records = []

    print(f"--> Iniciando batería estadística con {len(seeds)} semillas independientes...")

    for seed in seeds:
        print(f"    * Ejecutando semilla {seed}...")
        random.seed(seed)
        np.random.seed(seed)

        # 1. NSGA-II (Propio)
        t0 = time.time()
        nsga = NSGA2Orienteering(problem, GAConfig(population_size=100, generations=200))
        frente_nsga = nsga.evolve()
        pts_nsga = [(ind.total_time, ind.score) for ind in frente_nsga]
        t_nsga = time.time() - t0
        hv_nsga = calcular_hipervolumen(pts_nsga, ref_point=(problem.t_max, 0.0))
        sp_nsga = calcular_spread(pts_nsga)
        results["NSGA-II"]["hipervolumen"].append(hv_nsga)
        results["NSGA-II"]["spread"].append(sp_nsga)
        results["NSGA-II"]["tiempo_segundos"].append(t_nsga)
        raw_records.append({"semilla": seed, "algoritmo": "NSGA-II", "hipervolumen": hv_nsga, "spread": sp_nsga, "tiempo_s": t_nsga})

        # 2. Greedy Baseline (Determinista con presupuesto)
        t0 = time.time()
        greedy = GreedyOrienteering(problem)
        frente_greedy = greedy.generate_greedy_front(step_minutes=15.0)
        pts_greedy = [(s["total_time"], s["score"]) for s in frente_greedy]
        t_greedy = time.time() - t0
        hv_greedy = calcular_hipervolumen(pts_greedy, ref_point=(problem.t_max, 0.0))
        sp_greedy = calcular_spread(pts_greedy)
        results["Greedy"]["hipervolumen"].append(hv_greedy)
        results["Greedy"]["spread"].append(sp_greedy)
        results["Greedy"]["tiempo_segundos"].append(t_greedy)
        raw_records.append({"semilla": seed, "algoritmo": "Greedy", "hipervolumen": hv_greedy, "spread": sp_greedy, "tiempo_s": t_greedy})

        # 3. Random Search Baseline
        t0 = time.time()
        random_search = RandomSearchOrienteering(problem, total_evaluations=15000)
        frente_rs = random_search.run()
        pts_rs = [(ind.total_time, ind.score) for ind in frente_rs]
        t_rs = time.time() - t0
        hv_rs = calcular_hipervolumen(pts_rs, ref_point=(problem.t_max, 0.0))
        sp_rs = calcular_spread(pts_rs)
        results["Random Search"]["hipervolumen"].append(hv_rs)
        results["Random Search"]["spread"].append(sp_rs)
        results["Random Search"]["tiempo_segundos"].append(t_rs)
        raw_records.append({"semilla": seed, "algoritmo": "Random Search", "hipervolumen": hv_rs, "spread": sp_rs, "tiempo_s": t_rs})

        # 4. Weighted Sum GA Baseline
        t0 = time.time()
        ws_ga = WeightedSumGA(problem, pop_size=30, generations=40)
        frente_ws = ws_ga.run()
        pts_ws = [(ind.total_time, ind.score) for ind in frente_ws]
        t_ws = time.time() - t0
        hv_ws = calcular_hipervolumen(pts_ws, ref_point=(problem.t_max, 0.0))
        sp_ws = calcular_spread(pts_ws)
        results["Weighted Sum"]["hipervolumen"].append(hv_ws)
        results["Weighted Sum"]["spread"].append(sp_ws)
        results["Weighted Sum"]["tiempo_segundos"].append(t_ws)
        raw_records.append({"semilla": seed, "algoritmo": "Weighted Sum", "hipervolumen": hv_ws, "spread": sp_ws, "tiempo_s": t_ws})

    # Guardar CSV crudo
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df_raw = pd.DataFrame(raw_records)
    csv_path = OUTPUT_DIR / "resultados_estadisticos_semillas.csv"
    df_raw.to_csv(csv_path, index=False)

    # Análisis estadístico y tests de Wilcoxon
    summary_report: Dict[str, Any] = {"algoritmos": {}}
    hv_nsga_samples = results["NSGA-II"]["hipervolumen"]

    for algo in algorithms:
        stats_hv = resumen_estadistico(results[algo]["hipervolumen"])
        stats_sp = resumen_estadistico(results[algo]["spread"])
        stats_time = resumen_estadistico(results[algo]["tiempo_segundos"])

        wilcoxon = None
        if algo != "NSGA-II":
            wilcoxon = test_wilcoxon(hv_nsga_samples, results[algo]["hipervolumen"])

        summary_report["algoritmos"][algo] = {
            "hipervolumen": stats_hv,
            "spread": stats_sp,
            "tiempo_segundos": stats_time,
            "test_wilcoxon_vs_nsga2": wilcoxon,
        }

    json_path = OUTPUT_DIR / "resumen_estadistico.json"
    with open(json_path, "w", encoding="utf-8") as f:
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
