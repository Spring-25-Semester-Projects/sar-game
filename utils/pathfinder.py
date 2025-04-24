import heapq
from typing import Any, Dict, List, Tuple, Optional, Set

class AStar:
    def __init__(self, graph: Dict[Any, List[Tuple[Any, float]]], heuristic: Any) -> None:
        self.graph = graph
        self.heuristic = heuristic

    def search(self, start: Any, goal: Any) -> Optional[List[Any]]:
        open_heap: List[Tuple[float, Any]] = []
        heapq.heappush(open_heap, (self.heuristic(start, goal), start))
        open_set: Set[Any] = {start}
        closed_set: Set[Any] = set()

        g_score: Dict[Any, float] = {start: 0.0}
        f_score: Dict[Any, float] = {start: self.heuristic(start, goal)}
        came_from: Dict[Any, Any] = {}

        while open_heap:
            current_f, current = heapq.heappop(open_heap)
            open_set.remove(current)

            if current == goal:
                return self._reconstruct_path(came_from, current)

            closed_set.add(current)

            for neighbor, cost in self.graph.get(current, []):
                if neighbor in closed_set:
                    continue
                tentative_g = g_score[current] + cost

                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal)

                    if neighbor not in open_set:
                        heapq.heappush(open_heap, (f_score[neighbor], neighbor))
                        open_set.add(neighbor)

        return None

    def _reconstruct_path(self, came_from: Dict[Any, Any], current: Any) -> List[Any]:
        path: List[Any] = []
        while current in came_from:
            path.append(current)
            current = came_from[current]
        path.append(current)
        path.reverse()
        return path
