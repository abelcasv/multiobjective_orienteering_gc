# Memoria: Algoritmos, Experimentación y Validación (Modalidad C5)

**Autor:** Abel (Miembro 2: Optimization / AI Engineer)  
**Proyecto:** Optimización Multiobjetivo de Rutas Turísticas en Gran Canaria (MOOP)  
**Asignatura:** Optimización y Heurística (Grado en Ciencia e Ingeniería de Datos / IA)

Secciones de la memoria correspondientes al diseño algorítmico, líneas base, rigor experimental y validación analítica. Todas las cifras y tablas proceden de los ficheros generados en el repositorio y se pueden reproducir ejecutando `python main.py`, `python -m src.benchmarks.zdt` y `python -m src.benchmarks.statistical_suite`.

---

## 1. Algoritmo Propio: NSGA-II para MOOP

Para resolver el problema de orientación multiobjetivo (*Multi-Objective Orienteering Problem*, MOOP) definido en la sección de datos y modelo, se ha implementado desde cero el algoritmo genético de ordenamiento no dominado **NSGA-II** (*Non-dominated Sorting Genetic Algorithm II*, Deb et al., 2002), adaptándolo al espacio combinatorio de rutas de longitud variable.

### 1.1. Representación del Individuo y Espacio de Búsqueda

- **Cromosoma:** Un individuo se codifica como una lista ordenada de enteros $R = [g_1, g_2, \dots, g_k]$ sin duplicados, donde cada gen $g_j \in \{0, \dots, n-1\} \setminus \{h\}$ es el índice de un punto de interés (POI) a visitar.
- **Longitud variable:** La longitud $k$ no es fija ($2 \le k \le 30$). Esto permite que el algoritmo explore de forma simultánea itinerarios cortos y rápidos (como la opción *Express*, con 2 paradas) e itinerarios extensos que aprovechan al máximo la jornada (como la opción *Exhaustiva*, con 7 paradas).
- **Depósito implícito:** El hotel base (nodo depósito $h$, con puntuación 0 y tiempo de visita 0 min) no forma parte del cromosoma. Se añade de forma fija al inicio y al final durante la evaluación: la ruta física evaluada es siempre $[h, g_1, \dots, g_k, h]$.

### 1.2. Operadores Genéticos Adaptados

Dado que el problema requiere secuencias sin repetición de longitud variable, los operadores continuos estándar no son aplicables. Se han implementado operadores discretos especializados (`src/algorithms/genetic_algorithm.py`):

1. **Cruce de Preservación de Orden con Longitud Variable (*Single-Cut Preservation / Modified OX*):**
   - Se toma un punto de corte aleatorio en el primer progenitor $P_1$.
   - El primer descendiente recibe la primera parte de los genes de $P_1$.
   - El resto de posiciones se completa añadiendo los genes del segundo progenitor $P_2$ en el orden en que aparecen, ignorando los que ya estén presentes.
   - El segundo descendiente se construye de manera simétrica intercambiando los roles de $P_1$ y $P_2$.
   - La longitud de cada descendiente queda acotada entre 2 y el máximo de las longitudes de sus progenitores, permitiendo al algoritmo variar dinámicamente el número de paradas.

2. **Mutación Compuesta (4 Operadores Ponderados):**
   Para modificar tanto el subconjunto de lugares visitados como el orden del trayecto, cada mutación aplica uno de cuatro operadores con probabilidades calibradas:
   - **Inserción aleatoria (40 %):** Selecciona un POI disponible que no esté en la ruta y lo inserta en una posición aleatoria. Permite descubrir nuevas atracciones y aumentar la puntuación total.
   - **Eliminación aleatoria (30 %):** Suprime una parada al azar (siempre que la ruta tenga más de una). Esencial para reducir tiempo y reparar rutas que superan el límite de 8 h.
   - **Intercambio / *Swap* (20 %):** Intercambia la posición de dos paradas en la ruta. Permite reordenar el recorrido para aprovechar la asimetría de la red viaria sin cambiar los lugares visitados.
   - **Inversión de segmento (10 %):** Invierte el orden de un tramo completo entre dos posiciones elegidas al azar (operador 2-opt). Deshace bucles ineficientes en trayectos donde la ida y la vuelta se solapan.

### 1.3. Tratamiento de la Restricción ($T \le 480$ min): Reglas de Dominancia de Deb

