import pygame
from config import OFFSET

class Debugger():
    def __init__(self, game, live=True):
        self.game = game
        self.live = live
        self.toggleOverlay = False

    def get_entity_pos(self):
        for entity in self.game.entities:
            cube = [entity.hexEntity.x,entity.hexEntity.y,entity.hexEntity.z]
            print(f"Entity {entity}:{cube}.")
    
    def get_entity_stats(self):
        for entity in self.game.entities:
            print(f"Entity stats. are {entity.stats}.")

    def get_entity_feed(self):
        self.get_entity_pos()
        self.get_entity_stats()

    def get_event(self):
        if self.live:
            print(f"{self.game.events_info[-1] if self.game.events_info else None} occured.")

    def feed(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            cube = self.game.select_hex()
            print(f"Hexagon at {cube} was clicked.")
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RALT:
            self.toggleOverlay = not self.toggleOverlay
    
    def overlay(self):
        if not self.toggleOverlay:
            return
        
        for h in self.game.map.hexes.values():
            center = self.game.map.hex_to_screen(h)

            label = self.game.font.render(f"{h.x},{h.y},{h.z}", True, (255, 255, 255))
            text_rect = label.get_rect(center=[center.q + OFFSET[0],center.r + OFFSET[1]])

            self.game.screen.blit(label, text_rect)

        self.game.clock.tick(5)
