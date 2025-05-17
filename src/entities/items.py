import pygame
from map import Hex

# for survivor initial purpose, delete if not needed
class Item:
    def __init__(self, name: str, hex: Hex):
        self.name = name
        self.hex = hex

    def apply(self, target):
        raise NotImplementedError

    def render(self, surface: pygame.Surface, game_map):
        vertices, color = game_map.draw_hex(self.hex)
        pygame.draw.polygon(surface, color, vertices)
        pygame.draw.polygon(surface, (255, 255, 255), vertices, 2)

class Weapon(Item):
    def __init__(self, name: str, damage: int, hex: Hex):
        super().__init__(name, hex)
        self.damage = damage

    def apply(self, target):
        target.take_damage(self.damage)

class Food(Item):
    def __init__(self, name: str, nutrition: int, hex: Hex):
        super().__init__(name, hex)
        self.nutrition = nutrition

    def apply(self, target):
        target.eat(self.nutrition)

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