import sys
import os
import random
import pygame
from map import Map
from config import WIDTH, HEIGHT, FPS
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SAR Game")

from map import Map
from entities.rescuer import Rescuer
from entities.survivor import Survivor, Item, Weapon, Food
from config import WIDTH, HEIGHT, FPS, OFFSET, SURVIVOR_COLOR, ITEM_COLOR

class Game:
    def __init__(self, radius=10):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("SAR Game - Rescuer and Survivors")
        self.clock = pygame.time.Clock()
        self.running = True
        self.map = Map(radius)
        self.map.initialize_fog_of_war()
        self.rescuer = Rescuer(self.map)
        self.survivors = []
        self.map.fog_of_war[self.rescuer.hexEntity] = True
        self.items = []
        self.spawn_survivors(3)
        self.spawn_items(5)
        self.background = pygame.Surface((WIDTH, HEIGHT))
        self.background.fill((0, 0, 0))

    def spawn_survivors(self, count):
        for _ in range(count):
            hex_coords = random.choice(list(self.map.hexes.keys()))
            while hex_coords.x == 0 and hex_coords.y == 0 and hex_coords.z == 0:
                hex_coords = random.choice(list(self.map.hexes.keys()))

            survivor = Survivor(
                self.map, 
                SURVIVOR_COLOR, 
                health=100, 
                speed=1, 
                ai_type=random.choice(['wander', 'chase'])
            )
            survivor.hex = hex_coords
            survivor.position = survivor._hex_to_screen()
            self.survivors.append(survivor)

    def spawn_items(self, count):
        item_types = [
            ("Medkit", "weapon", 15),
            ("Knife", "weapon", 10),
            ("Food", "food", 20),
            ("Water", "food", 15)
        ]

        for _ in range(count):
            hex_coords = random.choice(list(self.map.hexes.keys()))
            item_type = random.choice(item_types)

            if item_type[1] == "weapon":
                item = Weapon(item_type[0], item_type[2], hex_coords)
            else:
                item = Food(item_type[0], item_type[2], hex_coords)

            self.items.append(item)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_6:
                    self.rescuer.move(event.key - pygame.K_1 + 1)
                elif event.key == pygame.K_e:
                    for item in self.items[:]:
                        if (item.hex.x == self.rescuer.hexEntity.x and 
                            item.hex.y == self.rescuer.hexEntity.y and 
                            item.hex.z == self.rescuer.hexEntity.z):
                            self.items.remove(item)
                elif event.key == pygame.K_d:
                    pass

    def draw(self):
        self.screen.fill((0, 0, 0))
        for hex_tile, is_visible in self.map.fog_of_war.items():
            if is_visible:
                vertices, color = self.map.draw_hex(hex_tile)
                pygame.draw.polygon(self.screen, color, vertices)
                pygame.draw.polygon(self.screen, (255, 255, 255), vertices, 1)
        self.rescuer.draw(self.screen)
        for survivor in self.survivors:
            if survivor.hex in self.map.fog_of_war and self.map.fog_of_war[survivor.hex]:
                survivor.draw(self.screen)
        for item in self.items:
            if item.hex in self.map.fog_of_war and self.map.fog_of_war[item.hex]:
                item.render(self.screen, self.map)

    def update(self):
        dt = self.clock.get_time() / 1000
        self.rescuer.update()
        self.map.update_visibility(self.rescuer.hexEntity)
        for survivor in self.survivors[:]:
            player_for_ai = type('', (), {'hex': self.rescuer.hexEntity})()
            survivor.update(dt, player_for_ai)
            if not survivor.is_alive():
                self.survivors.remove(survivor)
        for survivor in self.survivors:
            for item in self.items[:]:
                if (item.hex.x == survivor.hex.x and 
                    item.hex.y == survivor.hex.y and 
                    item.hex.z == survivor.hex.z):
                    if survivor.pick_item(item):
                        self.items.remove(item)

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
