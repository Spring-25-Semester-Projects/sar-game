import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pygame
from map import Map
from entities.mock_entity import Entity
from config import WIDTH, HEIGHT, FPS

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SAR Game")

fav_icon = pygame.image.load("assets/imgs/fav.png")
pygame.display.set_icon(fav_icon)

class Game:
    def __init__(self, radius=30):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.map = Map(radius)
        self.screen.fill((0, 0, 0))

        # ! Later on, Suvivor or Rescuer stricly, defined outside.
        self.entity = Entity(self.map)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    self.entity.move("NN")
                elif event.key == pygame.K_e:
                    self.entity.move("NE")
                elif event.key == pygame.K_q:
                    self.entity.move("NW")
                elif event.key == pygame.K_s:
                    self.entity.move("SS")
                elif event.key == pygame.K_d:
                    self.entity.move("SE")
                elif event.key == pygame.K_a:
                    self.entity.move("SW")
    
    def draw_map(self, entity: Entity):
        for h in self.map.hexes.values():
                vertices,color = self.map.draw_hex(h, entity.hexEntity)

                pygame.draw.polygon(self.screen, color, vertices)
                pygame.draw.polygon(self.screen, (255, 255, 255), vertices, 1)

    def spawn(self, entity: Entity):
        pygame.draw.circle(self.screen, entity.color, entity.position, radius=20)

    def run(self):
        while self.running:
            self.handle_events()
            self.draw_map(self.entity)
            self.spawn(self.entity)

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()