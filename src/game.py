import pygame
from . import Map
from config import WIDTH, HEIGHT, FPS

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SAR Game")

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.map = Map()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
    
    def draw(self):
        self.screen.fill((0, 0, 0))
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(60)

'''
# ! ONLY REMOVE COMMENT TO TEST

if __name__ == "__main__":
    game = Game()
    game.run()
'''