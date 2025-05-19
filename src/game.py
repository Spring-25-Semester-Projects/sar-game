import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
 
from collections import deque
import pygame
import numpy as np
import time
from src.map import Map
from src.entities.rescuer import Rescuer
from config import WIDTH, HEIGHT, FPS, DEBUG, SIZE, OFFSET, COST_COLORS

if DEBUG:
    from utilss.debugger import Debugger

screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("Pathfinding Game")

CONST_game_icon_path = "/home/n3tw0rkz/Documents/New Folder (2)/sar-game-8-field-of-view/assets/imgs/fav.png"
fav_icon = pygame.image.load(CONST_game_icon_path)
pygame.display.set_icon(fav_icon)

class Game:
    def __init__(self, radius=SIZE):
        pygame.init()
        self.screen = screen
        self.size = radius
        self.screen.fill((0, 0, 0))
        self.clock = pygame.time.Clock()
        
        # Font setup - separate fonts for different UI elements
        self.create_fonts()
        
        self.running = True
        self.debugger = None
        self.removeFog = True  # Changed to True to remove fog of war
        self.removeRed = False
        self.events_info = []
        self.map = Map(radius)
        self.costs = self.map.map_cost()
        self.rescuer = Rescuer(self.map)
        self.visited = deque([self.rescuer.hexEntity])
        
        # Track the rescuer's path/trail
        self.rescuer_trail = []  # Store the hexes the rescuer has visited
        
        # Pass costs to the rescuer for more informed decision making
        self.rescuer.costs = self.costs
        
        self.rescuer_moved = False
        self.ai_mode = False  # Toggle for AI control
        self.game_over = False
        self.game_won = False
        self.steps_taken = 0
        
        # Path visualization
        self.current_path = []
        
        # Search metrics
        self.search_start_time = None
        self.total_search_time = 0
        self.total_games = 0
        self.games_won = 0
        
        # Generate initial random target
        if not self.rescuer.target_hex:
            self.rescuer.set_random_target(self.visited, self.costs)
        
        if DEBUG:
            self.debugger = Debugger(self, False)
    
    def create_fonts(self):
        """Create different font sizes for various UI elements"""
        self.title_font = pygame.font.SysFont(None, int(self.size * 1.5))  # Larger font for titles
        self.info_font = pygame.font.SysFont(None, int(self.size * 2))   # Medium font for game info
        self.cost_font = pygame.font.SysFont(None, int(self.size * 1.0))   # Original font for costs
        self.result_font = pygame.font.SysFont(None, int(self.size * 3.0)) # Large font for win/lose messages
        self.help_font = pygame.font.SysFont(None, int(self.size * 0.9))   # Smaller font for help text

    def __get_cursor(self):
        return np.array(pygame.mouse.get_pos())
    
    def select_hex(self):
        point = self.__get_cursor() - OFFSET
        return self.map.screen_to_hex(point)
    
    def discover_hex(self):
        h = self.rescuer.hexEntity
        
        if h in self.visited:
            return None

        self.visited.append(h)
        
        # Add to trail when discovering a new hex
        if h not in self.rescuer_trail:
            self.rescuer_trail.append(h)
        
    def check_win_condition(self):
        """Check if rescuer has reached its target"""
        if self.rescuer.hexEntity == self.rescuer.target_hex:
            if not self.game_won:  # Only execute once
                self.game_won = True
                self.total_games += 1
                self.games_won += 1
                
                # Only calculate search time if AI mode was used
                if self.search_start_time is not None:
                    self.total_search_time = time.time() - self.search_start_time
                
                # Set new random target after a short delay
                self.set_new_target_timer = pygame.time.get_ticks()
            
            # If it's been 2 seconds since reaching target, set a new one
            if self.game_won and pygame.time.get_ticks() - self.set_new_target_timer > 2000:
                self.rescuer.set_random_target(self.visited, self.costs)
                self.game_won = False
            
            return True
        
        return False
    
    def check_lose_condition(self):
        """Check if resources are depleted"""
        if self.rescuer.resources <= 0:
            if not self.game_over:  # Only print and update stats once
                print("Out of resources! Game over!")
                self.game_over = True
                self.total_games += 1
                
                # Only calculate search time if AI mode was used
                if self.search_start_time is not None:
                    self.total_search_time = time.time() - self.search_start_time
            return True
        return False

    def handle_single_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return None
        
        if event.type == pygame.KEYDOWN:
            # Toggle AI mode with 'T' key
            if event.key == pygame.K_t:
                self.ai_mode = not self.ai_mode
                print(f"AI Mode: {'Enabled' if self.ai_mode else 'Disabled'}")
                
                # Start timing when AI is first enabled
                if self.ai_mode and self.search_start_time is None:
                    self.search_start_time = time.time()
                    
                return None
                
            # Reset game with 'R' key
            if event.key == pygame.K_r:
                self.__init__(self.size)
                print("Game Reset")
                return None
                
            # New target with 'N' key
            if event.key == pygame.K_n:
                success = self.rescuer.set_random_target(self.visited, self.costs)
                if success:
                    print("New target set!")
                else:
                    print("Could not find a valid target!")
                return None
                
            # Manual movement keys
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
                old_hex = self.rescuer.hexEntity  # Store current position before moving
                moved = self.rescuer.move(dir)
                self.discover_hex()
                
                # Add to trail when moving
                if moved is not None and old_hex not in self.rescuer_trail:
                    self.rescuer_trail.append(old_hex)

                if moved is not None:
                    self.rescuer_moved = True
                    self.steps_taken += 1
                    self.check_win_condition()

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
        # Always return original colors since fog is removed
        return color, border_color
    
    def color_me_red(self, cost, color):
        if self.debugger and self.debugger.toggleOverlay:
            if self.debugger.removeRed:
                return color
            else:
                # Convert numpy.float64 to integer for indexing
                if isinstance(cost, (float, np.float64)) and cost == float('-inf'):
                    idx = len(COST_COLORS) - 1  # Use last color for blocked cells
                else:
                    # Convert to Python int, ensuring it's within valid range
                    idx = min(int(cost), len(COST_COLORS) - 1)
                return COST_COLORS[idx]
        else:
            # Convert numpy.float64 to integer for indexing
            if isinstance(cost, (float, np.float64)) and cost == float('-inf'):
                idx = len(COST_COLORS) - 1  # Use last color for blocked cells
            else:
                # Convert to Python int, ensuring it's within valid range
                idx = min(int(cost), len(COST_COLORS) - 1)
            return COST_COLORS[idx]
    
    def highlight_path(self, h):
        """Highlight the current A* path if it exists"""
        # Return None to disable the blue A* path visualization
        return None
    
    def highlight_trail(self, h):
        """Highlight the rescuer's trail"""
        if h in self.rescuer_trail:
            return (0, 0, 0)  # Black color for trail
        return None
        
    def highlight_target(self, h):
        """Highlight the target hex"""
        if self.rescuer.target_hex == h:
            return (0, 255, 0)  # Green for target
        return None

    def draw_map(self):
        for h in self.map.hexes.values():
            border_color = (50,50,50)
            cost = self.costs[h]
            vertices, color = self.map.draw_hex(h)

            # Always show cost colors
            color = self.color_me_red(cost, color)

            # Highlight trail if this hex is part of it
            trail_color = self.highlight_trail(h)
            if trail_color:
                color = trail_color
                
            # Highlight target if applicable
            target_color = self.highlight_target(h)
            if target_color:
                color = target_color

            # Draw polygon with the determined color
            pygame.draw.polygon(self.screen, color, vertices)
            pygame.draw.polygon(self.screen, border_color, vertices, 1)
            
            # Display cost values
            if cost != float('-inf'):
                center = self.map.hex_to_screen(h)
                cost_text = self.cost_font.render(str(int(cost)), True, (255, 255, 255))
                text_rect = cost_text.get_rect(center=(center.q + OFFSET[0], center.r + OFFSET[1]))
                self.screen.blit(cost_text, text_rect)

    def draw_info_panel(self, text, position, line_number=0):
        """Draw text with a semi-transparent background"""
        line_height = 35
        y_position = position[1] + (line_height * line_number)
        
        # Create background surface
        text_surface = self.info_font.render(text, True, (255, 255, 255))
        text_width = text_surface.get_width()
        bg_surface = pygame.Surface((text_width + 20, 30), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))  # Semi-transparent black background
        
        # Draw background then text
        self.screen.blit(bg_surface, (position[0] - 10, y_position - 5))
        self.screen.blit(text_surface, (position[0], y_position))

    def draw_game_info(self):
        """Display game information like resources and steps"""
        # Position of the info panel
        info_x = 10
        info_y = 10
        
        # Resources text with updated font
        self.draw_info_panel(f"Resources: {self.rescuer.resources}", (info_x, info_y), 0)
        
        # Steps text
        self.draw_info_panel(f"Steps: {self.steps_taken}", (info_x, info_y), 1)
        
        # Search time (formatted to 2 decimal places)
        if self.ai_mode and self.search_start_time is not None and not self.game_over:
            current_time = time.time() - self.search_start_time
            time_text = f"Search Time: {current_time:.2f}s"
        elif self.game_over and self.total_search_time > 0:
            time_text = f"Search Time: {self.total_search_time:.2f}s"
        else:
            time_text = "Search Time: 0.00s"
        self.draw_info_panel(time_text, (info_x, info_y), 2)
        
        # Success rate based on games won
        rate_text = f"Targets Reached: {self.games_won}"
        self.draw_info_panel(rate_text, (info_x, info_y), 3)
        
        # AI mode indicator
        if self.ai_mode:
            ai_text = "AI Mode: ON"
            self.draw_info_panel(ai_text, (info_x, info_y), 4)
            
            # Display target distance
            if self.rescuer.target_hex:
                distance = self.map.hex_distance(self.rescuer.hexEntity, self.rescuer.target_hex)
                distance_text = f"Distance to Target: {distance}"
                self.draw_info_panel(distance_text, (info_x, info_y), 5)
            
        # Target reached message
        if self.game_won:
            result_text = "TARGET REACHED!"
            color = (0, 255, 0)
            
            # Use a larger font for result message
            result_surface = self.result_font.render(result_text, True, color)
            text_rect = result_surface.get_rect(center=(WIDTH//2, HEIGHT//2))
            self.screen.blit(result_surface, text_rect)
            
        # Game over message
        if self.game_over:
            result_text = "GAME OVER - OUT OF RESOURCES"
            color = (255, 0, 0)
                
            # Use a larger font for game over message
            result_surface = self.result_font.render(result_text, True, color)
            text_rect = result_surface.get_rect(center=(WIDTH//2, HEIGHT//2))
            self.screen.blit(result_surface, text_rect)
            
            # Instructions to restart
            restart_text = "Press 'R' to restart"
            restart_surface = self.info_font.render(restart_text, True, (255, 255, 255))
            restart_rect = restart_surface.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
            self.screen.blit(restart_surface, restart_rect)

        # Help text
        help_text = "Controls: WASDQE=Movement, T=Toggle AI, N=New Target, R=Reset"
        help_surface = self.help_font.render(help_text, True, (200, 200, 200))
        help_rect = help_surface.get_rect(center=(WIDTH//2, HEIGHT - 30))
        self.screen.blit(help_surface, help_rect)

    def ai_move(self):
        """Let AI control the rescuer using A* pathfinding"""
        if self.ai_mode and not self.game_over and not self.game_won:
            # Start the search timer if it hasn't been started yet
            if self.search_start_time is None:
                self.search_start_time = time.time()
                
            # Only perform AI move if no manual movement was made
            if not self.rescuer_moved:
                old_hex = self.rescuer.hexEntity  # Store position before AI move
                
                # Use A* to determine the next move
                self.rescuer.move_with_astar(self.visited, self.costs)
                
                # Add to trail if moved to a new position
                if old_hex != self.rescuer.hexEntity and old_hex not in self.rescuer_trail:
                    self.rescuer_trail.append(old_hex)
                
                self.discover_hex()
                self.rescuer_moved = False  # Reset for next frame
                self.steps_taken += 1
                
                # Check if we reached the target
                self.check_win_condition()

    def spawn(self):
        self.rescuer.update_animation()
        
        rescuer_sprite = self.rescuer.animation_list[self.rescuer.frame]
        
        rescuer_pos = (self.rescuer.position[0] - rescuer_sprite.get_width() // 2, 
                       self.rescuer.position[1] - rescuer_sprite.get_height() // 2)
        
        self.screen.blit(rescuer_sprite, rescuer_pos)

    def run(self):
        while self.running:
            self.handle_events()
            
            # AI move if enabled
            self.ai_move()
            
            # Check game conditions
            self.check_lose_condition()
            
            # Reset the movement flag for next frame
            self.rescuer_moved = False
            
            # Rendering
            self.screen.fill((0, 0, 0))
            self.draw_map()
            self.spawn()
            self.draw_game_info()

            if self.debugger:
                self.debugger.overlay()

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
