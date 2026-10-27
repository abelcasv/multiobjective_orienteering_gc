"""Estudio de hiperparámetros de NSGA-II con el mismo presupuesto de 20.100 evaluaciones.

Para cada hotel prueba, con las 15 semillas del benchmark (src/benchmarks/statistical_suite.py):
- Población y generaciones con N + N*G = 20.100: (50, 401), (100, 200), (150, 133), (300, 66),
  con la probabilidad de cruce y de mutación actuales (0,85 y 0,35).
- Rejilla completa de probabilidad de cruce {0,6; 0,85; 0,95} x mutación {0,15; 0,35; 0,55}
  con la población y las generaciones actuales (100, 200).

Solo se usan poblaciones pares: _create_offspring genera los hijos de dos en dos, así que con N
impar evalúa un hijo de más por generación y el presupuesto dejaría de ser 20.100.

Cada corrida fija random.seed(semilla) y np.random.seed(semilla) justo antes de ejecutar NSGA-II,
igual que la batería estadística, por lo que la configuración actual reproduce su hipervolumen.

Genera output/<escenario>/hiperparametros.csv con, por combinación, el hipervolumen medio, su
desviación típica poblacional (np.std), la mediana y el p-valor del test de Wilcoxon pareado
frente a la configuración actual.

Uso: python scripts/hyperparameter_study.py [--escenario santa_catalina] [--jobs 4]
"""
import argparse
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from src.algorithms.genetic_algorithm import NSGA2Orienteering  # noqa: E402
from src.core.metrics import calcular_hipervolumen, resumen_estadistico, test_wilcoxon  # noqa: E402
from src.core.problem import GAConfig  # noqa: E402
from src.pipeline import ESCENARIOS, create_problem_instance, load_distance_matrix, scenario_output_dir  # noqa: E402

SEEDS = [42, 101, 203, 314, 456, 578, 619, 723, 831, 954, 1024, 1234, 2048, 3072, 4096]
BUDGET = 20100
DEFAULT = GAConfig()
POP_GENS = [(50, 401), (100, 200), (150, 133), (300, 66)]
CROSSOVER_RATES = [0.6, 0.85, 0.95]
MUTATION_RATES = [0.15, 0.35, 0.55]

# (población, generaciones, p_cruce, p_mutación)
Combo = Tuple[int, int, float, float]


def build_combos() -> List[Combo]:
    combos: List[Combo] = [(n, g, DEFAULT.crossover_rate, DEFAULT.mutation_rate) for n, g in POP_GENS]
    for pc in CROSSOVER_RATES:
        for pm in MUTATION_RATES:
            combo = (DEFAULT.population_size, DEFAULT.generations, pc, pm)
            if combo not in combos:
                combos.append(combo)
    for n, g, _, _ in combos:
        assert n % 2 == 0 and n + n * g == BUDGET, f"({n}, {g}) no da {BUDGET} evaluaciones"
    return combos


def run_one(scenario: str, combo: Combo, seed: int) -> Tuple[Combo, int, float, float]:
    matrix, names = load_distance_matrix(scenario)
    problem = create_problem_instance(matrix, names, ESCENARIOS[scenario], scenario, t_max=480.0)
    n, g, pc, pm = combo
    config = GAConfig(population_size=n, generations=g, crossover_rate=pc, mutation_rate=pm)
    random.seed(seed)
    np.random.seed(seed)
    t0 = time.time()
    front = NSGA2Orienteering(problem, config).evolve()
    hv = calcular_hipervolumen([(ind.total_time, ind.score) for ind in front], ref_point=(problem.t_max, 0.0))
    return combo, seed, hv, time.time() - t0


def summarize(combos: List[Combo], hv: Dict[Combo, Dict[int, float]], secs: Dict[Combo, List[float]]) -> pd.DataFrame:
    default = (DEFAULT.population_size, DEFAULT.generations, DEFAULT.crossover_rate, DEFAULT.mutation_rate)
    ref = [hv[default][s] for s in SEEDS]
    rows = []
    for combo in combos:
        sample = [hv[combo][s] for s in SEEDS]
        stats = resumen_estadistico(sample)
        n, g, pc, pm = combo
        rows.append({
            "poblacion": n,
            "generaciones": g,
            "p_cruce": pc,
            "p_mutacion": pm,
            "evaluaciones": n + n * g,
            "hv_media": round(stats["mean"], 2),
            "hv_std": round(stats["std"], 2),
            "hv_mediana": round(stats["median"], 2),
            "hv_min": round(stats["min"], 2),
            "hv_max": round(stats["max"], 2),
            "p_wilcoxon_vs_actual": None if combo == default else test_wilcoxon(sample, ref)["p_value"],
            "tiempo_medio_s": round(float(np.mean(secs[combo])), 2),
            "es_actual": combo == default,
        })
    return pd.DataFrame(rows)


def run_scenario(scenario: str, jobs: int) -> pd.DataFrame:
    combos = build_combos()
    tasks = [(scenario, c, s) for c in combos for s in SEEDS]
    hv: Dict[Combo, Dict[int, float]] = {c: {} for c in combos}
    secs: Dict[Combo, List[float]] = {c: [] for c in combos}
    print(f"\n##### {scenario}: {len(combos)} combinaciones x {len(SEEDS)} semillas = {len(tasks)} corridas #####")
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for k, (combo, seed, value, elapsed) in enumerate(pool.map(run_one, *zip(*tasks)), start=1):
            hv[combo][seed] = value
            secs[combo].append(elapsed)
            if k % len(SEEDS) == 0:
                print(f"    {k}/{len(tasks)} corridas")

    df = summarize(combos, hv, secs)
    out_path = scenario_output_dir(scenario) / "hiperparametros.csv"
    df.to_csv(out_path, index=False)
    print(df.drop(columns=["hv_mediana", "hv_min", "hv_max"]).to_string(index=False))
    print(f"Guardado en {out_path.relative_to(BASE_DIR)}")
    return df


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Estudio de hiperparámetros de NSGA-II")
    parser.add_argument("--escenario", choices=list(ESCENARIOS), default=None,
                        help="Escenario (hotel). Por defecto, todos.")
    parser.add_argument("--jobs", type=int, default=None, help="Procesos en paralelo (por defecto, todos los núcleos).")
    args = parser.parse_args(argv)
    for scenario in ([args.escenario] if args.escenario else list(ESCENARIOS)):
        run_scenario(scenario, args.jobs)


if __name__ == "__main__":
    main()
