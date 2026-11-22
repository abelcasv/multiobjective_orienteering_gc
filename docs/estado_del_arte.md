# Estado del arte: el problema de orienteering y la planificación de rutas turísticas

Esta parte cubre el problema y su aplicación al turismo. Los métodos de resolución (NSGA-II, escalarización e indicadores de calidad) se revisan en la parte de algoritmos.

## El problema de orienteering

El problema de orienteering (OP) es un problema de optimización combinatoria presentado y resuelto heurísticamente por primera vez por Tsiligirides (1984). El nombre *orienteering problem* lo introdujeron Golden et al. (1987), que propusieron una heurística de centro de gravedad que superaba a las heurísticas anteriores. En su forma clásica es un problema de rutas: hay que decidir qué subconjunto de nodos visitar, y en qué orden, para maximizar la puntuación total recogida sin superar un presupuesto de tiempo (Gunawan et al., 2016). Contiene el problema del viajante (TSP) como caso particular, por lo que es NP-difícil, y eso justifica el uso de metaheurísticas en instancias realistas.

## Revisiones de la literatura

Vansteenwegen et al. (2011) describen formalmente el OP, presentan sus principales variantes y comparan los métodos exactos y (meta)heurísticos publicados hasta entonces. Gunawan et al. (2016) amplían esa revisión con variantes como el Team OP, el OP con ventanas temporales y el OP dependiente del tiempo, y con otras más recientes como el OP estocástico, el generalizado o el clusterizado. También recogen aplicaciones recientes, entre ellas el *Tourist Trip Design Problem*. Una revisión más reciente (Shen et al., 2025, preprint) sistematiza la investigación sobre el OP entre 2017 y 2025, con especial atención a las matheurísticas y a los métodos basados en aprendizaje por refuerzo y redes neuronales.

## El OP como problema biobjetivo

El OP pertenece a la familia de los problemas del viajante con beneficios (*TSPs with profits*), que generalizan el TSP: no es necesario visitar todos los vértices y cada vértice tiene un beneficio asociado. Feillet et al. (2005) señalan que estos problemas pueden verse como TSP bicriterio con dos objetivos opuestos. Ese es exactamente el planteamiento de este trabajo: maximizar la puntuación y minimizar el tiempo total, en lugar de fijar el tiempo como límite y maximizar solo la puntuación.

Para esta versión biobjetivo, Bérubé et al. (2009) proponen un método ε-restricción exacto. En él, el problema se resuelve mediante una serie de subproblemas de un solo objetivo en los que todos los objetivos salvo uno se convierten en restricciones. Con él obtienen por primera vez el frente de Pareto exacto del TSP con beneficios en instancias de hasta 150 vértices.

## Aplicación al turismo

El *Tourist Trip Design Problem* (TTDP) es un problema de planificación de rutas para turistas que quieren visitar varios puntos de interés. Gavalas et al. (2014) revisan los modelos y los métodos algorítmicos propuestos para resolverlo.

El trabajo más cercano al nuestro es el de Schilde et al. (2009). Desarrollan métodos para el OP multiobjetivo motivados por la planificación de rutas turísticas individuales en una ciudad, donde cada punto de interés aporta beneficios distintos según la categoría (cultura, compras…) y cada turista tiene preferencias diferentes por cada categoría. Para obtener el frente de Pareto usan una optimización por colonias de hormigas de Pareto y una búsqueda de vecindad variable extendida al caso multiobjetivo, ambas hibridadas con *path relinking*.

## Posición de este trabajo

A diferencia de Schilde et al. (2009), nuestros dos objetivos son la puntuación turística y el tiempo total (conducción más visitas), como en la versión biobjetivo del TSP con beneficios. Las preferencias por categorías no se tratan como objetivos, sino como restricciones sobre el conjunto de puntos visitables. El problema se resuelve con un algoritmo evolutivo multiobjetivo propio y se compara con métodos de escalarización (suma ponderada y ε-restricción) sobre la red viaria real de Gran Canaria, con dos hoteles como depósito.

## Referencias

- Bérubé, J.-F., Gendreau, M. y Potvin, J.-Y. (2009). An exact ε-constraint method for bi-objective combinatorial optimization problems: Application to the Traveling Salesman Problem with Profits. *European Journal of Operational Research*, 194(1), 39–50. https://doi.org/10.1016/j.ejor.2007.12.014
- Feillet, D., Dejax, P. y Gendreau, M. (2005). Traveling Salesman Problems with Profits. *Transportation Science*, 39(2), 188–205. https://doi.org/10.1287/trsc.1030.0079
- Gavalas, D., Konstantopoulos, C., Mastakas, K. y Pantziou, G. (2014). A survey on algorithmic approaches for solving tourist trip design problems. *Journal of Heuristics*, 20(3), 291–328. https://doi.org/10.1007/s10732-014-9242-5
- Golden, B. L., Levy, L. y Vohra, R. (1987). The orienteering problem. *Naval Research Logistics*, 34(3), 307–318.
- Gunawan, A., Lau, H. C. y Vansteenwegen, P. (2016). Orienteering Problem: A survey of recent variants, solution approaches and applications. *European Journal of Operational Research*, 255(2), 315–332. https://doi.org/10.1016/j.ejor.2016.04.059
- Schilde, M., Doerner, K. F., Hartl, R. F. y Kiechle, G. (2009). Metaheuristics for the bi-objective orienteering problem. *Swarm Intelligence*, 3(3), 179–201. https://doi.org/10.1007/s11721-009-0029-5
- Shen, S., Zhou, Y., Lei, Q. y Wu, Z. (2025). A survey of the orienteering problem: model evolution, algorithmic advances, and future directions. arXiv:2512.16865 (preprint).
- Tsiligirides, T. (1984). Heuristic methods applied to orienteering. *Journal of the Operational Research Society*, 35, 797–809. https://doi.org/10.1057/jors.1984.162
- Vansteenwegen, P., Souffriau, W. y Van Oudheusden, D. (2011). The orienteering problem: A survey. *European Journal of Operational Research*, 209(1), 1–10. https://doi.org/10.1016/j.ejor.2010.03.045
