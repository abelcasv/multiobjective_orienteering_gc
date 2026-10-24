"""Genera un mapa Folium por escenario (hotel) con las 3 rutas recomendadas.

Lee output/<escenario>/rutas_pareto.json (generado por main.py) y escribe
output/<escenario>/mapa_rutas.html. Los tramos se dibujan como líneas rectas
entre paradas: no siguen la carretera real.

Uso: python scripts/make_maps.py [--escenario santa_catalina]
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import folium

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from src.pipeline import ESCENARIOS, load_coordinates, scenario_output_dir  # noqa: E402

OPCIONES: Dict[str, Tuple[str, str]] = {
    "express": ("Express", "#2980b9"),
    "equilibrada": ("Equilibrada", "#27ae60"),
    "exhaustiva": ("Exhaustiva", "#c0392b"),
}


def _load_hotel_coords(scenario: str) -> Tuple[float, float]:
    coords = load_coordinates(scenario=scenario)[ESCENARIOS[scenario]]
    return coords["lat"], coords["lon"]


def _numbered_icon(number: int, color: str) -> folium.DivIcon:
    html = (
        f'<div style="background:{color};color:#fff;border:2px solid #fff;border-radius:50%;'
        f"width:24px;height:24px;line-height:20px;text-align:center;font:bold 12px sans-serif;"
        f'box-shadow:0 1px 3px rgba(0,0,0,.5)">{number}</div>'
    )
    return folium.DivIcon(html=html, icon_size=(24, 24), icon_anchor=(12, 12))


def _stop_popup(number: int, leg: Dict[str, Any], arrival_min: float) -> folium.Popup:
    html = (
        f"<b>{number}. {leg['destino']}</b><br>"
        f"Puntuación: {leg['score_parada']:.0f}<br>"
        f"Tiempo de visita: {leg['tiempo_estancia_min']:.0f} min<br>"
        f"Conducción desde la parada anterior: {leg['tiempo_conduccion_min']:.0f} min<br>"
        f"Llegada: {arrival_min // 60:.0f} h {arrival_min % 60:02.0f} min tras salir del hotel"
    )
    return folium.Popup(html, max_width=280)


def _add_route_layer(fmap: folium.Map, key: str, route: Dict[str, Any], hotel: Tuple[float, float]) -> None:
    name, color = OPCIONES[key]
    label = (
        f'<span style="color:{color}">&#9632;</span> {name}: {route["puntuacion_total"]:.0f} pts, '
        f'{route["tiempo_total_horas"]:.1f} h, {route["numero_paradas"]} paradas'
    )
    layer = folium.FeatureGroup(name=label, show=True)

    path: List[Tuple[float, float]] = [hotel]
    elapsed = 0.0
    stops = route["detalle_tramos"][:-1]  # el último tramo vuelve al hotel
    for number, leg in enumerate(stops, start=1):
        elapsed += leg["tiempo_conduccion_min"]
        point = (leg["coordenadas_destino"]["lat"], leg["coordenadas_destino"]["lon"])
        path.append(point)
        folium.Marker(
            point,
            icon=_numbered_icon(number, color),
            popup=_stop_popup(number, leg, elapsed),
            tooltip=f"{name} · {number}. {leg['destino']}",
        ).add_to(layer)
        elapsed += leg["tiempo_estancia_min"]
    path.append(hotel)

    folium.PolyLine(path, color=color, weight=4, opacity=0.8, dash_array="8 6").add_to(layer)
    layer.add_to(fmap)


def _add_legend(fmap: folium.Map, data: Dict[str, Any]) -> None:
    html = (
        '<div style="position:fixed;bottom:24px;left:24px;z-index:9999;background:#fff;'
        'padding:8px 12px;border-radius:6px;box-shadow:0 1px 4px rgba(0,0,0,.3);font:12px sans-serif">'
        f"<b>{data['origen_destino_depot']}</b><br>"
        f"Tiempo máximo: {data['tiempo_maximo_minutos'] / 60:.0f} h · Ruta cerrada (salida y vuelta al hotel)<br>"
        "<i>Tramos en línea recta, no siguen la carretera.</i></div>"
    )
    fmap.get_root().html.add_child(folium.Element(html))


def build_map(scenario: str) -> Path:
    out_dir = scenario_output_dir(scenario)
    with open(out_dir / "rutas_pareto.json", encoding="utf-8") as f:
        data = json.load(f)

    hotel = _load_hotel_coords(scenario)
    fmap = folium.Map(location=hotel, zoom_start=10, tiles="OpenStreetMap")
    folium.Marker(
        hotel,
        icon=folium.Icon(color="black", icon="home", prefix="fa"),
        popup=folium.Popup(f"<b>{ESCENARIOS[scenario]}</b><br>Salida y llegada", max_width=250),
        tooltip=ESCENARIOS[scenario],
    ).add_to(fmap)

    for key, route in data["opciones_recomendadas"].items():
        if route:
            _add_route_layer(fmap, key, route, hotel)

    folium.LayerControl(collapsed=False).add_to(fmap)
    _add_legend(fmap, data)

    out_path = out_dir / "mapa_rutas.html"
    fmap.save(str(out_path))
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Mapas Folium de las rutas recomendadas")
    parser.add_argument("--escenario", choices=list(ESCENARIOS), default=None,
                        help="Hotel base (carpeta de data/). Por defecto, todos.")
    args = parser.parse_args()
    for scenario in ([args.escenario] if args.escenario else list(ESCENARIOS)):
        print(f"Mapa guardado en {build_map(scenario).relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
