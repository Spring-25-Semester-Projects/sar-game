import pygame
import numpy as np
from collections import namedtuple
from map import Map, Hex
from config import OFFSET
import random
from add.crypto import SimpleCrypto

class SpriteSheet:
    def __init__(self, image):
        self.sheet = image
        
    def get_img(self, frame, width, height, scale, color):
        image = pygame.Surface((width, height)).convert_alpha()
        image.blit(self.sheet, (0, 0), (0, (frame * height), width, height)) 
        image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))  
        image.set_colorkey(color)
        return image

Directions = namedtuple('Direction', ['SS', 'SE', 'SW', 'NN', 'NE', 'NW'])
CONST_direction = Directions(SS=0, SE=1, SW=2, NN=3, NE=4, NW=5)

class Rescuer:
    def __init__(self, map: Map):
        # Movement properties
        self.hexEntity = self._get_valid_start_hex(map)  # Ensures spawn on valid terrain
        self.map = map
        self.position = self._calculate_position()
        self.target_position = None
        self.target_hex = None
        self.moving = False
        self.base_move_speed = 1.0  # Base speed (1 second for plains)
        
        # Sprite properties
        sprite_img = pygame.image.load("assets/Males/M_01.png").convert_alpha()
        self.sprite_sheet = SpriteSheet(sprite_img)
        self.animation_list = []
        self.animation_steps = 3
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.animation_cooldown = 200
        
        # Initialize animation frames
        for x in range(self.animation_steps):
            self.animation_list.append(self.sprite_sheet.get_img(x, 17, 17, 2.75, (0, 0, 0)))
        
        # Stats
        self.health = 100
        self.stamina = 100
        
        # Crypto
        self.encrypted_messages = []
        self.decryption_progress = 0
        self.current_message = None
        self.message_timer = 0
        self.decryption_speed = random.uniform(0.3, 0.8)

    def _get_valid_start_hex(self, map: Map):
        """Find a valid starting hex that's not water"""
        valid_hexes = [h for h in map.hexes.keys() if h.terrain_type != 'water']
        return random.choice(valid_hexes) if valid_hexes else Hex()

    def _calculate_position(self, hex_entity=None):
        hex_entity = hex_entity or self.hexEntity
        center = self.map.hex_to_screen(hex_entity)
        return (center.q + OFFSET[0], center.r + OFFSET[1])

    def move(self, direction):
        if self.moving:
            return False
            
        # Convert number key to direction
        dir_mapping = {
            1: "NE",
            2: "NN",
            3: "NW",
            4: "SE",
            5: "SS",
            6: "SW"
        }
        
        if direction in dir_mapping:
            move_dir = dir_mapping[direction]
            neighbors = self.map.neighbor_hex(self.hexEntity)
            direction_index = getattr(CONST_direction, move_dir, None)
            
            if direction_index is not None and direction_index < len(neighbors):
                target_hex_coords = neighbors[direction_index]
                # Find the actual Hex object in the map
                target_hex = next((h for h in self.map.hexes.keys() 
                                if (h.x, h.y, h.z) == (target_hex_coords[0], target_hex_coords[1], target_hex_coords[2])), None)
                
                # Check if target is valid (not water)
                if target_hex and target_hex.terrain_type != 'water':
                    # Set movement duration based on terrain type
                    terrain_speeds = {
                        'plain': 1.0,
                        'forest': 3.0,
                        'mountain': 5.0
                    }
                    move_duration = terrain_speeds.get(target_hex.terrain_type, 1.0)
                    
                    # Calculate stamina cost (higher for difficult terrain)
                    stamina_costs = {
                        'plain': 5,
                        'forest': 15,
                        'mountain': 25
                    }
                    stamina_cost = stamina_costs.get(target_hex.terrain_type, 5)
                    
                    if self.stamina >= stamina_cost:
                        self.target_hex = target_hex
                        self.target_position = self._calculate_position(target_hex)
                        self.moving = True
                        self.frame = 0
                        self.move_start_time = pygame.time.get_ticks()
                        self.move_duration = move_duration * 1000  # Convert to milliseconds
                        self.stamina = max(0, self.stamina - stamina_cost)
                        return True
        return False

    def update(self, dt):
        # Handle movement animation
        if self.moving and self.target_hex:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.move_start_time
            progress = min(1.0, elapsed / self.move_duration)
            
            # Interpolate position based on progress
            dx = self.target_position[0] - self.position[0]
            dy = self.target_position[1] - self.position[1]
            self.position = (
                self.position[0] + dx * progress,
                self.position[1] + dy * progress
            )
            
            # Update animation frame
            if current_time - self.last_update >= self.animation_cooldown:
                self.last_update = current_time
                self.frame = (self.frame + 1) % len(self.animation_list)
            
            # Check if movement complete
            if progress >= 1.0:
                self.position = self.target_position
                self.hexEntity = self.target_hex
                self.moving = False
                self.frame = 0
        
        # Regenerate stamina when not moving
        if not self.moving:
            self.stamina = min(100, self.stamina + 0.2)
            
          
        if random.random() < 0.9:  # % chance per frame 
            self.find_message()   
            
        self.update_decryption(dt)
        
        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.current_message = None
                
                
        
    def draw_message(self, screen):
        """Draw the current decrypted message with background box"""
        if self.current_message and self.message_timer > 0:
            font = pygame.font.SysFont('Arial', 20, bold=True)
            
            # Render text
            text = font.render(self.current_message, True, (0, 0, 0))
            
            # Create background surface
            bg_width = text.get_width() + 20
            bg_height = text.get_height() + 10
            background = pygame.Surface((bg_width, bg_height))
            background.fill((255, 255, 255))
            background.set_alpha(200)  # Semi-transparent
            
            # Calculate position (above survivor)
            pos_x = self.position[0] - bg_width // 2
            pos_y = self.position[1] - 50  # Adjust this value as needed
            
            # Draw background and text
            screen.blit(background, (pos_x, pos_y))
            screen.blit(text, (pos_x + 10, pos_y + 5))            

    def draw(self, screen):
        if self.moving:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_update >= self.animation_cooldown:
                self.last_update = current_time
                self.frame = (self.frame + 1) % len(self.animation_list)
        else:
            self.frame = 0
        
        player_img = self.animation_list[self.frame]
        sprite_rect = player_img.get_rect(center=self.position)
        screen.blit(player_img, sprite_rect)
        self.draw_message(screen)

    def heal(self, amount):
        self.health = min(100, self.health + amount)
        return self.health
    
    def rest(self):
        self.stamina = min(100, self.stamina + 20)
        return self.stamina
    
    def find_message(self):
        """Find a random encrypted message"""
        messages = [
            "Food cache at NW sector",
            "Danger in SE caves!",
            "Medkit hidden near mountains",
            "Rescue team arriving tomorrow",
            "Safe zone at coordinates 45.7, 32.1",
            "Radio frequency 108.7 has updates",
            "Water source 200m North",
            "Bandits spotted in Eastern woods",
            "Medical supplies in red crate",
            "Storm approaching from West",
            "Nightfall brings increased danger",
            "Look for the marked oak tree",
            "Underground bunker contains supplies",
            "Avoid river crossings at night",
            "Signal fire on highest hill"
        ]
        msg = random.choice(messages)
        key, encrypted = SimpleCrypto.encrypt(msg)
        self.encrypted_messages.append((key, encrypted)) 
        
        
    def update_decryption(self, dt):
        """Progressively decrypt messages"""
        if self.encrypted_messages:
            self.decryption_progress += dt * self.decryption_speed  # Faster decryption
            if self.decryption_progress >= 1.0:
                self.decryption_progress = 0
                key, encrypted = self.encrypted_messages.pop(0)
                decrypted = SimpleCrypto.decrypt(key, encrypted)
                self.current_message = decrypted
                self.message_timer = 4.0  # Show for 4 seconds
                return decrypted
        return None