En lugar de recurrir a penalizaciones artificiales en la función objetivo (que introducen hiperparámetros difíciles de ajustar), la restricción presupuestaria de tiempo ($T_{\max} = 480$ min = 8 h) se trata mediante el **criterio de dominancia con restricciones de Deb (2000)** (`Individual.dominates` en `src/core/problem.py`):

Definiendo la violación de un individuo como $V(R) = \max(0, T(R) - T_{\max})$:
1. Una solución **factible** ($V = 0$) domina a cualquier solución **no factible** ($V > 0$), sin importar la puntuación de esta última.
2. Entre dos soluciones **no factibles** ($V_A > 0, V_B > 0$), domina la que tenga **menor violación de tiempo** ($V_A < V_B$), guiando la población hacia el espacio admisible.
3. Entre dos soluciones **factibles** ($V_A = 0, V_B = 0$), se aplica la dominancia de Pareto convencional:
   $$R_A \succ R_B \iff (S_A \ge S_B \land T_A \le T_B) \land (S_A > S_B \lor T_A < T_B)$$

De este modo, las soluciones infactibles actúan como peldaños intermedios hacia rutas viables sin distorsionar la selección de las mejores opciones factibles.

### 1.4. Parámetros Elegidos y Justificación

| Parámetro | Valor | Justificación |
|---|:---:|---|
| Tamaño de población ($N$) | **100** | Mantiene suficiente diversidad genética a lo largo de todo el frente sin penalizar el coste por generación ($O(M N^2)$). |
| Número de generaciones ($G$) | **200** | Comprobado en las curvas de convergencia (`output/<hotel>/convergencia_nsga2.png`): el hipervolumen se estabiliza a partir de las generaciones 120–140. |
| Probabilidad de cruce ($p_c$) | **0,85** | Tasa alta para favorecer la recombinación de subrutas eficientes entre individuos distintos. |
| Probabilidad de mutación ($p_m$) | **0,35** | Moderadamente alta para compensar el espacio combinatorio discreto y evitar el estancamiento prematuro en óptimos locales. |
| Rango de inicialización | **3 a 7 POIs** | Las rutas iniciales se crean con un número de paradas cuyo tiempo estimado cae en un rango viable (150–350 min), acelerando la fase inicial de convergencia. |
| Presupuesto de evaluaciones | **20.100** | $N + N \times G = 100 + 100 \times 200 = \mathbf{20.100}$ evaluaciones de la función objetivo por corrida. |

---

## 2. Líneas Base de Comparación (Baselines)

La modalidad C5 exige comparar el algoritmo multiobjetivo propio frente a métodos de referencia:

### 2.1. Heurística Voraz Multiobjetivo (Greedy)
- **Construcción:** Partiendo del hotel, en cada paso evalúa todos los POIs no visitados. Para cada candidato $v$ calcula el coste marginal $C(u, v) = t_{uv} + \text{visita}_v$ y el ratio beneficio/coste $r = \text{score}_v / C(u, v)$. Selecciona el candidato con mayor ratio que permita regresar al hotel sin exceder un presupuesto de tiempo dado.
- **Frente Greedy:** Para obtener una curva comparable a la de NSGA-II, el algoritmo voraz se ejecuta barriendo presupuestos temporales desde 60 min hasta 480 min en pasos de 15 min ($\Delta t = 15$ min, 29 ejecuciones discretas).
- **Por qué Greedy no tiene presupuesto de evaluaciones por semilla:** El algoritmo voraz es **estrictamente determinista**. Para una matriz de tiempos y un catálogo de POIs dados, la regla de decisión miope siempre elige la misma secuencia de paradas. Su ejecución toma solo 4 milisegundos y su desviación típica entre semillas es exactamente 0,0. Repetir un algoritmo determinista con distintas semillas no aporta información estadística adicional; actúa como una cota inferior de referencia fija.

### 2.2. Búsqueda Aleatoria (Random Search)
- **Procedimiento:** Genera rutas seleccionando al azar una longitud entre 2 y 10 POIs y una muestra aleatoria de paradas sin reemplazo. Evalúa la ruta cerrada y descarta las que superen $T_{\max} = 480$ min.
- **Presupuesto equiparado:** Realiza **exactamente 20.100 evaluaciones** de la función objetivo por corrida, exactamente las mismas que NSGA-II.
- **Frente obtenido:** Se extraen las soluciones no dominadas de todo el conjunto de muestras factibles generadas.

