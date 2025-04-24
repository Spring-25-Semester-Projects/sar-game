import numpy as np
from hex import Hex, Center
from config import WIDTH, HEIGHT, HEX_COLOR

CONST_unit_direction = np.array([[0, -1, 1], [1, -1, 0], [-1, 0, 1], [0, 1, -1], [1, 0, -1], [-1, 1, 0]])

CONST_flatTopped_matrix = np.array([[3/2, 0],[np.sqrt(3)/2, np.sqrt(3)]])

CONST_screen_matrix = np.array([[0, 0],[WIDTH, 0],[0, HEIGHT],[WIDTH, HEIGHT]]) - np.array([WIDTH/2,HEIGHT/2]) # Sceond term is to center.

class Map(Hex):
    def __init__(self, radius=10):
        self.radius = radius

        # This long variable just turns the pixel coord.’s to hex coord. (for screen), so it knows where the tile boundary is.
        screen_to_hex_matrix = np.array([np.linalg.inv(self.radius * CONST_flatTopped_matrix) @ ar for ar in CONST_screen_matrix]) 

        min_screenHex = np.floor(np.min(screen_to_hex_matrix, axis=0))-2
        max_screenHex = np.ceil(np.max(screen_to_hex_matrix, axis=0))+2
        min_x, min_z = map(int, min_screenHex)
        max_x, max_z = map(int, max_screenHex)

        self.hexes = {}
        for q in range(min_x, max_x + 1):
            for r in range(min_z, max_z + 1):
                s = -q-r
                h = Hex(q, r, s)

                self.hexes[h] = h

    def hex_to_screen(self, hex: Hex):
        hexagon_matrix = self.radius * (CONST_flatTopped_matrix @ np.array([hex.x, hex.z]))

        return Center(*hexagon_matrix)
    
    def screen_to_hex(self, hex: Hex):
        center = self.hex_to_screen(hex)

        radius = np.sqrt(3)/2
        t1, t2 = center.q, center.r/radius

        z = np.floor((np.floor(center.r / radius) + np.floor(t2 - t1) + 2) / 3)
        x = np.floor((np.floor(t1 - t2) + np.floor(t2 - t1) + 2) / 3)

        class Cube:
            def __init__(self, a=0, b=0, c=0):
                self.a, self.b, self.c = a, b, c

        return Cube(x,-x-z,z)
    
    def neighbor_hex(self, hex: Hex):
        neighbors_matrix = (np.array([hex.x, hex.y, hex.z]) + CONST_unit_direction)

        return neighbors_matrix
    
    def draw_hex(self, hex: Hex, entityHex=None):
        center = self.hex_to_screen(hex)

        vertices = []
        color = HEX_COLOR

        if entityHex is not None:
            neighbors = self.neighbor_hex(entityHex)

            for hex_nb in neighbors:
                if np.array_equal([hex.x, hex.y, hex.z], hex_nb):
                    color = (231, 76, 60)

                    break

        for i in range(6):
            angle = np.radians(60 * i)

            x = center.q + (self.radius * np.cos(angle))
            y = center.r + (self.radius * np.sin(angle))

            vertices.append([x + WIDTH/2,y + HEIGHT/2])

        return vertices, color