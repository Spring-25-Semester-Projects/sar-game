import random
import pygame
import sys
import os
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

Directions = namedtuple('Direction', ['SS', 'SE', 'SW', 'NN', 'NE', 'NW'])
CONST_DIRECTION = Directions(SS=0, SE=1, SW=2, NN=3, NE=4, NW=5)

class Entity:

    def __init__(self, game_map: Map, color=ENTITY_COLOR, health=100):
        self.hex = Hex()
        self.map = game_map
        self.color = color
        self.health = health
        self.position = self._hex_to_screen()

    def _hex_to_screen(self):
        center = self.map.hex_to_screen(self.hex)
        return (int(center.q + OFFSET[0]), int(center.r + OFFSET[1]))

    def move(self, direction: str):
        neighbors = self.map.neighbor_hex(self.hex)
        idx = getattr(CONST_DIRECTION, direction, None)
        if idx is None or idx >= len(neighbors):
            return False
        self.hex = Hex(*neighbors[idx])
        self.position = self._hex_to_screen()
        return True

    def take_damage(self, amount: int) -> int:
        self.health -= amount
        return self.health

    def is_alive(self) -> bool:
        return self.health > 0

    def update(self, dt):
        pass

    def render(self, surface: pygame.Surface):
        vertices, _ = self.map.draw_hex(self.hex, self.hex)
        pygame.draw.polygon(surface, self.color, vertices)
        pygame.draw.polygon(surface, (255, 255, 255), vertices, 2)

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

class Item:
    def __init__(self, name: str, hex: Hex):
        self.name = name
        self.hex = hex

    def apply(self, target: Entity):
        raise NotImplementedError

    def render(self, surface: pygame.Surface, game_map: Map):
        vertices, color = game_map.draw_hex(self.hex)
        pygame.draw.polygon(surface, color, vertices)
        pygame.draw.polygon(surface, (255, 255, 255), vertices, 2)

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

    def move(self, direction: str):
        if self.stamina <= 0:
            return False
        for _ in range(self.speed):
            super().move(direction)
            self.stamina -= 1
            self.hunger += 0.5
        return True

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
        if item.hex.x == self.hex.x and item.hex.y == self.hex.y and item.hex.z == self.hex.z:
            return self.inventory.add(item)
        return False

    def drop_item(self, item: Item) -> bool:
        if self.inventory.remove(item):
            item.hex = self.hex
            return True
        return False

    def update(self, dt):
        self.hunger += 0.1 * dt
        if self.hunger > 100:
            self.take_damage(1 * dt)
        self.stamina = min(self.stamina + 0.5 * dt, 100)

    def render_status(self, surface: pygame.Surface):
        # Health bar
        pygame.draw.rect(surface, (255,0,0), (10,10, 200, 20))
        pygame.draw.rect(surface, (0,255,0), (10,10, 2 * max(self.health,0), 20))
        # Hunger bar
        pygame.draw.rect(surface, (139,69,19), (10,40, 200, 20))
        pygame.draw.rect(surface, (255,255,0), (10,40, 2 * min(self.hunger,100), 20))
        # Stamina bar
        pygame.draw.rect(surface, (169,169,169), (10,70, 200, 20))
        pygame.draw.rect(surface, (0,191,255), (10,70, 2 * self.stamina, 20))

class NPC(Survivor):
    def __init__(self, game_map: Map, ai_type: str ='wander', color=ENTITY_COLOR, health: int =100, speed: int =1):
        super().__init__(game_map, color, health, speed)
        self.ai_type = ai_type
        self.target = None

    def decide(self, player: Survivor) -> str:
        if self.ai_type == 'wander':
            return random.choice(list(CONST_DIRECTION._fields))
        elif self.ai_type == 'chase':
            # simple chase: find direction towards player
            dq = player.hex.x - self.hex.x
            dz = player.hex.z - self.hex.z
            if abs(dq) >= abs(dz):
                return 'SE' if dq>0 else 'NW'
            else:
                return 'SW' if dz>0 else 'NN'
        return None

    def update(self, dt, player: Survivor):
        super().update(dt)
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
