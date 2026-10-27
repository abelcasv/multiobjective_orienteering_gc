# Análisis de sensibilidad: tiempos de visita y puntuaciones

Las puntuaciones y los tiempos de visita de los POIs son valores ilustrativos ([`memoria_datos_y_modelo.md`](memoria_datos_y_modelo.md), sección 1). Este análisis mide cuánto cambian el frente de Pareto y los POIs elegidos si se modifican. Todas las cifras salen de `output/<escenario>/sensibilidad.csv` y `sensibilidad_pois.csv` y se regeneran con `python scripts/sensitivity_analysis.py` (unos 5 min con 8 procesos).

---

## Diseño

Se ejecuta NSGA-II con la configuración por defecto (100, 200, 0,85, 0,35; 20.100 evaluaciones) y las 15 semillas del benchmark en cinco variantes de los datos. La matriz de conducción y el límite de 8 h no cambian.

| Variante | Cambio |
|---|---|
| `base` | Datos originales. Reproduce el hipervolumen de NSGA-II de la batería estadística. |
| `visitas_x075` | Todos los tiempos de visita × 0,75. |
| `visitas_x050` | Todos los tiempos de visita × 0,5. |
| `puntuacion_uniforme` | Todos los POIs valen lo mismo (8,03, la media del catálogo): solo cuenta el número de paradas. |
| `puntuacion_cuadratica` | $s^2/10$: el 10 se mantiene y las puntuaciones medias bajan (9 → 8,1; 7 → 4,9), así que pesan más los lugares icónicos. |

Se mide, por variante: el hipervolumen (punto de referencia 480 min, 0 pts; desviación poblacional `np.std`), el número de soluciones del frente, la ruta de mayor puntuación y la frecuencia de cada POI: el % de las soluciones del frente (las 15 semillas juntas) que lo contienen. Las 3 rutas recomendadas son las de la semilla 42.

---

## Cómo cambia el frente

| Hotel | Variante | Hipervolumen (Media ± Std) | Soluciones del frente | Puntuación máx. | Puntuación máx. (escala original) | Paradas |
|---|---|:---:|:---:|:---:|:---:|:---:|
| Santa Catalina | base | 11.594,3 ± 24,5 | 24,6 | 51,5 | 51,5 | 6,9 |
| | visitas ×0,75 | 14.329,8 ± 31,2 | 30,2 | 60,8 | 60,8 | 8,0 |
| | visitas ×0,5 | 18.815,0 ± 104,7 | 43,8 | 78,3 | 78,3 | 10,0 |
| | uniforme | 12.166,5 ± 70,0 | 6,3 | 50,3 | 45,7 | 6,3 |
| | cuadrática | 8.998,2 ± 12,7 | 53,8 | 39,2 | 48,0 | 6,0 |
| Lopesan | base | 10.013,1 ± 64,4 | 23,6 | 46,1 | 46,1 | 6,0 |
| | visitas ×0,75 | 12.261,1 ± 24,8 | 27,3 | 55,1 | 55,1 | 7,0 |
| | visitas ×0,5 | 16.064,1 ± 41,0 | 40,1 | 71,3 | 71,3 | 9,0 |
| | uniforme | 10.478,2 ± 66,6 | 5,9 | 47,7 | 43,3 | 5,9 |
| | cuadrática | 7.941,0 ± 76,7 | 25,1 | 36,7 | 43,3 | 5,2 |

Las tres últimas columnas son medias sobre las 15 semillas de la ruta de mayor puntuación de cada frente.

- **Tiempos de visita.** Con visitas al 75 % el hipervolumen sube un 23,6 % (Santa Catalina) y un 22,5 % (Lopesan); al 50 %, un 62,3 % y un 60,4 %. La ruta más completa pasa de 6–7 paradas a 9–10 y su puntuación crece un 52–55 % al reducir las visitas a la mitad. El frente también tiene más soluciones (de unas 24 a más de 40): con visitas más cortas caben más combinaciones distintas en las 8 h.
- **Puntuaciones.** El hipervolumen de estas variantes no se puede comparar con el de la base, porque cambia la escala de la puntuación. Con puntuación uniforme el frente se reduce a unas 6 soluciones, una por número de paradas: entre dos rutas con las mismas paradas solo sobrevive la más corta. Con la cuadrática, en Santa Catalina el frente tiene más del doble de soluciones (53,8 frente a 24,6), y en Lopesan casi las mismas (25,1). Medidas en la escala original, las rutas más completas de ambas variantes valen menos que la de la base (45,7 y 48,0 frente a 51,5 en Santa Catalina): la base optimiza justo esa puntuación.

