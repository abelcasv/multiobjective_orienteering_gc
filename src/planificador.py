"""Planificador de una ruta a medida: categorías, lugares descartados y visita obligatoria.

`optimizar_ruta` traduce las preferencias del turista a las restricciones de
OrienteeringProblem (`forbidden_nodes` y `mandatory_node`), ejecuta NSGA-II y devuelve el
frente y las 3 rutas recomendadas. Si no hay ninguna ruta factible devuelve un resultado
vacío con un motivo legible en lugar de lanzar una excepción. Los argumentos mal escritos
(escenario, categoría o lugar que no existen) sí lanzan ValueError.
"""
import random
from dataclasses import dataclass, field, replace
from typing import Any, Dict, Iterable, List, Optional, Set

import numpy as np
import pandas as pd

from .algorithms.genetic_algorithm import NSGA2Orienteering, seleccionar_3_opciones_turisticas
from .core.problem import GAConfig, Individual, OrienteeringProblem
from .pipeline import (
    ESCENARIOS,
    _resolve_data_path,
    create_problem_instance,
    load_distance_matrix,
    serialize_route,
)

COLUMNAS_CATEGORIA = ("Categoria", "Categoria_2")


@dataclass
class ResultadoRuta:
    escenario: str
    t_max: float
    frente: List[Individual] = field(default_factory=list)  # ordenado por tiempo total
    express: Optional[Individual] = None
    equilibrada: Optional[Individual] = None
    exhaustiva: Optional[Individual] = None
    motivo: Optional[str] = None  # solo si el resultado está vacío
    nombres: List[str] = field(default_factory=list)
    problema: Optional[OrienteeringProblem] = None

    @property
    def vacio(self) -> bool:
        return not self.frente

    def paradas(self, ind: Individual) -> List[str]:
        return [self.nombres[i] for i in ind.genes]

    def a_dict(self) -> Dict[str, Any]:
        """Versión serializable (misma estructura de rutas que rutas_pareto.json)."""
        if self.vacio:
            return {"escenario": self.escenario, "tiempo_maximo_minutos": self.t_max,
                    "motivo": self.motivo, "opciones_recomendadas": {}, "frente_pareto_completo": []}
        assert self.problema is not None

        def ruta(ind: Optional[Individual], etiqueta: str) -> Dict[str, Any]:
            return serialize_route(ind, etiqueta, self.problema, self.nombres, self.escenario)

        return {
            "escenario": self.escenario,
            "tiempo_maximo_minutos": self.t_max,
            "motivo": None,
            "opciones_recomendadas": {
                "express": ruta(self.express, "Opción Express"),
                "equilibrada": ruta(self.equilibrada, "Opción Equilibrada"),
                "exhaustiva": ruta(self.exhaustiva, "Opción Exhaustiva"),
            },
            "frente_pareto_completo": [
                {"score": round(ind.score, 2), "tiempo_total_min": round(ind.total_time, 2),
                 "paradas": self.paradas(ind)}
                for ind in self.frente
            ],
        }


def cargar_categorias(escenario: str) -> Dict[str, Set[str]]:
    """Nombre del POI -> categorías (principal y secundaria). El hotel no se incluye."""
    df = pd.read_csv(_resolve_data_path("puntos_interes.csv", escenario))
    categorias: Dict[str, Set[str]] = {}
    for _, row in df.iterrows():
        cats = {str(row[c]).strip() for c in COLUMNAS_CATEGORIA if c in df.columns and pd.notna(row[c])}
        if "Hotel" not in cats:
            categorias[str(row["Nombre"])] = cats
    return categorias


def categorias_disponibles(escenario: str) -> List[str]:
    return sorted(set().union(*cargar_categorias(escenario).values()))


def _vacio(escenario: str, t_max: float, motivo: str) -> ResultadoRuta:
    return ResultadoRuta(escenario=escenario, t_max=t_max, motivo=motivo)


def _comprobar_nombres(escenario: str, categorias: Set[str], lugares: Iterable[str],
                       poi_cats: Dict[str, Set[str]]) -> None:
    desconocidas = categorias - set(categorias_disponibles(escenario))
    if desconocidas:
        raise ValueError(f"Categorías desconocidas: {sorted(desconocidas)}. "
                         f"Disponibles: {categorias_disponibles(escenario)}")
    no_poi = [n for n in lugares if n not in poi_cats]
    if no_poi:
        raise ValueError(f"No son puntos de interés de '{escenario}': {no_poi}")