### 2.3. Suma Ponderada (Weighted Sum GA)
- **Formulación:** Transforma los dos objetivos en uno solo mediante una combinación lineal normalizada con peso $w \in [0, 1]$:
  $$\max\; F(R, w) = w \cdot \frac{S(R)}{S_{\max}} - (1 - w) \cdot \frac{T(R)}{T_{\max}}$$
  donde $S_{\max}$ es la suma total de puntos del catálogo. Si la ruta es infactible, se penaliza con $-10^5 - 100 \cdot V$.
- **Presupuesto equiparado:** Se evalúan **10 pesos** ($w \in \{0{,}1; 0{,}2; 0{,}3; 0{,}4; 0{,}5; 0{,}6; 0{,}7; 0{,}8; 0{,}9; 0{,}95\}$). Para cada peso se ejecuta un algoritmo genético mono-objetivo con población de 30 individuos durante 66 generaciones:
  $$\text{Total evals} = 10 \text{ pesos} \times [30 + 30 \times 66] = 10 \times 2.010 = \mathbf{20.100} \text{ evaluaciones}$$
- **Por qué la suma ponderada obtiene resultados tan deficientes:**
  Los resultados experimentales reflejan un hipervolumen muy bajo (6.839 en Santa Catalina y 5.411 en Lopesan) y un Spread muy elevado ($\Delta > 1{,}07$). Esto se debe a dos razones fundamentales:
  1. **Incapacidad ante frentes no convexos:** Teóricamente, la suma ponderada solo puede encontrar soluciones situadas en la envoltura convexa (*convex hull*) del espacio de objetivos. Los problemas de rutas combinatorias con restricciones temporales presentan frentes intrínsecamente discontinuos y con zonas cóncavas; los puntos situados en esas regiones intermedias son matemáticamente inalcanzables para cualquier combinación lineal de pesos.
  2. **Colapso a un punto por peso:** Al optimizar una función escalar, toda la población del algoritmo genético converge hacia el único óptimo global para ese peso específico. Cada ejecución de 2.010 evaluaciones produce a lo sumo **un único punto no dominado**. Con 10 pesos, el método solo aporta entre 3 y 5 soluciones distintas en todo el frente, dejando enormes huecos vacíos y haciendo imposible cubrir el compromiso entre tiempo y puntuación.

---

## 3. Diseño Experimental y Rigor Estadístico

Siguiendo las pautas metodológicas de la asignatura:

1. **Mismo Presupuesto Computacional:**
   Todos los métodos estocásticos (NSGA-II, Random Search y Weighted Sum) se evalúan con exactamente **20.100 evaluaciones** de la función objetivo por corrida.
2. **15 Semillas Independientes:**
   Se utiliza una batería fija de 15 semillas pseudoaleatorias para garantizar reproducibilidad: $\{42, 101, 203, 314, 456, 578, 619, 723, 831, 954, 1024, 1234, 2048, 3072, 4096\}$.
3. **Métricas Multiobjetivo:**
   - **Hipervolumen ($HV$):** Mide el volumen del espacio de objetivos dominado por el frente respecto al punto de referencia peor admisible ($T_{\max} = 480$ min, $S_{\min} = 0$ pts). Captura conjuntamente la convergencia y la extensión del frente. Mayor valor indica mejor calidad.
   - **Spread ($\Delta$ de Deb):** Mide la uniformidad en la separación entre soluciones consecutivas y la extensión hacia los extremos del frente. Menor valor indica una distribución más homogénea.
4. **Test Estadístico de Hipótesis:**
   Dado que cada semilla evalúa los algoritmos bajo las mismas condiciones iniciales (muestras pareadas), se aplica el **test pareado de rangos con signo de Wilcoxon** (`scipy.stats.wilcoxon`, bilateral) sobre el hipervolumen entre NSGA-II y cada línea base, con un umbral de significancia $\alpha = 0{,}05$.

---

## 4. Resultados Experimentales y Discusión

Los resultados completos están guardados en `output/<hotel>/resumen_estadistico.json` y `resultados_estadisticos_semillas.csv`, y se visualizan en los diagramas de cajas de `output/<hotel>/boxplot_hipervolumen.png`.

### 4.1. Hotel Santa Catalina (Las Palmas)

