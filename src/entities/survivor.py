import numpy as np
from config import CONST_SURVIVOR_SPRITE_PATH
from src.entities.mock_entity import Entity, Hex
import random
from collections import deque

class Survivor(Entity):
    def __init__(self, map):
        super().__init__(map, sprite_path=CONST_SURVIVOR_SPRITE_PATH)
        self.hexEntity = map.hexes[Hex(-12,6,6)]
        self.position = self.entity_position()
        
        self.stamina = 100
        self.hunger = 0
        self.sane = True
        self.move_counter = 0
        self.move_frequency = random.randint(1, 3)
        self.costs = None
        self.visited_hexes = deque(maxlen=10)
        self.exploration_boost = 1.0

        
    def decide(self):
        self.move_counter += 1
        
        if self.move_counter < self.move_frequency:
            return None
            
        self.move_counter = 0
        self.move_frequency = random.randint(1, 3)
        
        if not self.sane:
            return self.move_randomly()
        else:
            return self.move_strategically()
    
    def move_randomly(self):
        directions = ["SS", "SE", "SW", "NN", "NE", "NW"]
        return self.move(random.choice(directions))
    
    def move_strategically(self):
        neighbors = self.map.neighbor_hex(self.hexEntity)
        valid_moves = []
        
        for i, neighbor in enumerate(neighbors):
            if neighbor is None or not self.costs or neighbor not in self.costs:
                continue
                
            cost = self.costs[neighbor]
            if cost == float('-inf'):
                continue
                
            visit_penalty = 0
            if neighbor in self.visited_hexes:
                visit_penalty = 5 * self.exploration_boost
                
            adjusted_cost = cost + visit_penalty
            valid_moves.append((i, adjusted_cost))
        
        if not valid_moves:
            return None
            
        valid_moves.sort(key=lambda x: x[1])
        
        if random.random() < 0.2:
            if len(valid_moves) > 1:
                best_move_index = random.choice(range(min(3, len(valid_moves))))
            else:
                best_move_index = 0
        else:
            best_move_index = 0
            
        directions = ["SS", "SE", "SW", "NN", "NE", "NW"]
        move_result = self.move(directions[valid_moves[best_move_index][0]])
        
        if move_result is not None:
            self.visited_hexes.append(self.hexEntity)
            if self.hexEntity in self.visited_hexes:
                self.exploration_boost = min(3.0, self.exploration_boost + 0.2)
            else:
                self.exploration_boost = max(1.0, self.exploration_boost - 0.1)
        
        return move_result
    
    def move(self, move_dir):
        result = super().move(move_dir)
        if result is not None:
            if np.random.random() < 0.3:
                self.stamina = max(0, self.stamina - 2)
                self.hunger = min(100, self.hunger + 1)
                
            if self.stamina <= 0 or self.hunger >= 100:
                self.sane = False
        return result
    
    def __repr__(self):
        return f"Entity={type(self).__name__}. Health={self.points}, Stamina={self.stamina}, Hunger={self.hunger}, Sane={self.sane}."