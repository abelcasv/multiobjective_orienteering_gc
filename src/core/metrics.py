from typing import List, Tuple, Dict, Any
import numpy as np
from scipy import stats


def calcular_hipervolumen(
    points: List[Tuple[float, float]],
    ref_point: Tuple[float, float] = (480.0, 0.0),
) -> float:
    t_ref, s_ref = ref_point
    valid = [p for p in points if p[0] <= t_ref and p[1] >= s_ref]
    if not valid:
        return 0.0

    valid.sort(key=lambda p: p[0])
    non_dominated: List[Tuple[float, float]] = []
    max_score = s_ref

    for t, s in valid:
        if s > max_score:
            non_dominated.append((t, s))
            max_score = s

    hypervolume = 0.0
    for i, (t_curr, s_curr) in enumerate(non_dominated):
        t_next = non_dominated[i + 1][0] if i + 1 < len(non_dominated) else t_ref
        hypervolume += (t_next - t_curr) * (s_curr - s_ref)

    return float(hypervolume)


def calcular_spread(points: List[Tuple[float, float]]) -> float:
    if len(points) < 2:
        return 0.0

    sorted_pts = sorted(points, key=lambda p: p[0])
    distances = [
        np.hypot(sorted_pts[i + 1][0] - sorted_pts[i][0], sorted_pts[i + 1][1] - sorted_pts[i][1])
        for i in range(len(sorted_pts) - 1)
    ]
    mean_dist = np.mean(distances)
    if mean_dist == 0:
        return 0.0

    numerator = sum(abs(d - mean_dist) for d in distances)
    denominator = len(distances) * mean_dist
    return float(numerator / denominator) if denominator > 0 else 0.0


def test_wilcoxon(sample_a: List[float], sample_b: List[float]) -> Dict[str, Any]:
    diffs = np.array(sample_a) - np.array(sample_b)
    if np.all(diffs == 0):
        return {"statistic": 0.0, "p_value": 1.0, "significant_at_005": False}
    try:
        res = stats.wilcoxon(sample_a, sample_b, alternative="two-sided")
        return {
            "statistic": float(res.statistic),
            "p_value": float(res.pvalue),
            "significant_at_005": bool(res.pvalue < 0.05),
        }
    except Exception:
        stat, p_val = stats.ranksums(sample_a, sample_b)
        return {
            "statistic": float(stat),
            "p_value": float(p_val),
            "significant_at_005": bool(p_val < 0.05),
        }


def resumen_estadistico(sample: List[float]) -> Dict[str, float]:
    arr = np.array(sample, dtype=float)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "median": float(np.median(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }
