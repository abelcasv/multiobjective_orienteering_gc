"""Calcula el recorrido por carretera entre todos los pares ordenados de nodos de cada hotel.

Reutiliza scripts/build_road_paths.py: mismo grafo en caché (gran_canaria_drive.graphml),
misma penalización por curvas y mismo cálculo de cada tramo. El K se toma de
output/<escenario>/caminos_rutas.json (el que detectó build_road_paths.py); si no existe,
se vuelve a deducir de la matriz. Escribe output/<escenario>/caminos_todos_pares.json.gz
(JSON comprimido con gzip):

    {"fuente", "penalizacion_curvas_k", "simplificacion_m",
     "pares": {origen: {destino: {"tiempo_red_min", "coordenadas": [[lat, lon], ...]}}}}

Cada polilínea se simplifica con Douglas-Peucker (shapely, que instala osmnx), que siempre
conserva el primer y el último punto, y se redondea a 5 decimales. Lo usa dashboard.py para
dibujar cualquier ruta por carretera.

tiempo_red_min es el tiempo del camino en el grafo, sin factor global. Coincide con
data/auxiliar/Matriz_sin_factor_global.csv salvo en unos pares que salen del Mirador del
Balcón y de Los Azulejos de Veneguera, unos 0,7 min más largos (probablemente porque el
grafo en caché es una descarga de OSM posterior a la del notebook). No afecta al dibujo y
el dashboard usa los tiempos de la matriz, no estos.

Uso: python scripts/build_all_road_paths.py [--k 3000 | --k ninguno] [--simplificar 5]
                                            [--escenario santa_catalina]
Requiere osmnx y el grafo en caché (se descarga ejecutando antes scripts/build_road_paths.py).
"""
import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "scripts"))

try:
    import build_road_paths as brp  # noqa: E402
except ImportError as exc:  # osmnx, networkx o scikit-learn no instalados
    sys.exit(f"Falta una dependencia ({exc.name}). Instálala con: pip install -r requirements.txt")

from src.pipeline import ESCENARIOS, load_coordinates, load_distance_matrix, scenario_output_dir  # noqa: E402

from shapely.geometry import LineString  # noqa: E402

DECIMALES = 5
METROS_POR_GRADO = 111_320.0  # aproximado; basta para fijar la tolerancia de simplificación


def _k_detectado() -> Tuple[bool, Optional[float]]:
    """(encontrado, K) leído de algún caminos_rutas.json ya generado."""
    for scenario in ESCENARIOS:
        path = scenario_output_dir(scenario) / "caminos_rutas.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return True, json.load(f)["penalizacion_curvas_k"]
    return False, None


def _simplificar(coords: List[List[float]], metros: float) -> List[List[float]]:
    if metros <= 0 or len(coords) < 3:
        return coords
    return [list(p) for p in LineString(coords).simplify(metros / METROS_POR_GRADO).coords]


def _redondear(coords: List[List[float]]) -> List[List[float]]:
    out: List[List[float]] = []
    for lat, lon in coords:
        punto = [round(lat, DECIMALES), round(lon, DECIMALES)]
        if not out or out[-1] != punto:
            out.append(punto)
    return out


def build_scenario(graph: Any, scenario: str, node_of: Dict[str, int], k: Optional[float],
                   metros: float, cache: Dict[Tuple[str, str], Dict[str, Any]]) -> Path:
    _, names = load_distance_matrix(scenario)
    pares: Dict[str, Dict[str, Any]] = {}
    for origin in names:
        pares[origin] = {}
        for dest in names:
            if dest == origin:
                continue
            if (origin, dest) not in cache:
                coords, minutes = brp._leg_path(graph, node_of[origin], node_of[dest])
                cache[(origin, dest)] = {"tiempo_red_min": round(minutes, 2),
                                         "coordenadas": _redondear(_simplificar(coords, metros))}
            pares[origin][dest] = cache[(origin, dest)]

    out_path = scenario_output_dir(scenario) / "caminos_todos_pares.json.gz"
    result = {"fuente": "© colaboradores de OpenStreetMap (ODbL)", "penalizacion_curvas_k": k,
              "simplificacion_m": metros, "pares": pares}
    # mtime=0 para que el .gz no cambie si el contenido es el mismo.
    with gzip.GzipFile(out_path, "wb", mtime=0) as f:
        f.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    n_pares = sum(len(d) for d in pares.values())
    print(f"{scenario}: {n_pares} pares -> {out_path.relative_to(BASE_DIR)} "
          f"({out_path.stat().st_size / 1e6:.1f} MB)")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Caminos por carretera entre todos los pares de nodos")
    parser.add_argument("--k", type=brp._parse_k, default="auto",
                        help="K de la penalización por curvas ('ninguno' para no penalizar). "
                             "Por defecto, el de caminos_rutas.json.")
    parser.add_argument("--simplificar", type=float, default=5.0,
                        help="Tolerancia de simplificación de las polilíneas en metros (0 para no simplificar).")
    parser.add_argument("--escenario", choices=list(ESCENARIOS), default=None,
                        help="Hotel base (carpeta de data/). Por defecto, todos.")
    args = parser.parse_args()

    if not brp.GRAFO_PATH.exists():
        sys.exit(f"No se encuentra el grafo {brp.GRAFO_PATH.name} en la raíz del repositorio. "
                 "Genéralo primero con: python scripts/build_road_paths.py")

    graph = brp.load_graph()
    for u, v, data in graph.edges(data=True):
        data["curv_deg_km"] = brp.curvatura_deg_km(graph, u, v, data)
    coords: Dict[str, Dict[str, float]] = {}
    for scenario in ESCENARIOS:
        coords.update(load_coordinates(scenario))
    node_of = brp.snap_nodes(graph, coords)

    k = args.k
    if k == "auto":
        encontrado, k = _k_detectado()
        if encontrado:
            print(f"K tomado de caminos_rutas.json: {'ninguno' if k is None else k}")
        else:
            k = brp.choose_k(graph, node_of)
    brp.apply_penalty(graph, k)

    cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for scenario in ([args.escenario] if args.escenario else list(ESCENARIOS)):
        build_scenario(graph, scenario, node_of, k, args.simplificar, cache)


if __name__ == "__main__":
    main()
