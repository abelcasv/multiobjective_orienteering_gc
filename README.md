# Optimización Multiobjetivo de Rutas Turísticas en Gran Canaria (MOOP)

Proyecto para la asignatura **Optimización y Heurística** (Grado en Ciencia e Ingeniería de Datos / IA).

El proyecto resuelve el **Problema de Orientación Multiobjetivo (Multi-Objective Orienteering Problem - MOOP)** para diseñar rutas turísticas óptimas en Gran Canaria bajo una restricción temporal (escala de crucero / jornada de 8 horas), buscando maximizar el valor turístico total y minimizar el tiempo invertido en conducción y estancia.

---

## Estructura del Repositorio

```text
multiobjective_orienteering_gc/
├── data/                                 # Datasets de entrada
│   ├── matriz_tiempos.csv                # Matriz asimétrica NxN de tiempos reales
│   ├── puntos_interes.csv                # (Opcional) Puntuación y tiempos de estancia
│   └── coordenadas.csv                   # (Opcional) Latitud y longitud de cada POI
├── output/                               # Artefactos y resultados generados
│   ├── rutas_pareto.json                 # Rutas no dominadas con detalle tramo a tramo
│   ├── comparativa_pareto_vs_greedy.png  # Gráfica comparativa NSGA-II vs Greedy
│   └── convergencia_nsga2.png            # Curvas de Hipervolumen y Score
├── src/                                  # Código fuente modular
│   ├── __init__.py                       # Paquete de Python
│   ├── genetic_algorithm.py              # Algoritmo NSGA-II adaptado a Orienteering
│   ├── greedy_algorithm.py               # Heurística Voraz (Baseline de comparación)
│   └── pipeline.py                       # Orquestación de benchmarking y exportación
├── main.py                               # Punto de entrada único del proyecto
├── requirements.txt                      # Dependencias de Python
└── README.md
```

---

## División de Roles

### Miembro 1: Data Engineer & Visualización
- Creación y refinamiento de la matriz de tiempos de conducción real (`data/matriz_tiempos.csv`).
- Dataset de coordenadas geográficas (`data/coordenadas.csv`) y atributos (`data/puntos_interes.csv`).
- Visualización interactiva con **Folium** consumiendo `output/rutas_pareto.json`.

### Miembro 2: Optimization / AI Engineer
- **`src/genetic_algorithm.py`**: Motor evolutivo **NSGA-II** para cromosomas de longitud variable, principio de dominancia con restricciones de Deb (2002), cruce de subconjuntos y mutaciones dinámicas (insert, remove, swap, 2-opt).
- **`src/greedy_algorithm.py`**: Heurística voraz constructiva multiobjetivo (*Baseline de comparación académica*).
- **`src/pipeline.py`**: Pipeline de benchmarking, cálculo de Hipervolumen (HV) y exportación estructurada.
- **`main.py`**: Punto de entrada minimalista.

---

## Resultados y Benchmarking

| Métrica / Algoritmo | Baseline Greedy (Voraz) | NSGA-II (Genético Multiobjetivo) | Mejora / Diferencia |
| :--- | :---: | :---: | :---: |
| **Soluciones en Frente F1** | 10 | **75** | **+650% diversidad** |
| **Hipervolumen (HV)** | 13,869.13 | **15,795.30** | **+13.9% espacio dominado** |
| **Puntuación Máxima Factible** | 60.70 pts | **64.10 pts** | **+3.4 pts** |
| **Cumplimiento de $T_{\max} \le 8$h** | 100% factible | 100% factible | Regla de Deb (sin penalizaciones ad-hoc) |

---

## Instalación y Ejecución

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar el pipeline de optimización
python main.py
```
*(Los resultados se guardan automáticamente en `output/rutas_pareto.json` y las figuras en `output/`)*.