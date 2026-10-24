import json
import random
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from .core.problem import OrienteeringProblem, GAConfig, Individual
from .core.metrics import calcular_hipervolumen
from .algorithms.genetic_algorithm import NSGA2Orienteering, seleccionar_3_opciones_turisticas
from .algorithms.greedy_algorithm import GreedyOrienteering


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# Escenarios: carpeta dentro de data/ -> nombre del nodo hotel (depósito) en la matriz.
ESCENARIOS: Dict[str, str] = {
    "santa_catalina": "Hotel Santa Catalina (Las Palmas)",
    "lopesan_villa_del_conde": "Hotel Lopesan Villa del Conde",
}


def _resolve_data_path(filename: str, scenario: str) -> Path:
    if scenario not in ESCENARIOS:
        raise ValueError(f"Escenario desconocido '{scenario}'. Disponibles: {list(ESCENARIOS)}")
    return DATA_DIR / scenario / filename


def scenario_output_dir(scenario: str) -> Path:
    return OUTPUT_DIR / scenario


def load_poi_catalog(scenario: str, filename: str = "puntos_interes.csv") -> Dict[str, Dict[str, float]]:
    filepath = _resolve_data_path(filename, scenario)
    df = pd.read_csv(filepath)
    col_name = next((c for c in df.columns if any(k in c.lower() for k in ["nomb", "poi", "lugar"])), df.columns[0])
    col_score = next((c for c in df.columns if any(k in c.lower() for k in ["punt", "score", "valor"])), df.columns[1])
    col_visit = next((c for c in df.columns if any(k in c.lower() for k in ["visit", "estanc", "tiempo"])), df.columns[2])
    return {
        str(row[col_name]): {"score": float(row[col_score]), "visita": float(row[col_visit])}
        for _, row in df.iterrows()
    }


def load_coordinates(scenario: str, filename: str = "coordenadas.csv") -> Dict[str, Dict[str, float]]:
    filepath = _resolve_data_path(filename, scenario)
    if not filepath.exists():
        return {}
    df = pd.read_csv(filepath)
    col_name = next((c for c in df.columns if any(k in c.lower() for k in ["nomb", "poi", "lugar"])), df.columns[0])
    col_lat = next((c for c in df.columns if "lat" in c.lower()), df.columns[1])
    col_lon = next((c for c in df.columns if any(k in c.lower() for k in ["lon", "lng"])), df.columns[2])
    return {
        str(row[col_name]): {"lat": float(row[col_lat]), "lon": float(row[col_lon])}
        for _, row in df.iterrows()
    }


def load_distance_matrix(scenario: str, filename: str = "matriz_tiempos.csv") -> Tuple[np.ndarray, List[str]]:
    filepath = _resolve_data_path(filename, scenario)
    df = pd.read_csv(filepath, index_col=0)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    broken_nodes = df.index[df.isnull().any(axis=1)].tolist()
    clean_df = df.drop(index=broken_nodes, columns=broken_nodes) if broken_nodes else df
    return clean_df.to_numpy(), clean_df.index.tolist()


def create_problem_instance(
    matrix: np.ndarray,
    node_names: List[str],
    depot_name: str,
    scenario: str,
    t_max: float = 480.0,
    poi_filename: str = "puntos_interes.csv",
) -> OrienteeringProblem:
    if depot_name not in node_names:
        raise ValueError(f"El depósito '{depot_name}' no está en la matriz de tiempos.")
    depot_idx = node_names.index(depot_name)
    catalog = load_poi_catalog(scenario, poi_filename)
    missing = [n for n in node_names if n not in catalog]
    if missing:
        raise ValueError(f"Los siguientes nodos no existen en el catalogo de POIs: {missing}")
    scores = np.array([catalog[n]["score"] for n in node_names])
    visits = np.array([catalog[n]["visita"] for n in node_names])
    return OrienteeringProblem(matrix, scores, visits, depot_idx, t_max)


def _build_leg_detail(
    k: int,
    origin: int,
    destination: int,
    is_last_leg: bool,
    problem: OrienteeringProblem,
    names: List[str],
    coords: Dict[str, Dict[str, float]],
) -> Dict[str, Any]:
    driving = problem.driving_time(origin, destination)
    visiting = 0.0 if is_last_leg else float(problem.visit_times[destination])
    score = 0.0 if is_last_leg else float(problem.scores[destination])
    dest_name = names[destination]
    leg_info: Dict[str, Any] = {
        "tramo": k + 1,
        "origen": names[origin],
        "destino": dest_name,
        "tiempo_conduccion_min": round(driving, 2),
        "tiempo_estancia_min": round(visiting, 2),
        "score_parada": round(score, 2),
    }
    if dest_name in coords:
        leg_info["coordenadas_destino"] = coords[dest_name]
    return leg_info


