"""Análisis de sensibilidad de NSGA-II a los tiempos de visita y a las puntuaciones de los POIs.

Para cada hotel repite NSGA-II (configuración por defecto, 20.100 evaluaciones) con las 15 semillas
del benchmark en cinco variantes de los datos:
- base: puntuaciones y tiempos de visita de data/<escenario>/puntos_interes.csv.
- visitas_x075 y visitas_x050: todos los tiempos de visita multiplicados por 0,75 y 0,5.
- puntuacion_uniforme: todos los POIs con la misma puntuación (la media del catálogo), de modo que
  solo cuenta el número de paradas.
- puntuacion_cuadratica: s^2 / 10, que conserva el 10 y castiga las puntuaciones medias
  (7 -> 4,9), así que pesan más los lugares icónicos.

La matriz de tiempos de conducción y el límite de 8 h no cambian. Cada corrida fija la semilla igual
que la batería estadística, por lo que la variante base reproduce su hipervolumen.

Genera en output/<escenario>/:
- sensibilidad.csv: por variante, hipervolumen (media y desviación poblacional), número de
  soluciones del frente, puntuación máxima (en la escala de la variante y en la original) y tiempo
  de la ruta de mayor puntuación, más las paradas de las 3 rutas recomendadas con la semilla 42.
- sensibilidad_pois.csv: por variante y POI, % de semillas en las que el POI aparece en alguna
  solución del frente y % de soluciones del frente (todas las semillas juntas) que lo contienen.

Uso: python scripts/sensitivity_analysis.py [--escenario santa_catalina] [--jobs 4]
"""
import argparse
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from src.algorithms.genetic_algorithm import NSGA2Orienteering, seleccionar_3_opciones_turisticas  # noqa: E402
from src.core.metrics import calcular_hipervolumen, resumen_estadistico  # noqa: E402
from src.core.problem import GAConfig, OrienteeringProblem  # noqa: E402
from src.pipeline import ESCENARIOS, create_problem_instance, load_distance_matrix, scenario_output_dir  # noqa: E402

SEEDS = [42, 101, 203, 314, 456, 578, 619, 723, 831, 954, 1024, 1234, 2048, 3072, 4096]
ROUTE_SEED = 42


def _uniform_scores(p: OrienteeringProblem) -> OrienteeringProblem:
    pois = np.arange(p.node_count) != p.depot_idx
    scores = np.where(pois, p.scores[pois].mean(), 0.0)
    return replace(p, scores=scores)


VARIANTS: Dict[str, Callable[[OrienteeringProblem], OrienteeringProblem]] = {
    "base": lambda p: p,
    "visitas_x075": lambda p: replace(p, visit_times=p.visit_times * 0.75),
    "visitas_x050": lambda p: replace(p, visit_times=p.visit_times * 0.5),
    "puntuacion_uniforme": _uniform_scores,
    "puntuacion_cuadratica": lambda p: replace(p, scores=p.scores ** 2 / 10.0),
}


def load_problem(scenario: str) -> Tuple[OrienteeringProblem, List[str]]:
    matrix, names = load_distance_matrix(scenario)
    return create_problem_instance(matrix, names, ESCENARIOS[scenario], scenario, t_max=480.0), names


def run_one(scenario: str, variant: str, seed: int) -> Tuple[str, int, List[Tuple[List[int], float, float]], Optional[Dict[str, List[int]]]]:
    base, _ = load_problem(scenario)
    problem = VARIANTS[variant](base)
    random.seed(seed)
    np.random.seed(seed)
    front = NSGA2Orienteering(problem, GAConfig()).evolve()
    solutions = [(list(ind.genes), ind.total_time, ind.score) for ind in front]
    routes = None
    if seed == ROUTE_SEED:
        express, balanced, exhaustive = seleccionar_3_opciones_turisticas(front)
        routes = {"express": express.genes, "equilibrada": balanced.genes, "exhaustiva": exhaustive.genes}
    return variant, seed, solutions, routes


def _route_label(genes: List[int], names: List[str]) -> str:
    return " > ".join(names[g] for g in genes)


