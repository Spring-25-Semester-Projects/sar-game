import heapq
from collections import deque

# we can add algos here 
class PathfindingAlgorithms:
    @staticmethod
    def bfs(graph, start, goal):
        queue = deque([[start]])
        visited = set()
        
        while queue:
            path = queue.popleft()
            node = path[-1]
            
            if node == goal:
                return path
                
            if node not in visited:
                for neighbor in graph.get(node, []):
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)
                    
                visited.add(node)
        return []

    @staticmethod
    def dfs(graph, start, goal):
        stack = [[start]]
        visited = set()
        
        while stack:
            path = stack.pop()
            node = path[-1]
            
            if node == goal:
                return path
                
            if node not in visited:
                for neighbor in graph.get(node, []):
                    new_path = list(path)
                    new_path.append(neighbor)
                    stack.append(new_path)
                    
                visited.add(node)
        return []

    @staticmethod
    def ucs(graph, start, goal, cost_func):
        heap = [(0, [start])]
        visited = set()
        
        while heap:
            cost, path = heapq.heappop(heap)
            node = path[-1]
            
            if node == goal:
                return path
                
            if node not in visited:
                for neighbor in graph.get(node, []):
                    new_cost = cost + cost_func(node, neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    heapq.heappush(heap, (new_cost, new_path))
                    
                visited.add(node)
        return []