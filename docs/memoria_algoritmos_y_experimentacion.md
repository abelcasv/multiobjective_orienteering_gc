# Memoria: Formulación Matemática, Algoritmos, Experimentación y Validación (Modalidad C5)

**Autor:** Abel (Miembro 2: Optimization / AI Engineer)  
**Proyecto:** Optimización Multiobjetivo de Rutas Turísticas en Gran Canaria (MOOP)  
**Asignatura:** Optimización y Heurística (Grado en Ciencia e Ingeniería de Datos / IA)

Secciones de la memoria correspondientes al estado del arte algorítmico, formulación matemática formal del modelo, diseño e implementación de NSGA-II y de las líneas base, rigor experimental y validación analítica. Todas las cifras, tablas y gráficas proceden de los ficheros generados en el repositorio y son reproducibles mediante `python main.py`, `python -m src.benchmarks.zdt`, `python -m src.benchmarks.statistical_suite` y `python -m unittest discover -s tests -v`.

---

## 1. Estado del Arte: Métodos Multiobjetivo, Escalarización e Indicadores

La planificación de rutas turísticas se encuadra dentro del problema de orientación (*Orienteering Problem*, OP) y, en particular, de su variante bicriterio (*Tourist Trip Design Problem* y *TSPs with Profits*), cuyo origen y aplicaciones turísticas se detallan en [`estado_del_arte.md`](estado_del_arte.md). Desde el punto de vista metodológico y algorítmico (modalidad C5), existen dos grandes enfoques para abordar problemas combinatorios multiobjetivo y un marco estándar de evaluación cuantitativa:

### 1.1. Métodos Clásicos de Escalarización

Los métodos de optimización multiobjetivo a priori o de generación paramétrica transforman el problema vectorial en una secuencia de subproblemas escalares mono-objetivo (Miettinen, 1999; Ehrgott, 2005):

- **Método de la Suma Ponderada (*Weighted Sum*):** Combina linealmente los objetivos normalizados mediante un vector de pesos no negativos $w$. Presenta una limitación teórica conocida (Das & Dennis, 1997): toda solución obtenida optimizando una combinación lineal convexa de los objetivos se apoya necesariamente sobre un hiperplano soporte, por lo que el método **solo puede recuperar soluciones situadas en la envoltura convexa** (*convex hull*) inferior del espacio de objetivos. En problemas combinatorios discretos, donde los frentes de Pareto son finitos, escalonados y frecuentemente no convexos, amplias zonas intermedias de compromiso quedan matemáticamente inalcanzables independientemente del peso elegido.
- **Método de $\varepsilon$-Restricción ($\varepsilon$-Constraint):** Introducido por Haimes et al. (1971) y sistematizado en su versión lexicográfica/aumentada por Mavrotas (2009), consiste en optimizar uno solo de los objetivos manteniendo los demás acotados por parámetros umbral $\varepsilon$. A diferencia de la suma ponderada, el método de $\varepsilon$-restricción **no requiere convexidad del frente** y es capaz de acceder a soluciones situadas en regiones cóncavas o discontinuas (como mostraron Bérubé et al., 2009 para el TSP bicriterio con beneficios). No obstante, su eficacia depende de discretizar adecuadamente la malla de umbrales y requiere resolver tantos problemas independientes como puntos del frente se deseen aproximar.

### 1.2. Algoritmos Evolutivos Multiobjetivo (MOEAs)

Para superar las limitaciones de la escalarización y aproximar el frente de Pareto completo en una única ejecución, los algoritmos evolutivos multiobjetivo trabajan sobre una población completa de soluciones candidatas en paralelo (Coello Coello et al., 2007). Entre ellos destaca **NSGA-II** (*Non-dominated Sorting Genetic Algorithm II*, Deb et al., 2002), referencia estándar en la literatura gracias a tres mecanismos combinados:

1. **Ordenamiento no dominado rápido** (*fast non-dominated sort*), que estratifica la población por niveles de dominancia de Pareto.
2. **Distancia de aglomeración** (*crowding distance*), estimador sin parámetros adicionales de la densidad local en el espacio de objetivos que promueve la diversidad uniforme a lo largo del frente.
3. **Elitismo combinado ($R_t = P_t \cup Q_t$)** con torneo binario aglomerado y manejo nativo de restricciones sin funciones de penalización mediante el **principio de dominancia con restricciones de Deb (2000)**.

### 1.3. Benchmarks Analíticos e Indicadores de Calidad

En optimización multiobjetivo no basta con comparar un valor escalar final; la literatura exige evaluar simultáneamente la **convergencia** hacia el frente óptimo y la **diversidad/extensión** a lo largo de los compromisos (Audet et al., 2021):

- **Familia analítica ZDT (Zitzler, Deb & Thiele, 2000):** Conjunto de funciones continuas de prueba con frente de Pareto teórico conocido en forma cerrada, diseñadas para validar algoritmos multiobjetivo ante frentes convexos (ZDT1), cóncavos/no convexos (ZDT2) y discontinuos (ZDT3).
- **Hipervolumen ($HV$, Zitzler & Thiele, 1999):** Único indicador unario estándar estrictamente monótono respecto a la dominancia de Pareto; mide la medida de Lebesgue del espacio de objetivos dominado por el frente respecto a un punto de referencia peor admisible, sintetizando en una sola métrica convergencia y extensión.
- **Spread ($\Delta$, Deb et al., 2002):** Mide la uniformidad de espaciado entre soluciones consecutivas en el frente aproximado (menor valor indica distribución más homogénea).
- **Distancia Generacional Invertida ($IGD$, Coello Coello et al., 2007):** Mide la distancia media desde un conjunto denso de puntos de referencia sobre el frente teórico exacto hacia la solución más cercana obtenida por el algoritmo (solo aplicable en benchmarks con frente real conocido).
- **Validación estadística no paramétrica:** Al comparar metaheurísticas estocásticas con distribuciones no necesariamente gaussianas sobre las mismas semillas independientes, se recomienda el test pareado de rangos con signo de Wilcoxon (1945) acompañado de estadísticas descriptivas robustas.

---

## 2. Formulación Matemática Formal y Clasificación del Problema

En coherencia estricta con la notación definida en [`memoria_datos_y_modelo.md`](memoria_datos_y_modelo.md), se formula a continuación el modelo matemático completo de programación entera lineal mixta (MILP) en variables de arco $x_{ij}$ para cada escenario (hotel base), su equivalencia con la codificación cromosómica por secuencia empleada por NSGA-II y su clasificación formal.

### 2.1. Conjuntos y Parámetros

