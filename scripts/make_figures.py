"""Figuras para la memoria, a partir de data/ y de output/<escenario>/rutas_pareto.json.

Genera en output/figuras/:
- mapa_pois_hoteles.png: los 30 POIs (color = puntuación, tamaño = tiempo de visita) y los 2 hoteles.
- calibracion_google.png y calibracion_google.csv: los 12 pares medidos en Google Maps frente a
  la matriz sin factor global y la matriz calibrada (reproduce la celda 5b del notebook).
- frentes_pareto.png: frente de Pareto de NSGA-II de cada hotel con las 3 rutas recomendadas.

Uso: python scripts/make_figures.py   (requiere haber ejecutado antes main.py)
"""
import json
import sys
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from src.pipeline import DATA_DIR, ESCENARIOS, OUTPUT_DIR, scenario_output_dir  # noqa: E402

FIG_DIR = OUTPUT_DIR / "figuras"
AUX_DIR = DATA_DIR / "auxiliar"

INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e4e3df"
ROUTE_COLORS = {"express": "#2a78d6", "equilibrada": "#eb6834", "exhaustiva": "#1baf7a"}
ROUTE_LABELS = {"express": "Express", "equilibrada": "Equilibrada", "exhaustiva": "Exhaustiva"}

# Desplazamiento (puntos) de las etiquetas que se solapan en el mapa de POIs; el resto va arriba a la derecha.
LABEL_OFFSETS = {
    "Charco de San Lorenzo": (6, 6, "left"),
    "Cueva Pintada (Gáldar)": (-6, 6, "right"),
    "Cenobio de Valerón": (-7, -9, "right"),
    "Jardín de la Marquesa (Arucas)": (0, 9, "center"),
    "Arucas (Iglesia)": (7, -10, "left"),
    "Firgas (Paseo de Gran Canaria)": (0, -15, "center"),
    "Puerto de las Nieves (Agaete)": (0, -16, "center"),
    "Roque Nublo": (-8, -3, "right"),
    "Pico de las Nieves": (7, -9, "left"),
    "Bufadero de la Garita": (-7, -3, "right"),
    "Tufia (Poblado y Playa)": (-7, -3, "right"),
    "Vegueta (Las Palmas)": (11, -3, "left"),
    "Playa de las Canteras": (-9, 4, "right"),
    "Los Azulejos de Veneguera": (-7, -3, "right"),
    "Dunas de Maspalomas": (9, -3, "left"),
}

# Copia de PARES_GOOGLE (celda 4a de scripts/build_time_matrix.ipynb): origen, destino, minutos en Google Maps.
PARES_GOOGLE: List[Tuple[str, str, float]] = [
    ("Vegueta (Las Palmas)", "Playa de las Canteras", 11),
    ("Vegueta (Las Palmas)", "Dunas de Maspalomas", 38),
    ("Playa del Inglés", "Puerto de Mogán", 26),
    ("Vegueta (Las Palmas)", "Playa de Amadores", 46),
    ("Vegueta (Las Palmas)", "Cueva Pintada (Gáldar)", 32),
    ("Arucas (Iglesia)", "Puerto de las Nieves (Agaete)", 27),
    ("Roque Nublo", "Puerto de Mogán", 81),
    ("Tejeda (Pueblo)", "Teror (Basílica)", 46),
    ("Mirador de Unamuno", "Puerto de Mogán", 106),
    ("Pico de las Nieves", "Vegueta (Las Palmas)", 52),
    ("Mirador del Balcón", "Puerto de las Nieves (Agaete)", 35),
    ("Barranco de Fataga", "Dunas de Maspalomas", 28),
]

plt.rcParams.update({
    "font.size": 10,
    "axes.edgecolor": INK_SECONDARY,
    "axes.labelcolor": INK,
    "xtick.color": INK_SECONDARY,
    "ytick.color": INK_SECONDARY,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
})


def plot_pois_map(output_path: Path) -> None:
    pois = pd.read_csv(DATA_DIR / "santa_catalina" / "puntos_interes.csv")
    pois = pois[pois["Nombre"] != ESCENARIOS["santa_catalina"]]
    hotels = pd.concat(
        pd.read_csv(DATA_DIR / esc / "puntos_interes.csv").query("Nombre == @name")
        for esc, name in ESCENARIOS.items()
    )

    fig, ax = plt.subplots(figsize=(9, 8.5))
    sc = ax.scatter(
        pois["Longitud"], pois["Latitud"], c=pois["Puntuacion"], cmap="Blues", vmin=4, vmax=10,
        s=pois["Tiempo_Visita_Min"] * 1.6, edgecolors=INK_SECONDARY, linewidths=0.6, zorder=3,
    )
    ax.scatter(hotels["Longitud"], hotels["Latitud"], marker="*", s=380, c="#eb6834",
               edgecolors="white", linewidths=1.2, zorder=4, label="Hotel (depósito)")
    for _, row in pois.iterrows():
        ax.annotate(row["Nombre"], (row["Longitud"], row["Latitud"]), xytext=LABEL_OFFSETS.get(row["Nombre"], (5, 4, "left"))[:2],
                    ha=LABEL_OFFSETS.get(row["Nombre"], (5, 4, "left"))[2],
                    textcoords="offset points", fontsize=7, color=INK_SECONDARY)
    hotel_offsets = {ESCENARIOS["santa_catalina"]: (11, -4), ESCENARIOS["lopesan_villa_del_conde"]: (-10, -4)}
    for _, row in hotels.iterrows():
        dx, dy = hotel_offsets[row["Nombre"]]
        ax.annotate(row["Nombre"], (row["Longitud"], row["Latitud"]), xytext=(dx, dy),
                    ha="left" if dx > 0 else "right", textcoords="offset points", fontsize=8.5, fontweight="bold", color=INK)

    ax.set_aspect(1.0 / np.cos(np.radians(pois["Latitud"].mean())))
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    ax.set_title("Puntos de interés y hoteles de Gran Canaria", fontweight="bold", color=INK)
    ax.margins(x=0.08, y=0.05)
    ax.set_xlim(right=-15.25)
    fig.colorbar(sc, ax=ax, orientation="horizontal", shrink=0.5, pad=0.08, label="Puntuación")
    for minutes in (30, 90, 150):
        ax.scatter([], [], s=minutes * 1.6, c="white", edgecolors=INK_SECONDARY, label=f"Visita {minutes} min")
    ax.legend(loc="lower left", bbox_to_anchor=(1.02, 0.0), labelspacing=1.4, borderpad=1, frameon=False)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def build_calibration_table() -> pd.DataFrame:
    raw = pd.read_csv(AUX_DIR / "Matriz_sin_factor_global.csv", index_col=0)
    calibrated = pd.read_csv(AUX_DIR / "Matriz_completa_con_hoteles.csv", index_col=0)
    table = pd.DataFrame(PARES_GOOGLE, columns=["origen", "destino", "google_min"])
    table["sin_factor_min"] = [raw.loc[o, d] for o, d, _ in PARES_GOOGLE]
    table["calibrado_min"] = [calibrated.loc[o, d] for o, d, _ in PARES_GOOGLE]
    table["error_sin_factor_min"] = table["sin_factor_min"] - table["google_min"]
    table["error_calibrado_min"] = table["calibrado_min"] - table["google_min"]
    return table.round(1)


