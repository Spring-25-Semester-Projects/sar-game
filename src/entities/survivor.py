import random
import pygame
import sys
import os
import heapq
from collections import namedtuple
import numpy as np

# the true start of survivor from line 112 approx.
#from config import WIDTH, HEIGHT, FPS, ENTITY_COLOR, OFFSET, HEX_COLOR

WIDTH, HEIGHT = 800, 600
FPS = 60

HEX_W = 10
HEX_H = 10

ENTITY_COLOR = (0,255,0)
OFFSET = (WIDTH // 2, HEIGHT // 2)
HEX_COLOR = (50, 50, 50)

#start from map import Map, Hex
CONST_unit_direction = np.array([[1, -1, 0],[1, 0, -1],[0, 1, -1],[-1, 1, 0],[-1, 0, 1],[0, -1, 1]])

CONST_flatTopped_matrix = np.array([[3/2, 0],[np.sqrt(3)/2, np.sqrt(3)]])

CONST_screen_matrix = np.array([[0, 0],[WIDTH, 0],[0, HEIGHT],[WIDTH, HEIGHT]]) - np.array([WIDTH/2,HEIGHT/2]) # Sceond term is to center.

class Center:
    def __init__(self, q=0, r=0):
        self.q, self.r = q, r

class Hex:
    def __init__(self, x=0, y=0, z=0):
        self.x, self.y, self.z = x, y, z

    def __hash__(self):
        hq = hash(self.x)
        hr = hash(self.y)

        return hq ^ (hr + 0x9e3779b9 + ((hq << 6) & 0xFFFFFFFFFFFFFFFF) + (hq >> 2))

class Map(Hex):
    def __init__(self, radius=10):
        self.radius = radius

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

# end of map.py

# Direction indices for flat-topped hex grid
Directions = namedtuple('Direction', ['SS', 'SE', 'SW', 'NN', 'NE', 'NW'])
CONST_DIRECTION = Directions(SS=0, SE=1, SW=2, NN=3, NE=4, NW=5)

class AStarPathfinder:
    def __init__(self, game_map: Map):
        self.map = game_map

    def heuristic(self, a: Hex, b: Hex) -> int:
        return max(abs(a.x - b.x), abs(a.y - b.y), abs(a.z - b.z))

    def get_neighbors(self, node: Hex) -> list:
        raw = self.map.neighbor_hex(node)
        neighbors = []
        for coords in raw:
            q, r, s = coords
            h = Hex(int(q), int(r), int(s))
            if h in self.map.hexes:
                neighbors.append(h)
        return neighbors

    def find_path(self, start: Hex, goal: Hex) -> list:
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return list(reversed(path))

            for neighbor in self.get_neighbors(current):
                tentative_g = g_score[current] + 1
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        return []

class Inventory:
    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        self.items = []

    def add(self, item) -> bool:
        if len(self.items) < self.capacity:
            self.items.append(item)
            return True
        return False

    def remove(self, item) -> bool:
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    def has(self, name: str) -> bool:
        return any(item.name == name for item in self.items)

    def clear(self):
        self.items.clear()

    def list_items(self) -> list:
        return [item.name for item in self.items]

class Entity:
    def __init__(self, game_map: Map, color=ENTITY_COLOR, health=100):
        self.hex = Hex()
        self.map = game_map
        self.color = color
        self.health = health
        self.position = self._hex_to_screen()

    def _hex_to_screen(self) -> tuple:
        center = self.map.hex_to_screen(self.hex)
        return (int(center.q + OFFSET[0]), int(center.r + OFFSET[1]))

    def move(self, direction: str) -> bool:
        neighbors = self.map.neighbor_hex(self.hex)
        idx = getattr(CONST_DIRECTION, direction, None)
        if idx is None or idx >= len(neighbors):
            return False
        self.hex = Hex(*neighbors[idx])
        self.position = self._hex_to_screen()
        return True

    def move_to(self, target_hex: Hex, pathfinder: AStarPathfinder) -> bool:
        path = pathfinder.find_path(self.hex, target_hex)
        if not path:
            return False
        for step in path:
            self.hex = step
            self.position = self._hex_to_screen()
        return True

    def take_damage(self, amount: int) -> int:
        self.health -= amount
        return self.health

    def is_alive(self) -> bool:
        return self.health > 0

class Item:
    def __init__(self, name: str, hex: Hex):
        self.name = name
        self.hex = hex

    def apply(self, target: Entity):
        raise NotImplementedError

class Weapon(Item):
    def __init__(self, name: str, damage: int, hex: Hex):
        super().__init__(name, hex)
        self.damage = damage

    def apply(self, target: Entity):
        target.take_damage(self.damage)

class Food(Item):
    def __init__(self, name: str, nutrition: int, hex: Hex):
        super().__init__(name, hex)
        self.nutrition = nutrition

    def apply(self, target: 'Survivor'):
        target.eat(self.nutrition)

class Survivor(Entity):
    def __init__(self, game_map: Map, color=ENTITY_COLOR, health: int =100, speed: int =1):
        super().__init__(game_map, color, health)
        self.speed = speed
        self.inventory = Inventory()
        self.stamina = 100.0
        self.hunger = 0.0
        self.pathfinder = AStarPathfinder(game_map)

    def move(self, direction: str) -> bool:
        if self.stamina < 1:
            return False
        moved = super().move(direction)
        if moved:
            self.stamina -= 1
            self.hunger += 0.5
        return moved

    def move_towards(self, target: Hex) -> bool:
        if self.stamina < 1:
            return False
        return super().move_to(target, self.pathfinder)

    def attack(self, target: Entity, weapon: Weapon = None):
        if weapon and weapon in self.inventory.items:
            weapon.apply(target)
        else:
            target.take_damage(5)
        self.stamina = max(self.stamina - 2, 0)

    def eat(self, amount: int):
        self.hunger = max(self.hunger - amount, 0)
        self.stamina = min(self.stamina + amount * 0.5, 100)

    def pick_item(self, item: Item) -> bool:
        if item.hex == self.hex:
            return self.inventory.add(item)
        return False

    def drop_item(self, item: Item) -> bool:
        if self.inventory.remove(item):
            item.hex = self.hex
            return True
        return False

    def rest(self, duration: float):
        self.stamina = min(self.stamina + duration * 5, 100)
        self.hunger = min(self.hunger + duration * 0.2, 100)

    def heal(self, amount: int):
        self.health = min(self.health + amount, 100)

    def update(self, dt):
        self.hunger += 0.1 * dt
        if self.hunger > 100:
            self.take_damage(1 * dt)
        self.stamina = min(self.stamina + 0.5 * dt, 100)

class NPC(Survivor):
    def __init__(self, game_map: Map, ai_type: str ='wander', color=ENTITY_COLOR, health: int =100, speed: int =1):
        super().__init__(game_map, color, health, speed)
        self.ai_type = ai_type

    def decide(self, player: Survivor) -> str:
        if self.ai_type == 'wander':
            return random.choice(list(CONST_DIRECTION._fields))
        if self.ai_type == 'chase':
            dq = player.hex.x - self.hex.x
            dz = player.hex.z - self.hex.z
            if abs(dq) >= abs(dz):
                return 'SE' if dq>0 else 'NW'
            return 'SW' if dz>0 else 'NN'
        return None

    def update(self, dt, player: Survivor):
        super().update(dt)
        if self.ai_type == 'chase':
            self.move_towards(player.hex)
        else:
            direction = self.decide(player)
            if direction:
                self.move(direction)

def spawn_items(game_map: Map, num_items: int =10) -> list:
    items = []
    hexes = list(game_map.hexes.keys())
    for _ in range(num_items):
        hex_pos = random.choice(hexes)
        if random.random() < 0.5:
            items.append(Weapon('Sword', 10, hex_pos))
        else:
            items.append(Food('Apple', 20, hex_pos))
    return items
