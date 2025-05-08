import pygame
import numpy as np
from config import HEX_W, HEX_H
from hex import Hex, Center
from config import WIDTH, HEIGHT, HEX_COLOR

class Map:
    def __init__(self, width = HEX_W, height = HEX_H):
        pass
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

    def screen_to_hex(self, point):
        scale = np.sqrt(3)/2

        t1 = point[0] / self.radius
        t2 = (point[1] / self.radius) / np.sqrt(3)

        y = np.floor((np.floor((point[1] / self.radius) / scale) + np.floor(t2 - t1) + 2.0) / 3.0)
        x = np.floor((np.floor(t1 - t2) + np.floor(t1 + t2) + 2.0) / 3.0)

        class Cube:
            def __init__(self, a=0, b=0, c=0):
                self.a, self.b, self.c = int(a), int(b), int(c)

        return Cube(x,y,-x-y)
    
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

    def initialize_fog_of_war(self):
        self.fog_of_war = {hex_tile: False for hex_tile in self.hexes.values()}  

    def update_visibility(self, center_hex):
       
        self.fog_of_war[center_hex] = True
        
        for direction in CONST_unit_direction:
            neighbor = Hex(center_hex.x + direction[0], 
                        center_hex.y + direction[1], 
                        center_hex.z + direction[2])
            if neighbor in self.fog_of_war:
                self.fog_of_war[neighbor] = True
