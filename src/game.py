import sys
import os
import random
import pygame
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from map import Map
from entities.rescuer import Rescuer
from entities.survivor import Survivor, Item, Weapon, Food
from config import WIDTH, HEIGHT, FPS, OFFSET, SURVIVOR_COLOR, ITEM_COLOR

class Game:
    def __init__(self, radius=30):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("SAR Game - Rescuer and Survivors")
        self.clock = pygame.time.Clock()
        self.running = True
        self.map = Map(radius)

        # Initialize game entities
        self.rescuer = Rescuer(self.map)
        self.survivors = []
        self.items = []
        
        # Spawn initial entities
        self.spawn_survivors(3)  # 3 survivors
        self.spawn_items(5)      # 5 items
        
        self.background = pygame.Surface((WIDTH, HEIGHT))
        self.background.fill((0, 0, 0))

    def spawn_survivors(self, count):
        """Spawn survivors at random locations"""
        for _ in range(count):
            # Get random hex that's not the center
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
        """Spawn random items at random locations"""
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
        """Handle all pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                # Rescuer movement (keys 1-6)
                if pygame.K_1 <= event.key <= pygame.K_6:
                    self.rescuer.move(event.key - pygame.K_1 + 1)
                
                # Item pickup (E key)
                elif event.key == pygame.K_e:
                    for item in self.items[:]:
                        if (item.hex.x == self.rescuer.hexEntity.x and 
                            item.hex.y == self.rescuer.hexEntity.y and 
                            item.hex.z == self.rescuer.hexEntity.z):
                            # Add inventory system for rescuer here if needed
                            self.items.remove(item)
                
                # Item drop (D key)
                elif event.key == pygame.K_d:
                    pass  # Implement if rescuer has inventory

    def draw(self):
        """Draw all game elements"""
        self.screen.blit(self.background, (0, 0))
        
        # Draw hex grid
        for h in self.map.hexes.values():
            vertices, color = self.map.draw_hex(h, self.rescuer.hexEntity)
            pygame.draw.polygon(self.screen, color, vertices)
            pygame.draw.polygon(self.screen, (255, 255, 255), vertices, 1)
        
        # Draw items
        for item in self.items:
            item.render(self.screen, self.map)
        
        # Draw survivors
        # In Game class's draw method:
        for survivor in self.survivors:
            survivor.draw(self.screen)  # Changed from render() to draw()
            survivor.render_status(self.screen)
        # Draw rescuer
        self.rescuer.draw(self.screen)

    def update(self):
        """Update game state"""
        dt = self.clock.get_time() / 1000.0  # Delta time in seconds
        
        # Update rescuer
        self.rescuer.update()
        
        # Update survivors - create a compatible player object for AI decisions
        for survivor in self.survivors[:]:
            # Create a temporary object with hex attribute for the survivor's AI
            player_for_ai = type('', (), {'hex': self.rescuer.hexEntity})()
            survivor.update(dt, player_for_ai)
            
            if not survivor.is_alive():
                self.survivors.remove(survivor)
        
        # Handle survivor-item interactions
        for survivor in self.survivors:
            for item in self.items[:]:
                if (item.hex.x == survivor.hex.x and 
                    item.hex.y == survivor.hex.y and 
                    item.hex.z == survivor.hex.z):
                    if survivor.pick_item(item):
                        self.items.remove(item)

    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()