def summarize_variant(
    variant: str,
    runs: Dict[int, List[Tuple[List[int], float, float]]],
    routes: Dict[str, List[int]],
    base: OrienteeringProblem,
    names: List[str],
) -> Dict[str, object]:
    hv = [calcular_hipervolumen([(t, s) for _, t, s in runs[seed]], ref_point=(base.t_max, 0.0)) for seed in SEEDS]
    best = [max(runs[seed], key=lambda sol: sol[2]) for seed in SEEDS]
    hv_stats = resumen_estadistico(hv)
    return {
        "variante": variant,
        "hv_media": round(hv_stats["mean"], 2),
        "hv_std": round(hv_stats["std"], 2),
        "soluciones_frente_media": round(float(np.mean([len(runs[s]) for s in SEEDS])), 2),
        "puntuacion_max_media": round(float(np.mean([s for _, _, s in best])), 2),
        "puntuacion_original_max_media": round(float(np.mean([base.scores[g].sum() for g, _, _ in best])), 2),
        "tiempo_ruta_max_media": round(float(np.mean([t for _, t, _ in best])), 2),
        "paradas_ruta_max_media": round(float(np.mean([len(g) for g, _, _ in best])), 2),
        **{f"ruta_{k}_semilla{ROUTE_SEED}": _route_label(v, names) for k, v in routes.items()},
    }


def poi_frequencies(variant: str, runs: Dict[int, List[Tuple[List[int], float, float]]], base: OrienteeringProblem, names: List[str]) -> List[Dict[str, object]]:
    all_solutions = [genes for seed in SEEDS for genes, _, _ in runs[seed]]
    rows = []
    for poi in base.available_nodes():
        seeds_with = sum(any(poi in genes for genes, _, _ in runs[seed]) for seed in SEEDS)
        rows.append({
            "variante": variant,
            "poi": names[poi],
            "puntuacion": base.scores[poi],
            "tiempo_visita_min": base.visit_times[poi],
            "pct_semillas": round(100.0 * seeds_with / len(SEEDS), 1),
            "pct_soluciones": round(100.0 * sum(poi in g for g in all_solutions) / len(all_solutions), 1),
        })
    return rows


def run_scenario(scenario: str, jobs: Optional[int]) -> None:
    base, names = load_problem(scenario)
    tasks = [(scenario, v, s) for v in VARIANTS for s in SEEDS]
    runs: Dict[str, Dict[int, List[Tuple[List[int], float, float]]]] = {v: {} for v in VARIANTS}
    routes: Dict[str, Dict[str, List[int]]] = {}
    print(f"\n##### {scenario}: {len(VARIANTS)} variantes x {len(SEEDS)} semillas = {len(tasks)} corridas #####")
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for variant, seed, solutions, seed_routes in pool.map(run_one, *zip(*tasks)):
            runs[variant][seed] = solutions
            if seed_routes is not None:
                routes[variant] = seed_routes

    out_dir = scenario_output_dir(scenario)
    summary = pd.DataFrame([summarize_variant(v, runs[v], routes[v], base, names) for v in VARIANTS])
    pois = pd.DataFrame([row for v in VARIANTS for row in poi_frequencies(v, runs[v], base, names)])
    summary.to_csv(out_dir / "sensibilidad.csv", index=False)
    pois.to_csv(out_dir / "sensibilidad_pois.csv", index=False)
    print(summary.iloc[:, :8].to_string(index=False))
    print(f"Guardado en {(out_dir / 'sensibilidad.csv').relative_to(BASE_DIR)} y sensibilidad_pois.csv")


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Análisis de sensibilidad de NSGA-II")
    parser.add_argument("--escenario", choices=list(ESCENARIOS), default=None,
                        help="Escenario (hotel). Por defecto, todos.")
    parser.add_argument("--jobs", type=int, default=None, help="Procesos en paralelo (por defecto, todos los núcleos).")
    args = parser.parse_args(argv)
    for scenario in ([args.escenario] if args.escenario else list(ESCENARIOS)):
        run_scenario(scenario, args.jobs)


if __name__ == "__main__":
    main()
