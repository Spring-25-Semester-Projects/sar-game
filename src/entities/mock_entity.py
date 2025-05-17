from collections import namedtuple
from map import Map, Hex
from config import ENTITY_COLOR, OFFSET

Directions = namedtuple('Direction', ['SS', 'SE', 'SW', 'NN', 'NE', 'NW'])
CONST_direction = Directions(SS=5, SE=4, SW=6, NN=2, NE=1, NW=3)


class Entity():
    def __init__(self, map: Map, color=ENTITY_COLOR, health=100):
        self.hexEntity = Hex()
        self.map = map
        self.color = color
        self.health = health
        self.points = 100
        self.position = self._hex_to_screen()
        self.alive = True  
    
    
    
    def _hex_to_screen(self, hex_coords=None):
        """Convert hex coordinates to screen position"""
        if hex_coords is None:
            hex_coords = self.hexEntity
        center = self.map.hex_to_screen(hex_coords)
        return (int(center.q + OFFSET[0]), int(center.r + OFFSET[1]))
        

    def entity_position(self):
        center = self.map.hex_to_screen(self.hexEntity)
        return (center.q + OFFSET[0], center.r + OFFSET[1])
        
    def move(self, move_dir):
        move_to_tiles = self.map.neighbor_hex(self.hexEntity)
        i = getattr(CONST_direction, move_dir, None)
        if i is not None and i < len(move_to_tiles):
            self.hexEntity = Hex(*move_to_tiles[i])
            self.position = self.entity_position()
            return [*move_to_tiles[i]]
        return None
    
    def hurt(self, vl):
        self.points -= vl
        return self.points
        
    def take_damage(self, amount):  
        self.health -= amount
        return self.health
        
    def is_alive(self): 
        return self.health > 0