- **Depósito (hotel base):** $h$, con puntuación turística nula ($s_h = 0$) y tiempo de visita nulo ($v_h = 0$).
- **Conjunto de puntos de interés (POIs):** $P = \{1, \dots, n\}$ ($n = 30$ en ambos escenarios).
- **Conjunto total de nodos:** $V = \{h\} \cup P$ ($|V| = 31$).
- **Matriz asimétrica de conducción:** $t_{ij} \ge 0$ para todo $i, j \in V$ ($t_{ii} = 0$), que representa los minutos de desplazamiento por la red viaria calibrada de Gran Canaria del nodo $i$ al nodo $j$.
- **Atributos de cada POI $i \in P$:** puntuación turística $s_i > 0$ y tiempo de visita física $v_i > 0$ (en minutos).
- **Presupuesto temporal máximo:** $T_{\max} = 480$ minutos (8 horas, modificable en el planificador).
- **Preferencias del turista:** dadas las categorías marcadas $C^* \subseteq \mathcal{C}$, los lugares descartados $E \subseteq P$ y la visita obligatoria opcional $m \in P$ ($m \notin E$), sea el conjunto de nodos prohibidos:
  $$F = \bigl(\{\, i \in P : C(i) \cap C^* = \emptyset \,\} \cup E\bigr) \setminus \{m\} \subseteq P,$$
  y el conjunto de POIs permitidos $P' = P \setminus F$. En el caso base sin filtros ($C^* = \mathcal{C},\; E = \emptyset$, sin obligatorio), $F = \emptyset$ y $P' = P$.

### 2.2. Variables de Decisión

1. $x_{ij} \in \{0, 1\}$ para todo $i, j \in V$ con $i \ne j$: toma el valor $1$ si la ruta turística recorre directamente el arco dirigido $(i, j)$, y $0$ en caso contrario.
2. $y_i \in \{0, 1\}$ para todo $i \in V$: toma el valor $1$ si el nodo $i$ es visitado en la ruta, y $0$ si no se visita (fijando $y_h = 1$).
3. $u_i \in \mathbb{R}$ para todo $i \in P$: variable auxiliar de posición relativa de visita en la ruta, empleada para la eliminación de subciclos mediante las restricciones de Miller–Tucker–Zemlin (MTZ).

### 2.3. Funciones Objetivo y Restricciones (Formulación MILP con $x_{ij}$)

$$\max\; f_1(x, y) = \sum_{i \in P} s_i\, y_i \qquad \text{(Maximizar valor turístico total)}$$

$$\min\; f_2(x, y) = \sum_{i \in V} \sum_{\substack{j \in V \\ j \ne i}} t_{ij}\, x_{ij} + \sum_{i \in P} v_i\, y_i \qquad \text{(Minimizar tiempo total: conducción + visitas)}$$

sujeto a:

1. **Salida y retorno único al hotel base $h$:**
   $$\sum_{j \in P} x_{hj} = 1, \qquad \sum_{i \in P} x_{ih} = 1$$
2. **Conservación de flujo y acoplamiento con la visita en cada POI $k \in P$:**
   $$\sum_{\substack{i \in V \\ i \ne k}} x_{ik} = y_k, \qquad \sum_{\substack{j \in V \\ j \ne k}} x_{kj} = y_k \qquad \forall k \in P$$
3. **Restricción de presupuesto temporal:**
   $$\sum_{i \in V} \sum_{\substack{j \in V \\ j \ne i}} t_{ij}\, x_{ij} + \sum_{i \in P} v_i\, y_i \le T_{\max}$$
4. **Eliminación de subciclos (Miller–Tucker–Zemlin, 1960):**
   $$u_i - u_j + |P|\, x_{ij} \le |P| - 1 \quad \forall i, j \in P,\; i \ne j, \qquad 1 \le u_i \le |P| \quad \forall i \in P$$
   Si un arco $x_{ij} = 1$ se activa entre dos POIs, entonces $u_j \ge u_i + 1$, lo que impide la formación de ciclos cerrados desconectados que no pasen por el hotel $h$.
