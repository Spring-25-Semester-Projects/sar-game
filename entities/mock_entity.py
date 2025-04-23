from .. import Game, pygame
from config import ENTITY_COLOR

class Entity(pygame.sprite.Sprite, Game):
    def __init__(self, position, radius, color=ENTITY_COLOR, width=0):
        pygame.sprite.Sprite.__init__(self)
        screen = Game().screen
        self.rect = pygame.draw.circle(screen, position, color, radius, width)
        self.area = screen.get_rect()
