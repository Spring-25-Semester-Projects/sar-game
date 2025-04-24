import pygame
import numpy as np
from collections import namedtuple
from map import Map, Hex
from config import OFFSET

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
        self.hexEntity = Hex()
        self.map = map
        self.position = self._calculate_position()
        self.target_position = None
        self.moving = False
        self.move_speed = 6
        
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

    def _calculate_position(self):
        center = self.map.hex_to_screen(self.hexEntity)
        return (center.q + OFFSET[0], center.r + OFFSET[1])

    def move(self, direction):
        if self.moving:
            return
            
        # Convert number key to direction
        dir_mapping = {
            1: "NW",
            2: "NN",
            3: "NE",
            4: "SW",
            5: "SS",
            6: "SE"
        }
        
        if direction in dir_mapping:
            move_dir = dir_mapping[direction]
            move_to_tiles = self.map.neighbor_hex(self.hexEntity)
            direction_index = getattr(CONST_direction, move_dir, None)
            
            if direction_index is not None:
                new_hex = Hex(*move_to_tiles[direction_index])
                self.hexEntity = new_hex
                self.target_position = self._calculate_position()
                self.moving = True
                self.frame = 0  # Reset animation
                self.stamina = max(0, self.stamina - 5)

    def update(self):
        # Handle movement animation
        if self.moving and self.target_position:
            dx = self.target_position[0] - self.position[0]
            dy = self.target_position[1] - self.position[1]
            distance = np.sqrt(dx**2 + dy**2)
            
            if distance < self.move_speed:
                self.position = self.target_position
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

    def heal(self, amount):
        self.health = min(100, self.health + amount)
        return self.health
    
    def rest(self):
        self.stamina = min(100, self.stamina + 20)
        return self.stamina