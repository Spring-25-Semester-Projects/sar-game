from src.entities.mock_entity import Entity, Hex
from collections import defaultdict, Counter
from config import CONST_RESCUER_SPRITE_PATH
from src.hex import Hex
import heapq
import random
import numpy as np
import time



class Rescuer(Entity):
    def __init__(self, map):
        super().__init__(map, sprite_path=CONST_RESCUER_SPRITE_PATH)

        self.resources = float('inf') 
        self.stats = [self.points, self.resources]
        self.inventory = {}
        self.target_path = []
        self.costs = None  
        
        self.visit_count = Counter()  
        self.visit_history = []       
        self.history_size = 10        
        self.last_exploration_time = time.time()  
        self.stuck_threshold = 3      
        self.exploration_boost = 1.0  
        
        self.survivor_move_history = []  
        self.survivor_position_history = []  
        self.survivor_last_seen_position = None
        self.survivor_last_seen_time = 0  
        self.survivor_direction_counts = Counter()  
        self.survivor_terrain_prefs = defaultdict(Counter)  
        self.laplace_smoothing = 1.0  
        
    
    def hex_distance(self, hex1, hex2):
        return self.map.hex_distance(hex1, hex2)
    
    def a_star_pathfinding(self, start_hex, goal_hex, costs):
        open_set = []
        closed_set = set()
        
        heapq.heappush(open_set, (0, id(start_hex), start_hex))
        
        g_score = defaultdict(lambda: float('inf'))
        g_score[start_hex] = 0
        
        f_score = defaultdict(lambda: float('inf'))
        f_score[start_hex] = self.hex_distance(start_hex, goal_hex)
        
        came_from = {}
        
        while open_set:
            _, _, current_hex = heapq.heappop(open_set)
            
            if current_hex == goal_hex:
                path = []
                while current_hex in came_from:
                    path.append(current_hex)
                    current_hex = came_from[current_hex]
                path.append(start_hex)
                return list(reversed(path))
            
            closed_set.add(current_hex)
            
            for neighbor in self.map.neighbor_hex(current_hex):
                if neighbor is None or neighbor in closed_set:
                    continue
                
                if costs[neighbor] == float('-inf'):
                    continue
                
                visit_penalty = self._calculate_visit_penalty(neighbor)
                
                tentative_g = g_score[current_hex] + costs[neighbor] + visit_penalty
                
                if tentative_g >= g_score[neighbor]:
                    continue
                
                came_from[neighbor] = current_hex
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + self.hex_distance(neighbor, goal_hex)
                
                if neighbor not in [h for _, _, h in open_set]:
                    heapq.heappush(open_set, (f_score[neighbor], id(neighbor), neighbor))
        
        return []
    
    def _calculate_visit_penalty(self, hex):
        visit_count = self.visit_count[hex]
        
        if visit_count >= self.stuck_threshold:
            return visit_count * self.exploration_boost * 5.0  
        
        if hex in self.visit_history:
            return 2.0 * self.exploration_boost  
            
        return 0
    
    def update_survivor_model(self, current_survivor_pos):
        if current_survivor_pos is None:
            return
            
        if self.survivor_last_seen_position is None:
            self.survivor_last_seen_position = current_survivor_pos
            self.survivor_position_history.append(current_survivor_pos)
            self.survivor_last_seen_time = time.time()
            return
            
        if current_survivor_pos != self.survivor_last_seen_position:
            neighbors = self.map.neighbor_hex(self.survivor_last_seen_position)
            for i, neighbor in enumerate(neighbors):
                if neighbor == current_survivor_pos:
                    directions = ["SS", "SE", "SW", "NN", "NE", "NW"]
                    moved_direction = directions[i]
                    self.survivor_direction_counts[moved_direction] += 1
                    self.survivor_move_history.append(moved_direction)
                    
                    if self.costs and current_survivor_pos in self.costs:
                        cost = self.costs[current_survivor_pos]
                        if cost != float('-inf'):  
                            self.survivor_terrain_prefs[moved_direction][cost] += 1
                    
                    if len(self.survivor_move_history) > 20:
                        self.survivor_move_history.pop(0)
                    break
            
            self.survivor_position_history.append(current_survivor_pos)
            if len(self.survivor_position_history) > 20:
                self.survivor_position_history.pop(0)
                
            self.survivor_last_seen_position = current_survivor_pos
            self.survivor_last_seen_time = time.time()
    
    def predict_survivor_movement_probs(self, current_pos, valid_moves):
        if not self.survivor_move_history:
            num_options = len(valid_moves) + 1  
            stay_prob = 1.0 / num_options
            move_prob = 1.0 / num_options
            
            probs = {current_pos: stay_prob}
            for move in valid_moves:
                if move != current_pos:  
                    probs[move] = move_prob
            return probs
        
        total_moves = sum(self.survivor_direction_counts.values()) + len(self.survivor_direction_counts) * self.laplace_smoothing
        
        probs = {}
        
        neighbors = self.map.neighbor_hex(current_pos)
        directions = ["SS", "SE", "SW", "NN", "NE", "NW"]
        
        raw_probs = {}
        for i, neighbor in enumerate(neighbors):
            if neighbor is None or neighbor not in valid_moves:
                continue
                
            direction = directions[i]
            
            dir_count = self.survivor_direction_counts[direction] + self.laplace_smoothing
            dir_prob = dir_count / total_moves
            
            terrain_prob = 1.0
            if self.costs and neighbor in self.costs:
                cost = self.costs[neighbor]
                if cost != float('-inf'):
                    cost_count = self.survivor_terrain_prefs[direction][cost] + self.laplace_smoothing
                    total_cost_counts = sum(self.survivor_terrain_prefs[direction].values()) + \
                                     len(self.survivor_terrain_prefs[direction]) * self.laplace_smoothing
                    if total_cost_counts > 0:
                        terrain_prob = cost_count / total_cost_counts
            
            raw_probs[neighbor] = dir_prob * terrain_prob
        
        move_activity = min(0.9, len(self.survivor_move_history) / 20)  
        stay_prob = 1.0 - move_activity
        raw_probs[current_pos] = stay_prob
        
        total_prob = sum(raw_probs.values())
        if total_prob > 0:
            for pos, prob in raw_probs.items():
                probs[pos] = prob / total_prob
        else:
            even_prob = 1.0 / len(raw_probs)
            for pos in raw_probs:
                probs[pos] = even_prob
                
        return probs
    
    def expectimax_decision(self, survivor_hex, visited_hexes, costs):
        self.update_survivor_model(survivor_hex)
        
        current_time = time.time()
        time_since_last_exploration = current_time - self.last_exploration_time
        
        if time_since_last_exploration > 3.0:  
            self.exploration_boost = min(3.0, self.exploration_boost + 0.5)
        else:
            self.exploration_boost = max(1.0, self.exploration_boost - 0.1)  
            
        if survivor_hex is None:
            return self.explore_decision(visited_hexes, costs)
        
        max_depth = 2
        
        base_path = self.a_star_pathfinding(self.hexEntity, survivor_hex, costs)
        
        if not base_path:
            return self.explore_decision(visited_hexes, costs)
        
        self.target_path = base_path
        
        if len(base_path) <= 2:
            return base_path[1] if len(base_path) > 1 else None
        
        neighbors = self.map.neighbor_hex(self.hexEntity)
        valid_moves = [n for n in neighbors if n is not None and costs[n] != float('-inf')]
        
        if not valid_moves:
            return None
        
        best_score = float('-inf')
        best_move = None
        
        for move in valid_moves:
            score = self._expectimax_score(
                move,                
                survivor_hex,        
                costs,               
                1,                   
                max_depth,           
                visited_hexes        
            )
            
            visit_penalty = self._calculate_visit_penalty(move)
            score -= visit_penalty
            
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move if best_move else base_path[1]
    
    def _expectimax_score(self, rescuer_pos, survivor_pos, costs, depth, max_depth, visited_hexes):
        if depth >= max_depth or rescuer_pos == survivor_pos:
            if rescuer_pos == survivor_pos:
                return 1000  
            
            distance_score = -self.hex_distance(rescuer_pos, survivor_pos) * 10
            cost_score = -costs[rescuer_pos] if costs[rescuer_pos] != float('-inf') else -100
            
            exploration_score = 50 if rescuer_pos not in visited_hexes else 0  
            novelty_bonus = 25 if rescuer_pos not in self.visit_history else 0  
            
            return distance_score + cost_score + exploration_score + novelty_bonus
        
        if depth % 2 == 1:
            neighbors = self.map.neighbor_hex(rescuer_pos)
            valid_moves = [n for n in neighbors if n is not None and costs[n] != float('-inf')]
            
            if not valid_moves:
                return -1000  
            
            best_score = float('-inf')
            for move in valid_moves:
                score = self._expectimax_score(move, survivor_pos, costs, depth + 1, max_depth, visited_hexes)
                best_score = max(best_score, score)
                
            return best_score
        
        else:
            neighbors = self.map.neighbor_hex(survivor_pos)
            valid_moves = [n for n in neighbors if n is not None and costs[n] != float('-inf')]
            
            if not valid_moves:
                valid_moves = [survivor_pos]  
            
            valid_moves.append(survivor_pos)  
            move_probs = self.predict_survivor_movement_probs(survivor_pos, valid_moves)
            
            total_score = 0
            
            for move, probability in move_probs.items():
                score = self._expectimax_score(rescuer_pos, move, costs, depth + 1, max_depth, visited_hexes)
                total_score += probability * score
            
            return total_score
    

    def explore_decision(self, visited_hexes, costs):
        neighbors = self.map.neighbor_hex(self.hexEntity)
        valid_neighbors = [n for n in neighbors if n is not None and costs[n] != float('-inf')]
        
        if not valid_neighbors:
            return None
        
        visited_set = set(visited_hexes)
        
        unvisited = [n for n in valid_neighbors if n not in visited_set]
        
        if unvisited:
            self.last_exploration_time = time.time()
            self.exploration_boost = 1.0
            
            unvisited.sort(key=lambda x: (costs[x], random.random()))  
            return unvisited[0]
        
        all_unvisited = [h for h in self.map.hexes.values() if h not in visited_set]
        if all_unvisited:
            closest_hexes = sorted(
                all_unvisited,
                key=lambda h: self.hex_distance(self.hexEntity, h)
            )[:5]  
            
            if closest_hexes:
                target_hex = random.choice(closest_hexes)
                path = self.a_star_pathfinding(self.hexEntity, target_hex, costs)
                if path and len(path) > 1:
                    return path[1]
        
        valid_neighbors.sort(key=lambda x: (
            self.visit_count[x] * 5,  
            costs[x],
            random.random()  
        ))
        return valid_neighbors[0]


    
    def get_direction_to_hex(self, target_hex):
        if target_hex is None:
            return None
            
        neighbors = self.map.neighbor_hex(self.hexEntity)
        
        for i, neighbor in enumerate(neighbors):
            if neighbor == target_hex:
                directions = ["SS", "SE", "SW", "NN", "NE", "NW"]
                return directions[i]
                
        return None
    
    def move_with_ai(self, survivor_hex, visited_hexes, costs):
        current_pos = self.hexEntity
        self.visit_count[current_pos] += 1
        
        self.visit_history.append(current_pos)
        if len(self.visit_history) > self.history_size:
            self.visit_history.pop(0)
            
        target_hex = self.expectimax_decision(survivor_hex, visited_hexes, costs)
        direction = self.get_direction_to_hex(target_hex)
        
        if direction:
            return self.move(direction)
        return None
    
    def move(self, move_dir):
        result = super().move(move_dir)
        if result is not None:
            hex_moved_to = self.hexEntity
            
            if self.costs is not None:
                move_cost = max(1, self.costs[hex_moved_to] if self.costs[hex_moved_to] != float('-inf') else 1)
            else:
                move_cost = 1  
                
            self.resources = max(0, self.resources - move_cost)
        
        return result