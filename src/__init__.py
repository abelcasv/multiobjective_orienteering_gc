"""
Paquete del optimizador de rutas turísticas en Gran Canaria (MOOP).
"""

from .core.problem import OrienteeringProblem, GAConfig, Individual
from .core.metrics import (
    calcular_hipervolumen,
    calcular_spread,
    test_wilcoxon,
    resumen_estadistico,
)
from .algorithms.genetic_algorithm import NSGA2Orienteering, seleccionar_3_opciones_turisticas
from .algorithms.greedy_algorithm import GreedyOrienteering
from .algorithms.random_search import RandomSearchOrienteering
from .algorithms.weighted_sum import WeightedSumGA
from .pipeline import run_pipeline

__all__ = [
    "OrienteeringProblem",
    "GAConfig",
    "Individual",
    "calcular_hipervolumen",
    "calcular_spread",
    "test_wilcoxon",
    "resumen_estadistico",
    "NSGA2Orienteering",
    "seleccionar_3_opciones_turisticas",
    "GreedyOrienteering",
    "RandomSearchOrienteering",
    "WeightedSumGA",
    "run_pipeline",
]
