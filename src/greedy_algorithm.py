from typing import List, Dict, Any, Set, Optional, Tuple
import numpy as np

try:
    from .genetic_algorithm import OrienteeringProblem
except ImportError:
    from genetic_algorithm import OrienteeringProblem


class GreedyOrienteering:
    def __init__(self, problem: OrienteeringProblem):
        self.problem = problem

    def _marginal_cost(self, current: int, candidate: int) -> float:
        driving = self.problem.driving_time(current, candidate)
        visiting = float(self.problem.visit_times[candidate])
        return max(1.0, driving + visiting)

    def _can_visit_and_return(
        self, current: int, candidate: int, elapsed_time: float, budget: float
    ) -> bool:
        to_candidate = self.problem.driving_time(current, candidate)
        visiting = float(self.problem.visit_times[candidate])
        to_depot = self.problem.driving_time(candidate, self.problem.depot_idx)
        return (elapsed_time + to_candidate + visiting + to_depot) <= budget

    def _select_best_candidate(
        self, current: int, candidates: Set[int], elapsed: float, budget: float
    ) -> Optional[int]:
        best_node = None
        best_ratio = -1.0

        for cand in candidates:
            if not self._can_visit_and_return(current, cand, elapsed, budget):
                continue
            ratio = float(self.problem.scores[cand]) / self._marginal_cost(current, cand)
            if ratio > best_ratio:
                best_ratio = ratio
                best_node = cand

        return best_node

    def solve_for_budget(self, budget_time: float) -> Dict[str, Any]:
        current_node = self.problem.depot_idx
        visited: List[int] = []
        elapsed = 0.0
        available = set(self.problem.available_nodes())

        while available:
            next_node = self._select_best_candidate(current_node, available, elapsed, budget_time)
            if next_node is None:
                break
            elapsed += self.problem.driving_time(current_node, next_node)
            elapsed += float(self.problem.visit_times[next_node])
            visited.append(next_node)
            available.remove(next_node)
            current_node = next_node

        elapsed += self.problem.driving_time(current_node, self.problem.depot_idx)
        total_score = sum(self.problem.scores[n] for n in visited)

        return {
            "genes": visited,
            "score": round(float(total_score), 2),
            "total_time": round(float(elapsed), 2),
            "budget": budget_time,
        }

    def generate_greedy_front(self, step_minutes: float = 15.0) -> List[Dict[str, Any]]:
        budgets = np.arange(60.0, self.problem.t_max + step_minutes, step_minutes)
        all_solutions = [self.solve_for_budget(float(b)) for b in budgets]
        valid_solutions = [s for s in all_solutions if s["genes"]]
        return self._filter_non_dominated(valid_solutions)

    def _filter_non_dominated(self, solutions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pareto: List[Dict[str, Any]] = []
        for candidate in solutions:
            if not any(self._is_dominated(candidate, other) for other in solutions):
                if not any(self._are_equal(candidate, p) for p in pareto):
                    pareto.append(candidate)
        pareto.sort(key=lambda s: s["total_time"])
        return pareto

    def _is_dominated(self, a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        better_or_equal = (b["score"] >= a["score"]) and (b["total_time"] <= a["total_time"])
        strictly_better = (b["score"] > a["score"]) or (b["total_time"] < a["total_time"])
        return better_or_equal and strictly_better

    def _are_equal(self, a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        return a["score"] == b["score"] and a["total_time"] == b["total_time"]