def plot_calibration(table: pd.DataFrame, output_path: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), gridspec_kw={"width_ratios": [1, 1.4]})
    series = [("sin_factor_min", "Sin factor global", "#2a78d6"), ("calibrado_min", "Calibrada", "#eb6834")]

    lim = float(max(table["google_min"].max(), table["sin_factor_min"].max(), table["calibrado_min"].max())) * 1.05
    ax1.plot([0, lim], [0, lim], color=INK_SECONDARY, linewidth=1, linestyle="--", label="Igual a Google")
    for col, label, color in series:
        mae = (table[col] - table["google_min"]).abs().mean()
        ax1.scatter(table["google_min"], table[col], s=50, color=color, edgecolors="white",
                    linewidths=1.5, zorder=3, label=f"{label} (error medio {mae:.1f} min)")
    ax1.set_xlim(0, lim)
    ax1.set_ylim(0, lim)
    ax1.set_aspect("equal")
    ax1.set_xlabel("Google Maps (min)")
    ax1.set_ylabel("Matriz (min)")
    ax1.set_title("Tiempo de la matriz frente a Google Maps", fontweight="bold", color=INK)
    ax1.legend(frameon=False, loc="upper left", fontsize=8.5)

    labels = [f"{o} → {d}" for o, d in zip(table["origen"], table["destino"])]
    y = np.arange(len(table))
    height = 0.38
    ax2.barh(y - height / 2, table["error_sin_factor_min"], height=height - 0.04, color="#2a78d6", label="Sin factor global")
    ax2.barh(y + height / 2, table["error_calibrado_min"], height=height - 0.04, color="#eb6834", label="Calibrada")
    ax2.axvline(0, color=INK_SECONDARY, linewidth=1)
    ax2.set_yticks(y, labels, fontsize=8)
    ax2.invert_yaxis()
    ax2.grid(axis="y", visible=False)
    ax2.set_xlabel("Error = matriz − Google (min); negativo = la matriz es optimista")
    ax2.set_title("Error por par de referencia", fontweight="bold", color=INK)
    ax2.legend(frameon=False, loc="lower right", fontsize=8.5)

    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_pareto_fronts(output_path: Path) -> None:
    fig, axes = plt.subplots(1, len(ESCENARIOS), figsize=(13, 5), sharex=True, sharey=True)
    for ax, (scenario, hotel) in zip(np.atleast_1d(axes), ESCENARIOS.items()):
        with open(scenario_output_dir(scenario) / "rutas_pareto.json", encoding="utf-8") as f:
            data = json.load(f)
        front = sorted(data["frente_pareto_completo"], key=lambda p: p["tiempo_total_min"])
        times = [p["tiempo_total_min"] / 60 for p in front]
        scores = [p["score"] for p in front]
        ax.step(times, scores, where="post", color=INK_SECONDARY, linewidth=1.2, alpha=0.6)
        ax.scatter(times, scores, s=30, color=INK_SECONDARY, zorder=3, label="Frente de Pareto (NSGA-II)")

        labelled = set()
        for key, route in data["opciones_recomendadas"].items():
            if not route:
                continue
            point = (route["tiempo_total_min"] / 60, route["puntuacion_total"])
            ax.scatter(*point, s=140, color=ROUTE_COLORS[key], edgecolors="white", linewidths=2, zorder=4,
                       label=ROUTE_LABELS[key])
            if point in labelled:
                continue
            labelled.add(point)
            names = " = ".join(ROUTE_LABELS[k] for k, r in data["opciones_recomendadas"].items()
                               if r and (r["tiempo_total_min"] / 60, r["puntuacion_total"]) == point)
            ax.annotate(f"{names}\n{route['puntuacion_total']:.0f} pts · {route['tiempo_total_horas']:.1f} h",
                        point, xytext=(-12, 10), textcoords="offset points", ha="right", fontsize=8, color=INK)

        ax.axvline(data["tiempo_maximo_minutos"] / 60, color=INK_SECONDARY, linestyle=":", linewidth=1)
        ax.set_title(hotel, fontweight="bold", color=INK, pad=12)
        ax.set_xlabel("Tiempo total de la ruta (h)")
    np.atleast_1d(axes)[0].set_ylim(0, np.atleast_1d(axes)[0].get_ylim()[1] * 1.1)
    np.atleast_1d(axes)[0].set_ylabel("Puntuación turística")
    np.atleast_1d(axes)[0].legend(frameon=False, loc="lower right", fontsize=8.5)
    fig.suptitle("Frentes de Pareto por hotel (línea punteada: tiempo máximo)", fontweight="bold", color=INK)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    plot_pois_map(FIG_DIR / "mapa_pois_hoteles.png")
    table = build_calibration_table()
    table.to_csv(FIG_DIR / "calibracion_google.csv", index=False)
    plot_calibration(table, FIG_DIR / "calibracion_google.png")
    plot_pareto_fronts(FIG_DIR / "frentes_pareto.png")
    print(table.to_string(index=False))
    print(f"\nError medio absoluto: sin factor {table['error_sin_factor_min'].abs().mean():.1f} min | "
          f"calibrada {table['error_calibrado_min'].abs().mean():.1f} min")
    print(f"Factor global aplicado (calibrada / sin factor): x{(table['calibrado_min'] / table['sin_factor_min']).median():.3f}")
    print(f"Figuras guardadas en {FIG_DIR.relative_to(BASE_DIR)}/")


if __name__ == "__main__":
    main()
