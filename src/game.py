import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
 
from collections import deque, namedtuple
import pygame
import numpy as np
import time
from src.map import Map
from src.entities.survivor import Survivor
from src.entities.rescuer import Rescuer
from crypto_system import MessageManager
from config import WIDTH, HEIGHT, FPS, DEBUG, SIZE, OFFSET, COST_COLORS

if DEBUG:
    from utilss.debugger import Debugger

screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("SAR Game")

CONST_game_icon_path = "/home/mostafabakr/Pictures/sar-game-8-field-of-view/assets/imgs/fav.png"
fav_icon = pygame.image.load(CONST_game_icon_path)
pygame.display.set_icon(fav_icon)

Entities = namedtuple('Entities', ['survivor','rescuer'])

class Game:
    def __init__(self, radius=SIZE):
        pygame.init()
        self.screen = screen
        self.size = radius
        self.screen.fill((0, 0, 0))
        self.clock = pygame.time.Clock()
        
        self.create_fonts()
        
        self.running = True
        self.debugger = None
        self.removeFog = False
        self.removeRed = False
        self.events_info = []
        self.map = Map(radius)
        self.costs = self.map.map_cost()
        self.entities = Entities(Survivor(self.map), Rescuer(self.map))
        self.visited = deque([self.entities.rescuer.hexEntity])

        self.survivor_visibility_counter = 0
        self.last_ping_position = None
        self.ping_sent = False
        
        self.message_manager = MessageManager(self.map)
        
        self.entities.rescuer.costs = self.costs
        self.entities.survivor.costs = self.costs
        
        self.rescuer_moved = False
        self.ai_mode = False
        self.game_over = False
        self.game_won = False
        self.steps_taken = 0
        
        self.survivor_spotted = False
        self.last_known_survivor_position = None
        self.turns_since_spotted = 0
        
        self.current_path = []
        
        self.search_start_time = None
        self.ai_active_time = 0
        self.total_search_time = 0
        self.total_games = 0
        self.games_won = 0
        self.win_message_shown = False
        
        self.initial_distance = self.map.hex_distance(
            self.entities.rescuer.hexEntity, 
            self.entities.survivor.hexEntity
        )
        self.success_rate = 0
        
        if DEBUG:
            self.debugger = Debugger(self, False)

    def create_fonts(self):
        self.title_font = pygame.font.SysFont(None, int(self.size * 1.5))
        self.info_font = pygame.font.SysFont(None, int(self.size * 1.0))
        self.cost_font = pygame.font.SysFont(None, int(self.size * 1.0))
        self.result_font = pygame.font.SysFont(None, int(self.size * 3.0))
        self.help_font = pygame.font.SysFont(None, int(self.size * 0.9))

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
        
        found_message = self.message_manager.check_for_message(h)
        if found_message:
            print(f"Found encrypted message at {h}! Decrypting...")
        
    def check_win_condition(self):
        if self.entities.rescuer.hexEntity == self.entities.survivor.hexEntity:
            if not self.game_over:
                print("Survivor Found! Game Won!")
                self.game_over = True
                self.game_won = True
                self.total_games += 1
                self.games_won += 1
                
                if self.search_start_time is not None:
                    self.total_search_time = time.time() - self.search_start_time
                
                self.win_message_shown = True
            return True
        return False
    
    def check_lose_condition(self):
        if self.entities.rescuer.resources <= 0:
            if not self.game_over:
                print("Out of resources! Game over!")
                self.game_over = True
                self.total_games += 1
                
                if self.search_start_time is not None:
                    self.total_search_time = time.time() - self.search_start_time
            return True
            
        if self.entities.survivor.points <= 0:
            if not self.game_over:
                print("Survivor died! Game over!")
                self.game_over = True
                self.total_games += 1
                
                if self.search_start_time is not None:
                    self.total_search_time = time.time() - self.search_start_time
            return True
            
        return False
    
    def can_see_survivor(self):
            rescuer_hex = self.entities.rescuer.hexEntity
            survivor_hex = self.entities.survivor.hexEntity
            
            if rescuer_hex == survivor_hex:
                return True
                
            distance = self.map.hex_distance(rescuer_hex, survivor_hex)
            if distance <= 3:
                path = self.map.walkable_hex_distance(rescuer_hex, survivor_hex)
                if path:
                    for hex in path[1:-1]:
                        if self.costs[hex] == float('-inf'):
                            return False
                    return True
            return False

    def update_survivor_tracking(self):
            if self.can_see_survivor():
                self.survivor_spotted = True
                self.last_known_survivor_position = self.entities.survivor.hexEntity
                self.survivor_visibility_counter += 1
                self.turns_since_spotted = 0
                
                if self.survivor_visibility_counter >= 2 and not self.ping_sent:
                    self.last_ping_position = self.entities.survivor.hexEntity
                    print(f"PING! Survivor spotted at {self.last_ping_position}")
                    self.ping_sent = True
            else:
                self.survivor_spotted = False
                self.survivor_visibility_counter = 0
                self.ping_sent = False
                self.turns_since_spotted += 1
                
                if self.turns_since_spotted > 10:
                    if np.random.random() < 0.3:
                        self.last_known_survivor_position = None
    
    def update_success_rate(self):
        current_distance = self.map.hex_distance(
            self.entities.rescuer.hexEntity,
            self.entities.survivor.hexEntity
        )
        
        if self.initial_distance > 0:
            distance_covered = self.initial_distance - current_distance
            self.success_rate = min(100, max(0, (distance_covered / self.initial_distance) * 100))
        else:
            self.success_rate = 100
    
    def survivor_takes_tile_damage(self):
        survivor_hex = self.entities.survivor.hexEntity
        tile_cost = self.costs[survivor_hex]
        
        if tile_cost != float('-inf'):
            damage = tile_cost
            self.entities.survivor.points = max(0, self.entities.survivor.points - damage)
            print(f"Survivor took {damage} damage from terrain. Health: {self.entities.survivor.points}")
    
    def ai_move(self):
        if self.ai_mode and not self.game_over:
            if self.search_start_time is None:
                self.search_start_time = time.time()
                
            if not self.rescuer_moved:
                self.update_survivor_tracking()
                
                rescuer_hex = self.entities.rescuer.hexEntity
                survivor_hex = self.entities.survivor.hexEntity
                
                if survivor_hex in self.map.neighbor_hex(rescuer_hex):
                    neighbors = self.map.neighbor_hex(rescuer_hex)
                    for i, neighbor in enumerate(neighbors):
                        if neighbor == survivor_hex:
                            directions = ["SS", "SE", "SW", "NN", "NE", "NW"]
                            direction = directions[i]
                            self.entities.rescuer.move(direction)
                            self.discover_hex()
                            self.rescuer_moved = True
                            self.steps_taken += 1
                            self.move_survivor_randomly()
                            self.update_success_rate()
                            return
                
                ai_move_start = time.time()
                
                target_hex = None
                
                if self.survivor_spotted:
                    target_hex = self.entities.survivor.hexEntity
                elif self.last_known_survivor_position is not None:
                    target_hex = self.last_known_survivor_position
                
                self.entities.rescuer.move_with_ai(
                    target_hex,
                    self.visited, 
                    self.costs
                )
                
                ai_move_time = time.time() - ai_move_start
                
                self.discover_hex()
                self.rescuer_moved = True
                self.steps_taken += 1
                self.move_survivor_randomly()
                
                self.update_success_rate()

    def handle_single_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return None
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                self.ai_mode = not self.ai_mode
                print(f"AI Mode: {'Enabled' if self.ai_mode else 'Disabled'}")
                
                if self.ai_mode and self.search_start_time is None:
                    self.search_start_time = time.time()
                    
                return None
                
            if event.key == pygame.K_r:
                self.__init__(self.size)
                print("Game Reset")
                return None
                
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

                if moved is not None:
                    self.rescuer_moved = True
                    self.steps_taken += 1
                    self.move_survivor_randomly()
                    
                    self.update_survivor_tracking()
                    
                    self.update_success_rate()

                if moved == None:
                    dir = "nowhere"

                if self.debugger:
                    self.debugger.get_entity_feed(dir)
    
    def move_survivor_randomly(self):
        move_result = self.entities.survivor.decide()
        
        if move_result is not None:
            self.survivor_takes_tile_damage()
            self.update_survivor_tracking()
        
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

        if any(neighbor == h for neighbor in self.map.neighbor_hex(self.entities.rescuer.hexEntity)):
            if color == (0,0,0):
                color = (30,30,30)
                border_color = (30,30,30)

        return color, border_color
    
    def color_me_red(self, cost, color):
        if self.debugger and self.debugger.toggleOverlay:
            if self.debugger.removeRed:
                return color
            else:
                return COST_COLORS[(cost if cost != float('-inf') else 6)]
        else:
            return color
    
    def highlight_path(self, h):
        if hasattr(self.entities.rescuer, "target_path") and self.entities.rescuer.target_path:
            if h in self.entities.rescuer.target_path:
                return (100, 100, 255)
        return None
        
    def highlight_last_known_position(self, h):
        if self.last_known_survivor_position == h and not self.survivor_spotted:
            return (255, 165, 0)
        return None

    def draw_map(self):
        for h in self.map.hexes.values():
                border_color = (50,50,50)
                cost = self.costs[h]
                vertices, color = self.map.draw_hex(h)

                path_color = self.highlight_path(h)
                if path_color:
                    color = path_color
                    
                last_known_color = self.highlight_last_known_position(h)
                if last_known_color:
                    color = last_known_color

                if self.debugger:
                    color = self.color_me_red(cost, color)

                color, border_color = self.fog(h, color, border_color)

                pygame.draw.polygon(self.screen, color, vertices)
                pygame.draw.polygon(self.screen, border_color, vertices, 1)
                
                if self.debugger and self.debugger.toggleOverlay and cost != float('-inf'):
                    center = self.map.hex_to_screen(h)
                    cost_text = self.cost_font.render(str(cost), True, (255, 255, 255))
                    text_rect = cost_text.get_rect(center=(center.q + OFFSET[0], center.r + OFFSET[1]))
                    self.screen.blit(cost_text, text_rect)

        if self.last_ping_position:
            vertices, _ = self.map.draw_hex(self.last_ping_position)
            pygame.draw.polygon(self.screen, (255, 255, 0), vertices, 3) 

    def draw_game_info(self):
        line_height = 30
        
        resources_text = f"Resources: {self.entities.rescuer.resources}"
        text_surface = self.info_font.render(resources_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, 10))
        
        health_text = f"Survivor Health: {self.entities.survivor.points}"
        health_surface = self.info_font.render(health_text, True, (255, 255, 255))
        self.screen.blit(health_surface, (10, 10 + line_height))
        
        steps_text = f"Steps: {self.steps_taken}"
        steps_surface = self.info_font.render(steps_text, True, (255, 255, 255))
        self.screen.blit(steps_surface, (10, 10 + 2 * line_height))
        
        found_count = self.message_manager.get_found_count()
        decrypted_count = self.message_manager.get_decrypted_count()
        message_text = f"Messages: {found_count}/5 found, {decrypted_count}/5 decrypted"
        message_surface = self.info_font.render(message_text, True, (255, 255, 255))
        self.screen.blit(message_surface, (10, 10 + 3 * line_height))
        
        if self.ai_mode and self.search_start_time is not None and not self.game_over:
            current_time = time.time() - self.search_start_time
            time_text = f"Search Time: {current_time:.2f}s"
        elif self.game_over and self.total_search_time > 0:
            time_text = f"Search Time: {self.total_search_time:.2f}s"
        else:
            time_text = "Search Time: 0.00s"
        time_surface = self.info_font.render(time_text, True, (255, 255, 255))
        self.screen.blit(time_surface, (10, 10 + 4 * line_height))
        
        rate_text = f"Success Rate: {self.success_rate:.1f}%"
        rate_surface = self.info_font.render(rate_text, True, (255, 255, 255))
        self.screen.blit(rate_surface, (10, 10 + 5 * line_height))
        
        if self.ai_mode:
            ai_text = "AI Mode: ON"
            ai_surface = self.info_font.render(ai_text, True, (100, 255, 100))
            self.screen.blit(ai_surface, (10, 10 + 6 * line_height))
            
            if self.survivor_spotted:
                tracking_text = "Survivor: VISIBLE"
                tracking_color = (0, 255, 0)
            elif self.last_known_survivor_position:
                tracking_text = f"Survivor: LAST SEEN {self.turns_since_spotted} TURNS AGO"
                tracking_color = (255, 165, 0)
            else:
                tracking_text = "Survivor: UNKNOWN"
                tracking_color = (255, 0, 0)
                
            tracking_surface = self.info_font.render(tracking_text, True, tracking_color)
            self.screen.blit(tracking_surface, (10, 10 + 7 * line_height))
            
        help_y = HEIGHT - 120
        help_texts = [
            "Controls:",
            "WASD/QEZX - Move rescuer",
            "T - Toggle AI mode",
            "R - Reset game"
        ]
        
        for i, text in enumerate(help_texts):
            color = (200, 200, 200) if i == 0 else (150, 150, 150)
            help_surface = self.help_font.render(text, True, color)
            self.screen.blit(help_surface, (10, help_y + i * 25))
            
        if self.game_over:
            if self.game_won:
                result_text = "SURVIVOR FOUND!"
                color = (0, 255, 0)
            elif self.entities.survivor.points <= 0:
                result_text = "SURVIVOR DIED!"
                color = (255, 100, 100)
            else:
                result_text = "GAME OVER - OUT OF RESOURCES"
                color = (255, 0, 0)
                
            result_surface = self.result_font.render(result_text, True, color)
            text_rect = result_surface.get_rect(center=(WIDTH//2, HEIGHT//2))
            self.screen.blit(result_surface, text_rect)
            
            restart_text = "Press 'R' to restart"
            restart_surface = self.info_font.render(restart_text, True, (255, 255, 255))
            restart_rect = restart_surface.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
            self.screen.blit(restart_surface, restart_rect)

    def spawn(self):
        self.entities.rescuer.update_animation()
        self.entities.survivor.update_animation()
        
        rescuer_sprite = self.entities.rescuer.animation_list[self.entities.rescuer.frame]
        
        rescuer_pos = (self.entities.rescuer.position[0] - rescuer_sprite.get_width() // 2, 
                       self.entities.rescuer.position[1] - rescuer_sprite.get_height() // 2)
        
        survivor_hex = self.entities.survivor.hexEntity
        rescuer_hex = self.entities.rescuer.hexEntity
        
        is_visible = (
            survivor_hex in self.visited or
            survivor_hex == rescuer_hex or
            survivor_hex in self.map.neighbor_hex(rescuer_hex) or
            (self.debugger and self.debugger.toggleOverlay and self.debugger.removeFog)
        )
        
        if is_visible:
            survivor_sprite = self.entities.survivor.animation_list[self.entities.survivor.frame]
            survivor_pos = (self.entities.survivor.position[0] - survivor_sprite.get_width() // 2, 
                           self.entities.survivor.position[1] - survivor_sprite.get_height() // 2)
            self.screen.blit(survivor_sprite, survivor_pos)
        
        self.screen.blit(rescuer_sprite, rescuer_pos)

    def run(self):
        while self.running:
            self.handle_events()
            
            self.ai_move()
            
            current_hex = self.entities.rescuer.hexEntity
            decrypted_messages = self.message_manager.update_messages(current_hex, self.clock.get_time() / 1000.0)
            
            for message in decrypted_messages:
                print(f"Message decrypted: {message}")
                
            self.check_win_condition()
            self.check_lose_condition()
            
            self.rescuer_moved = False
            self.update_survivor_tracking()
            self.screen.fill((0, 0, 0))
            self.draw_map()
            
            self.message_manager.draw_papers(self.screen)
            
            self.spawn()
            self.draw_game_info()
            
            rescuer_screen_pos = self.entities.rescuer.position
            self.message_manager.draw_active_messages(self.screen, rescuer_screen_pos)

            if self.debugger:
                self.debugger.overlay()

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()