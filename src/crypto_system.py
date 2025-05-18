import random
import pygame
from math import gcd
from config import OFFSET

class SimpleCrypto:
    @staticmethod
    def encrypt(message: str) -> tuple:
        """Encrypt using Affine cipher"""
        try:
            message = message.upper()
            
            # Generate valid Affine cipher keys
            # a must be coprime with 26 (alphabet size)
            possible_a = [1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25]
            a = random.choice(possible_a)
            b = random.randint(0, 25)
            
            encrypted = []
            for char in message:
                if char.isalpha():
                    # Encrypt: E(x) = (ax + b) mod 26
                    x = ord(char) - ord('A')
                    encrypted_char = chr(((a * x + b) % 26) + ord('A'))
                    encrypted.append(encrypted_char)
                else:
                    encrypted.append(char)
            
            return (a, b), ''.join(encrypted)
            
        except Exception as e:
            print(f"Encryption error: {e}")
            return None, None

    @staticmethod
    def decrypt(key: tuple, encrypted: str) -> str:
        """Decrypt using Affine cipher"""
        try:
            a, b = key
            decrypted = []
            
            # Find modular multiplicative inverse of a
            # This is the value that satisfies: a * a_inv ≡ 1 mod 26
            a_inv = None
            for i in range(26):
                if (a * i) % 26 == 1:
                    a_inv = i
                    break
            
            if a_inv is None:
                return "INVALID KEY"
            
            for char in encrypted:
                if char.isalpha():
                    # Decrypt: D(y) = a_inv(y - b) mod 26
                    y = ord(char) - ord('A')
                    decrypted_char = chr(((a_inv * (y - b)) % 26) + ord('A'))
                    decrypted.append(decrypted_char)
                else:
                    decrypted.append(char)
            
            return ''.join(decrypted)
            
        except Exception as e:
            print(f"Decryption error: {e}")
            return "DECRYPTION FAILED"

class EncryptedMessage:
    def __init__(self, hex_position, key, encrypted_content):
        self.hex_position = hex_position
        self.key = key
        self.encrypted_content = encrypted_content
        self.is_found = False
        self.is_decrypted = False
        self.decrypted_content = None
        self.decryption_progress = 0.0
        self.decryption_speed = random.uniform(0.3, 0.8)
        self.message_timer = 0.0
        
    def start_decryption(self):
        """Start the decryption process"""
        self.decryption_progress = 0.0
        
    def update_decryption(self, dt):
        """Update decryption progress"""
        if self.is_found and not self.is_decrypted:
            self.decryption_progress += dt * self.decryption_speed
            if self.decryption_progress >= 1.0:
                self.decrypted_content = SimpleCrypto.decrypt(self.key, self.encrypted_content)
                self.is_decrypted = True
                self.message_timer = 4.0  # Show message for 4 seconds
                return self.decrypted_content
        return None
        
    def update_timer(self, dt):
        """Update message display timer"""
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer < 0:
                self.message_timer = 0
                
    def draw_message(self, screen, position):
        """Draw the decrypted message with background box"""
        if self.is_decrypted and self.message_timer > 0:
            font = pygame.font.SysFont('Arial', 16, bold=True)
            
            # Render text with word wrapping
            words = self.decrypted_content.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + word + " "
                if font.size(test_line)[0] < 250:  # Max width
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = word + " "
            if current_line:
                lines.append(current_line.strip())
            
            # Calculate background size
            max_width = max(font.size(line)[0] for line in lines) if lines else 0
            total_height = len(lines) * font.get_linesize()
            
            bg_width = max_width + 20
            bg_height = total_height + 10
            background = pygame.Surface((bg_width, bg_height))
            background.fill((255, 255, 255))
            background.set_alpha(220)  # Semi-transparent
            
            # Calculate position
            pos_x = position[0] - bg_width // 2
            pos_y = position[1] - 60
            
            # Draw background
            screen.blit(background, (pos_x, pos_y))
            
            # Draw text lines
            for i, line in enumerate(lines):
                text_surface = font.render(line, True, (0, 0, 0))
                text_rect = text_surface.get_rect()
                text_rect.x = pos_x + 10
                text_rect.y = pos_y + 5 + i * font.get_linesize()
                screen.blit(text_surface, text_rect)

    def draw_paper(self, screen):
        """Draw paper icon for unfound messages"""
        if not self.is_found:
            center = self.hex_position.get_pixel()
            # Draw a simple paper icon (white rectangle with black border)
            paper_size = 12
            paper_rect = pygame.Rect(
                center[0] - paper_size // 2,
                center[1] - paper_size // 2,
                paper_size,
                paper_size
            )
            pygame.draw.rect(screen, (255, 255, 255), paper_rect)
            pygame.draw.rect(screen, (0, 0, 0), paper_rect, 2)
            
            # Add a small "?" or paper texture
            font = pygame.font.SysFont('Arial', 8, bold=True)
            text = font.render('?', True, (0, 0, 0))
            text_rect = text.get_rect(center=paper_rect.center)
            screen.blit(text, text_rect)
            
            
            
