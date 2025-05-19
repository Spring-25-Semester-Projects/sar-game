from collections import namedtuple
import numpy as np
from src.hex import Hex, Center
from config import WIDTH, HEIGHT, HEX_COLOR, SIZE, OFFSET

CONST_unit_direction = np.array([[0, -1, 1], [1, -1, 0], [-1, 0, 1], [0, 1, -1], [1, 0, -1], [-1, 1, 0]])

CONST_scale_matrix = np.array([[1,0],[0,(1.15)*(3/2)/(np.sqrt(3))]])

CONST_flatTopped_matrix = np.array([[3/2, 0],[np.sqrt(3)/2, np.sqrt(3)]])

CONST_screen_matrix = np.array([[0, 0],[WIDTH, 0],[0, HEIGHT],[WIDTH, HEIGHT]]) - OFFSET # Sceond term is to center.

Costs = namedtuple('Cost', ['zero', 'one', 'two', 'three', 'four', 'block'])
CONST_cost = tuple(Costs(zero=0, one=1, two=2, three=3, four=4, block=float('-inf')))

class Map:
    def __init__(self, radius=SIZE):
        self.radius = radius

        # This long variable just turns the pixel coord.’s to hex coord. (for screen), so it knows where the tile boundary is.
        screen_to_hex_matrix = np.array([np.linalg.inv(self.radius * CONST_flatTopped_matrix) @ ar for ar in CONST_screen_matrix]) 

        min_screenHex = np.floor(np.min(screen_to_hex_matrix, axis=0))-2
        max_screenHex = np.ceil(np.max(screen_to_hex_matrix, axis=0))+2

        self.min_x, self.min_z = map(int, min_screenHex)
        self.max_x, self.max_z = map(int, max_screenHex)

        min_x, min_z = map(int, min_screenHex)
        max_x, max_z = map(int, max_screenHex)

        self.hexes = {}
        for q in range(min_x, max_x + 1):
            for r in range(min_z, max_z + 1):
                px, py = (self.radius * (CONST_scale_matrix @ CONST_flatTopped_matrix @ np.array([q, r]))) + OFFSET

                if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                   s = -q-r
                   h = Hex(q, r, s)

                   self.hexes[h] = h

    def hex_to_screen(self, hex: Hex):
        hexagon_matrix = self.radius * (CONST_flatTopped_matrix @ np.array([hex.x, hex.z]))

        return Center(*hexagon_matrix)
    
    def screen_to_hex(self, point):
        scale = np.sqrt(3)/2

        t1 = point[0] / self.radius
        t2 = (point[1] / self.radius) / np.sqrt(3)

        z = np.floor((np.floor((point[1] / self.radius) / scale) + np.floor(t2 - t1) + 2.0) / 3.0)
        x = np.floor((np.floor(t1 - t2) + np.floor(t1 + t2) + 2.0) / 3.0)

        return self.hexes.get(Hex(int(x),int(-x-z),int(z)))

    def neighbor_hex(self, hex: Hex):
        neighbors_matrix = (np.array([*hex]) + CONST_unit_direction)

        neighbors = list()

        for nb in neighbors_matrix:
            if not self.hexes.get(Hex(*nb)):
                neighbors.append(None)
            else:
                neighbors.append(self.hexes[Hex(*nb)])

        return np.array(neighbors, dtype=object)
    
    def hex_distance(self, h1 : Hex, h2 : Hex):
        return max(abs(h1.x - h2.x), abs(h1.y - h2.y), abs(h1.z - h2.z))
    
    def hex_round(self, hex: Hex):
        fcube = np.array([*hex])
        cube = np.round(fcube)

        diff = np.abs(cube-fcube)

        max_i = np.argmax(diff)

        cube[max_i] = -np.sum(np.delete(cube, max_i))

        hex = Hex(*np.int32(cube))
        
        return hex

    def walkable_hex_distance(self, h1 : Hex, h2 : Hex):
        distance = self.hex_distance(h1,h2)

        if distance == 0:
            return [h1]

        interpol_vl = np.linspace(1, distance, num=distance)

        hexes_to_walk = []
        def interpol():
            cube_h1 = np.array([*h1])
            cube_h2 = np.array([*h2])

            for t in interpol_vl:
                i = cube_h1 + ((cube_h2 - cube_h1) * t * (1/distance))

                hexes_to_walk.append(self.hex_round(Hex(*i)))

            return hexes_to_walk

        return interpol()
    
    def map_cost(self):
        costs = {}
        
        for h in self.hexes.values():
            costs[h] = CONST_cost[np.random.randint(0,6)]

        return costs

    def draw_hex(self, hex: Hex):
        center = self.hex_to_screen(hex)

        vertices = []
        color = HEX_COLOR

        for i in range(6):
            angle = np.radians(60 * i)

            x = center.q + (self.radius * np.cos(angle))
            y = center.r + (self.radius * np.sin(angle))

            vertices.append(np.array([x,y])+OFFSET)

        return vertices, color