import pygame
import numpy as np
from map import Map, Hex
from config import WIDTH, HEIGHT, OFFSET

class FogOfWar:
    def __init__(self, map: Map, vision_radius=3):
        self.map = map
        self.vision_radius = vision_radius
        self.active = True
        self.fog_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.explored_hexes = set()
        
    def toggle(self):
        self.active = not self.active
        
    def update(self, rescuer_hex):
        """Update which hexes are visible based on rescuer's position"""
        if not self.active:
            return
            
        self.explored_hexes.add((rescuer_hex.x, rescuer_hex.y, rescuer_hex.z))
        
        # Get all hexes within vision radius
        visible_hexes = set()
        for dx in range(-self.vision_radius, self.vision_radius + 1):
            for dy in range(max(-self.vision_radius, -dx - self.vision_radius), 
                          min(self.vision_radius, -dx + self.vision_radius) + 1):
                dz = -dx - dy
                visible_hexes.add((rescuer_hex.x + dx, rescuer_hex.y + dy, rescuer_hex.z + dz))
        
        # Mark these hexes as explored
        for hex_coords in visible_hexes:
            self.explored_hexes.add(hex_coords)
    
    def apply_fog(self, screen, entities, items):
        """Apply fog of war to the screen"""
        if not self.active:
            return
            
        # Clear fog surface
        self.fog_surface.fill((0, 0, 0, 0))
        
        # Draw fog everywhere except explored hexes
        for hex_coord in self.map.hexes:
            hex_key = (hex_coord.x, hex_coord.y, hex_coord.z)
            if hex_key not in self.explored_hexes:
                vertices, _ = self.map.draw_hex(hex_coord, None)
                pygame.draw.polygon(self.fog_surface, (0, 0, 0, 180), vertices)
        
        # Draw entities and items only if they're in explored hexes
        for entity in entities:
            hex_key = (entity.hex.x, entity.hex.y, entity.hex.z)
            if hex_key in self.explored_hexes:
                entity.draw(screen)
                
        for item in items:
            hex_key = (item.hex.x, item.hex.y, item.hex.z)
            if hex_key in self.explored_hexes:
                item.render(screen, self.map)
        
        # Apply the fog overlay
        screen.blit(self.fog_surface, (0, 0))