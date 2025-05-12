import numpy as np
from entities.mock_entity import *

class Survivor(Entity):
    def __init__(self, map, color=ENTITY_COLOR):
        super().__init__(map, color)
        self.stamina = 100
        self.hunger = 0
        self.stats = [self.points, self.stamina, self.hunger]
        self.sane = True # Well, for now.

        def hurt(self, vl):
            self.stats -= vl

            return self.stats
        
        def eat(self, vl):
            hurt([0, max(self.hunger - vl, 0), min(self.stamina + ((1/3) * vl), 100)])
        
        def decide(self, need_to_move):
            if not self.sane:
                super().move()
            else:
                return CONST_direction[np.random.randint(0,6)]


        

            
            
            
        
            

