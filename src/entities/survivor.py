import random
import pygame
import numpy as np
from collections import namedtuple
from utils.sprites import SpriteSheet
from config import *
from map import *
from entities.mock_entity import Entity
from entities.items import Inventory, Item, Weapon
Directions = namedtuple('Direction', ['SS', 'SE', 'SW', 'NN', 'NE', 'NW'])
CONST_DIRECTION = Directions(SS=0, SE=1, SW=2, NN=3, NE=4, NW=5)
import pygame



class SpriteSheet:
    """Utility class for handling sprite sheets"""
    def __init__(self, image):
        self.sheet = image
        
    def get_img(self, frame, width, height, scale, color):
        """Extract a single image from a sprite sheet"""
        image = pygame.Surface((width, height)).convert_alpha()
        image.blit(self.sheet, (0, 0), (0, (frame * height), width, height))
        image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        image.set_colorkey(color)
        return image

def load_sprite_sheet(path, frame_count, frame_size, scale=1, colorkey=(0, 0, 0)):
    """Helper function to load and prepare a sprite sheet"""
    sheet_img = pygame.image.load(path).convert_alpha()
    sheet = SpriteSheet(sheet_img)
    return [sheet.get_img(i, *frame_size, scale, colorkey) for i in range(frame_count)] 


    
    

