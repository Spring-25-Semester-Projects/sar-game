import numpy as np
from entities.mock_entity import *

class Survivor(Entity):
    def __init__(self, map):
        super().__init__(map)

        # ! THIS IS ONLY FOR TESTING, DEFAUT SPAWN POSITION IS BASED ON SEED
        self.hexEntity = Hex(-12,6,6)
        self.position = self.entity_position()

        self.stamina = 100
        self.hunger = 0
        self.stats = [self.points, self.stamina, self.hunger]
        self.sane = True # Well, for now.
        
        def eat(self, vl):
            self.stats += ([0, max(self.hunger - vl, 0), min(self.stamina + ((1/3) * vl), 100)])
        
        def decide(self):
            if not self.sane:
                return super().move(CONST_direction[np.random.randint(0,6)])
            
            else:
                return None # Minimax Function later.


        

            
            
            
        
            

