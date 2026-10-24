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
├── data/                                      # Datasets de entrada (ver data/README.md)
│   ├── santa_catalina/                        # Escenario 1: depósito en el Hotel Santa Catalina
│   │   ├── matriz_tiempos.csv                 # Matriz asimétrica 31x31 de tiempos de conducción (min)
│   │   ├── puntos_interes.csv                 # Puntuaciones (0-10) y tiempos de visita
│   │   └── coordenadas.csv                    # Latitud y longitud de cada nodo
│   ├── lopesan_villa_del_conde/               # Escenario 2: depósito en el Hotel Lopesan Villa del Conde
│   ├── auxiliar/                              # Matriz 32x32 con ambos hoteles y matriz sin factor global
│   └── README.md                              # Origen, licencia, calibración y limitaciones de los datos
├── output/                                    # Artefactos y resultados generados
│   ├── <escenario>/                           # Un directorio por hotel
│   │   ├── rutas_pareto.json                  # Rutas óptimas con coordenadas y desglose de tramos
│   │   ├── caminos_rutas.json                 # Recorrido por carretera de cada tramo (OSMnx)
│   │   ├── mapa_rutas.html                    # Mapa Folium de las 3 rutas recomendadas
│   │   ├── comparativa_pareto_vs_greedy.png   # Frente de Pareto vs Línea base Greedy
│   │   ├── convergencia_nsga2.png             # Curvas de Hipervolumen y Score factible
│   │   ├── boxplot_hipervolumen.png           # Boxplots estadísticos de los 4 algoritmos
│   │   ├── resultados_estadisticos_semillas.csv  # Registro detallado de las 15 semillas
│   │   └── resumen_estadistico.json           # Métricas agregadas y p-valores de Wilcoxon
│   ├── figuras/                               # Figuras para la memoria (scripts/make_figures.py)
│   └── validacion_zdt1.png                    # Validación analítica de NSGA-II en ZDT1
├── docs/
│   └── memoria_datos_y_modelo.md              # Secciones de la memoria: datos, matriz, calibración, modelo e IA
├── scripts/
│   ├── build_time_matrix.ipynb                # Construcción y calibración de la matriz (OSMnx + Google Maps)
│   ├── build_road_paths.py                    # Caminos por carretera de las rutas (OSMnx)
│   ├── make_maps.py                           # Mapas Folium a partir de rutas_pareto.json
│   └── make_figures.py                        # Mapa de POIs, calibración y frentes de Pareto
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
│   ├── pipeline.py                            # Orquestación del caso de Gran Canaria (por escenario)
│   └── __init__.py
├── main.py                                    # Punto de entrada principal
├── requirements.txt                           # Dependencias del proyecto (versiones fijadas)
└── README.md
```

---

## División de Roles

### Miembro 1: Data Engineer & Visualización
- Extracción de la red viaria real con OSMnx, cálculo de la matriz asimétrica de tiempos y calibración con Google Maps (`scripts/build_time_matrix.ipynb`).
- Datasets por hotel de coordenadas y atributos (`data/<escenario>/`), documentados en `data/README.md`.
- Visualización interactiva con **Folium** (`scripts/make_maps.py`) y figuras de la memoria (`scripts/make_figures.py`).

### Miembro 2: Optimization / AI Engineer
- **Algoritmo propio NSGA-II:** Cromosomas de longitud variable, selección por torneo de Deb con manejo de restricciones, operadores genéticos específicos y ordenamiento no dominado rápido.
- **Líneas base de comparación:** Heurística voraz (Greedy), búsqueda aleatoria (Random Search) y escalarización lineal (Weighted Sum GA).
- **Validación matemática:** Demostración de convergencia en benchmark continuo ZDT1 ($IGD = 0.0210$).
- **Experimentación rigurosa:** Batería con 15 semillas independientes y test de Wilcoxon ($p < 0.001$).

---

## Resultados Experimentales y Validación Estadística

### 1. Batería Estadística (15 Semillas Independientes)

Todos los métodos estocásticos se comparan con el mismo presupuesto de **20.100 evaluaciones** de la función objetivo por corrida (NSGA-II: 100 + 200×100; Random Search: 20.100; Weighted Sum: 10 pesos × 30 × (1 + 66)). Greedy es determinista. La comparación usa el test pareado de rangos con signo de Wilcoxon (`scipy.stats.wilcoxon`, bilateral) sobre el hipervolumen ($T_{\max} = 480$ min).

**Hotel Santa Catalina (Las Palmas)**

| Algoritmo | Hipervolumen (Media ± Std) | Spread $\Delta$ (Media) | p-valor vs NSGA-II | Mejora de NSGA-II |
| :--- | :---: | :---: | :---: | :---: |
| **NSGA-II (Propio)** | **11.594,3 ± 24,5** | 0,428 | — | — |
| Greedy | 10.188,9 ± 0,0 | 0,275 | $6{,}4 \times 10^{-4}$ | +13,8 % |
| Random Search | 10.050,3 ± 99,9 | 0,447 | $6{,}1 \times 10^{-5}$ | +15,4 % |
| Weighted Sum GA | 6.839,8 ± 490,3 | 1,076 | $6{,}1 \times 10^{-5}$ | +69,5 % |

**Hotel Lopesan Villa del Conde**

| Algoritmo | Hipervolumen (Media ± Std) | Spread $\Delta$ (Media) | p-valor vs NSGA-II | Mejora de NSGA-II |
| :--- | :---: | :---: | :---: | :---: |
| **NSGA-II (Propio)** | **10.013,1 ± 64,4** | 0,597 | — | — |
| Greedy | 9.095,0 ± 0,0 | 0,346 | $6{,}1 \times 10^{-5}$ | +10,1 % |
| Random Search | 8.694,5 ± 90,4 | 0,632 | $6{,}1 \times 10^{-5}$ | +15,2 % |
| Weighted Sum GA | 5.411,4 ± 726,3 | 1,091 | $6{,}1 \times 10^{-5}$ | +85,0 % |

> **Conclusión estadística:** en ambos escenarios NSGA-II obtiene un hipervolumen mayor que los tres baselines con diferencias significativas ($p < 0{,}001$). $6{,}1 \times 10^{-5}$ es el p-valor mínimo posible del test exacto con 15 pares: NSGA-II gana en las 15 semillas. La suma ponderada solo encuentra un punto por peso y no cubre el frente.

### 2. Validación Analítica en Benchmark ZDT1
* Implementación de NSGA-II validada formalmente sobre el benchmark analítico canónico continuo ZDT1 de Deb et al. (2002).
* Incorpora el operador de comparación por aglomeración (*Crowded Tournament Selection*) y operadores continuos SBX y mutación polinomial con semilla reproducible (seed=42).
* **Inverted Generational Distance (IGD):** **0.0210**, demostrando convergencia visual y numérica exacta a lo largo de todo el Frente de Pareto teórico ($f_1 \in [0, 1]$, $f_2 = 1 - \sqrt{f_1}$).

---

## Guía de Ejecución

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Optimización de Gran Canaria para los dos hoteles (o uno con --escenario santa_catalina)
#    Genera output/<escenario>/rutas_pareto.json y gráficas. Semilla fija (--seed, por defecto 42).
python main.py

# 3. Mapas Folium y figuras de la memoria (requieren el paso 2)
#    build_road_paths.py es opcional: calcula el recorrido por carretera (pip install osmnx scikit-learn;
#    descarga la red de OSM la primera vez). Sin él, los mapas dibujan los tramos en línea recta.
python scripts/build_road_paths.py
python scripts/make_maps.py
python scripts/make_figures.py

# 4. Validación analítica ZDT1
python -m src.benchmarks.zdt

# 5. Batería estadística completa con 15 semillas y Wilcoxon (~4 min, admite --escenario)
python -m src.benchmarks.statistical_suite
```
