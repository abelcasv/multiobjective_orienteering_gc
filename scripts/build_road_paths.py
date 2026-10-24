"""Calcula el recorrido por carretera de las rutas recomendadas de cada hotel.

Para cada tramo de output/<escenario>/rutas_pareto.json busca el camino mínimo en la red
de OpenStreetMap con la misma penalización por curvas que scripts/build_time_matrix.ipynb
y lo guarda en output/<escenario>/caminos_rutas.json, que usa scripts/make_maps.py.
El factor global de calibración multiplica todos los tiempos por igual, así que no
cambia el camino y no hace falta aplicarlo.

Si no se pasa --k, se elige el K candidato cuyos tiempos reproducen mejor
data/auxiliar/Matriz_sin_factor_global.csv (la matriz del notebook antes del factor).

Uso: python scripts/build_road_paths.py [--k 700 | --k ninguno] [--escenario santa_catalina]
Requiere osmnx y scikit-learn (pip install osmnx scikit-learn). El grafo se guarda en
gran_canaria_drive.graphml en la raíz del repo y se reutiliza en siguientes ejecuciones.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from src.pipeline import DATA_DIR, ESCENARIOS, load_coordinates, scenario_output_dir  # noqa: E402

GRAFO_PATH = BASE_DIR / "gran_canaria_drive.graphml"
RAW_MATRIX_PATH = DATA_DIR / "auxiliar" / "Matriz_sin_factor_global.csv"

# Mismos parámetros que las celdas 4a y 4b del notebook.
K_CANDIDATOS: List[Optional[float]] = [None, 3000, 1500, 1000, 700, 500, 350]
VEL_MIN_KMH = 15.0
LONG_MIN_M = 50.0


def load_graph() -> nx.MultiDiGraph:
    if GRAFO_PATH.exists():
        print(f"Grafo cargado desde {GRAFO_PATH.name}")
        return ox.load_graphml(GRAFO_PATH)
    print("Descargando la red de carreteras de Gran Canaria (un par de minutos)...")
    graph = ox.graph_from_place("Gran Canaria, Spain", network_type="drive")
    graph = ox.truncate.largest_component(graph, strongly=True)
    graph = ox.add_edge_speeds(graph)
    graph = ox.add_edge_travel_times(graph)
    ox.save_graphml(graph, GRAFO_PATH)
    return graph


def _edge_points(graph: nx.MultiDiGraph, u: int, v: int, data: Dict[str, Any]) -> List[Tuple[float, float]]:
    """Puntos (lon, lat) del tramo u -> v, orientados de u a v."""
    geom = data.get("geometry")
    if geom is None:
        return [(graph.nodes[u]["x"], graph.nodes[u]["y"]), (graph.nodes[v]["x"], graph.nodes[v]["y"])]
    pts = list(geom.coords)
    start_u = np.hypot(pts[0][0] - graph.nodes[u]["x"], pts[0][1] - graph.nodes[u]["y"])
    start_v = np.hypot(pts[0][0] - graph.nodes[v]["x"], pts[0][1] - graph.nodes[v]["y"])
    return pts if start_u <= start_v else pts[::-1]


def curvatura_deg_km(graph: nx.MultiDiGraph, u: int, v: int, data: Dict[str, Any]) -> float:
    largo = data.get("length", 0.0) or 0.0
    if largo < LONG_MIN_M:
        return 0.0
    pts = _edge_points(graph, u, v, data)
    if len(pts) < 3:
        return 0.0
    lat0 = np.radians(np.mean([p[1] for p in pts]))
    xy = np.array([[(p[0] - pts[0][0]) * 111_320 * np.cos(lat0),
                    (p[1] - pts[0][1]) * 110_574] for p in pts])
    d = np.diff(xy, axis=0)
    d = d[np.hypot(d[:, 0], d[:, 1]) > 1.0]
    if len(d) < 2:
        return 0.0
    rumbo = np.arctan2(d[:, 1], d[:, 0])
    giro = np.abs((np.diff(rumbo) + np.pi) % (2 * np.pi) - np.pi)
    return min(float(np.degrees(giro).sum()) / (largo / 1000.0), 3000.0)


def apply_penalty(graph: nx.MultiDiGraph, k: Optional[float]) -> None:
    for _, _, data in graph.edges(data=True):
        vel = data["speed_kph"]
        if k is not None:
            vel = max(vel / (1 + data["curv_deg_km"] / k), min(VEL_MIN_KMH, vel))
        data["travel_time"] = data["length"] / (vel * 1000 / 3600)


def snap_nodes(graph: nx.MultiDiGraph, coords: Dict[str, Dict[str, float]]) -> Dict[str, int]:
    names = list(coords)
    nodes = ox.distance.nearest_nodes(graph, X=[coords[n]["lon"] for n in names], Y=[coords[n]["lat"] for n in names])
    return dict(zip(names, (int(n) for n in nodes)))


def matrix_error(graph: nx.MultiDiGraph, node_of: Dict[str, int], raw: pd.DataFrame) -> float:
    names = [n for n in raw.index if n in node_of]
    errors = []
    for origin in names:
        times = nx.single_source_dijkstra_path_length(graph, node_of[origin], weight="travel_time")
        errors.extend(abs(times[node_of[dest]] / 60.0 - raw.loc[origin, dest]) for dest in names if dest != origin)
    return float(np.mean(errors))


def choose_k(graph: nx.MultiDiGraph, node_of: Dict[str, int]) -> Optional[float]:
    raw = pd.read_csv(RAW_MATRIX_PATH, index_col=0)
    print("Error medio frente a la matriz del notebook (sin factor global) para cada K:")
    best_k, best_err = None, float("inf")
    for k in K_CANDIDATOS:
        apply_penalty(graph, k)
        err = matrix_error(graph, node_of, raw)
        print(f"  K = {'ninguno' if k is None else k:>7}: {err:6.2f} min")
        if err < best_err:
            best_k, best_err = k, err
    print(f"K elegido: {'ninguno' if best_k is None else best_k}")
    return best_k


def _leg_path(graph: nx.MultiDiGraph, source: int, target: int) -> Tuple[List[List[float]], float]:
    nodes = nx.shortest_path(graph, source, target, weight="travel_time")
    coords: List[List[float]] = []
    seconds = 0.0
    for u, v in zip(nodes[:-1], nodes[1:]):
        data = min(graph.get_edge_data(u, v).values(), key=lambda d: d["travel_time"])
        seconds += data["travel_time"]
        pts = [[round(lat, 6), round(lon, 6)] for lon, lat in _edge_points(graph, u, v, data)]
        coords.extend(pts[1:] if coords else pts)
    return coords, seconds / 60.0


def build_scenario_paths(graph: nx.MultiDiGraph, scenario: str, node_of: Dict[str, int],
                         raw: pd.DataFrame, k: Optional[float]) -> Path:
    out_dir = scenario_output_dir(scenario)
    with open(out_dir / "rutas_pareto.json", encoding="utf-8") as f:
        routes = json.load(f)["opciones_recomendadas"]

    result: Dict[str, Any] = {
        "fuente": "© colaboradores de OpenStreetMap (ODbL)",
        "penalizacion_curvas_k": k,
        "rutas": {},
    }
    for key, route in routes.items():
        if not route:
            continue
        itinerary = route["itinerario_completo"]
        legs = []
        for origin, dest in zip(itinerary[:-1], itinerary[1:]):
            coords, minutes = _leg_path(graph, node_of[origin], node_of[dest])
            legs.append({
                "origen": origin,
                "destino": dest,
                "tiempo_red_min": round(minutes, 2),
                "tiempo_matriz_sin_factor_min": float(raw.loc[origin, dest]),
                "coordenadas": coords,
            })
        result["rutas"][key] = legs

    out_path = out_dir / "caminos_rutas.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    diffs = [abs(l["tiempo_red_min"] - l["tiempo_matriz_sin_factor_min"]) for legs in result["rutas"].values() for l in legs]
    print(f"{scenario}: {len(diffs)} tramos, diferencia máxima con la matriz {max(diffs):.2f} min -> "
          f"{out_path.relative_to(BASE_DIR)}")
    return out_path


def _parse_k(value: str) -> Any:
    if value == "auto":
        return value
    return None if value.lower() in ("ninguno", "none") else float(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Caminos por carretera de las rutas recomendadas")
    parser.add_argument("--k", type=_parse_k, default="auto",
                        help="K de la penalización por curvas ('ninguno' para no penalizar). Por defecto se deduce de la matriz.")
    parser.add_argument("--escenario", choices=list(ESCENARIOS), default=None,
                        help="Hotel base (carpeta de data/). Por defecto, todos.")
    args = parser.parse_args()

    graph = load_graph()
    for u, v, data in graph.edges(data=True):
        data["curv_deg_km"] = curvatura_deg_km(graph, u, v, data)

    coords: Dict[str, Dict[str, float]] = {}
    for scenario in ESCENARIOS:
        coords.update(load_coordinates(scenario))
    node_of = snap_nodes(graph, coords)

    k = choose_k(graph, node_of) if args.k == "auto" else args.k
    apply_penalty(graph, k)
    raw = pd.read_csv(RAW_MATRIX_PATH, index_col=0)
    for scenario in ([args.escenario] if args.escenario else list(ESCENARIOS)):
        build_scenario_paths(graph, scenario, node_of, raw, k)


if __name__ == "__main__":
    main()