def serialize_route(
    ind: Optional[Individual],
    label: str,
    problem: OrienteeringProblem,
    names: List[str],
    scenario: str,
) -> Dict[str, Any]:
    if not ind:
        return {}
    stops = ind.genes
    route = [problem.depot_idx] + stops + [problem.depot_idx]
    coords = load_coordinates(scenario)
    tramos = [
        _build_leg_detail(k, route[k], route[k + 1], k == len(stops), problem, names, coords)
        for k in range(len(route) - 1)
    ]
    stops_info = [
        {"nombre": names[i], **({"coordenadas": coords[names[i]]} if names[i] in coords else {})}
        for i in stops
    ]
    return {
        "tipo_opcion": label,
        "puntuacion_total": round(ind.score, 2),
        "tiempo_total_min": round(ind.total_time, 2),
        "tiempo_total_horas": round(ind.total_time / 60.0, 2),
        "tiempo_conduccion_min": round(ind.driving_time, 2),
        "tiempo_visitas_min": round(ind.visiting_time, 2),
        "eficiencia_score_hora": round(ind.score / max(0.1, ind.total_time / 60.0), 2),
        "numero_paradas": len(stops),
        "paradas_ordenadas": [names[i] for i in stops],
        "paradas_detalle": stops_info,
        "itinerario_completo": [names[problem.depot_idx]] + [names[i] for i in stops] + [names[problem.depot_idx]],
        "detalle_tramos": tramos,
    }


def export_results_json(
    filepath: Path,
    problem: OrienteeringProblem,
    names: List[str],
    hv_nsga2: float,
    hv_greedy: float,
    express: Optional[Individual],
    balanced: Optional[Individual],
    exhaustive: Optional[Individual],
    pareto_front: List[Individual],
    scenario: str,
) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "proyecto": "Optimización Multiobjetivo de Rutas Turísticas en Gran Canaria",
        "asignatura": "Optimización y Heurística",
        "algoritmo": "NSGA-II (Deb et al., 2002)",
        "baseline_comparado": "Greedy Multi-Objetivo",
        "origen_destino_depot": names[problem.depot_idx],
        "tiempo_maximo_minutos": problem.t_max,
        "metricas_comparativas": {
            "hipervolumen_nsga2": round(hv_nsga2, 2),
            "hipervolumen_greedy": round(hv_greedy, 2),
            "mejora_porcentual_hv": round(((hv_nsga2 - hv_greedy) / max(1.0, hv_greedy)) * 100.0, 2),
        },
        "opciones_recomendadas": {
            "express": serialize_route(express, "Opción Express", problem, names, scenario),
            "equilibrada": serialize_route(balanced, "Opción Equilibrada", problem, names, scenario),
            "exhaustiva": serialize_route(exhaustive, "Opción Exhaustiva", problem, names, scenario),
        },
        "frente_pareto_completo": [
            {
                "score": round(ind.score, 2),
                "tiempo_total_min": round(ind.total_time, 2),
                "paradas": [names[i] for i in ind.genes],
            }
            for ind in sorted(pareto_front, key=lambda x: x.total_time)
        ],
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def plot_pareto_comparison(
    filepath: Path,
    nsga_front: List[Individual],
    greedy_front: List[Dict[str, Any]],
    hv_nsga: float,
    hv_greedy: float,
    t_max: float,
    express: Optional[Individual],
    balanced: Optional[Individual],
    exhaustive: Optional[Individual],
) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 6))

    tg = [s["total_time"] / 60.0 for s in greedy_front]
    sg = [s["score"] for s in greedy_front]
    plt.plot(tg, sg, color="#8e44ad", linestyle="--", linewidth=1.8, label=f"Baseline Greedy (HV = {hv_greedy:.0f})")
    plt.scatter(tg, sg, color="#8e44ad", marker="s", s=50)

    tn = [ind.total_time / 60.0 for ind in nsga_front]
    sn = [ind.score for ind in nsga_front]
    improvement = ((hv_nsga - hv_greedy) / max(1.0, hv_greedy)) * 100.0
    plt.scatter(tn, sn, color="#2980b9", alpha=0.6, s=65, label=f"Frente NSGA-II (HV = {hv_nsga:.0f}, +{improvement:.1f}%)")

    if express:
        plt.scatter([express.total_time / 60.0], [express.score], color="#27ae60", s=180, edgecolors="black", zorder=6, label=f"Express ({express.score:.1f} pts, {express.total_time/60:.1f}h)")
    if balanced:
        plt.scatter([balanced.total_time / 60.0], [balanced.score], color="#e67e22", s=180, edgecolors="black", zorder=6, label=f"Equilibrada ({balanced.score:.1f} pts, {balanced.total_time/60:.1f}h)")
    if exhaustive:
        plt.scatter([exhaustive.total_time / 60.0], [exhaustive.score], color="#c0392b", s=180, edgecolors="black", zorder=6, label=f"Exhaustiva ({exhaustive.score:.1f} pts, {exhaustive.total_time/60:.1f}h)")

    plt.axvline(x=t_max / 60.0, color="red", linestyle=":", linewidth=1.5, label=f"Límite T_max ({t_max/60:.1f}h)")
    plt.title("Comparativa de Optimización: Frente de Pareto NSGA-II vs Baseline Voraz", fontsize=12, fontweight="bold")
    plt.xlabel("Tiempo Total de Viaje (horas)", fontsize=11)
    plt.ylabel("Puntuación Turística Total (Score)", fontsize=11)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper left", framealpha=0.9)
    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()