class Survivor(Entity):
    def __init__(self, game_map: Map, color=SURVIVOR_COLOR, health: int = 100, speed: int = 1, ai_type: str = None):
        super().__init__(game_map, color, health)
        # Movement properties
        self.speed = speed * 2
        self.target_hex = None
        self.irrational_chance = 0.3
        

        # Sprite properties
        sprite_img = pygame.image.load("assets/Males/M_06.png").convert_alpha()
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
        
        # Stats and inventory
        self.inventory = Inventory()
        self.stamina = 100.0
        self.hunger = 0.0
        self.ai_type = ai_type
        self.target = None
        self.alive = True

    def move(self, direction: str):
        if self.stamina <= 0 or self.moving:
            return False
            
        neighbors = self.map.neighbor_hex(self.hexEntity)
        idx = getattr(CONST_DIRECTION, direction, None)
        
        if idx is not None and idx < len(neighbors):
            target_hex_coords = neighbors[idx]
            target_hex = next((h for h in self.map.hexes.keys() 
                            if (h.x, h.y, h.z) == (target_hex_coords[0], target_hex_coords[1], target_hex_coords[2])), None)
                
            # Strict water and impassable terrain check
            if target_hex and target_hex.terrain_type != 'water':
                # Set movement duration based on terrain type
                terrain_speeds = {
                    'plain': 1.0,
                    'forest': 3.0,
                    'mountain': 5.0
                }
                move_duration = terrain_speeds.get(target_hex.terrain_type, 1.0)
                
                # Calculate stamina cost (higher for difficult terrain)
                stamina_costs = {
                    'plain': 5,
                    'forest': 15,
                    'mountain': 25
                }
                stamina_cost = stamina_costs.get(target_hex.terrain_type, 5)
                
                if self.stamina >= stamina_cost or random.random() < self.irrational_chance:
                    self.target_hex = target_hex
                    self.target_position = self._hex_to_screen(target_hex)
                    self.moving = True
                    self.frame = 0
                    self.move_start_time = pygame.time.get_ticks()
                    self.move_duration = move_duration * 1000  # Convert to milliseconds
                    self.stamina = max(0, self.stamina - stamina_cost)
                    self.hunger += stamina_cost * 0.05
                    return True
        return False

    def update(self, dt, player=None):
        # Handle movement animation
        if self.moving and self.target_hex:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.move_start_time
            progress = min(1.0, elapsed / self.move_duration)
            
            # Interpolate position based on progress
            dx = self.target_position[0] - self.position[0]
            dy = self.target_position[1] - self.position[1]
            self.position = (
                self.position[0] + dx * progress,
                self.position[1] + dy * progress
            )
            
            # Update animation frame
            if current_time - self.last_update >= self.animation_cooldown:
                self.last_update = current_time
                self.frame = (self.frame + 1) % len(self.animation_list)
            
            # Check if movement complete
            if progress >= 1.0:
                self.position = self.target_position
                self.hexEntity = self.target_hex
                self.moving = False
                self.frame = 0
        
        # Stamina regeneration when not moving
        if not self.moving:
            self.stamina = min(100, self.stamina + 80 * dt)
        
        # Hunger system
        self.hunger += 0.05 * dt
        
        # Starvation damage
        if self.hunger >= 100:
            self.take_damage(0.5 * dt)
            
        # Check for death
        if self.health <= 0:
            self.handle_death()
            return
        
        # AI movement decision
        if self.ai_type and player and not self.moving:
            if random.random() < self.irrational_chance:
                direction = self.random_move()
            else:
                direction = self.rational_move(player)
            
            if direction:
                self.move(direction)
              
         

    def random_move(self):
        """Completely random movement without considering terrain or strategy"""
        possible_directions = []
        for direction in CONST_DIRECTION._fields:
            neighbors = self.map.neighbor_hex(self.hexEntity)
            idx = getattr(CONST_DIRECTION, direction)
            if idx < len(neighbors):
                target_hex_coords = neighbors[idx]
                target_hex = next((h for h in self.map.hexes.keys() 
                                if (h.x, h.y, h.z) == (target_hex_coords[0], target_hex_coords[1], target_hex_coords[2])), None)
                
                if target_hex and target_hex.terrain_type != 'water':
                    possible_directions.append(direction)
        
        return random.choice(possible_directions) if possible_directions else None

    def rational_move(self, player):
        """Movement that considers terrain costs and strategy"""
        if self.ai_type == 'wander':
            possible_directions = []
            for direction in CONST_DIRECTION._fields:
                neighbors = self.map.neighbor_hex(self.hexEntity)
                idx = getattr(CONST_DIRECTION, direction)
                if idx < len(neighbors):
                    target_hex_coords = neighbors[idx]
                    target_hex = next((h for h in self.map.hexes.keys() 
                                     if (h.x, h.y, h.z) == (target_hex_coords[0], target_hex_coords[1], target_hex_coords[2])), None)
                    if target_hex and target_hex.terrain_type != 'water':
                        # Prefer easier terrain when wandering
                        terrain_weights = {
                            'plain': 3,
                            'forest': 2,
                            'mountain': 1
                        }
                        weight = terrain_weights.get(target_hex.terrain_type, 1)
                        possible_directions.append((direction, weight))
            
            if possible_directions:
                # Weighted random choice based on terrain preference
                directions, weights = zip(*possible_directions)
                chosen = random.choices(directions, weights=weights, k=1)[0]
                return chosen
            return None
            
        elif self.ai_type == 'chase':
            dq = player.hex.x - self.hexEntity.x
            dz = player.hex.z - self.hexEntity.z
            
            preferred_directions = []
            if abs(dq) >= abs(dz):
                preferred_directions.append('SE' if dq > 0 else 'NW')
                preferred_directions.append('NE' if dq > 0 else 'SW')
            else:
                preferred_directions.append('SW' if dz > 0 else 'NN')
                preferred_directions.append('SE' if dz > 0 else 'NW')
            
            # Check if preferred directions are passable and not water
            for direction in preferred_directions:
                neighbors = self.map.neighbor_hex(self.hexEntity)
                idx = getattr(CONST_DIRECTION, direction)
                if idx < len(neighbors):
                    target_hex_coords = neighbors[idx]
                    target_hex = next((h for h in self.map.hexes.keys() 
                                     if (h.x, h.y, h.z) == (target_hex_coords[0], target_hex_coords[1], target_hex_coords[2])), None)
                    if target_hex and target_hex.terrain_type != 'water':
                        return direction
            
            # Fallback to any passable direction
            possible_directions = []
            for direction in CONST_DIRECTION._fields:
                neighbors = self.map.neighbor_hex(self.hexEntity)
                idx = getattr(CONST_DIRECTION, direction)
                if idx < len(neighbors):
                    target_hex_coords = neighbors[idx]
                    target_hex = next((h for h in self.map.hexes.keys() 
                                     if (h.x, h.y, h.z) == (target_hex_coords[0], target_hex_coords[1], target_hex_coords[2])), None)
                    if target_hex and target_hex.terrain_type != 'water':
                        possible_directions.append(direction)
            
            return random.choice(possible_directions) if possible_directions else None

    def draw(self, screen):
        """Draw sprite with current animation frame"""
        if self.moving:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_update >= self.animation_cooldown:
                self.last_update = current_time
                self.frame = (self.frame + 1) % len(self.animation_list)
        else:
            self.frame = 0
        
        survivor_img = self.animation_list[self.frame]
        sprite_rect = survivor_img.get_rect(center=self.position)
        screen.blit(survivor_img, sprite_rect)

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
        if (item.hex.x == self.hexEntity.x and 
            item.hex.y == self.hexEntity.y and 
            item.hex.z == self.hexEntity.z):
            return self.inventory.add(item)
        return False

    def drop_item(self, item: Item) -> bool:
        if self.inventory.remove(item):
            item.hex = Hex(self.hexEntity.x, self.hexEntity.y, self.hexEntity.z)
            return True
        return False

    def render_status(self, surface: pygame.Surface):
        pygame.draw.rect(surface, (255, 0, 0), (10, 10, 200, 20))
        pygame.draw.rect(surface, (0, 255, 0), (10, 10, 2 * max(self.health, 0), 20))
        pygame.draw.rect(surface, (139, 69, 19), (10, 40, 200, 20))
        pygame.draw.rect(surface, (255, 255, 0), (10, 40, 2 * min(self.hunger, 100), 20))
        pygame.draw.rect(surface, (169, 169, 169), (10, 70, 200, 20))
        pygame.draw.rect(surface, (0, 191, 255), (10, 70, 2 * self.stamina, 20))
        
    def is_alive(self):
        return self.health > 0
        
    def handle_death(self):
        """Handle death of the survivor"""
        self.alive = False
    