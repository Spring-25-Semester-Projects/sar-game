import pygame
import numpy as np
from src.hex import Hex
from config import OFFSET

class Debugger:
    def __init__(self, game, live=True):
        self.game = game
        self.live = live
        self.walk = []
        self.removeFog = self.game.removeFog
        self.toggleOverlay = False

    def get_entity_pos(self, direction):
        for entity in self.game.entities:
            cube = [entity.hexEntity.x,entity.hexEntity.y,entity.hexEntity.z]

            print(f"Entity {entity}:{cube}.\nNeighbors: {self.game.map.neighbor_hex(entity.hexEntity)}.\nEntity moved {direction}.")
    
    def get_entity_stats(self):
        for entity in self.game.entities:
            print(f"Entity stats. are: Health: {entity.stats[0]}, Stamina: {entity.stats[1]}, Hunger: {entity.stats[2]}.")

    def get_entity_feed(self, direction):
        self.get_entity_pos(direction)
        self.get_entity_stats()

    def get_event(self):
        if self.live:
            print(f"{self.game.events_info[-1] if self.game.events_info else None} occured.")

    def feed(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            cube = self.game.select_hex()
            self.walk = self.game.map.walkable_hex_distance(self.game.entities[0].hexEntity, Hex(cube.a,cube.b,cube.c))

            print(f"Hexagon at {{x: {cube.a}, y: {cube.b}, z: {cube.c}}} was clicked.")
            print("Hexagons to walk:")
            for h in self.walk:
                print(f"{h.x,h.y,h.z}.")

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RALT:
            self.toggleOverlay = not self.toggleOverlay

        elif event.type == pygame.MOUSEMOTION and self.toggleOverlay:
            mouse_position = np.array(event.pos)-OFFSET
            pcube = self.game.map.screen_to_hex(mouse_position)

            print(f"{{x: {pcube.a}, y: {pcube.b}, z: {pcube.c}.}}:{{x: {mouse_position[0]}, y: {mouse_position[1]}}}")  

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_f and self.toggleOverlay:
            self.removeFog = not self.removeFog

            print("Hexagons visited:")
            for h in self.game.visited:
                print(f"{h.x,h.y,h.z}.")

    def overlay(self):
        if not self.toggleOverlay:
            return
        
        for h in self.game.map.hexes.values():
            center = self.game.map.hex_to_screen(h)

            label = self.game.font.render(f"{h.x},{h.y},{h.z}", True, (255, 255, 255))
            text_rect = label.get_rect(center=(np.array([center.q,center.r])+OFFSET))

            self.game.screen.blit(label, text_rect)

        for entity in self.game.entities:
            for nb in self.game.map.neighbor_hex(entity.hexEntity):
                h = Hex(*nb)
                vertices = self.game.map.draw_hex(h)[0]
                color = (231, 76, 60)

                pygame.draw.polygon(self.game.screen, color, vertices)
                pygame.draw.polygon(self.game.screen, (200, 200, 200), vertices, 1)
        
        if self.walk:
            for h in self.walk:
                vertices = self.game.map.draw_hex(h)[0]
                color = (128, 0, 128)

                pygame.draw.polygon(self.game.screen, color, vertices)
                pygame.draw.polygon(self.game.screen, (200, 200, 200), vertices, 1)

        self.game.clock.tick(60)
