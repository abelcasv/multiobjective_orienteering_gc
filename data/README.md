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
- Puntuaciones y tiempos de visita de los POIs: TODO (Hugo): indicar el criterio o la fuente.

## Limitaciones

- Los tiempos son aproximados: no incluyen tráfico ni aparcamiento y pueden desviarse de Google Maps, sobre todo en rutas de montaña.
- Pares pendientes de validar con Google Maps: Lopesan -> Dunas de Maspalomas (matriz: 2 min, parece corto), Lopesan -> Roque Nublo (56 min), Santa Catalina <-> Vegueta (4,3 min ida / 7,3 min vuelta).
- Los ficheros `puntos_interes.csv`, `matriz_tiempos.csv` y `coordenadas.csv` de la raíz de `data/` pertenecen al modelo anterior (depósito en Vegueta) y ya no los usa `main.py`.
