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
        image = pygame.Surface((width, height)).convert_alpha()
        image.blit(self.sheet, (0, 0), (0, (frame * height), width, height)) 
        image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))  
        image.set_colorkey(color)
        return image

class Entity:
    def __init__(self, map: Map, sprite_path=None, color=ENTITY_COLOR):
        self.map = map
        self.hexEntity = self.map.hexes[Hex()]
        self.color = color
        self.points = float('inf')
        self.position = self.entity_position()
        
        if sprite_path:
            self.init_sprite_animation(sprite_path)
        else:
            self.animation_list = [pygame.Surface((17 * 2.75, 17 * 2.75))]
            self.animation_list[0].fill(self.color)
            self.frame = 0
            self.last_update = pygame.time.get_ticks()
            self.animation_cooldown = 200
        
    def init_sprite_animation(self, sprite_path):
        try:
            sprite_img = pygame.image.load(sprite_path).convert_alpha()
            self.sprite_sheet = SpriteSheet(sprite_img)
            self.animation_list = []
            self.animation_steps = 3 
            self.frame = 0
            self.last_update = pygame.time.get_ticks()
            self.animation_cooldown = 200
            
            for x in range(self.animation_steps):
                self.animation_list.append(self.sprite_sheet.get_img(x, 17, 17, 2.75, (0, 0, 0)))
        except Exception as e:
            print(f"Error loading sprite from {sprite_path}: {e}")
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
        
        self.update_animation(force=True)

        return list(move_to_tiles[dir_attr])

    def update_animation(self, force=False):
        if not hasattr(self, 'animation_steps') or self.animation_steps <= 1:
            return
            
        current_time = pygame.time.get_ticks()
        if force or current_time - self.last_update >= self.animation_cooldown:
            self.frame = (self.frame + 1) % self.animation_steps
            self.last_update = current_time