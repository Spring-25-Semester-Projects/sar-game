from entities.mock_entity import *

class Rescuer(Entity):
    def __init__(self, map):
        super().__init__(map)
        self.resources = 100
        self.stats = [self.points, self.resources]
    
    def replinsh(self, vl):
        self.resources += max(self.hunger - vl, 0)
    
    def seek(self):
        return None # Path-finder later.