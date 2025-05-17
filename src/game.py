import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
 
from collections import deque, namedtuple
import pygame
import numpy as np
from src.map import Map
from src.entities.survivor import Survivor
from src.entities.rescuer import Rescuer
from config import WIDTH, HEIGHT, FPS, DEBUG, SIZE, OFFSET, COST_COLORS

if DEBUG:
    from utils.debugger import Debugger

screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("SAR Game")

CONST_game_icon_path = "assets/imgs/fav.png"
fav_icon = pygame.image.load(CONST_game_icon_path)
pygame.display.set_icon(fav_icon)

Entities = namedtuple('Entities', ['survivor','rescuer'])

CONST_rescuer_character_path = "assets/Males/M_01.png"
CONST_survivor_character_path = "assets/Females/F_01.png"

rescuer_img = pygame.image.load(CONST_rescuer_character_path).convert_alpha()
survivor_img = pygame.image.load(CONST_survivor_character_path).convert_alpha()

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
        self.removeRed = False
        self.events_info = []
        self.map = Map(radius)
        self.costs = self.map.map_cost()
        self.entities = Entities(Survivor(self.map), Rescuer(self.map))
        self.visited = deque([self.entities.rescuer.hexEntity])

        if DEBUG:
            self.debugger = Debugger(self, False)

    def __get_cursor(self):
        return np.array(pygame.mouse.get_pos())
    
    def select_hex(self):
        point = self.__get_cursor() - OFFSET

        return self.map.screen_to_hex(point)
    
    def discover_hex(self):
        h = self.entities.rescuer.hexEntity
        
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
                moved = self.entities.rescuer.move(dir)
                self.discover_hex()

                if moved == None:
                    dir = "nowhere"

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

        if any(neighbor == h for neighbor in  self.map.neighbor_hex(self.entities.rescuer.hexEntity)):
            if color == (0,0,0):
                color = (30,30,30)
                border_color = (30,30,30)

        return color, border_color
    
    def color_me_red(self, cost, color):
        if self.debugger.toggleOverlay and self.debugger.removeRed:
            return color
        elif self.debugger.toggleOverlay:
            return COST_COLORS[(cost if cost != float('-inf') else 6)]
        else:
            return color

    def draw_map(self):
        for h in self.map.hexes.values():
                border_color = (50,50,50)
                cost = self.costs[h]
                vertices, color = self.map.draw_hex(h)

                if self.debugger:
                    color = self.color_me_red(cost,color)

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