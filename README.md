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
│   │   ├── caminos_todos_pares.json.gz        # Recorrido por carretera entre todos los pares de nodos (dashboard)
│   │   ├── mapa_rutas.html                    # Mapa Folium de las 3 rutas recomendadas
│   │   ├── comparativa_pareto_vs_greedy.png   # Frente de Pareto vs Línea base Greedy
│   │   ├── convergencia_nsga2.png             # Curvas de Hipervolumen y Score factible
│   │   ├── boxplot_hipervolumen.png           # Boxplots estadísticos de los 5 algoritmos
│   │   ├── resultados_estadisticos_semillas.csv  # Registro detallado de las 15 semillas
│   │   ├── resumen_estadistico.json           # Métricas agregadas y p-valores de Wilcoxon
│   │   ├── hiperparametros.csv                # Hipervolumen por combinación de hiperparámetros
│   │   ├── sensibilidad.csv                   # Frente por variante de visitas y puntuaciones
│   │   └── sensibilidad_pois.csv              # Frecuencia de cada POI en el frente por variante
│   ├── figuras/                               # Figuras para la memoria (scripts/make_figures.py)
│   ├── validacion_zdt1.png                    # Validación analítica de NSGA-II en ZDT1
│   └── validacion_zdt_familia.png             # Comparativa en familia ZDT (ZDT1, ZDT2 y ZDT3)
├── docs/
│   ├── estado_del_arte.md                     # Estado del arte del OP, TTDP y rutas turísticas
│   ├── memoria_datos_y_modelo.md              # Secciones de la memoria: datos, matriz, calibración, modelo e IA
│   ├── memoria_algoritmos_y_experimentacion.md  # Formulación x_ij, NSGA-II, baselines, estadística, ZDT e IA
│   ├── estudio_hiperparametros.md             # Estudio de población, generaciones, cruce y mutación
│   └── analisis_sensibilidad.md               # Sensibilidad a tiempos de visita y puntuaciones
├── scripts/
│   ├── build_time_matrix.ipynb                # Construcción y calibración de la matriz (OSMnx + Google Maps)
│   ├── build_road_paths.py                    # Caminos por carretera de las rutas (OSMnx)
│   ├── build_all_road_paths.py                # Caminos por carretera entre todos los pares de nodos
│   ├── make_maps.py                           # Mapas Folium a partir de rutas_pareto.json
│   ├── make_figures.py                        # Mapa de POIs, calibración y frentes de Pareto
│   ├── hyperparameter_study.py                # Estudio de hiperparámetros de NSGA-II (15 semillas)
│   └── sensitivity_analysis.py                # Análisis de sensibilidad a visitas y puntuaciones
├── src/                                       # Código fuente modular
│   ├── core/                                  # Modelos y métricas compartidas
│   │   ├── problem.py                         # OrienteeringProblem, Individual, GAConfig
│   │   └── metrics.py                         # Hipervolumen, Spread y Test de Wilcoxon
│   ├── algorithms/                            # Algoritmos de optimización
│   │   ├── genetic_algorithm.py               # NSGA-II con dominancia de Deb (2002)
│   │   ├── greedy_algorithm.py                # Heurística Voraz (Baseline)
│   │   ├── random_search.py                   # Búsqueda Aleatoria (Baseline)
│   │   ├── weighted_sum.py                    # Suma Ponderada / Escalarización (Baseline)
│   │   └── epsilon_constraint.py              # Método ε-restricción (Baseline)
│   ├── benchmarks/                            # Suite experimental exigida por rúbrica C5
│   │   ├── zdt.py                             # Validación matemática en benchmarks ZDT1, ZDT2 y ZDT3
│   │   └── statistical_suite.py               # Batería con 15 semillas + Test de Wilcoxon
│   ├── pipeline.py                            # Orquestación del caso de Gran Canaria (por escenario)
│   ├── planificador.py                        # optimizar_ruta: categorías, descartes y visita obligatoria
│   └── __init__.py
├── tests/                                     # Tests unitarios (unittest)
│   ├── test_constraints.py                    # Visita obligatoria y nodos prohibidos en el núcleo
│   └── test_planificador.py                   # optimizar_ruta con los datos reales
├── main.py                                    # Punto de entrada principal
├── dashboard.py                               # Dashboard de demostración (Streamlit)
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
- **Algoritmo propio NSGA-II:** Cromosomas de longitud variable, selección por torneo de Deb con manejo de restricciones, operadores genéticos específicos, reparación para restricciones duras y ordenamiento no dominado rápido ($O(M N^2)$).
- **Líneas base de comparación:** Heurística voraz (Greedy), búsqueda aleatoria (Random Search), suma ponderada (Weighted Sum GA) y $\varepsilon$-restricción ($\varepsilon$-Constraint GA).
- **Validación matemática:** Demostración de convergencia en benchmarks continuos ZDT1 ($IGD = 0.0210$), ZDT2 ($IGD = 0.0547$) y ZDT3 ($IGD = 0.0127$).
- **Experimentación rigurosa:** Batería con 15 semillas independientes y test de Wilcoxon ($p < 0.001$).

---

## Resultados Experimentales y Validación Estadística

### 1. Batería Estadística (15 Semillas Independientes)

