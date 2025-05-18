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
from crypto_system import MessageManager  # Import the crypto system
from config import WIDTH, HEIGHT, FPS, DEBUG, SIZE, OFFSET, COST_COLORS

if DEBUG:
    from utilss.debugger import Debugger

screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("SAR Game")

CONST_game_icon_path = "sar-game-8-field-of-view/assets/imgs/fav.png"
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
        
        # Create different font sizes for various UI elements
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
        
        # Initialize the crypto message system
        self.message_manager = MessageManager(self.map)
        
        # Pass costs to the rescuer for more informed decision making
        self.entities.rescuer.costs = self.costs
        
        # Set fair amount of resources for rescuer (200 instead of infinite)
        #self.entities.rescuer.resources = 200
        
        self.rescuer_moved = False
        self.ai_mode = False  # Toggle for AI control
        self.game_over = False
        self.game_won = False
        self.steps_taken = 0
        
        # New: Tracking for fog of war
        self.survivor_spotted = False
        self.last_known_survivor_position = None
        self.turns_since_spotted = 0
        
        # Path visualization
        self.current_path = []
        
        # New: Search metrics
        self.search_start_time = None  # Changed: We'll set this when AI mode is activated
        self.ai_active_time = 0  # New: Track how long AI has been active
        self.total_search_time = 0
        self.total_games = 0
        self.games_won = 0
        self.win_message_shown = False  # New: Flag to track if win message has been displayed
        
        # New: Success rate based on proximity
        self.initial_distance = self.map.hex_distance(
            self.entities.rescuer.hexEntity, 
            self.entities.survivor.hexEntity
        )
        self.success_rate = 0
        
        if DEBUG:
            self.debugger = Debugger(self, False)

    def create_fonts(self):
        """Create different font sizes for various UI elements"""
        self.title_font = pygame.font.SysFont(None, int(self.size * 1.5))  # Larger font for titles
        self.info_font = pygame.font.SysFont(None, int(self.size * 1.0))   # Medium font for game info
        self.cost_font = pygame.font.SysFont(None, int(self.size * 1.0))   # Original font for costs
        self.result_font = pygame.font.SysFont(None, int(self.size * 3.0)) # Large font for win/lose messages
        self.help_font = pygame.font.SysFont(None, int(self.size * 0.9))   # Smaller font for help text

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
        
        # Only check for messages when discovering a new hex
        found_message = self.message_manager.check_for_message(h)
        if found_message:
            print(f"Found encrypted message at {h}! Decrypting...")
            
        
    def check_win_condition(self):
        """Check if rescuer has found survivor"""
        if self.entities.rescuer.hexEntity == self.entities.survivor.hexEntity:
            if not self.game_over:  # Only print and update stats once
                print("Survivor Found! Game Won!")
                self.game_over = True
                self.game_won = True
                self.total_games += 1
                self.games_won += 1
                
                # Only calculate search time if AI mode was used
                if self.search_start_time is not None:
                    self.total_search_time = time.time() - self.search_start_time
                
                self.win_message_shown = True  # Mark that we've shown the message
            return True
        return False
    
    def check_lose_condition(self):
        """Check if resources are depleted or survivor's health reaches 0"""
        # Check rescuer resources
        if self.entities.rescuer.resources <= 0:
            if not self.game_over:  # Only print and update stats once
                print("Out of resources! Game over!")
                self.game_over = True
                self.total_games += 1
                
                # Only calculate search time if AI mode was used
                if self.search_start_time is not None:
                    self.total_search_time = time.time() - self.search_start_time
            return True
            
        # Check survivor health
        if self.entities.survivor.points <= 0:
            if not self.game_over:  # Only print and update stats once
                print("Survivor died! Game over!")
                self.game_over = True
                self.total_games += 1
                
                # Only calculate search time if AI mode was used
                if self.search_start_time is not None:
                    self.total_search_time = time.time() - self.search_start_time
            return True
            
        return False
    
    def can_see_survivor(self):
        """Check if the survivor is visible to the rescuer within fog of war constraints"""
        # Check if survivor is in a visible hex (rescuer's hex or adjacent)
        rescuer_hex = self.entities.rescuer.hexEntity
        survivor_hex = self.entities.survivor.hexEntity
        
        # If they're in the same hex
        if rescuer_hex == survivor_hex:
            return True
            
        # If survivor is in adjacent hex
        if survivor_hex in self.map.neighbor_hex(rescuer_hex):
            return True
            
        # If survivor is in a visited hex and within a certain distance
        # This simulates being able to see further in areas you've already explored
        if survivor_hex in self.visited:
            # Can see within 2 hexes in visited areas
            if self.map.hex_distance(rescuer_hex, survivor_hex) <= 2:
                return True
                
        return False

    def update_survivor_tracking(self):
        """Update the tracking of the survivor based on visibility"""
        if self.can_see_survivor():
            self.survivor_spotted = True
            self.last_known_survivor_position = self.entities.survivor.hexEntity
            self.turns_since_spotted = 0
        else:
            self.survivor_spotted = False
            self.turns_since_spotted += 1
            
            # After many turns without spotting, increase uncertainty
            if self.turns_since_spotted > 10:
                # Gradually reduce confidence in last known position
                if np.random.random() < 0.3:  # 30% chance to forget position completely
                    self.last_known_survivor_position = None
    
    def update_success_rate(self):
        """Update success rate based on proximity to survivor"""
        current_distance = self.map.hex_distance(
            self.entities.rescuer.hexEntity,
            self.entities.survivor.hexEntity
        )
        
        # Calculate success rate as a percentage of distance covered
        # The closer we get, the higher the success rate
        if self.initial_distance > 0:  # Avoid division by zero
            distance_covered = self.initial_distance - current_distance
            self.success_rate = min(100, max(0, (distance_covered / self.initial_distance) * 100))
        else:
            # If they're starting in the same hex, immediate success
            self.success_rate = 100
    
    def survivor_takes_tile_damage(self):
        """Survivor takes damage based on the cost of the tile they're standing on"""
        survivor_hex = self.entities.survivor.hexEntity
        tile_cost = self.costs[survivor_hex]
        
        # If the tile has a valid cost (not blocked), apply damage
        if tile_cost != float('-inf'):
            damage = tile_cost
            self.entities.survivor.points = max(0, self.entities.survivor.points - damage)
            print(f"Survivor took {damage} damage from terrain. Health: {self.entities.survivor.points}")
    
    def ai_move(self):
        """Let AI control the rescuer with fog of war constraints"""
        if self.ai_mode and not self.game_over:
            # Start the search timer if it hasn't been started yet
            if self.search_start_time is None:
                self.search_start_time = time.time()
                
            # Only perform AI move if no manual movement was made
            if not self.rescuer_moved:
                # Update survivor tracking information
                self.update_survivor_tracking()
                
                # Check if rescuer can see survivor (adjacent check)
                rescuer_hex = self.entities.rescuer.hexEntity
                survivor_hex = self.entities.survivor.hexEntity
                
                # If survivor is adjacent, move directly to them (simplified pathfinding)
                if survivor_hex in self.map.neighbor_hex(rescuer_hex):
                    # Find the direction to the survivor
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
                
                # Measure the AI move time
                ai_move_start = time.time()
                
                # Determine target for AI based on fog of war
                target_hex = None
                
                if self.survivor_spotted:
                    # We can see the survivor! Go directly to them
                    target_hex = self.entities.survivor.hexEntity
                elif self.last_known_survivor_position is not None:
                    # Go to last known position
                    target_hex = self.last_known_survivor_position
                
                # Use AI to determine the next move
                self.entities.rescuer.move_with_ai(
                    target_hex,  # Pass None if we have no info about survivor
                    self.visited, 
                    self.costs
                )
                
                # Track AI move time
                ai_move_time = time.time() - ai_move_start
                
                self.discover_hex()
                self.rescuer_moved = True
                self.steps_taken += 1
                self.move_survivor_randomly()
                
                # Update success rate based on new positions
                self.update_success_rate()

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
                    
                # If AI is disabled, we don't reset the timer
                # This way we only count time when AI is active
                
                return None
                
            # Reset game with 'R' key
            if event.key == pygame.K_r:
                self.__init__(self.size)
                print("Game Reset")
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
                moved = self.entities.rescuer.move(dir)
                self.discover_hex()

                if moved is not None:
                    self.rescuer_moved = True
                    self.steps_taken += 1
                    self.move_survivor_randomly()
                    
                    # Update survivor tracking when player moves manually
                    self.update_survivor_tracking()
                    
                    # Update success rate based on new positions
                    self.update_success_rate()

                if moved == None:
                    dir = "nowhere"

                if self.debugger:
                    self.debugger.get_entity_feed(dir)
    
    def move_survivor_randomly(self):
        """Move survivor randomly and apply tile damage"""
        if np.random.random() < 0.75:
            random_dir_index = np.random.randint(0, 6)
            directions = ["NN", "NE", "NW", "SS", "SE", "SW"]
            random_dir = directions[random_dir_index]
            
            # Move the survivor
            moved = self.entities.survivor.move(random_dir)
            
            # If the survivor successfully moved, apply tile damage
            if moved is not None:
                self.survivor_takes_tile_damage()
    
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
        """Highlight the current A* path if it exists"""
        if hasattr(self.entities.rescuer, "target_path") and self.entities.rescuer.target_path:
            if h in self.entities.rescuer.target_path:
                return (100, 100, 255)  # Light blue path highlight
        return None
        
    def highlight_last_known_position(self, h):
        """Highlight the last known position of the survivor"""
        if self.last_known_survivor_position == h and not self.survivor_spotted:
            return (255, 165, 0)  # Orange for last known position
        return None

    def draw_map(self):
        for h in self.map.hexes.values():
                border_color = (50,50,50)
                cost = self.costs[h]
                vertices, color = self.map.draw_hex(h)

                # Highlight path if this hex is part of it
                path_color = self.highlight_path(h)
                if path_color:
                    color = path_color
                    
                # Highlight last known position if applicable
                last_known_color = self.highlight_last_known_position(h)
                if last_known_color:
                    color = last_known_color

                if self.debugger:
                    color = self.color_me_red(cost, color)

                color, border_color = self.fog(h, color, border_color)

                pygame.draw.polygon(self.screen, color, vertices)
                pygame.draw.polygon(self.screen, border_color, vertices, 1)
                
                # Display cost values for DEBUG
                if self.debugger and self.debugger.toggleOverlay and cost != float('-inf'):
                    center = self.map.hex_to_screen(h)
                    cost_text = self.cost_font.render(str(cost), True, (255, 255, 255))
                    text_rect = cost_text.get_rect(center=(center.q + OFFSET[0], center.r + OFFSET[1]))
                    self.screen.blit(cost_text, text_rect)

    def draw_game_info(self):
        """Display game information like resources and steps"""
        # Vertical spacing between lines
        line_height = 30
        
        # Resources text
        resources_text = f"Resources: {self.entities.rescuer.resources}"
        text_surface = self.info_font.render(resources_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, 10))
        
        # Survivor health text
        health_text = f"Survivor Health: {self.entities.survivor.points}"
        health_surface = self.info_font.render(health_text, True, (255, 255, 255))
        self.screen.blit(health_surface, (10, 10 + line_height))
        
        # Steps text
        steps_text = f"Steps: {self.steps_taken}"
        steps_surface = self.info_font.render(steps_text, True, (255, 255, 255))
        self.screen.blit(steps_surface, (10, 10 + 2 * line_height))
        
        # Message progress
        found_count = self.message_manager.get_found_count()
        decrypted_count = self.message_manager.get_decrypted_count()
        message_text = f"Messages: {found_count}/5 found, {decrypted_count}/5 decrypted"
        message_surface = self.info_font.render(message_text, True, (255, 255, 255))
        self.screen.blit(message_surface, (10, 10 + 3 * line_height))
        
        # Search time (formatted to 2 decimal places)
        if self.ai_mode and self.search_start_time is not None and not self.game_over:
            current_time = time.time() - self.search_start_time
            time_text = f"Search Time: {current_time:.2f}s"
        elif self.game_over and self.total_search_time > 0:
            time_text = f"Search Time: {self.total_search_time:.2f}s"
        else:
            time_text = "Search Time: 0.00s"
        time_surface = self.info_font.render(time_text, True, (255, 255, 255))
        self.screen.blit(time_surface, (10, 10 + 4 * line_height))
        
        # Success rate based on proximity to target
        rate_text = f"Success Rate: {self.success_rate:.1f}%"
        rate_surface = self.info_font.render(rate_text, True, (255, 255, 255))
        self.screen.blit(rate_surface, (10, 10 + 5 * line_height))
        
        # AI mode indicator
        if self.ai_mode:
            ai_text = "AI Mode: ON"
            ai_surface = self.info_font.render(ai_text, True, (100, 255, 100))
            self.screen.blit(ai_surface, (10, 10 + 6 * line_height))
            
            # Display survivor tracking status
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
            
        # Controls help text
        help_y = HEIGHT - 120  # Position near bottom
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
            
        # Game over message
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
                
            # Use a larger font for game over message
            result_surface = self.result_font.render(result_text, True, color)
            text_rect = result_surface.get_rect(center=(WIDTH//2, HEIGHT//2))
            self.screen.blit(result_surface, text_rect)
            
            # Instructions to restart
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
        
        # Draw the survivor if their hex is visible (in visited list or adjacent to rescuer)
        survivor_hex = self.entities.survivor.hexEntity
        rescuer_hex = self.entities.rescuer.hexEntity
        
        # Check if survivor hex is visible according to fog of war rules
        is_visible = (
            survivor_hex in self.visited or  # In previously visited hexes
            survivor_hex == rescuer_hex or   # Same hex as rescuer
            survivor_hex in self.map.neighbor_hex(rescuer_hex) or  # Adjacent to rescuer
            (self.debugger and self.debugger.toggleOverlay and self.debugger.removeFog)  # Debug mode
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
            
            # AI move if enabled
            self.ai_move()
            
            # Only update messages if rescuer is on a message tile
            current_hex = self.entities.rescuer.hexEntity
            decrypted_messages = self.message_manager.update_messages(current_hex, self.clock.get_time() / 1000.0)
            
            # Print decrypted messages to console
            for message in decrypted_messages:
                print(f"Message decrypted: {message}")
                
            # Check game conditions
            self.check_win_condition()
            self.check_lose_condition()
            
            # Reset the movement flag for next frame
            self.rescuer_moved = False
            
            # Rendering
            self.screen.fill((0, 0, 0))
            self.draw_map()
            
            # Draw paper icons for unfound messages
            self.message_manager.draw_papers(self.screen)
            
            self.spawn()
            self.draw_game_info()
            
            # Draw active decrypted messages
            rescuer_screen_pos = self.entities.rescuer.position
            self.message_manager.draw_active_messages(self.screen, rescuer_screen_pos)

            if self.debugger:
                self.debugger.overlay()

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