| Algoritmo | Presupuesto | Hipervolumen (Media ± Std) | Spread $\Delta$ (Media) | $p$-valor vs NSGA-II | ¿Significativo? |
|---|:---:|:---:|:---:|:---:|:---:|
| **NSGA-II (Propio)** | **20.100** | **11.594,3 ± 24,5** | **0,428** | — (Referencia) | — |
| Greedy | Determ. ($T_{\max}$) | 10.188,9 ± 0,0 | 0,275 | $6{,}4 \times 10^{-4}$ | **Sí ($p < 0{,}001$)** |
| Random Search | **20.100** | 10.050,3 ± 99,9 | 0,447 | $6{,}1 \times 10^{-5}$ | **Sí ($p < 0{,}001$)** |
| Weighted Sum GA | **20.100** | 6.839,8 ± 490,3 | 1,076 | $6{,}1 \times 10^{-5}$ | **Sí ($p < 0{,}001$)** |

### 4.2. Hotel Lopesan Villa del Conde (Meloneras)

| Algoritmo | Presupuesto | Hipervolumen (Media ± Std) | Spread $\Delta$ (Media) | $p$-valor vs NSGA-II | ¿Significativo? |
|---|:---:|:---:|:---:|:---:|:---:|
| **NSGA-II (Propio)** | **20.100** | **10.013,1 ± 64,4** | **0,597** | — (Referencia) | — |
| Greedy | Determ. ($T_{\max}$) | 9.095,0 ± 0,0 | 0,346 | $6{,}1 \times 10^{-5}$ | **Sí ($p < 0{,}001$)** |
| Random Search | **20.100** | 8.694,5 ± 90,4 | 0,632 | $6{,}1 \times 10^{-5}$ | **Sí ($p < 0{,}001$)** |
| Weighted Sum GA | **20.100** | 5.411,4 ± 726,3 | 1,091 | $6{,}1 \times 10^{-5}$ | **Sí ($p < 0{,}001$)** |

### 4.3. Discusión de los Resultados
- **Superioridad estadística:** En ambos hoteles, NSGA-II obtiene un hipervolumen significativamente mayor que los tres baselines ($p < 0{,}001$). El valor $6{,}1 \times 10^{-5}$ es el $p$-valor mínimo posible del test exacto de Wilcoxon con $N=15$ pares: NSGA-II supera a la búsqueda aleatoria y a la suma ponderada en el 100 % de las semillas evaluadas.
- **Consistencia y estabilidad:** La desviación típica del hipervolumen de NSGA-II es de solo 24,5 unidades en Santa Catalina (un 0,2 % de la media) y 64,4 unidades en Lopesan (un 0,6 %), lo que confirma que el algoritmo converge de forma muy robusta y con escasa dependencia de la semilla inicial.
- **Efecto de la ubicación del hotel:** Desde Lopesan (sur), el hipervolumen medio de NSGA-II baja a 10.013,1 frente a 11.594,3 en Santa Catalina (una reducción del 13,6 %). Como se analizó en la sección de datos y modelo, la mayoría de los atractivos culturales con alta eficiencia (puntos por minuto) se ubican en el norte y medianías, forzando al turista del sur a invertir más tiempo en carretera (autopista GC-1) antes de realizar visitas efectivas.

---

## 5. Validación Analítica en Benchmark Estándar: ZDT1

Para validar el funcionamiento del algoritmo propio NSGA-II sobre un frente de Pareto conocido exactamente de antemano y sin interferencia de las particularidades del mapa de Gran Canaria, la modalidad C5 pide contrastar el algoritmo en un benchmark analítico continuo estándar.

Se implementó el problema bi-objetivo **ZDT1** (Zitzler, Deb & Thiele, 2000) con $m = 30$ variables continuas $x_i \in [0, 1]$ (`src/benchmarks/zdt.py`):
$$f_1(x) = x_1, \qquad g(x) = 1 + \frac{9}{m-1} \sum_{i=2}^{m} x_i, \qquad f_2(x) = g(x) \left[1 - \sqrt{\frac{f_1(x)}{g(x)}}\right]$$
El frente de Pareto teórico exacto se alcanza con $g(x) = 1$, dando la curva convexa $f_2 = 1 - \sqrt{f_1}$ para $f_1 \in [0, 1]$.