def _ida_visita_vuelta(problema: OrienteeringProblem, nodo: int) -> float:
    h = problema.depot_idx
    return problema.driving_time(h, nodo) + float(problema.visit_times[nodo]) + problema.driving_time(nodo, h)


def _motivo_sin_rutas(problema: OrienteeringProblem, nombres: List[str], t_max: float,
                      obligatorio: Optional[str]) -> str:
    if obligatorio is not None:
        minutos = _ida_visita_vuelta(problema, nombres.index(obligatorio))
        if minutos > t_max:
            return (f"La visita obligatoria '{obligatorio}' no cabe en {t_max:.0f} min: "
                    f"ir desde el hotel, visitarla y volver lleva {minutos:.0f} min.")
        return f"No se ha encontrado ninguna ruta de {t_max:.0f} min o menos que incluya '{obligatorio}'."
    minimo = min(_ida_visita_vuelta(problema, n) for n in problema.available_nodes())
    return (f"Ningún lugar permitido cabe en {t_max:.0f} min: el más rápido de visitar "
            f"lleva {minimo:.0f} min entre ida, visita y vuelta.")


def optimizar_ruta(
    escenario: str,
    t_max: float,
    categorias: Iterable[str],
    excluidos: Iterable[str],
    obligatorio: Optional[str] = None,
    semilla: int = 42,
    *,
    config: Optional[GAConfig] = None,
) -> ResultadoRuta:
    """Rutas recomendadas desde el hotel de `escenario` con las preferencias del turista.

    - `categorias`: categorías marcadas. Un POI está permitido si su categoría principal o
      la secundaria está marcada; los demás pasan a `forbidden_nodes`.
    - `excluidos`: nombres de POIs descartados a mano (también a `forbidden_nodes`).
    - `obligatorio`: POI que debe aparecer en todas las rutas (`mandatory_node`). Se admite
      aunque su categoría no esté marcada, porque el turista lo ha pedido expresamente.
    - `config`: configuración de NSGA-II; por defecto la del proyecto (100 x 200).
    """
    if escenario not in ESCENARIOS:
        raise ValueError(f"Escenario desconocido '{escenario}'. Disponibles: {list(ESCENARIOS)}")
    categorias = set(categorias)
    excluidos = list(excluidos)
    poi_cats = cargar_categorias(escenario)
    _comprobar_nombres(escenario, categorias, excluidos + ([obligatorio] if obligatorio else []), poi_cats)

    if not categorias:
        return _vacio(escenario, t_max, "No has marcado ninguna categoría de lugares.")
    if obligatorio is not None and obligatorio in excluidos:
        return _vacio(escenario, t_max, f"Has descartado la visita obligatoria '{obligatorio}'.")

    matriz, nombres = load_distance_matrix(escenario)
    base = create_problem_instance(matriz, nombres, ESCENARIOS[escenario], escenario, t_max=t_max)
    prohibidos = {n for n, cats in poi_cats.items() if not cats & categorias} | set(excluidos)
    prohibidos.discard(obligatorio)
    problema = replace(
        base,
        mandatory_node=nombres.index(obligatorio) if obligatorio is not None else None,
        forbidden_nodes=sorted(nombres.index(n) for n in prohibidos if n in nombres),
    )
    if not problema.available_nodes():
        return _vacio(escenario, t_max, "Con las categorías marcadas y los lugares descartados no queda ningún lugar que visitar.")

    random.seed(semilla)
    np.random.seed(semilla)
    frente = sorted(NSGA2Orienteering(problema, config or GAConfig()).evolve(), key=lambda ind: ind.total_time)
    if not frente:
        return _vacio(escenario, t_max, _motivo_sin_rutas(problema, nombres, t_max, obligatorio))

    express, equilibrada, exhaustiva = seleccionar_3_opciones_turisticas(frente)
    return ResultadoRuta(escenario=escenario, t_max=t_max, frente=frente, express=express,
                         equilibrada=equilibrada, exhaustiva=exhaustiva, nombres=nombres, problema=problema)