---

## Qué POIs aparecen

% de las soluciones del frente que contienen cada POI. Se muestran los POIs que superan el 15 % en alguna variante, más las Dunas y el Roque Nublo. El listado completo está en `sensibilidad_pois.csv`.

**Santa Catalina**

| POI | Punt. / visita | base | ×0,75 | ×0,5 | uniforme | cuadrática |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Bufadero de la Garita | 7 / 30 | 87,8 | 94,3 | 88,6 | 100,0 | 88,8 |
| Arucas (Iglesia) | 8 / 60 | 75,6 | 76,8 | 86,3 | 55,3 | 75,6 |
| Tufia | 7 / 45 | 63,4 | 80,1 | 83,7 | 84,0 | 62,6 |
| Cueva Pintada | 9 / 60 | 52,8 | 45,5 | 50,5 | 2,1 | 54,0 |
| Caldera de Bandama | 8 / 60 | 40,1 | 47,7 | 52,2 | 22,3 | 33,3 |
| Jardín de la Marquesa | 7 / 60 | 25,2 | 39,5 | 70,6 | 48,9 | 14,6 |
| Cenobio de Valerón | 7 / 45 | 19,0 | 35,5 | 28,3 | 6,4 | 18,8 |
| Firgas | 7 / 45 | 13,3 | 17,0 | 25,3 | 37,2 | 2,6 |
| Playa de las Canteras | 10 / 120 | 4,1 | 26,9 | 48,4 | 0,0 | 47,0 |
| Jardín Botánico Viera y Clavijo | 8 / 90 | 0,8 | 4,2 | 21,5 | 0,0 | 0,4 |
| Charco de San Lorenzo | 7 / 60 | 0,5 | 3,1 | 19,3 | 8,5 | 0,0 |
| Dunas de Maspalomas | 10 / 120 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 |
| Roque Nublo | 10 / 90 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 |

**Lopesan Villa del Conde**

| POI | Punt. / visita | base | ×0,75 | ×0,5 | uniforme | cuadrática |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Bufadero de la Garita | 7 / 30 | 86,7 | 89,0 | 91,2 | 100,0 | 76,7 |
| Barranco de Fataga | 8 / 45 | 62,4 | 36,8 | 22,9 | 29,2 | 58,4 |
| Tufia | 7 / 45 | 61,9 | 73,9 | 86,2 | 83,1 | 41,4 |
| Arucas (Iglesia) | 8 / 60 | 29,4 | 50,0 | 65,9 | 49,4 | 11,4 |
| Dunas de Maspalomas | 10 / 120 | 28,5 | 38,3 | 58,1 | 0,0 | 41,1 |
| Caldera de Bandama | 8 / 60 | 19,5 | 32,2 | 59,3 | 1,1 | 19,6 |
| Jardín de la Marquesa | 7 / 60 | 18,6 | 41,0 | 60,6 | 49,4 | 1,9 |
| Cueva Pintada | 9 / 60 | 11,6 | 26,8 | 18,6 | 0,0 | 14,6 |
| Pico de las Nieves | 9 / 45 | 10,7 | 2,2 | 4,0 | 0,0 | 28,6 |
| Firgas | 7 / 45 | 9,0 | 11,7 | 26,9 | 32,6 | 0,0 |
| Cenobio de Valerón | 7 / 45 | 6,2 | 19,5 | 11,0 | 0,0 | 6,9 |
| Roque Nublo | 10 / 90 | 1,4 | 0,7 | 4,0 | 0,0 | 19,4 |
| Jardín Botánico Viera y Clavijo | 8 / 90 | 0,0 | 0,0 | 34,7 | 0,0 | 0,0 |