### 5.1. Operadores Continuos y Selección
- **Cruce:** *Simulated Binary Crossover* (SBX) con índice de distribución $\eta_c = 15{,}0$ y probabilidad $p_c = 0{,}9$.
- **Mutación:** Mutación polinomial con índice de distribución $\eta_m = 20{,}0$ y probabilidad $p_m = 1/m = 1/30$.
- **Selección:** Torneo binario aglomerado (*Crowded Tournament Selection* de Deb et al., 2002), seleccionando por rango de dominancia y desempatando por mayor distancia de aglomeración.
- **Configuración:** Población de 100 individuos, 250 generaciones y semilla fija (`seed=42`).

### 5.2. Medida de Convergencia (IGD) y Gráfica
- Se calcula la **Distancia Generacional Invertida** (*Inverted Generational Distance*, $IGD$) midiendo la distancia euclídea media desde 500 puntos uniformemente distribuidos sobre el frente teórico exacto hacia el punto más cercano obtenido por NSGA-II:
  $$IGD = \frac{1}{|P^*|} \sum_{v \in P^*} \min_{u \in P} \|u - v\|_2 = \mathbf{0{,}0210}$$
- **Conclusión de la validación:** Como se aprecia en la figura [`output/validacion_zdt1.png`](../output/validacion_zdt1.png), las 100 soluciones obtenidas cubren todo el rango $f_1 \in [0{,}000; 1{,}000]$ y se superponen sobre la curva teórica exacta. Esto valida formalmente que los módulos de ordenamiento no dominado rápido, asignación de aglomeración y reemplazo ambiental élite de la implementación funcionan con total corrección matemática.

---

## 6. Uso de Inteligencia Artificial

Se han usado asistentes de IA (Antigravity de Google DeepMind y Claude Code de Anthropic) como herramienta de soporte, depuración y contraste técnico en las siguientes tareas de esta parte:

1. **Refactorización y Clean Code de la arquitectura algorítmica.** La estructura inicial de los algoritmos se desarrolló por el autor y se utilizó el asistente de IA para revisar la modularidad según buenas prácticas de Clean Code (descomposición en métodos auxiliares de 5 a 10 líneas con responsabilidad única, reducción de parámetros y tipado estático estricto en `Individual` y `OrienteeringProblem`). El autor revisó y validó que la refactorización preservara exactamente la lógica de dominancia de Deb y la evaluación temporal.
2. **Diagnóstico y corrección en la validación continua de ZDT1.** Al contrastar la implementación analítica inicial de ZDT1 frente a la curva teórica, el autor detectó una dispersión incompleta hacia los extremos ($f_1 > 0{,}64$, IGD 0,1020). Se utilizó el asistente para auditar paso a paso el flujo de selección frente al artículo original de Deb et al. (2002), identificando que el torneo binario continuo omitía el desempate por distancia de aglomeración (*crowding distance*). Tras corregir el operador de torneo y fijar la semilla reproducible, el autor comprobó que la población cubría todo el frente ($f_1 \in [0, 1]$) con un IGD de **0,0210**, tal como refleja la gráfica actual.
3. **Auditoría del presupuesto computacional de las líneas base.** El autor diseñó la batería experimental sobre 20.100 evaluaciones para NSGA-II y recurrió al asistente para contrastar el recuento analítico de llamadas a la función objetivo en los baselines. Esto permitió corregir dos discrepancias previas en la suma ponderada (que en una versión temprana realizaba 11.070 evaluaciones y en otra 20.000), ajustando el bucle a $10 \text{ pesos} \times 30 \times (1 + 66) = \mathbf{20.100}$ evaluaciones exactas para cumplir con el rigor de presupuesto idéntico exigido por la rúbrica.
4. **Revisión del test de hipótesis estadístico.** La implementación inicial calculaba `scipy.stats.ranksums` (test de suma de rangos para muestras independientes). Al revisar con el asistente la adecuación metodológica a la batería de 15 semillas compartidas, se confirmó la necesidad de emplear un test para muestras pareadas, migrando a `scipy.stats.wilcoxon` (test de rangos con signo).
5. **Redacción y maquetación de la memoria.** El asistente de IA generó un borrador inicial de estas secciones a partir del código fuente y de los archivos de salida del repositorio (`resumen_estadistico.json` y `rutas_pareto.json`). El autor revisó, corrigió la redacción y verificó personalmente que cada ecuación, tabla y cifra fuera exacta y correspondiera a las ejecuciones reales.

La IA **no** se utilizó para generar soluciones sintéticas ni simular resultados experimentales. Todos los hipervolúmenes, tiempos de cómputo, frentes de Pareto y contrastes estadísticos proceden de ejecuciones reales del código en local.
