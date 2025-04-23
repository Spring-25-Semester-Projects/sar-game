from .. import Game, pygame
from config import ENTITY_COLOR

class Entity(pygame.sprite.Sprite):
    def __init__(self, game, position, radius, color=ENTITY_COLOR, width=0):
        super().__init__(self)
        self.game = game
        self.rect = pygame.draw.circle(self.game.screen, position, color, radius, width)
        self.area = self.screen.get_rect()
