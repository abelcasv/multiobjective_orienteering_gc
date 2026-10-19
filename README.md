# Optimización Multiobjetivo de Rutas Turísticas en Gran Canaria (MOOP)

Proyecto para la asignatura **Optimización y Heurística** (Grado en Ciencia e Ingeniería de Datos / IA).
Encuadrado en la modalidad **C5: Optimización Multiobjetivo (Dificultad Alta)**.

El proyecto resuelve el **Problema de Orientación Multiobjetivo (Multi-Objective Orienteering Problem - MOOP)** para diseñar rutas turísticas óptimas en Gran Canaria bajo una restricción presupuestaria de tiempo ($T_{\max} = 8$ horas de escala de crucero o jornada turística), buscando simultáneamente:
1. **Maximizar el valor turístico total** ($\sum S_i$).
2. **Minimizar el tiempo invertido** (tiempo de conducción real + tiempo de estancia física).

---

## Estructura del Repositorio

```text
multiobjective_orienteering_gc/
├── data/                                      # Datasets de entrada
│   ├── matriz_tiempos.csv                     # Matriz asimétrica 30x30 de tiempos de conducción
│   ├── puntos_interes.csv                     # Puntuaciones (1-10) y tiempos de visita
│   └── coordenadas.csv                        # Latitud y longitud de cada POI
├── output/                                    # Artefactos y resultados generados
│   ├── rutas_pareto.json                      # Rutas óptimas con coordenadas y desglose de tramos
│   ├── comparativa_pareto_vs_greedy.png       # Frente de Pareto vs Línea base Greedy
│   ├── convergencia_nsga2.png                 # Curvas de Hipervolumen y Score factible
│   ├── validacion_zdt1.png                    # Validación analítica de NSGA-II en ZDT1
│   ├── boxplot_hipervolumen.png               # Boxplots estadísticos de los 4 algoritmos
│   ├── resultados_estadisticos_semillas.csv   # Registro detallado de las 15 semillas
│   └── resumen_estadistico.json               # Métricas agregadas y p-valores de Wilcoxon
├── src/                                       # Código fuente modular
│   ├── core/                                  # Modelos y métricas compartidas
│   │   ├── problem.py                         # OrienteeringProblem, Individual, GAConfig
│   │   └── metrics.py                         # Hipervolumen, Spread y Test de Wilcoxon
│   ├── algorithms/                            # Algoritmos de optimización
│   │   ├── genetic_algorithm.py               # NSGA-II con dominancia de Deb (2002)
│   │   ├── greedy_algorithm.py                # Heurística Voraz (Baseline)
│   │   ├── random_search.py                   # Búsqueda Aleatoria (Baseline)
│   │   └── weighted_sum.py                    # Suma Ponderada / Escalarización (Baseline)
│   ├── benchmarks/                            # Suite experimental exigida por rúbrica C5
│   │   ├── zdt.py                             # Validación matemática en benchmark ZDT1
│   │   └── statistical_suite.py               # Batería con 15 semillas + Test de Wilcoxon
│   ├── pipeline.py                            # Orquestación del caso de Gran Canaria
│   └── __init__.py
├── main.py                                    # Punto de entrada principal
├── requirements.txt                           # Dependencias del proyecto
└── README.md
```

---

## División de Roles

### Miembro 1: Data Engineer & Visualización
- Extracción de la red viaria real con OSMnx y cálculo de la matriz asimétrica de tiempos (`data/matriz_tiempos.csv`).
- Dataset de coordenadas geográficas (`data/coordenadas.csv`) y atributos (`data/puntos_interes.csv`).
- Visualización interactiva con **Folium** consumiendo `output/rutas_pareto.json`.

### Miembro 2: Optimization / AI Engineer
- **Algoritmo propio NSGA-II:** Cromosomas de longitud variable, selección por torneo de Deb con manejo de restricciones, operadores genéticos específicos y ordenamiento no dominado rápido.
- **Líneas base de comparación:** Heurística voraz (Greedy), búsqueda aleatoria (Random Search) y escalarización lineal (Weighted Sum GA).
- **Validación matemática:** Demostración de convergencia en benchmark continuo ZDT1 ($IGD = 0.032$).
- **Experimentación rigurosa:** Batería con 15 semillas independientes y test de Wilcoxon ($p < 0.001$).

---

## Resultados Experimentales y Validación Estadística

### 1. Batería Estadística (15 Semillas Independientes)

Siguiendo las pautas de evaluación de la asignatura, todos los métodos se compararon bajo el mismo presupuesto computacional:

| Algoritmo | Hipervolumen (Media ± Std) | Spread $\Delta$ (Media) | $p$-valor vs NSGA-II (Wilcoxon) | Significativo ($p < 0.05$) |
| :--- | :---: | :---: | :---: | :---: |
| **NSGA-II (Propio)** | **11,620.8 ± 21.5** | **0.388** | **— (Referencia)** | — |
| **Greedy Baseline** | 10,287.1 ± 0.0 | 0.289 | $3.067 \times 10^{-6}$ | **Sí ($p < 0.001$)** |
| **Random Search** | 10,024.9 ± 151.6 | 0.473 | $3.067 \times 10^{-6}$ | **Sí ($p < 0.001$)** |
| **Weighted Sum GA** | 7,181.6 ± 269.3 | 0.924 | $3.067 \times 10^{-6}$ | **Sí ($p < 0.001$)** |

> **Conclusión estadística:** La superioridad de NSGA-II sobre la heurística voraz (+13.0%), la búsqueda aleatoria (+15.9%) y la suma ponderada (+61.8%) está demostrada con significancia estadística formal ($p < 0.0001$). La suma ponderada fracasa al no ser capaz de explorar frentes no convexos.

### 2. Validación Analítica en Benchmark ZDT1
* Implementación verificada sobre el benchmark estándar de Deb et al. (2002).
* **Inverted Generational Distance (IGD):** $0.0320$, demostrando convergencia visual y numérica contra el Frente de Pareto teórico exacto ($f_2 = 1 - \sqrt{f_1}$).

---

## Guía de Ejecución

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar la optimización de Gran Canaria (genera output/rutas_pareto.json y gráficas)
python main.py

# 3. Ejecutar la validación analítica ZDT1
python src/benchmarks/zdt.py

# 4. Ejecutar la batería estadística completa con 15 semillas y Wilcoxon
python src/benchmarks/statistical_suite.py
```