# Optimización Multiobjetivo de Rutas Turísticas en Gran Canaria (MOOP)

Proyecto para la asignatura **Optimización y Heurística** (Grado en Ciencia e Ingeniería de Datos / IA).

El proyecto resuelve el **Problema de Orientación Multiobjetivo (Multi-Objective Orienteering Problem - MOOP)** para diseñar rutas turísticas óptimas en Gran Canaria bajo una restricción temporal (escala de crucero / jornada de 8 horas), buscando maximizar el valor turístico total y minimizar el tiempo empleado.

---

## Estructura del Proyecto y División de Roles

### Miembro 1: Data Engineer & Visualización
- Creación y refinamiento de la matriz de tiempos de conducción real (`matriz_tiempos.csv`).
- Dataset de coordenadas geográficas (`coordenadas.csv`).
- Visualización interactiva con **Folium** consumiendo `rutas_pareto.json` para trazar los itinerarios en el mapa.

### Miembro 2: Optimization / AI Engineer
- **[`genetic_algorithm.py`](genetic_algorithm.py)**: Motor evolutivo **NSGA-II** adaptado a cromosomas de longitud variable, principio de dominancia con restricciones de Deb (2002), cruce de subconjuntos y mutaciones dinámicas (insert, remove, swap, 2-opt).
- **[`greedy_algorithm.py`](greedy_algorithm.py)**: Heurística voraz constructiva multiobjetivo (*Baseline de comparación académica*).
- **[`optimizacion.py`](optimizacion.py)**: Pipeline principal de ejecución, benchmarking de Hipervolumen (HV), curvas de convergencia y exportación de datos.

---

## Resultados y Comparativa Experimental

| Métrica / Algoritmo | Baseline Greedy (Voraz) | NSGA-II (Genético Multiobjetivo) | Mejora / Diferencia |
| :--- | :---: | :---: | :---: |
| **Soluciones en Frente F1** | 10 | **75** | +650% diversidad |
| **Hipervolumen (HV)** | 13,869.13 | **15,794.68** | **+13.9% espacio dominado** |
| **Puntuación Máxima Factible** | 60.70 pts | **64.10 pts** | +3.4 pts |
| **Tiempo Límite ($T_{\max}$)** | 8.0 horas (480 min) | 8.0 horas (480 min) | 100% factibles (Regla de Deb) |

### Gráficas Científicas Generadas
- **`comparativa_pareto_vs_greedy.png`**: Frente de Pareto de NSGA-II frente a la línea base Greedy.
- **`convergencia_nsga2.png`**: Curvas de evolución del Hipervolumen y del mejor Score factible a lo largo de las 200 generaciones.
- **`rutas_pareto.json`**: Itinerarios completos estructurados para la integración con Folium.

---

## Ejecución

```bash
python optimizacion.py
```