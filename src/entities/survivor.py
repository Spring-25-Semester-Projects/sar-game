import numpy as np
from config import CONST_SURVIVOR_SPRITE_PATH
from src.entities.mock_entity import Entity, Hex




class Survivor(Entity):
    def __init__(self, map):
        # Call parent constructor with the specific sprite path
        super().__init__(map, sprite_path=CONST_SURVIVOR_SPRITE_PATH)

        # ! THIS IS ONLY FOR TESTING, DEFAULT SPAWN POSITION IS BASED ON SEED
        self.hexEntity = map.hexes[Hex(-12,6,6)]
        self.position = self.entity_position()

        self.stamina = 100
        self.hunger = 0
        self.stats = [self.points, self.stamina, self.hunger]
        self.sane = True # Well, for now.

    def eat(self, vl):
        self.stats = [self.stats[0], max(self.hunger - vl, 0), min(self.stamina + ((1/3) * vl), 100)]
        
    def decide(self):
        """Implements random movement decision logic based on sanity level"""
        if not self.sane:
            # When insane, picks completely random direction
            random_dir_index = np.random.randint(0, 6)
            directions = ["NN", "NE", "NW", "SS", "SE", "SW"]
            random_dir = directions[random_dir_index]
            return self.move(random_dir)
        else:
            # When sane, will implement more advanced behavior later with minimax
            return None
    
    def move(self, move_dir):
        """Override the parent move method to track stamina and hunger"""
        result = super().move(move_dir)
        if result is not None:
            # Randomly decrease stamina and increase hunger when moving
            if np.random.random() < 0.3:  # 30% chance
                self.stamina = max(0, self.stamina - 2)
                self.hunger = min(100, self.hunger + 1)
                
            # If stamina reaches 0 or hunger reaches 100, survivor goes insane
            if self.stamina <= 0 or self.hunger >= 100:
                self.sane = False
        
        return result
    
    def __repr__(self):
        return f"Entity={type(self).__name__}. Health={self.points}, Stamina={self.stamina}, Hunger={self.hunger}, Sane={self.sane}."
