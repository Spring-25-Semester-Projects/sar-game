import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
 
import pygame
import numpy as np
from map import Map
from entities.survivor import Survivor
from config import WIDTH, HEIGHT, FPS, DEBUG, SIZE, OFFSET

if DEBUG:
    from utils.debugger import Debugger

screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("SAR Game")

CONST_game_icon_path = "assets/imgs/fav.png"
fav_icon = pygame.image.load(CONST_game_icon_path)
pygame.display.set_icon(fav_icon)

class Game:
    def __init__(self, radius=SIZE):
        pygame.init()
        self.screen = screen
        self.size = radius
        self.screen.fill((0, 0, 0))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, int(self.size*(2/3)))
        self.running = True
        self.debugger = None
        self.events_info = []
        self.map = Map(radius)
        self.entities = [Survivor(self.map)]
        
        # ! This is just for testing.
        self.entity = self.entities[0]

        if DEBUG:
            self.debugger = Debugger(self, False)

    def __get_cursor(self):
        return np.array(pygame.mouse.get_pos())
    
    def select_hex(self):
        point = self.__get_cursor() - OFFSET

        cube = self.map.screen_to_hex(point)

        return cube

    def handle_single_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return None
        
        if event.type == pygame.KEYDOWN:
            mapping = {
                pygame.K_w: "NN",
                pygame.K_e: "NE",
                pygame.K_q: "NW",
                pygame.K_s: "SS",
                pygame.K_d: "SE",
                pygame.K_a: "SW",
            }
            
            dir = mapping.get(event.key)
            if dir:
                self.entity.move(dir)

                if self.debugger:
                    self.debugger.get_entity_feed(dir)
    
    def update_event_info(self):
        for event in pygame.event.get():

            if self.debugger:
                self.debugger.feed(event)

                self.debugger.get_event()

            eventName = pygame.event.event_name(event.type)
            eventInfo = [eventName, self.clock.get_time()]

            if eventName == "KeyDown":
                eventInfo.append(pygame.key.name(event.key))
            elif eventName == "MouseButtonDown":
                eventInfo.append(event.pos)

            self.events_info.append(eventInfo)
            self.handle_single_event(event)

    def handle_events(self):
        self.update_event_info()
            
    def draw_map(self):
        for h in self.map.hexes.values():
                vertices, color = self.map.draw_hex(h)

                pygame.draw.polygon(self.screen, color, vertices)
                pygame.draw.polygon(self.screen, (200, 200, 200), vertices, 1)

    def spawn(self):
        for entity in self.entities:
            pygame.draw.circle(self.screen, entity.color, entity.position, radius=int(self.size*(3/5)))

    def run(self):
        while self.running:
            self.handle_events()
            self.draw_map()
            self.spawn()

            if self.debugger:
                self.debugger.overlay()

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()