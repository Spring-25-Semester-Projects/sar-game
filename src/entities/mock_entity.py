from collections import namedtuple
from map import Map, Hex
from config import ENTITY_COLOR, OFFSET

Directions = namedtuple('Direction', ['SS', 'SE', 'SW', 'NN', 'NE', 'NW'])
CONST_direction = Directions(SS=0, SE=1, SW=2, NN=3, NE=4, NW=5)

class Entity():
    def __init__(self, map: Map, color=ENTITY_COLOR):
        self.hexEntity = Hex()
        self.map = map
        self.color = color
        self.points = 100
        self.position = self.entity_position()
        
    def entity_position(self):
        center = self.map.hex_to_screen(self.hexEntity)

        position = (center.q + OFFSET[0], center.r + OFFSET[1])

        return position
        
    def move(self, move_dir):
        move_to_tiles = self.map.neighbor_hex(self.hexEntity)

        i = getattr(CONST_direction, move_dir, None)

        self.hexEntity = Hex(*move_to_tiles[i])

        self.position = self.entity_position()

        return [*move_to_tiles[i]]
    
    def hurt(self, vl):
        self.points -= vl

        return self.points