5. **Preferencias del turista (restricciones duras):**
   $$y_i = 0 \quad \forall i \in F \quad \text{(exclusión de nodos prohibidos)}$$
   $$y_m = 1 \quad \text{(inclusión obligatoria del nodo } m\text{, si está definido con } m \in P'\text{)}$$
6. **Dominio de las variables:**
   $$x_{ij} \in \{0, 1\} \;\; \forall i \ne j, \qquad y_i \in \{0, 1\} \;\; \forall i \in V,\; y_h = 1$$

### 2.4. Relación entre la Formulación $x_{ij}$ y la Representación por Secuencia

En lugar de evolucionar matrices binarias $x \in \{0, 1\}^{31 \times 30}$ (espacio de tamaño $2^{930}$ donde la inmensa mayoría de asignaciones violan la conservación de flujo o contienen subciclos), NSGA-II y los baselines operan sobre la **representación compacta por secuencia de longitud variable** $R = (r_1, \dots, r_k)$ sin duplicados, con $k \ge 1$ y $r_j \in P'$:

- **Correspondencia directa (Secuencia $\to$ MILP):** Toda secuencia sin repeticiones $R = (r_1, \dots, r_k)$ define unívocamente una ruta cerrada $h \to r_1 \to \dots \to r_k \to h$ mediante:
  - $y_{r_j} = 1$ para $j = 1, \dots, k$, $y_h = 1$, y $y_i = 0$ para el resto;
  - $x_{h r_1} = 1$, $x_{r_j r_{j+1}} = 1$ para $j = 1, \dots, k-1$, $x_{r_k h} = 1$, y $x_{ab} = 0$ en los demás arcos;
  - $u_{r_j} = j$ para $j = 1, \dots, k$ (y $u_i = 1$ para $i \notin R$).
- **Recíproco (MILP $\to$ Secuencia):** Toda solución $(x, y, u)$ que cumple las restricciones (1), (2) y (4) describe un único ciclo simple dirigido que parte de $h$ y regresa a $h$, generando de forma unívoca la lista ordenada $R = (r_1, \dots, r_k)$ de POIs visitados con $y_{r_j} = 1$.
- **Invariantes por construcción:** Esta biyección garantiza *a priori* las restricciones de salida/retorno al hotel, conservación de flujo y ausencia de subciclos (y, junto con el operador de reparación de cromosomas de la sección 3.3, garantiza también las restricciones de preferencias $F$ y $m$). Como consecuencia, el único criterio de factibilidad que deben resolver dinámicamente las reglas de Deb durante la evolución es la restricción presupuestaria $T(R) \le T_{\max}$.

### 2.5. Clasificación Formal del Problema

El problema planteado queda clasificado formalmente según las categorías de la optimización matemática como:

| Dimensión | Clasificación | Justificación |
|---|---|---|
| **Variables** | **Discreto / Combinatorio** | Selección de un subconjunto variable de POIs $R \subseteq P'$ y de su permutación óptima en un grafo asimétrico ($x_{ij}, y_i \in \{0, 1\}$). |
| **Objetivos** | **Multiobjetivo (Bi-objetivo en conflicto)** | Maximizar $f_1$ (puntuación) y minimizar $f_2$ (tiempo total) están en conflicto directo: añadir paradas o visitar zonas alejadas aumenta $f_1$ a costa de incrementar $f_2$. |
| **Geometría del frente** | **No lineal y No convexo** | El frente de Pareto en el espacio de objetivos es discreto, discontinuo y no convexo; soluciones de compromiso intermedias no pertenecen a la envoltura convexa. |
| **Restricciones** | **Con restricciones duras** | Límite de presupuesto temporal $T_{\max}$ (tratado mediante dominancia restringida de Deb) más exclusión de $F$ e inclusión obligatoria de $m$. |
| **Incertidumbre** | **Determinista** | Todos los tiempos de viaje $t_{ij}$, puntuaciones $s_i$ y tiempos de visita $v_i$ son conocidos de forma determinista para cada instancia. |
| **Complejidad teórica** | **NP-difícil** | Generaliza el *Orienteering Problem* mono-objetivo (Golden et al., 1987) y contiene el Problema del Viajante (TSP) como caso particular ($s_i = 1$, $T_{\max}$ igual al tour óptimo TSP). No existen algoritmos exactos de tiempo polinómico conocidos, lo que justifica el diseño de NSGA-II. |

---

## 3. Algoritmo Propio: NSGA-II para MOOP

Para resolver el problema definido en la sección anterior, se ha implementado desde cero el algoritmo evolutivo **NSGA-II** (*Non-dominated Sorting Genetic Algorithm II*, Deb et al., 2002), adaptado al espacio combinatorio de rutas de longitud variable (`src/algorithms/genetic_algorithm.py`).

### 3.1. Representación del Individuo y Espacio de Búsqueda

- **Cromosoma:** Un individuo se codifica como una lista ordenada de enteros $R = [g_1, g_2, \dots, g_k]$ sin duplicados, donde cada gen $g_j \in P' = P \setminus F$ es el índice de un POI permitido.
- **Longitud variable:** La longitud $k$ no es fija a priori y evoluciona dinámicamente con los operadores genéticos. En las rutas finales del frente de Pareto sin filtros, las soluciones factibles abarcan desde **1 hasta 7 paradas en Santa Catalina (1 a 6 en Lopesan)**. La cota superior de seguridad del cruce está fijada en 12 nodos (`max_len = 12` en `crossover`), dado que en la práctica ninguna solución factible del frente llega a superar las 7 paradas.
- **Depósito implícito:** El hotel base $h$ no forma parte del cromosoma y se añade al principio y al final al evaluar el tiempo de conducción en `Individual._compute_driving_time`: $[h, g_1, \dots, g_k, h]$.

### 3.2. Operadores Genéticos Adaptados

Dado que el problema requiere secuencias sin repetición de longitud variable, se han diseñado operadores discretos específicos (`src/algorithms/genetic_algorithm.py`):

1. **Cruce de Preservación de Orden con Acotación (*Single-Cut Preservation with Remainder*):**
   - Toma un punto de corte aleatorio en el primer progenitor $P_1$ y copia el prefijo hasta el corte al primer descendiente.
   - Añade los genes del segundo progenitor $P_2$ ausentes en el prefijo, manteniendo su orden relativo de aparición.
   - Recorta la lista resultante a un máximo de `max_len = 12` genes (`child_genes[:max_len]`).
   - Construye el segundo descendiente de forma simétrica intercambiando $P_1$ y $P_2$.
   - **Comportamiento sobre la longitud:** Al concatenar el prefijo de un padre con los genes no presentes del otro, el cruce tiende a producir hijos más largos que sus padres. El crecimiento queda contenido por el límite `max_len = 12`, el operador de eliminación (30 %) y, principalmente, la presión selectiva de las reglas de Deb hacia $T \le 480$ min.

2. **Mutación Compuesta (4 Operadores):**
   En cada mutación se elige un único operador con probabilidades fijadas de forma empírica:
   - **Inserción aleatoria (40 %):** Inserta en una posición aleatoria un POI de `candidates` ($P'$) que no esté en la ruta.
   - **Eliminación aleatoria (30 %):** Suprime una parada al azar (siempre que la ruta tenga más de una y protegiendo expresamente el `mandatory_node` si está presente).
   - **Intercambio / *Swap* (20 %):** Permuta dos paradas para explotar la asimetría de la matriz de tiempos.
   - **Inversión de segmento (10 %):** Invierte un subsegmento completo entre dos índices aleatorios (movimiento tipo 2-opt para deshacer cruces ineficientes).

### 3.3. Operador de Reparación del Cromosoma y Garantía de Restricciones Duras

Para dar soporte al planificador interactivo (`src/planificador.py` y `dashboard.py`), cuando el turista fija un conjunto de nodos prohibidos $F$ (`forbidden_nodes`) y/o una parada obligatoria $m$ (`mandatory_node`), las rutas deben cumplir estrictamente las preferencias como **restricciones duras**. La arquitectura garantiza estas invariantes mediante cuatro mecanismos coordinados:

1. **Validación estructural temprana (*Fail Fast*):** Al instanciar `OrienteeringProblem.__post_init__` (`src/core/problem.py`), se verifica que $m \ne h$, que $0 \le m < |V|$ y que $m \notin F$, lanzando `ValueError` ante cualquier especificación contradictoria. Además, `available_nodes()` filtra $h$ y todos los nodos de $F$ para construir la lista de candidatos $P'$.
2. **Función pura `_repair_chromosome(genes, problem)`:** Dadas una secuencia arbitraria `genes` y la instancia del problema, ejecuta en $O(k)$:
   - *Paso 1 (Filtrado de prohibidos y unicidad):* Recorre `genes` en orden e incorpora cada gen $g$ a `repaired` únicamente si $g \notin F$ y $g \notin \text{seen}$ (usando un conjunto auxiliar `seen`), preservando íntegramente el orden relativo de las subrutas heredadas del cruce.
   - *Paso 2 (Garantía de visita obligatoria):* Si existe $m$ y $m \notin \text{seen}$, inserta $m$ en una posición aleatoria uniforme dentro de `repaired` (`random.randint(0, len(repaired))`).
3. **Protección específica en mutación (`_remove_random_node`):** Si se selecciona el operador de eliminación y existe $m$, el conjunto de índices eliminables se restringe a $\{i : g_i \ne m\}$. Esto evita que la mutación borre el nodo obligatorio para que `_repair_chromosome` tenga que reinsertarlo en un índice arbitrario destruyendo la posición optimizada durante la evolución.
4. **Aplicación sistemática en el ciclo evolutivo:** `_repair_chromosome` se invoca tras el muestreo aleatorio en `_create_random_individual`, inmediatamente después del `crossover` (o de copiar progenitores sin cruce) en `_create_offspring`, y al final de cada llamada a `mutate` (tanto en `NSGA2Orienteering` como en `WeightedSumGA` y `EpsilonConstraintGA`).

**Por qué toda solución devuelta cumple siempre las restricciones:** Por inducción sobre las generaciones, todo individuo de la población inicial pasa por `_repair_chromosome` antes de ser evaluado, y todo descendiente generado en `_create_offspring` pasa por `_repair_chromosome` tras el cruce y tras la mutación antes de evaluarse. Dado que $m \notin F$ por validación en constructor, `_repair_chromosome` es idempotente respecto a la factibilidad combinatoria: en todo individuo evaluado $R$ se cumple $R \subseteq P'$, ausencia de duplicados y $m \in R$. Si el viaje directo de ida y vuelta al nodo obligatorio supera el presupuesto ($t_{hm} + v_m + t_{mh} > T_{\max}$), la reparación mantiene $m \in R$ pero todos los individuos tendrán $V(R) > 0$, por lo que `_extract_unique_feasible_pareto` devuelve un frente vacío (`[]`) sin vulnerar jamás $T_{\max}$ (propiedad verificada automáticamente en `tests/test_constraints.py` y `tests/test_planificador.py`).

### 3.4. Tratamiento de la Restricción $T \le T_{\max}$: Reglas de Dominancia de Deb

La restricción temporal ($T_{\max} = 480$ min en el estudio base) se trata mediante el **criterio de dominancia con restricciones de Deb (2000)** (`Individual.dominates`). Sea la violación temporal $V(R) = \max(0, T(R) - T_{\max})$:

1. Una solución **factible** ($V = 0$) domina a cualquier solución **no factible** ($V > 0$), independientemente de su puntuación.
2. Entre dos soluciones **no factibles** ($V_A > 0, V_B > 0$), domina la de **menor violación temporal** ($V_A < V_B$).
3. Entre dos soluciones **factibles** ($V_A = 0, V_B = 0$), se aplica la dominancia de Pareto bi-objetivo:
   $$R_A \succ R_B \iff (S_A \ge S_B \land T_A \le T_B) \land (S_A > S_B \lor T_A < T_B)$$

### 3.5. Pseudocódigo y Complejidad Computacional de NSGA-II

```text
ALGORITMO NSGA-II para MOOP(problem, N, G, p_c, p_m)
  candidates <- problem.available_nodes()                       // P \ F
  P_0 <- []
  PARA i = 1 HASTA N HACER
      genes <- muestrear entre [min_init, max_init] nodos de candidates
      ind <- Individual(_repair_chromosome(genes, problem))
      ind.evaluate(problem)
      P_0 <- P_0 ∪ {ind}
  FIN PARA

  PARA g = 1 HASTA G HACER
      Q_g <- []                                                 // Descendencia de tamaño N
      MIENTRAS |Q_g| < N HACER
          p1 <- torneo_binario_aglomerado(P_{g-1})
          p2 <- torneo_binario_aglomerado(P_{g-1})
          SI random() < p_c ENTONCES
              c1_raw, c2_raw <- crossover(p1, p2, max_len=12)
          SINO
              c1_raw, c2_raw <- copia(p1), copia(p2)
          FIN SI
          c1 <- Individual(_repair_chromosome(c1_raw.genes, problem))
          c2 <- Individual(_repair_chromosome(c2_raw.genes, problem))
          SI random() < p_m ENTONCES c1 <- mutate(c1, candidates, problem)
          SI random() < p_m ENTONCES c2 <- mutate(c2, candidates, problem)
          evaluar(c1, problem); evaluar(c2, problem)
          Q_g <- Q_g ∪ {c1, c2}
      FIN MIENTRAS

      R_g <- P_{g-1} ∪ Q_g[1..N]                                // Población combinada 2N
      Frentes <- fast_non_dominated_sort(R_g)                   // Usando dominancia de Deb
      P_g <- []; i <- 1
      MIENTRAS |P_g| + |Frentes[i]| <= N HACER
          calculate_crowding_distance(Frentes[i])
          P_g <- P_g ∪ Frentes[i]
          i <- i + 1
      FIN MIENTRAS
      SI |P_g| < N ENTONCES
          calculate_crowding_distance(Frentes[i])
          ordenar Frentes[i] por crowding_distance descendente
          P_g <- P_g ∪ Frentes[i][1 .. N - |P_g|]
      FIN SI
      registrar mejor score factible e hipervolumen(P_g)
  FIN PARA
  DEVOLVER soluciones únicas no dominadas y factibles de Frentes[1] en P_G
```

**Análisis de complejidad temporal por generación ($M = 2$ objetivos, población $N = 100$, longitud máxima de cromosoma acotada $k_{\max} = 12$):**

1. **Reproducción, reparación y evaluación de $N$ descendientes:** cada cruce y reparación recorre a lo sumo $k$ genes con búsquedas en conjunto hash en $O(k_{\max})$, y la evaluación suma $k_{\max} + 1$ tiempos de la matriz en $O(k_{\max})$. Coste total de generación de hijos: $O(N \cdot k_{\max})$.
2. **Ordenamiento no dominado rápido (`fast_non_dominated_sort`):** sobre la población combinada $R_g$ de tamaño $2N$, el cálculo inicial de dominancia enfrenta cada par $(p, q)$ comparando los $M$ objetivos y la violación temporal, con coste $O\bigl(M (2N)^2\bigr) = O(M N^2)$; la asignación iterativa de rangos recorre cada arista del grafo de dominancia una sola vez en $O(N^2)$.
3. **Distancia de aglomeración (`calculate_crowding_distance`):** en el peor caso en que un frente contenga $O(N)$ individuos, requiere ordenar dicho frente una vez por cada objetivo en $O(M N \log N)$.

Por consiguiente, la complejidad asintótica por generación viene dominada por el ordenamiento no dominado rápido:
$$T_{\text{generación}} = O(M N^2 + M N \log N + N \cdot k_{\max}) = \mathbf{O(M N^2)},$$
y para una ejecución completa de $G$ generaciones el coste total es **$O(G \cdot M N^2)$**. Con $M = 2$, $N = 100$ y $G = 200$, el coste por ejecución es reducido (~14,5–17,4 s medidos dentro del bucle completo de la batería estadística en nuestro entorno), permitiendo además su ejecución interactiva en el dashboard de Streamlit.

### 3.6. Parámetros Elegidos y Justificación

Los hiperparámetros de NSGA-II se fijaron de forma empírica y se contrastaron posteriormente con un estudio específico de hiperparámetros sobre las mismas 15 semillas y 20.100 evaluaciones ([`estudio_hiperparametros.md`](estudio_hiperparametros.md)). Ninguna de las 11 alternativas probadas mejora el hipervolumen de la configuración base de forma estadísticamente significativa en ambos hoteles, mientras que una mutación demasiado baja ($p_m = 0{,}15$) sí lo degrada.

| Parámetro | Valor | Justificación empírica |
|---|:---:|---|
| Tamaño de población ($N$) | **100** | Mantiene diversidad genética a lo largo de todo el frente manteniendo bajo el coste $O(M N^2)$. |
| Número de generaciones ($G$) | **200** | Con la semilla 42 en Santa Catalina, el hipervolumen alcanza el **99 % de su valor final en la generación 139** (11.472 de 11.580) y continúa mejorando lentamente hasta la 200 (`convergencia_nsga2.png`). |
| Probabilidad de cruce ($p_c$) | **0,85** | Tasa estándar elevada para recombinar subrutas eficientes de los progenitores. |
| Probabilidad de mutación ($p_m$) | **0,35** | Moderadamente alta para explorar el espacio combinatorio discreto y evitar estancamiento prematuro. |
| Rango de inicialización | **3 a 7 POIs** | Muestreo aleatorio sin reemplazo de entre 3 y 7 paradas permitidas. En Santa Catalina el 77 % de las rutas iniciales supera las 8 h (mediana de 650 min), pero las reglas de Deb conducen la población al 100 % de factibilidad en unas 4 o 5 generaciones. |
| Presupuesto de evaluaciones | **20.100** | $N + N \times G = 100 + 100 \times 200 = \mathbf{20.100}$ evaluaciones por ejecución. |

---

## 4. Líneas Base de Comparación (Baselines)

La modalidad C5 exige comparar el algoritmo multiobjetivo propio frente a heurísticas simples y a los dos métodos clásicos de escalarización (**suma ponderada** y **$\varepsilon$-restricción**). Todos los métodos estocásticos se han diseñado para consumir exactamente el mismo presupuesto computacional de **20.100 evaluaciones**.

### 4.1. Heurística Voraz Multiobjetivo (Greedy)

- **Procedimiento (`GreedyOrienteering`, `src/algorithms/greedy_algorithm.py`):** Para un presupuesto $B$, parte del hotel $h$ y en cada iteración selecciona el POI no visitado $v$ con mayor ratio beneficio/coste marginal $s_v / \max(1, t_{uv} + v_v)$ tal que el tiempo acumulado más el retorno al hotel no supere $B$. Barre $K_B = 29$ presupuestos entre 60 y 480 min ($\Delta t = 15$ min) y extrae el frente no dominado.
- **Complejidad:** $O(K_B \cdot |P|^2)$ (aproximadamente 9 ms en ejecución). Es **estrictamente determinista** (desviación típica 0,0 entre semillas).

```text
ALGORITMO Greedy(problem, paso=15)
  Frente <- []
  PARA B = 60 HASTA T_max PASO paso HACER
      actual <- h; tiempo <- 0; ruta <- []; disp <- available_nodes()
      MIENTRAS disp != ∅ HACER
          candidatos_viables <- {v ∈ disp : tiempo + t_{actual,v} + v_v + t_{v,h} <= B}
          SI candidatos_viables == ∅ ENTONCES SALIR
          v* <- argmax_{v ∈ candidatos_viables} ( s_v / max(1, t_{actual,v} + v_v) )
          añadir v* a ruta; tiempo <- tiempo + t_{actual,v*} + v_{v*}
          actual <- v*; disp <- disp \ {v*}
      FIN MIENTRAS
      SI ruta != [] ENTONCES añadir (tiempo + t_{actual,h}, suma_score(ruta)) a Frente
  FIN PARA
  DEVOLVER soluciones no dominadas de Frente
```

### 4.2. Búsqueda Aleatoria (Random Search)

- **Procedimiento (`RandomSearchOrienteering`, `src/algorithms/random_search.py`):** Muestrea exactamente $E = 20.100$ rutas independientes eligiendo un tamaño aleatorio entre 2 y 10 POIs de $P'$ sin reemplazo, descarta las rutas que exceden $T_{\max}$ y filtra las soluciones no dominadas.
- **Complejidad:** $O(E \cdot k_{\text{rs}} + F_{\text{rs}}^2)$, donde $F_{\text{rs}}$ es el número de individuos factibles acumulados antes del filtrado de Pareto.

```text
ALGORITMO RandomSearch(problem, E=20100)
  Factibles <- []
  PARA iter = 1 HASTA E HACER
      k <- entero aleatorio en [2, min(10, |available_nodes()|)]
      ind <- Individual(muestra sin reemplazo de tamaño k)
      ind.evaluate(problem)
      SI ind.violation == 0 ENTONCES añadir ind a Factibles
  FIN PARA
  DEVOLVER soluciones únicas no dominadas de Factibles
```

### 4.3. Suma Ponderada (Weighted Sum GA)

- **Formulación (`WeightedSumGA`, `src/algorithms/weighted_sum.py`):** Escalara los dos objetivos mediante combinación lineal normalizada con 10 pesos $w \in \{0{,}1; 0{,}2; \dots; 0{,}9; 0{,}95\}$:
  $$\max\; F_{\text{WS}}(R, w) = \begin{cases} w \cdot \dfrac{S(R)}{S_{\max}} - (1 - w) \cdot \dfrac{T(R)}{T_{\max}}, & \text{si } T(R) \le T_{\max}, \\ -10^5 - 100 \cdot (T(R) - T_{\max}), & \text{en caso contrario.} \end{cases}$$
- **Presupuesto equiparado:** Para cada peso ejecuta un GA elitista mono-objetivo con $N_{\text{sub}} = 30$ y $G_{\text{sub}} = 66$:
  $$\text{Evaluaciones totales} = 10 \text{ pesos} \times [30 + 30 \times 66] = 10 \times 2.010 = \mathbf{20.100}.$$
- **Por qué obtiene el peor resultado ($HV \approx 6.840$ / $5.411$, $\Delta > 1{,}07$):** (1) Solo puede localizar puntos situados sobre la envoltura convexa del frente discreto; (2) cada corrida mono-objetivo colapsa hacia un único óptimo, aportando apenas entre 3 y 5 soluciones distintas entre las 10 ejecuciones y dejando grandes huecos sin cubrir.

### 4.4. Método de $\varepsilon$-Restricción ($\varepsilon$-Constraint GA)

- **Formulación (`EpsilonConstraintGA`, `src/algorithms/epsilon_constraint.py`):** Implementa el método clásico de $\varepsilon$-restricción optimizando el objetivo principal (puntuación turística $S(R)$) mientras transforma el tiempo total en una cota paramétrica $T(R) \le \varepsilon_k$:
  $$\max\; S(R) - 10^{-4} \cdot \frac{T(R)}{T_{\max}} \qquad \text{sujeto a}\quad T(R) \le \min(\varepsilon_k, T_{\max})$$
  El término secundario $-10^{-4} \cdot (T/T_{\max})$ (estrictamente menor que cualquier incremento mínimo de puntuación en el catálogo) actúa como desempate lexicográfico para evitar soluciones débilmente eficientes con igual puntuación pero distinto tiempo (Mavrotas, 2009). Las rutas con $T(R) > \min(\varepsilon_k, T_{\max})$ se penalizan mediante $-10^5 - 100 \cdot (T(R) - \varepsilon_k)$.
- **Malla de cotas y presupuesto idéntico:** Se evalúan **10 cotas temporales equiespaciadas** $\varepsilon_k \in [60, 480]$ min ($\Delta\varepsilon \approx 46{,}67$ min), dedicando a cada cota un algoritmo genético mono-objetivo de población $N_{\text{sub}} = 30$ durante $G_{\text{sub}} = 66$ generaciones con los mismos operadores de cruce, mutación y reparación:
  $$\text{Evaluaciones totales} = 10 \text{ cotas} \times [30 + 30 \times 66] = 10 \times 2.010 = \mathbf{20.100}.$$

```text
ALGORITMO Escalarización_GA(problem, Parámetros_K, pop=30, gens=66)   // K = 10 (pesos w o cotas ε)
  Soluciones <- []
  PARA cada param ∈ Parámetros_K HACER
      P <- inicializar y reparar 30 rutas; evaluar cada ruta
      PARA gen = 1 HASTA gens HACER
          Q <- generar 30 hijos mediante torneo(fitness(param)), cruce, reparación y mutación; evaluar
          P <- 30 mejores individuos de (P ∪ Q) según fitness(param)
      FIN PARA
      mejor <- individuo factible con mayor fitness(param) en P
      SI mejor existe ENTONCES añadir mejor a Soluciones
  FIN PARA
  DEVOLVER soluciones únicas no dominadas de Soluciones
```

**Complejidad de ambos métodos de escalarización ($K=10$, $N_{\text{sub}}=30$, $G_{\text{sub}}=66$):** $O\bigl(K \cdot G_{\text{sub}} \cdot (N_{\text{sub}} \cdot k_{\max} + N_{\text{sub}} \log N_{\text{sub}})\bigr)$, dado que cada generación ordena $2 N_{\text{sub}}$ individuos por una única aptitud escalar en lugar de requerir ordenamiento no dominado $O(M N^2)$.

---

## 5. Diseño Experimental y Resultados Estadísticos (15 Semillas)

Siguiendo la metodología de la asignatura:
1. **Mismo presupuesto computacional:** todos los algoritmos estocásticos (NSGA-II, Random Search, Weighted Sum y $\varepsilon$-Constraint) realizan exactamente **20.100 evaluaciones** por ejecución.
2. **15 semillas independientes:** $\{42, 101, 203, 314, 456, 578, 619, 723, 831, 954, 1024, 1234, 2048, 3072, 4096\}$.
3. **Métricas multiobjetivo:** Hipervolumen ($HV$, punto de referencia $(T_{\max}=480, S=0)$) y Spread ($\Delta$).
4. **Contraste de hipótesis:** Test pareado bilateral de rangos con signo de Wilcoxon (`scipy.stats.wilcoxon`, $\alpha = 0{,}05$) comparando el hipervolumen de cada línea base frente a NSGA-II.

Los datos brutos y agregados residen en `output/<hotel>/resultados_estadisticos_semillas.csv`, `resumen_estadistico.json` y se visualizan en `output/<hotel>/boxplot_hipervolumen.png`.

> **Nota sobre la dispersión:** Las desviaciones típicas corresponden a la desviación típica poblacional (`np.std`, con $N = 15$), coincidente con `resumen_estadistico.json` (por ejemplo, 24,5 en Santa Catalina frente a 25,4 si se emplea la desviación típica muestral con $N - 1$).

### 5.1. Hotel Santa Catalina (Las Palmas)

| Algoritmo | Presupuesto | Hipervolumen (Media ± Std) | Spread $\Delta$ (Media) | $p$-valor vs NSGA-II | Mejora de NSGA-II | ¿Significativo? |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **NSGA-II (Propio)** | **20.100** | **11.594,3 ± 24,5** | **0,428** | — (Referencia) | — | — |
| Greedy | Determ. ($T_{\max}$) | 10.188,9 ± 0,0 | 0,275 | $6{,}4 \times 10^{-4}$ | +13,8 % | **Sí ($p < 0{,}001$)** |
| Random Search | **20.100** | 10.050,3 ± 99,9 | 0,447 | $6{,}1 \times 10^{-5}$ | +15,4 % | **Sí ($p < 0{,}001$)** |
| Epsilon-Constraint | **20.100** | 9.711,9 ± 254,0 | 0,307 | $6{,}1 \times 10^{-5}$ | +19,4 % | **Sí ($p < 0{,}001$)** |
| Weighted Sum | **20.100** | 6.839,8 ± 490,3 | 1,076 | $6{,}1 \times 10^{-5}$ | +69,5 % | **Sí ($p < 0{,}001$)** |

### 5.2. Hotel Lopesan Villa del Conde (Meloneras)

| Algoritmo | Presupuesto | Hipervolumen (Media ± Std) | Spread $\Delta$ (Media) | $p$-valor vs NSGA-II | Mejora de NSGA-II | ¿Significativo? |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **NSGA-II (Propio)** | **20.100** | **10.013,1 ± 64,4** | **0,597** | — (Referencia) | — | — |
| Greedy | Determ. ($T_{\max}$) | 9.095,0 ± 0,0 | 0,346 | $6{,}1 \times 10^{-5}$ | +10,1 % | **Sí ($p < 0{,}001$)** |
| Random Search | **20.100** | 8.694,5 ± 90,4 | 0,632 | $6{,}1 \times 10^{-5}$ | +15,2 % | **Sí ($p < 0{,}001$)** |
| Epsilon-Constraint | **20.100** | 8.389,8 ± 286,4 | 0,332 | $6{,}1 \times 10^{-5}$ | +19,3 % | **Sí ($p < 0{,}001$)** |
| Weighted Sum | **20.100** | 5.411,4 ± 726,3 | 1,091 | $6{,}1 \times 10^{-5}$ | +85,0 % | **Sí ($p < 0{,}001$)** |

### 5.3. Discusión de los Resultados

- **Superioridad estadística de NSGA-II:** En ambos hoteles NSGA-II supera de forma estadísticamente significativa ($p < 0{,}001$) a las cuatro líneas base y **gana en el 100 % de las semillas evaluadas (15 de 15 pares en todos los cruces)**, ya que incluso su peor ejecución (11.524,5 en Santa Catalina y 9.857,0 en Lopesan) supera al máximo de cualquiera de los cuatro competidores. El valor $6{,}1 \times 10^{-5}$ ($= 2 / 2^{15}$) es el $p$-valor mínimo posible del test exacto bilateral de Wilcoxon con $N = 15$ pares sin empates; frente a Greedy en Santa Catalina, al repetirse el mismo frente en algunas semillas (11.608,62 en cuatro semillas y 11.609,79 en dos) con Greedy constante (10.188,89), las diferencias presentan empates y SciPy aplica la aproximación normal con corrección por empates ($p = 6{,}4 \times 10^{-4}$).
- **Comparativa crítica entre $\varepsilon$-Restricción y Suma Ponderada:** El experimento confirma empíricamente la teoría de escalarización: $\varepsilon$-Constraint logra un **+42,0 % más de hipervolumen que Weighted Sum en Santa Catalina** (9.711,9 frente a 6.839,8) y un **+55,0 % en Lopesan** (8.389,8 frente a 5.411,4), además de reducir drásticamente el Spread de $\Delta \approx 1{,}08$ a $\Delta = 0{,}307$–$0{,}332$. Esto ocurre porque fijar cotas temporales equiespaciadas $\varepsilon_k \in [60, 480]$ permite capturar soluciones en zonas no convexas distribuidas uniformemente a lo largo del eje del tiempo. Sin embargo, al fragmentar el presupuesto de 20.100 evaluaciones en 10 búsquedas aisladas de apenas 2.010 evaluaciones, $\varepsilon$-Constraint produce como máximo 10 puntos y converge peor en cada tramo que NSGA-II (+19,4 % y +19,3 % a favor de NSGA-II).
- **Consistencia entre semillas:** La desviación típica de NSGA-II es de solo 24,5 unidades en Santa Catalina (0,2 % de la media) y 64,4 unidades en Lopesan (0,6 %).
- **Efecto geográfico del hotel:** Desde Lopesan (sur), el hipervolumen medio de NSGA-II cae un 13,6 % respecto a Santa Catalina (10.013,1 frente a 11.594,3) por el mayor tiempo de traslado por la autopista GC-1 hasta los atractivos del norte y la cumbre.

---

## 6. Validación Analítica en Benchmarks Estándar: Familia ZDT (ZDT1, ZDT2 y ZDT3)

Para validar la corrección matemática del motor de NSGA-II (ordenamiento no dominado rápido, distancia de aglomeración y selección por torneo aglomerado) sobre frentes de Pareto teóricos conocidos con distintas geometrías y sin interferencia de la matriz de Gran Canaria, se implementaron tres problemas canónicos bi-objetivo de la familia **ZDT** (Zitzler, Deb & Thiele, 2000) con $m = 30$ variables continuas $x_i \in [0, 1]$ (`src/benchmarks/zdt.py`).

En todos ellos $f_1(x) = x_1$, $g(x) = 1 + \frac{9}{m - 1} \sum_{i=2}^{m} x_i$, $f_2(x) = g(x) \cdot h(f_1, g)$ y el frente teórico exacto corresponde a $g(x) = 1$:

| Problema | Geometría del Frente | Función $h(f_1, g)$ | Soluciones $F_1$ | $IGD$ (vs 500 pts teóricos) |
|---|---|---|:---:|:---:|
| **ZDT1** | **Convexo continuo** | $1 - \sqrt{f_1 / g}$ | 100 | **0,0210** |
| **ZDT2** | **Cóncavo (no convexo)** | $1 - (f_1 / g)^2$ | 100 | **0,0547** |
| **ZDT3** | **Discontinuo (5 arcos)** | $1 - \sqrt{f_1 / g} - (f_1 / g) \sin(10\pi f_1)$ | 100 | **0,0127** |

### 6.1. Operadores Continuos y Configuración
- **Cruce:** *Simulated Binary Crossover* (SBX) con índice de distribución $\eta_c = 15{,}0$. Se aplica a cada par seleccionado cruzando cada variable con probabilidad independiente de 0,5 (`random.random() <= 0.5`).
- **Mutación:** Mutación polinomial con $\eta_m = 20{,}0$ y probabilidad por variable $p_m = 1/m = 1/30$.
- **Selección y ejecución:** Torneo binario aglomerado (*Crowded Tournament Selection*, Deb et al., 2002), población $N = 100$, $G = 250$ generaciones y semilla fija (`seed = 42`).

### 6.2. Resultados de Convergencia ($IGD$)

Como se observa en [`output/validacion_zdt1.png`](../output/validacion_zdt1.png) y en la comparativa completa [`output/validacion_zdt_familia.png`](../output/validacion_zdt_familia.png):
- En **ZDT1**, las 100 soluciones cubren uniformemente todo el espectro $f_1 \in [0, 1]$ sobre la curva convexa teórica con **$IGD = 0{,}0210$**.
- En **ZDT2**, pese a la concavidad del frente (donde la suma ponderada lineal colapsaría a los extremos), NSGA-II distribuye las 100 soluciones a lo largo de la curva cóncava $f_2 = 1 - f_1^2$ con **$IGD = 0{,}0547$**.
- En **ZDT3**, el algoritmo identifica simultáneamente las 5 regiones inconexas del frente discontinuo con **$IGD = 0{,}0127$**.

Esto demuestra de forma empírica y matemática que los mecanismos centrales de dominancia y preservación de diversidad de la implementación propia funcionan correctamente en frentes convexos, cóncavos y discontinuos.

---

## 7. Uso de Inteligencia Artificial: Peticiones Relevantes y Valoración Crítica

Se emplearon asistentes de IA (Antigravity de Google DeepMind y Claude Code de Anthropic) como apoyo de diseño, depuración, auditoría de código y redacción en la parte algorítmica. Todas las ejecuciones experimentales y resultados numéricos proceden íntegramente del código ejecutado en local.

### 7.1. Ejemplos de Peticiones (Prompts) Más Relevantes

1. **Diseño de la estructura modular y Clean Code:**
   > *"Refactoriza la implementación inicial de NSGA-II y Greedy en módulos separados (`src/core/problem.py`, `src/algorithms/`, `src/benchmarks/`) aplicando responsabilidad única, dataclasses inmutables para configuración del problema y tipado estático estricto, asegurando que la lógica de dominancia de Deb y la evaluación temporal no varíen."*
2. **Auditoría del torneo binario en ZDT1:**
   > *"En la validación continua de ZDT1 las soluciones convergen al frente pero se quedan cortas en los extremos ($f_1 > 0{,}64$, $IGD = 0{,}1020$). Compara paso a paso nuestra implementación de selección, SBX y reemplazo con Deb et al. (2002) e identifica la causa."*
3. **Soporte de restricciones duras para el planificador:**
   > *"Añade soporte en `OrienteeringProblem` y `genetic_algorithm.py` para `mandatory_node` y `forbidden_nodes` mediante una función pura `_repair_chromosome` que elimine prohibidos y duplicados manteniendo el orden, inserte el obligatorio si falta y proteja el operador de eliminación. Incluye tests unitarios automatizados."*
4. **Incorporación de $\varepsilon$-restricción con presupuesto equiparado:**
   > *"Implementa la línea base de $\varepsilon$-restricción en `src/algorithms/epsilon_constraint.py` maximizando la puntuación con cota $T(R) \le \varepsilon_k$ para 10 umbrales entre 60 y 480 min, consumiendo exactamente 20.100 evaluaciones igual que NSGA-II, Random Search y Weighted Sum, e intégralo en `statistical_suite.py`."*

### 7.2. Valoración Crítica y Errores Detectados en los Asistentes de IA

El uso de IA aceleró la refactorización, la creación de scripts de prueba y la redacción estructurada, pero **no fue fiable sin verificación directa contra el código y las ejecuciones reales**. Concretamente, el equipo detectó y corrigió cinco errores relevantes producidos por los asistentes:

| Episodio | Error cometido / detectado en la IA | Cómo se detectó y se corrigió |
|---|---|---|
| **1. Torneo binario en ZDT1** | En una primera versión del benchmark ZDT1 generada con apoyo de IA, la selección por torneo comparaba solo por rango de dominancia e ignoraba el desempate por distancia de aglomeración (*crowding distance*), acumulando las soluciones en la zona izquierda ($IGD = 0{,}1020$). | Al contrastar el gráfico contra la curva teórica en $f_1 \in [0{,}64; 1{,}0]$ y auditar el código frente a Deb et al. (2002), se corrigió `_tournament_selection` para desempatar por mayor `crowding_distance`, logrando cobertura completa e $IGD = 0{,}0210$. |
| **2. Presupuesto desigual en Weighted Sum** | Versiones iniciales de la línea base de suma ponderada realizaban 11.070 o 20.000 evaluaciones frente a las 20.100 de NSGA-II, invalidando la comparación justa exigida por la rúbrica. | Mediante contaje analítico explícito de evaluaciones por generación ($N + N \cdot G$), se ajustó el bucle a $10 \times 30 \times (1 + 66) = 20.100$ evaluaciones exactas. |
| **3. Test estadístico inadecuado** | La primera versión de `metrics.py` usaba `scipy.stats.ranksums` (test para muestras independientes) en lugar de un test pareado sobre las mismas 15 semillas. | Se identificó el fallo metodológico al revisar las pruebas pareadas y se migró a `scipy.stats.wilcoxon` (test bilateral de rangos con signo). |
| **4. Afirmaciones inexactas en un borrador de memoria** | Al redactar una versión previa de este documento, el asistente afirmó detalles no fieles al código: longitudes $2 \le k \le 30$ (cuando el cruce recorta a 12 y los frentes tienen 1–7 paradas), inicialización viable en 150–350 min (cuando el código muestrea 3–7 POIs sin mirar el tiempo, superando las 8 h el 77 % inicial), y $p_c = 0{,}9$ en ZDT1 (cuando SBX se aplica al par cruzando variables con probabilidad 0,5). | Una auditoría línea por línea contrastando cada frase y número contra el código fuente y pruebas directas permitió corregir todas las discrepancias antes de la entrega. |
| **5. Conflicto silencioso entre restricciones** | La primera implementación de `_repair_chromosome` ignoraba silenciosamente `mandatory_node` si también figuraba en `forbidden_nodes`. | Tras la revisión en equipo, se aplicó el principio *Fail Fast* añadiendo validación explícita (`ValueError`) en `OrienteeringProblem.__post_init__` y cubriéndolo con `tests/test_constraints.py`. |

---

## 8. Referencias Bibliográficas

- Audet, C., Bigeon, J., Cartier, D., Le Digabel, S., & Salomon, L. (2021). Performance indicators in multiobjective optimization. *European Journal of Operational Research*, 292(2), 397–422.
- Bérubé, J.-F., Gendreau, M., & Potvin, J.-Y. (2009). An exact $\varepsilon$-constraint method for bi-objective combinatorial optimization problems: Application to the Traveling Salesman Problem with Profits. *European Journal of Operational Research*, 194(1), 39–50.
- Coello Coello, C. A., Lamont, G. B., & Van Veldhuizen, D. A. (2007). *Evolutionary Algorithms for Solving Multi-Objective Problems* (2.ª ed.). Springer.
- Das, I., & Dennis, J. E. (1997). A closer look at drawbacks of minimizing weighted sums of objectives for Pareto set generation in multicriteria optimization problems. *Structural Optimization*, 14(1), 63–69.
- Deb, K. (2000). An efficient constraint handling method for genetic algorithms. *Computer Methods in Applied Mechanics and Engineering*, 186(2–4), 311–338.
- Deb, K., Pratap, A., Agarwal, S., & Meyarivan, T. (2002). A fast and elitist multiobjective genetic algorithm: NSGA-II. *IEEE Transactions on Evolutionary Computation*, 6(2), 182–197.
- Ehrgott, M. (2005). *Multicriteria Optimization* (2.ª ed.). Springer.
- Golden, B. L., Levy, L., & Vohra, R. (1987). The orienteering problem. *Naval Research Logistics*, 34(3), 307–318.
- Haimes, Y. Y., Lasdon, L. S., & Wismer, D. A. (1971). On a bicriterion formulation of the problems of integrated system identification and system optimization. *IEEE Transactions on Systems, Man, and Cybernetics*, SMC-1(3), 296–297.
- Mavrotas, G. (2009). Effective implementation of the $\varepsilon$-constraint method in Multi-Objective Mathematical Programming problems. *Applied Mathematics and Computation*, 213(2), 455–465.
- Miettinen, K. (1999). *Nonlinear Multiobjective Optimization*. Kluwer Academic Publishers.
- Miller, C. E., Tucker, A. W., & Zemlin, R. A. (1960). Integer programming formulation of traveling salesman problems. *Journal of the ACM*, 7(4), 326–329.
- Wilcoxon, F. (1945). Individual comparisons by ranking methods. *Biometrics Bulletin*, 1(6), 80–83.
- Zitzler, E., & Thiele, L. (1999). Multiobjective evolutionary algorithms: A comparative case study and the strength Pareto approach. *IEEE Transactions on Evolutionary Computation*, 3(4), 257–271.
- Zitzler, E., Deb, K., & Thiele, L. (2000). Comparison of multiobjective evolutionary algorithms: Empirical results. *Evolutionary Computation*, 8(2), 173–195.
