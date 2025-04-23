import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pygame
from map import Map, Hex
from config import WIDTH, HEIGHT, FPS

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SAR Game")

fav_icon = pygame.image.load("assets/imgs/fav.png")
pygame.display.set_icon(fav_icon)

class Game(Hex):
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.map = Map(30)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
    
    def draw(self):
        self.screen.fill((0, 0, 0))

        entityHex = Hex(0,0,0)

        for h in self.map.hexes.values():
                vertices,color = self.map.draw_hex(h, entityHex)

                pygame.draw.polygon(self.screen, color, vertices)
                pygame.draw.polygon(self.screen, (255, 255, 255), vertices, 1)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()