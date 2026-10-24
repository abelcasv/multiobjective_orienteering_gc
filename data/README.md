# Datos del proyecto

Cada escenario (hotel base) tiene su carpeta con 31 nodos: el hotel (depósito, puntuación 0 y visita 0 min) y los 30 POIs.

| Carpeta | Depósito |
|---|---|
| `santa_catalina/` | Hotel Santa Catalina (Las Palmas) |
| `lopesan_villa_del_conde/` | Hotel Lopesan Villa del Conde |

Ficheros de cada carpeta:

- `matriz_tiempos.csv`: tiempos de conducción en minutos entre todos los nodos (31x31, asimétrica, sin `inf`/NaN).
- `puntos_interes.csv`: nombre, latitud, longitud, puntuación y tiempo de visita (min).
- `coordenadas.csv`: nombre, latitud, longitud (usado para exportar las rutas con coordenadas).

`auxiliar/` contiene la matriz completa de 32x32 con ambos hoteles y la matriz sin factor global de calibración (útil para el análisis de sensibilidad).

## Cómo se generaron

Con `scripts/build_time_matrix.ipynb` (ejecutable en Colab):

1. Red viaria de Gran Canaria (`network_type='drive'`) con OSMnx, quedándose con la mayor componente fuertemente conexa.
2. Cada POI y cada hotel se asocia al nodo de red más cercano.
3. Tiempos por camino mínimo (Dijkstra) con velocidades por tipo de vía y una penalización por sinuosidad de las carreteras.
4. Calibración con 12 pares medidos en Google Maps y un factor global de ajuste (mediana de la razón matriz final / matriz sin factor global: ver `auxiliar/`).

## Origen y licencia

- Red viaria: © colaboradores de OpenStreetMap, licencia ODbL (https://www.openstreetmap.org/copyright).
- Tiempos de referencia para la calibración: consultas manuales a Google Maps (solo una muestra pequeña, no se redistribuyen datos de Google).
- Coordenadas de los hoteles: obtenidas de Google Maps.
- Puntuaciones (escala 0-10) y tiempos de visita (min) de los POIs: propuestos con un asistente de IA a partir del interés turístico general de cada lugar y revisados a mano por el equipo. Son valores ilustrativos, no proceden de una fuente medible (ver la sección de uso de IA de la memoria). Los hoteles tienen puntuación 0 y visita 0 por ser el depósito.

## Limitaciones

- Los tiempos son aproximados: no incluyen tráfico ni aparcamiento y pueden desviarse de Google Maps, sobre todo en rutas de montaña.
- Las puntuaciones y los tiempos de visita son subjetivos: otro criterio cambiaría el frente de Pareto y las rutas recomendadas.
- Validación con 4 pares con hotel medidos en Google Maps después de construir la matriz (no se usaron para calibrar). La matriz es optimista en todos, con un error medio de 8,2 min frente a los 2,9 min de los pares de calibración (`output/figuras/validacion_hoteles.csv`):

  | Par | Matriz (min) | Google Maps (min) |
  |---|---|---|
  | Lopesan -> Dunas de Maspalomas | 2,3 | 4-10 (según el acceso) |
  | Lopesan -> Roque Nublo | 56,3 | 76 |
  | Santa Catalina -> Vegueta | 4,3 | 10 |
  | Vegueta -> Santa Catalina | 7,3 | 10 |

  Los mayores errores están en montaña (como Roque Nublo -> Puerto de Mogán en la calibración) y en tramos urbanos cortos, donde semáforos y tráfico pesan más que la velocidad de la vía. Las rutas que suben a la cumbre desde el sur y los trayectos urbanos son, por tanto, más largos en la realidad.
