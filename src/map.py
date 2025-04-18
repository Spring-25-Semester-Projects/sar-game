import sys
import pygame
import math
import random

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Hex Grid')
        self.screen = pygame.display.set_mode((1080, 800))
        self.clock = pygame.time.Clock()

        self.hex_size = 30
        self.rows, self.cols = 100, 100

        self.hex_height = math.sqrt(3) * self.hex_size
        self.hex_width = 2 * self.hex_size

        self.terrain_colors = {
            'plain': (180, 220, 160),
            'forest': (34, 139, 34),
            'mountain': (128, 128, 128),
            'water': (70, 130, 180)
        }

        self.traversal_costs = {
            'plain': 1,
            'forest': 3,
            'mountain': 5,
            'water': float('inf')  #Means that they can never cross water
        }

        self.grid = self.generate_grid()

    def generate_grid(self):
        grid = []
        for col in range(self.cols):
            for row in range(self.rows):
                terrain = random.choices(
                    list(self.terrain_colors.keys()),
                    weights=[0.2, 0.6, 0.15, 0.05]
                )[0]
                cost = self.traversal_costs[terrain]
                grid.append((col, row, terrain, cost))
        return grid

    def get_hex_position(self, col, row):
        x = self.hex_size * 3/2 * col
        y = self.hex_height * (row + 0.5 * (col % 2))
        return int(x), int(y)

    def draw_hex(self, x, y, color):
        corners = []
        for i in range(6):
            angle = math.pi / 3 * i
            cx = x + self.hex_size * math.cos(angle)
            cy = y + self.hex_size * math.sin(angle)
            corners.append((cx, cy))
        pygame.draw.polygon(self.screen, color, corners)
        pygame.draw.polygon(self.screen, (0, 0, 0), corners, 2)

    def run(self):
        while True:
            self.screen.fill((255, 255, 255))

            for col, row, terrain, cost in self.grid:
                x, y = self.get_hex_position(col, row)
                color = self.terrain_colors[terrain]
                self.draw_hex(x, y, color)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            pygame.display.update()
            self.clock.tick(60)

game = Game()
game.run()
