import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
 
from collections import deque
import pygame
import numpy as np
from map import Map, Hex
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
        self.removeFog = False
        self.events_info = []
        self.map = Map(radius)
        self.entities = [Survivor(self.map)]
        
        # ! This is just for testing.
        self.visited = deque([self.entities[0].hexEntity]) # ! Change it through out doc
        self.entity = self.entities[0]

        if DEBUG:
            self.debugger = Debugger(self, False)

    def __get_cursor(self):
        return np.array(pygame.mouse.get_pos())
    
    def select_hex(self):
        point = self.__get_cursor() - OFFSET

        cube = self.map.screen_to_hex(point)

        return cube
    
    def discover_hex(self):
        h = self.entities[0].hexEntity
        
        if h in self.visited:
            return None

        self.visited.append(h)    

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
                self.discover_hex()

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

    def fog(self, h, color, border_color):
        if self.debugger:
            if self.debugger.toggleOverlay and self.debugger.removeFog:
                return color, border_color

        if not (h in self.visited):
            border_color,color = (0,0,0),(0,0,0)

        if np.any(np.all(self.map.neighbor_hex(self.entities[0].hexEntity) == np.array([h.x,h.y,h.z]), axis=1)):
            if color == (0,0,0) and color != (50,50,50):
                color = (30,30,30)

        return color, border_color
            
    def draw_map(self):
        border_color = (200,200,200)

        for h in self.map.hexes.values():
                vertices, color = self.map.draw_hex(h)

                color, border_color = self.fog(h,color,border_color)

                pygame.draw.polygon(self.screen, color, vertices)
                pygame.draw.polygon(self.screen, border_color, vertices, 1)

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