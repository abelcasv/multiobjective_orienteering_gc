# Estudio de hiperparámetros de NSGA-II

Este estudio comprueba si la configuración de NSGA-II usada en el proyecto (población 100, 200 generaciones, cruce 0,85 y mutación 0,35) es razonable. Todas las cifras salen de `output/<escenario>/hiperparametros.csv` y se regeneran con `python scripts/hyperparameter_study.py` (unos 15 min con 8 procesos).

---

## Diseño

- **Presupuesto fijo.** Todas las combinaciones hacen **20.100 evaluaciones** ($N + N \times G$), igual que la batería estadística. El número de evaluaciones se contó durante la ejecución. Solo se usan poblaciones pares: los hijos se generan de dos en dos, así que con $N$ impar se evaluaría un hijo de más en cada generación.
- **Población × generaciones:** (50, 401), (100, 200), (150, 133) y (300, 66), con cruce 0,85 y mutación 0,35.
- **Cruce × mutación:** rejilla completa de $p_c \in \{0{,}6;\ 0{,}85;\ 0{,}95\}$ por $p_m \in \{0{,}15;\ 0{,}35;\ 0{,}55\}$, con población 100 y 200 generaciones.
- **Semillas:** las mismas 15 del benchmark, fijadas justo antes de cada corrida. La configuración actual reproduce exactamente el hipervolumen de NSGA-II de `resumen_estadistico.json` en los dos hoteles.
- **Métrica:** hipervolumen con punto de referencia (480 min, 0 pts). La desviación es la poblacional (`np.std`), como en el resto de la memoria.
- **Contraste:** test pareado de Wilcoxon (bilateral) de cada combinación frente a la actual. Son 11 comparaciones por hotel, así que además del umbral 0,05 se indica el de Bonferroni, $0{,}05/11 \approx 0{,}0045$.

---

## Resultados

La columna "Dif." es la diferencia del hipervolumen medio respecto a la configuración actual (en negrita).

**Hotel Santa Catalina**

| $N$ | $G$ | $p_c$ | $p_m$ | Hipervolumen (Media ± Std) | Dif. | $p$ vs actual |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 50 | 401 | 0,85 | 0,35 | 11.598,0 ± 37,0 | +0,03 % | 0,733 |
| **100** | **200** | **0,85** | **0,35** | **11.594,3 ± 24,5** | — | — |
| 150 | 133 | 0,85 | 0,35 | 11.575,0 ± 56,5 | −0,17 % | 0,454 |
| 300 | 66 | 0,85 | 0,35 | 11.571,4 ± 19,4 | −0,20 % | 0,010 |
| 100 | 200 | 0,60 | 0,15 | 11.526,0 ± 83,5 | −0,59 % | $3{,}1 \times 10^{-4}$ |
| 100 | 200 | 0,60 | 0,35 | 11.590,8 ± 35,5 | −0,03 % | 0,889 |
| 100 | 200 | 0,60 | 0,55 | 11.604,7 ± 18,5 | +0,09 % | 0,041 |
| 100 | 200 | 0,85 | 0,15 | 11.546,0 ± 37,9 | −0,42 % | 0,002 |
| 100 | 200 | 0,85 | 0,55 | 11.607,0 ± 6,7 | +0,11 % | 0,158 |
| 100 | 200 | 0,95 | 0,15 | 11.532,8 ± 44,3 | −0,53 % | $8{,}5 \times 10^{-4}$ |
| 100 | 200 | 0,95 | 0,35 | 11.585,1 ± 42,7 | −0,08 % | 0,330 |
| 100 | 200 | 0,95 | 0,55 | 11.601,5 ± 15,8 | +0,06 % | 0,530 |

**Hotel Lopesan Villa del Conde**

| $N$ | $G$ | $p_c$ | $p_m$ | Hipervolumen (Media ± Std) | Dif. | $p$ vs actual |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 50 | 401 | 0,85 | 0,35 | 10.018,2 ± 11,5 | +0,05 % | 0,454 |
| **100** | **200** | **0,85** | **0,35** | **10.013,1 ± 64,4** | — | — |
| 150 | 133 | 0,85 | 0,35 | 10.014,1 ± 49,1 | +0,01 % | 1,000 |
| 300 | 66 | 0,85 | 0,35 | 9.988,0 ± 62,2 | −0,25 % | 0,095 |
| 100 | 200 | 0,60 | 0,15 | 9.912,6 ± 110,7 | −1,00 % | 0,010 |
| 100 | 200 | 0,60 | 0,35 | 10.004,1 ± 48,3 | −0,09 % | 0,890 |
| 100 | 200 | 0,60 | 0,55 | 10.033,4 ± 32,8 | +0,20 % | 0,359 |
| 100 | 200 | 0,85 | 0,15 | 9.927,8 ± 88,4 | −0,85 % | 0,010 |
| 100 | 200 | 0,85 | 0,55 | 10.046,7 ± 25,3 | +0,34 % | 0,073 |
| 100 | 200 | 0,95 | 0,15 | 9.936,0 ± 93,4 | −0,77 % | 0,008 |
| 100 | 200 | 0,95 | 0,35 | 10.014,0 ± 44,5 | +0,01 % | 0,847 |
| 100 | 200 | 0,95 | 0,55 | 10.036,7 ± 24,1 | +0,24 % | 0,303 |

---

## Conclusiones

- **La configuración actual es razonable.** Las diferencias de media van del −1,00 % al +0,34 %. Solo una alternativa con más media llega a $p < 0{,}05$: $p_c = 0{,}6$, $p_m = 0{,}55$ en Santa Catalina (+0,09 %, $p = 0{,}041$). No pasa el umbral de Bonferroni y en Lopesan no es significativa ($p = 0{,}359$).
- **La mutación es el parámetro que más influye.** Con $p_m = 0{,}15$ el hipervolumen baja en los tres valores de cruce y en los dos hoteles (−0,42 % a −1,00 %) y la desviación aumenta. En Santa Catalina las tres caídas siguen siendo significativas con Bonferroni; en Lopesan no ($p$ entre 0,008 y 0,010).
- **Subir la mutación a 0,55 tiende a mejorar, sin significación.** Con $p_c = 0{,}85$ y $p_m = 0{,}55$ se obtiene la mayor media de los dos hoteles (+0,11 % y +0,34 %) y menos dispersión (6,7 frente a 24,5 y 25,3 frente a 64,4), pero con $p = 0{,}158$ y $p = 0{,}073$. Como la mejora se ha visto con las mismas 15 semillas con las que se elige, habría que confirmarla con semillas nuevas antes de cambiar el valor por defecto.
- **El cruce apenas influye.** Con la mutación fija, cambiar $p_c$ entre 0,6 y 0,95 mueve la media como mucho un 0,24 %. Con $p_m = 0{,}35$, ni 0,6 ni 0,95 se distinguen de 0,85 ($p \ge 0{,}33$ en los dos hoteles).
- **Población y generaciones.** (50, 401) y (150, 133) quedan a la par de (100, 200). (300, 66) es la peor en los dos hoteles (−0,20 % y −0,25 %), aunque solo en Santa Catalina con $p < 0{,}05$ ($p = 0{,}010$, no significativa con Bonferroni): con 66 generaciones no da tiempo a converger. Las poblaciones grandes también son más lentas, porque la ordenación no dominada cuesta $O(N^2)$ por generación. La columna `tiempo_medio_s` del CSV se midió con 8 corridas en paralelo y solo sirve para comparar combinaciones entre sí.