Todos los métodos estocásticos se comparan con el mismo presupuesto de **20.100 evaluaciones** de la función objetivo por corrida (NSGA-II: 100 + 200×100; Random Search: 20.100; Weighted Sum y $\varepsilon$-Constraint: 10 subproblemas × 30 × (1 + 66)). Greedy es determinista. La comparación usa el test pareado de rangos con signo de Wilcoxon (`scipy.stats.wilcoxon`, bilateral) sobre el hipervolumen ($T_{\max} = 480$ min).

**Hotel Santa Catalina (Las Palmas)**

| Algoritmo | Hipervolumen (Media ± Std) | Spread $\Delta$ (Media) | p-valor vs NSGA-II | Mejora de NSGA-II |
| :--- | :---: | :---: | :---: | :---: |
| **NSGA-II (Propio)** | **11.594,3 ± 24,5** | 0,428 | — | — |
| Greedy | 10.188,9 ± 0,0 | 0,275 | $6{,}4 \times 10^{-4}$ | +13,8 % |
| Random Search | 10.050,3 ± 99,9 | 0,447 | $6{,}1 \times 10^{-5}$ | +15,4 % |
| Epsilon-Constraint GA | 9.711,9 ± 254,0 | 0,307 | $6{,}1 \times 10^{-5}$ | +19,4 % |
| Weighted Sum GA | 6.839,8 ± 490,3 | 1,076 | $6{,}1 \times 10^{-5}$ | +69,5 % |

**Hotel Lopesan Villa del Conde**

| Algoritmo | Hipervolumen (Media ± Std) | Spread $\Delta$ (Media) | p-valor vs NSGA-II | Mejora de NSGA-II |
| :--- | :---: | :---: | :---: | :---: |
| **NSGA-II (Propio)** | **10.013,1 ± 64,4** | 0,597 | — | — |
| Greedy | 9.095,0 ± 0,0 | 0,346 | $6{,}1 \times 10^{-5}$ | +10,1 % |
| Random Search | 8.694,5 ± 90,4 | 0,632 | $6{,}1 \times 10^{-5}$ | +15,2 % |
| Epsilon-Constraint GA | 8.389,8 ± 286,4 | 0,332 | $6{,}1 \times 10^{-5}$ | +19,3 % |
| Weighted Sum GA | 5.411,4 ± 726,3 | 1,091 | $6{,}1 \times 10^{-5}$ | +85,0 % |

> **Conclusión estadística:** en ambos escenarios NSGA-II obtiene un hipervolumen mayor que los cuatro baselines con diferencias significativas ($p < 0{,}001$), ganando en las 15 semillas evaluadas. $\varepsilon$-Constraint supera ampliamente a la suma ponderada (+42 % y +55 %) al poder cubrir cotas temporales en zonas no convexas, pero queda limitado a un máximo de 10 puntos discretos frente al frente continuo generado por NSGA-II.

### 2. Validación Analítica en Benchmarks ZDT1, ZDT2 y ZDT3
* Implementación de NSGA-II validada formalmente sobre tres benchmarks canónicos continuos de la familia ZDT (Zitzler, Deb & Thiele, 2000): **ZDT1** (frente convexo), **ZDT2** (frente cóncavo) y **ZDT3** (frente discontinuo en 5 tramos).
* Incorpora *Crowded Tournament Selection*, SBX y mutación polinomial con semilla reproducible (`seed=42`).
* **Inverted Generational Distance (IGD):** **0.0210** (ZDT1), **0.0547** (ZDT2) y **0.0127** (ZDT3), demostrando convergencia visual y numérica exacta a lo largo de las tres geometrías de frente (`output/validacion_zdt_familia.png`).

---

## Guía de Ejecución

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Optimización de Gran Canaria para los dos hoteles (o uno con --escenario santa_catalina)
#    Genera output/<escenario>/rutas_pareto.json y gráficas. Semilla fija (--seed, por defecto 42).
python main.py

# 3. Mapas Folium y figuras de la memoria (requieren el paso 2)
#    build_road_paths.py es opcional: calcula el recorrido por carretera con OSMnx
#    (descarga la red de OSM la primera vez). Sin él, los mapas dibujan los tramos en línea recta.
python scripts/build_road_paths.py
python scripts/make_maps.py
python scripts/make_figures.py

# 4. Validación analítica ZDT1
python -m src.benchmarks.zdt

# 5. Batería estadística completa con 15 semillas y Wilcoxon (~4 min, admite --escenario)
python -m src.benchmarks.statistical_suite

# 6. Estudio de hiperparámetros (~15 min) y análisis de sensibilidad (~5 min), con 8 procesos
#    en paralelo (admiten --escenario y --jobs)
python scripts/hyperparameter_study.py
python scripts/sensitivity_analysis.py

# 7. Tests unitarios (~10 s)
python -m unittest discover -s tests -v

# 8. Dashboard de demostración (http://localhost:8501). Usa los caminos precalculados de
#    output/<escenario>/caminos_todos_pares.json.gz, que ya están en el repositorio; solo hace
#    falta regenerarlos (~1 min, requiere el grafo de build_road_paths.py) si cambian los datos.
python scripts/build_all_road_paths.py
streamlit run dashboard.py
```
