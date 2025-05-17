import pygame
import numpy as np
from collections import namedtuple
from map import Map, Hex
from config import OFFSET
import random

class SpriteSheet:
    def __init__(self, image):
        self.sheet = image
        
    def get_img(self, frame, width, height, scale, color):
        image = pygame.Surface((width, height)).convert_alpha()
        image.blit(self.sheet, (0, 0), (0, (frame * height), width, height)) 
        image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))  
        image.set_colorkey(color)
        return image

Directions = namedtuple('Direction', ['SS', 'SE', 'SW', 'NN', 'NE', 'NW'])
CONST_direction = Directions(SS=0, SE=1, SW=2, NN=3, NE=4, NW=5)

class Rescuer:
    def __init__(self, map: Map):
        # Movement properties
        self.hexEntity = self._get_valid_start_hex(map)  # Ensures spawn on valid terrain
        self.map = map
        self.position = self._calculate_position()
        self.target_position = None
        self.target_hex = None
        self.moving = False
        self.base_move_speed = 1.0  # Base speed (1 second for plains)
        
        # Sprite properties
        sprite_img = pygame.image.load("assets/Males/M_01.png").convert_alpha()
        self.sprite_sheet = SpriteSheet(sprite_img)
        self.animation_list = []
        self.animation_steps = 3
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.animation_cooldown = 200
        
        # Initialize animation frames
        for x in range(self.animation_steps):
            self.animation_list.append(self.sprite_sheet.get_img(x, 17, 17, 2.75, (0, 0, 0)))
        
        # Stats
        self.health = 100
        self.stamina = 100

    def _get_valid_start_hex(self, map: Map):
        """Find a valid starting hex that's not water"""
        valid_hexes = [h for h in map.hexes.keys() if h.terrain_type != 'water']
        return random.choice(valid_hexes) if valid_hexes else Hex()

    def _calculate_position(self, hex_entity=None):
        hex_entity = hex_entity or self.hexEntity
        center = self.map.hex_to_screen(hex_entity)
        return (center.q + OFFSET[0], center.r + OFFSET[1])

    def move(self, direction):
        if self.moving:
            return False
            
        # Convert number key to direction
        dir_mapping = {
            1: "NE",
            2: "NN",
            3: "NW",
            4: "SE",
            5: "SS",
            6: "SW"
        }
        
        if direction in dir_mapping:
            move_dir = dir_mapping[direction]
            neighbors = self.map.neighbor_hex(self.hexEntity)
            direction_index = getattr(CONST_direction, move_dir, None)
            
            if direction_index is not None and direction_index < len(neighbors):
                target_hex_coords = neighbors[direction_index]
                # Find the actual Hex object in the map
                target_hex = next((h for h in self.map.hexes.keys() 
                                if (h.x, h.y, h.z) == (target_hex_coords[0], target_hex_coords[1], target_hex_coords[2])), None)
                
                # Check if target is valid (not water)
                if target_hex and target_hex.terrain_type != 'water':
                    # Set movement duration based on terrain type
                    terrain_speeds = {
                        'plain': 1.0,
                        'forest': 3.0,
                        'mountain': 6.0
                    }
                    move_duration = terrain_speeds.get(target_hex.terrain_type, 1.0)
                    
                    # Calculate stamina cost (higher for difficult terrain)
                    stamina_costs = {
                        'plain': 5,
                        'forest': 15,
                        'mountain': 25
                    }
                    stamina_cost = stamina_costs.get(target_hex.terrain_type, 5)
                    
                    if self.stamina >= stamina_cost:
                        self.target_hex = target_hex
                        self.target_position = self._calculate_position(target_hex)
                        self.moving = True
                        self.frame = 0
                        self.move_start_time = pygame.time.get_ticks()
                        self.move_duration = move_duration * 1000  # Convert to milliseconds
                        self.stamina = max(0, self.stamina - stamina_cost)
                        return True
        return False

    def update(self):
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
        
        # Regenerate stamina when not moving
        if not self.moving:
            self.stamina = min(100, self.stamina + 0.2)

    def draw(self, screen):
        if self.moving:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_update >= self.animation_cooldown:
                self.last_update = current_time
                self.frame = (self.frame + 1) % len(self.animation_list)
        else:
            self.frame = 0
        
        player_img = self.animation_list[self.frame]
        sprite_rect = player_img.get_rect(center=self.position)
        screen.blit(player_img, sprite_rect)

# delete these 2 if not needed 

    def heal(self, amount):
        self.health = min(100, self.health + amount)
        return self.health
    
    def rest(self):
        self.stamina = min(100, self.stamina + 20)
        return self.stamina