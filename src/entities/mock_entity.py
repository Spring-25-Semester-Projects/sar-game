from collections import namedtuple
import pygame
import numpy as np
from src.map import Map, Hex
from config import ENTITY_COLOR, OFFSET

Directions = namedtuple('Direction', ['SS', 'SE', 'SW', 'NN', 'NE', 'NW'])
CONST_direction = Directions(SS=0, SE=1, SW=2, NN=3, NE=4, NW=5)

class SpriteSheet:
    def __init__(self, image):
        self.sheet = image
        
    def get_img(self, frame, width, height, scale, color):
        """Extract an image from a sprite sheet
        
        Args:
            frame: The frame number to extract
            width: Width of each frame
            height: Height of each frame
            scale: Scale factor to apply
            color: Color key to make transparent
            
        Returns:
            The extracted and scaled image
        """
        image = pygame.Surface((width, height)).convert_alpha()
        # Use vertical position (frame * height) instead of horizontal position
        image.blit(self.sheet, (0, 0), (0, (frame * height), width, height)) 
        image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))  
        image.set_colorkey(color)
        return image

class Entity:
    def __init__(self, map: Map, sprite_path=None, color=ENTITY_COLOR):
        self.map = map
        self.hexEntity = self.map.hexes[Hex()]
        self.color = color
        self.points = 100
        self.position = self.entity_position()
        
        # Sprite properties
        if sprite_path:
            self.init_sprite_animation(sprite_path)
        else:
            # Create default animation list with a placeholder
            self.animation_list = [pygame.Surface((17 * 2.75, 17 * 2.75))]
            self.animation_list[0].fill(self.color)
            self.frame = 0
            self.last_update = pygame.time.get_ticks()
            self.animation_cooldown = 200
        
    def init_sprite_animation(self, sprite_path):
        """Initialize sprite animation properties"""
        try:
            sprite_img = pygame.image.load(sprite_path).convert_alpha()
            self.sprite_sheet = SpriteSheet(sprite_img)
            self.animation_list = []
            self.animation_steps = 3  # Using only 3 front-facing frames
            self.frame = 0
            self.last_update = pygame.time.get_ticks()
            self.animation_cooldown = 200
            
            # Initialize animation frames - use the front-facing frames only
            for x in range(self.animation_steps):
                self.animation_list.append(self.sprite_sheet.get_img(x, 17, 17, 2.75, (0, 0, 0)))
        except Exception as e:
            print(f"Error loading sprite from {sprite_path}: {e}")
            # Create placeholder animation list with a colored rectangle
            self.animation_list = [pygame.Surface((17 * 2.75, 17 * 2.75))]
            self.animation_list[0].fill(self.color)
            self.frame = 0
            self.animation_steps = 1
        
    def entity_position(self):
        center = self.map.hex_to_screen(self.hexEntity)
        position = np.array([*center])+OFFSET
        return position
        
    def move(self, move_dir):
        if self.points <= 0:
            return None

        move_to_tiles = self.map.neighbor_hex(self.hexEntity)

        dir_attr = getattr(CONST_direction, move_dir, None)
        
        if dir_attr is None or move_to_tiles[dir_attr] is None:
            return None

        self.hexEntity = move_to_tiles[dir_attr]
        self.position = self.entity_position()
        
        # Update animation frame when moving
        self.update_animation(force=True)

        return list(move_to_tiles[dir_attr])
    
    def hurt(self, vl):
        self.points -= vl
        return self.points
        
    def update_animation(self, force=False):
        """Updates animation frame based on cooldown timer"""
        if not hasattr(self, 'animation_steps') or self.animation_steps <= 1:
            return
            
        current_time = pygame.time.get_ticks()
        if force or current_time - self.last_update >= self.animation_cooldown:
            self.frame = (self.frame + 1) % self.animation_steps
            self.last_update = current_time