- **El núcleo de las rutas es estable.** Bufadero de la Garita, Tufia y Arucas aparecen en todas las variantes y en ambos hoteles: son visitas cortas en el noreste de la isla, junto a la GC-1. Los POIs que aparecen alguna vez son 13 de 30 en Santa Catalina y 16 en Lopesan con los datos base; con visitas a la mitad pasan a 13 y 21.
- **Visitas más cortas favorecen a las visitas largas del norte.** Al acortar los tiempos ganan presencia la Playa de las Canteras (de 4,1 % a 48,4 % en Santa Catalina), el Jardín Botánico y el Jardín de la Marquesa. En Lopesan, el Barranco de Fataga, cercano al hotel, pierde peso (de 62,4 % a 22,9 %) frente a esos POIs del norte.
- **La puntuación uniforme expulsa los lugares con visita larga.** Si todos los POIs valen lo mismo, el algoritmo maximiza el número de paradas: las Dunas, la Playa de las Canteras y la Cueva Pintada (60 min) desaparecen o casi.
- **La puntuación cuadrática favorece los lugares icónicos.** Suben la Playa de las Canteras (47,0 % en Santa Catalina), las Dunas (41,1 % en Lopesan) y el Roque Nublo y el Pico de las Nieves en Lopesan.

### Dunas de Maspalomas y Roque Nublo

Con los datos base, ninguno de los dos aparece en las 3 rutas recomendadas de ningún hotel. El coste de ir, visitar y volver desde cada hotel explica la diferencia:

| Desde | Dunas (10 pts) | Roque Nublo (10 pts) |
|---|:---:|:---:|
| Santa Catalina | 42,2 + 120 + 42,7 = 205,0 min | 69,2 + 90 + 70,8 = 230,0 min |
| Lopesan | 2,3 + 120 + 2,2 = 124,4 min | 56,3 + 90 + 55,5 = 201,8 min |

- **Desde Santa Catalina no aparecen en ninguna variante.** Ni con las visitas a la mitad ni con la puntuación cuadrática. Cada uno cuesta más de 3 h por 10 puntos. En comparación, la ruta Express base (Tufia y Bufadero) da 14 puntos en 1,9 h y la Equilibrada, 29 puntos en 4,4 h.
- **Desde Lopesan las Dunas sí están en el frente, pero solo en rutas cortas.** Aparecen en las 15 semillas y en el 28,5 % de las soluciones. Con la semilla 42 están en 6 de las 26 soluciones del frente, desde la ruta solo a las Dunas (124,4 min, 10 pts) hasta Tufia, Bufadero, Fataga y Dunas (340,8 min, 32 pts). No las elige ninguna de las 3 rutas recomendadas porque con 120 min de visita su puntuación por hora es baja. Entran en ellas en cuanto la visita se acorta o el 10 pesa más:
  - **×0,75:** Equilibrada (Tufia, Bufadero, Fataga, Dunas) y Exhaustiva.
  - **×0,5:** la ruta Express es solo las Dunas, y también entran en la Exhaustiva.
  - **Cuadrática:** Equilibrada (Tufia, Bufadero, Dunas).
- **El Roque Nublo solo sale con la puntuación cuadrática.** Desde Lopesan aparece en 3 de las 15 semillas con los datos base (1,4 % de las soluciones). Con la cuadrática pasa a 10 de 15 semillas (19,4 %), y la ruta Exhaustiva de la semilla 42, que coincide con la Express, sube a la cumbre: Bufadero, Pico de las Nieves, Tejeda, Roque Nublo y Barranco de Fataga. Acortar la visita no basta (0,7 % con ×0,75 y 4,0 % con ×0,5), porque lo que pesa es la conducción de ida y vuelta, casi 2 h.

Además, la matriz es optimista en la montaña: Lopesan → Roque Nublo sale 20 min más corto que en Google Maps ([`memoria_datos_y_modelo.md`](memoria_datos_y_modelo.md), sección 3). Con tiempos reales, el Roque Nublo aparecería todavía menos.

---

## Conclusiones

- **Las rutas dependen sobre todo de la puntuación por minuto, no de la puntuación sola.** Tener un 10 no basta: el POI tiene que caber en el presupuesto con poca conducción y una visita corta.
- **Lo más estable es el núcleo Bufadero, Tufia y Arucas, cercano a la GC-1.** Lo más sensible son las visitas largas (Canteras, Dunas, Jardín Botánico) y la cumbre, que solo entran si se acortan las visitas o se premian los lugares icónicos.
- **Si se quiere que las rutas incluyan los iconos de la isla**, cambiar a la escala cuadrática lo consigue en parte desde Lopesan, pero no desde Santa Catalina. Otra opción sería añadirlos como paradas obligatorias. Esa decisión depende del perfil de turista que se quiera modelar, no del algoritmo.