class MessageManager:
    def __init__(self, game_map):
        self.map = game_map
        self.messages = []
        self.message_templates = [
            "FOOD CACHE AT NW SECTOR",
            "DANGER IN SE CAVES!",
            "MEDKIT HIDDEN NEAR MOUNTAINS",
            "RESCUE TEAM ARRIVING TOMORROW",
            "SAFE ZONE AT COORDINATES 45.7, 32.1",
            "RADIO FREQUENCY 108.7 HAS UPDATES",
            "WATER SOURCE 200M NORTH",
            "BANDITS SPOTTED IN EASTERN WOODS",
            "MEDICAL SUPPLIES IN RED CRATE",
            "STORM APPROACHING FROM WEST",
            "NIGHTFALL BRINGS INCREASED DANGER",
            "LOOK FOR THE MARKED OAK TREE",
            "UNDERGROUND BUNKER CONTAINS SUPPLIES",
            "AVOID RIVER CROSSINGS AT NIGHT",
            "SIGNAL FIRE ON HIGHEST HILL"
        ]
        self.generate_messages()
        
    def generate_messages(self):
        """Generate 5 random encrypted messages at different locations"""
        available_hexes = list(self.map.hexes.values())
        selected_hexes = random.sample(available_hexes, min(5, len(available_hexes)))
        
        for hex_pos in selected_hexes:
            message_text = random.choice(self.message_templates)
            key, encrypted = SimpleCrypto.encrypt(message_text)
            if key and encrypted:
                message = EncryptedMessage(hex_pos, key, encrypted)
                self.messages.append(message)
                
    
        
    def check_for_message(self, rescuer_hex):
        """Check if rescuer found a message at current position"""
        for message in self.messages:
            if message.hex_position == rescuer_hex and not message.is_found:
                message.is_found = True
                message.start_decryption()
                return message
        return None


    def update_messages(self, current_hex, dt):
        """Update all messages - decrypt all found messages, not just the current one"""
        decrypted_messages = []
        for message in self.messages:
            # Update decryption for ALL found messages (not just current hex)
            if message.is_found:
                decrypted = message.update_decryption(dt)
                if decrypted:
                    decrypted_messages.append(decrypted)
            # Always update timer for all messages
            message.update_timer(dt)
        return decrypted_messages


    def draw_papers(self, screen):
        """Draw paper icons for unfound messages at the center of their hex tiles"""
        for message in self.messages:
            if not message.is_found:
                # Get the center position of the hex tile in screen coordinates
                center = self.map.hex_to_screen(message.hex_position)
                screen_pos = (center.q + OFFSET[0], center.r + OFFSET[1])  # Add the map offset
                
                # Draw a simple paper icon (white rectangle with black border)
                paper_size = 12
                paper_rect = pygame.Rect(
                    screen_pos[0] - paper_size // 2,  # Center horizontally
                    screen_pos[1] - paper_size // 2,  # Center vertically
                    paper_size,
                    paper_size
                )
                pygame.draw.rect(screen, (255, 255, 255), paper_rect)
                pygame.draw.rect(screen, (0, 0, 0), paper_rect, 2)
                
                # Add a small "?" or paper texture
                font = pygame.font.SysFont('Arial', 8, bold=True)
                text = font.render('?', True, (0, 0, 0))
                text_rect = text.get_rect(center=paper_rect.center)
                screen.blit(text, text_rect)
                
            
    def draw_active_messages(self, screen, rescuer_position):
        """Draw currently decrypted messages that have active timers"""
        for message in self.messages:
            # Only draw messages that are decrypted AND have an active timer
            if message.is_decrypted and message.message_timer > 0:
                message.draw_message(screen, rescuer_position)
                
    def get_found_count(self):
        """Get number of messages found"""
        return sum(1 for message in self.messages if message.is_found)
        
    def get_decrypted_count(self):
        """Get number of messages decrypted"""
        return sum(1 for message in self.messages if message.is_decrypted)