def plot_convergence(
    filepath: Path,
    history_hv: List[float],
    history_score: List[float],
    hv_greedy: float,
) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(11, 5))

    plt.subplot(1, 2, 1)
    plt.plot(range(1, len(history_hv) + 1), history_hv, color="#2980b9", linewidth=2.0)
    plt.axhline(y=hv_greedy, color="#8e44ad", linestyle="--", label=f"HV Greedy ({hv_greedy:.0f})")
    plt.title("Convergencia del Hipervolumen (HV)", fontsize=11, fontweight="bold")
    plt.xlabel("Generación", fontsize=10)
    plt.ylabel("Hipervolumen", fontsize=10)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="lower right")

    plt.subplot(1, 2, 2)
    plt.plot(range(1, len(history_score) + 1), history_score, color="#27ae60", linewidth=2.0)
    plt.title("Evolución del Mejor Score Factible", fontsize=11, fontweight="bold")
    plt.xlabel("Generación", fontsize=10)
    plt.ylabel("Puntuación Turística Máxima", fontsize=10)
    plt.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()


def run_pipeline(scenario: str, seed: int = 42) -> None:
    """Ejecuta el pipeline de un escenario (hotel de data/<scenario>/)."""
    random.seed(seed)
    np.random.seed(seed)

    out_dir = scenario_output_dir(scenario)
    matrix, names = load_distance_matrix(scenario)
    problem = create_problem_instance(matrix, names, depot_name=ESCENARIOS[scenario], scenario=scenario, t_max=480.0)

    greedy = GreedyOrienteering(problem)
    greedy_front = greedy.generate_greedy_front(step_minutes=15.0)
    pts_greedy = [(s["total_time"], s["score"]) for s in greedy_front]
    hv_greedy = calcular_hipervolumen(pts_greedy, ref_point=(problem.t_max, 0.0))

    nsga2 = NSGA2Orienteering(problem, GAConfig(population_size=100, generations=200))
    pareto_front = nsga2.evolve()
    pts_nsga2 = [(ind.total_time, ind.score) for ind in pareto_front]
    hv_nsga2 = calcular_hipervolumen(pts_nsga2, ref_point=(problem.t_max, 0.0))

    express, balanced, exhaustive = seleccionar_3_opciones_turisticas(pareto_front)

    export_results_json(
        out_dir / "rutas_pareto.json",
        problem,
        names,
        hv_nsga2,
        hv_greedy,
        express,
        balanced,
        exhaustive,
        pareto_front,
        scenario,
    )

    plot_pareto_comparison(
        out_dir / "comparativa_pareto_vs_greedy.png",
        pareto_front,
        greedy_front,
        hv_nsga2,
        hv_greedy,
        problem.t_max,
        express,
        balanced,
        exhaustive,
    )

    plot_convergence(
        out_dir / "convergencia_nsga2.png",
        nsga2.history_hypervolume,
        nsga2.history_best_score,
        hv_greedy,
    )

    improvement = ((hv_nsga2 - hv_greedy) / max(1.0, hv_greedy)) * 100.0
    print(f"Benchmarking completado: NSGA-II HV={hv_nsga2:.1f} vs Greedy HV={hv_greedy:.1f} (+{improvement:.1f}%)")
    print(f"Archivos exportados exitosamente en '{out_dir.relative_to(BASE_DIR)}/'")
