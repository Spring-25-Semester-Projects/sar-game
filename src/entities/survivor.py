import random
import pygame
import sys
import os
from collections import namedtuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import *
from map import *

Directions = namedtuple('Direction', ['SS', 'SE', 'SW', 'NN', 'NE', 'NW'])
CONST_DIRECTION = Directions(SS=0, SE=1, SW=2, NN=3, NE=4, NW=5)

class Entity:
    def __init__(self, game_map: Map, color=ENTITY_COLOR, health=100):
        self.hex = Hex()
        self.map = game_map
        self.color = color
        self.health = health
        self.position = self._hex_to_screen()

    def _hex_to_screen(self, hex_coords=None):
        """Convert hex coordinates to screen position"""
        if hex_coords is None:
            hex_coords = self.hex
        center = self.map.hex_to_screen(hex_coords)
        return (int(center.q + OFFSET[0]), int(center.r + OFFSET[1]))

    def update(self, dt, player=None):  # Added player parameter with default None
        pass

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
        
        
class SpriteSheet:
    def __init__(self, image):
        self.sheet = image
        
    def get_img(self, frame, width, height, scale, color):
        image = pygame.Surface((width, height)).convert_alpha()
        image.blit(self.sheet, (0, 0), (0, (frame * height), width, height)) 
        image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))  
        image.set_colorkey(color)
        return image
class Survivor(Entity):
    def __init__(self, game_map: Map, color=SURVIVOR_COLOR, health: int = 100, speed: int = 1, ai_type: str = None):
        super().__init__(game_map, color, health)
        # Movement properties
        self.speed = speed * 2
        self.move_speed = 6  # Movement speed for animation
        self.target_hex = None  # New target hex for movement
        
        # Sprite properties
        sprite_img = pygame.image.load("assets/Males/M_05.png").convert_alpha()
        self.sprite_sheet = SpriteSheet(sprite_img)
        self.animation_list = []
        self.animation_steps = 3
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.animation_cooldown = 200
        self.moving = False
        self.target_position = None
        
        # Initialize animation frames
        for x in range(self.animation_steps):
            self.animation_list.append(self.sprite_sheet.get_img(x, 17, 17, 2.75, (0, 0, 0)))
        
        # Existing stats and inventory
        self.inventory = Inventory()
        self.stamina = 100.0
        self.hunger = 0.0
        self.ai_type = ai_type
        self.target = None

    def move(self, direction: str):
        if self.stamina <= 0 or self.moving:  # Prevent movement while already moving
            return False
            
        neighbors = self.map.neighbor_hex(self.hex)
        idx = getattr(CONST_DIRECTION, direction, None)
        
        if idx is not None and idx < len(neighbors):
            self.target_hex = Hex(*neighbors[idx])
            self.target_position = self._hex_to_screen(self.target_hex)  # Now works with the modified _hex_to_screen
            self.moving = True
            self.frame = 0  # Reset animation
            self.stamina -= 1
            self.hunger += 0.5
            return True
        return False

    def update(self, dt, player=None):
        # Handle movement animation
        if self.moving and self.target_position:
            dx = self.target_position[0] - self.position[0]
            dy = self.target_position[1] - self.position[1]
            distance = np.sqrt(dx**2 + dy**2)
            
            if distance < self.move_speed:  # Close enough to target
                self.position = self.target_position
                self.hex = self.target_hex  # Update actual hex position
                self.target_hex = None
                self.moving = False
                self.frame = 0
            else:
                # Move toward target
                self.position = (
                    self.position[0] + (dx/distance) * self.move_speed,
                    self.position[1] + (dy/distance) * self.move_speed
                )
                
                # Update animation frame
                current_time = pygame.time.get_ticks()
                if current_time - self.last_update >= self.animation_cooldown:
                    self.last_update = current_time
                    self.frame = (self.frame + 1) % len(self.animation_list)

        # Original stat updates
        self.hunger += 0.1 * dt
        if self.hunger > 100:
            self.take_damage(1 * dt)
        self.stamina = min(self.stamina + 0.5 * dt, 100)
        
        # AI movement decision
        if self.ai_type and player and not self.moving:  # Only decide when not moving
            direction = self.decide(player)
            if direction:
                self.move(direction)

    def draw(self, surface):
        """Draw sprite with current animation frame"""
        if self.moving:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_update >= self.animation_cooldown:
                self.last_update = current_time
                self.frame = (self.frame + 1) % len(self.animation_list)
        else:
            self.frame = 0  # Reset to first frame when not moving
        
        survivor_img = self.animation_list[self.frame]
        sprite_rect = survivor_img.get_rect(center=self.position)
        surface.blit(survivor_img, sprite_rect)

    # Keep all original methods unchanged
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

    def decide(self, player: 'Survivor') -> str:
        if self.ai_type == 'wander':
            return random.choice(list(CONST_DIRECTION._fields))
        elif self.ai_type == 'chase':
            dq = player.hex.x - self.hex.x
            dz = player.hex.z - self.hex.z
            if abs(dq) >= abs(dz):
                return 'SE' if dq > 0 else 'NW'
            else:
                return 'SW' if dz > 0 else 'NN'
        return None

    def render_status(self, surface: pygame.Surface):
        pygame.draw.rect(surface, (255, 0, 0), (10, 10, 200, 20))
        pygame.draw.rect(surface, (0, 255, 0), (10, 10, 2 * max(self.health, 0), 20))
        pygame.draw.rect(surface, (139, 69, 19), (10, 40, 200, 20))
        pygame.draw.rect(surface, (255, 255, 0), (10, 40, 2 * min(self.hunger, 100), 20))
        pygame.draw.rect(surface, (169, 169, 169), (10, 70, 200, 20))
        pygame.draw.rect(surface, (0, 191, 255), (10, 70, 2 * self.stamina, 20))