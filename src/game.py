import sys
import os
import random
import pygame
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from map import Map, Hex
from entities.rescuer import Rescuer
from entities.survivor import Survivor
from entities.items import Item, Weapon, Food
from config import WIDTH, HEIGHT, FPS, OFFSET, SURVIVOR_COLOR, ITEM_COLOR, HEX_COLOR
from add.chest import Chest
class FogOfWar:
    def __init__(self, map: Map, vision_radius=3):
        self.map = map
        self.vision_radius = vision_radius
        self.active = True
        self.fog_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.explored_hexes = set()
        
    def toggle(self):
        self.active = not self.active
        
    def update(self, rescuer_hex):
        """Update which hexes are visible based on rescuer's position"""
        if not self.active:
            return
            
        self.explored_hexes.add((rescuer_hex.x, rescuer_hex.y, rescuer_hex.z))
        
        # Get all hexes within vision radius
        visible_hexes = set()
        for dx in range(-self.vision_radius, self.vision_radius + 1):
            for dy in range(max(-self.vision_radius, -dx - self.vision_radius), 
                          min(self.vision_radius, -dx + self.vision_radius) + 1):
                dz = -dx - dy
                visible_hexes.add((rescuer_hex.x + dx, rescuer_hex.y + dy, rescuer_hex.z + dz))
        
        # Mark these hexes as explored
        for hex_coords in visible_hexes:
            self.explored_hexes.add(hex_coords)
    
    def apply_fog(self, screen, entities, items):
        """Apply fog of war to the screen"""
        if not self.active:
            return
            
        # Clear fog surface
        self.fog_surface.fill((0, 0, 0, 0))
        
        # Draw fog everywhere except explored hexes
        for hex_coord in self.map.hexes:
            hex_key = (hex_coord.x, hex_coord.y, hex_coord.z)
            if hex_key not in self.explored_hexes:
                vertices, _ = self.map.draw_hex(hex_coord, None)
                pygame.draw.polygon(self.fog_surface, (0, 0, 0, 200), vertices)
        
        # Draw entities and items only if they're in explored hexes
        for entity in entities:
            # Handle both Rescuer (hexEntity) and Survivor (hexEntity) cases
            hex_key = (entity.hexEntity.x, entity.hexEntity.y, entity.hexEntity.z)
            if hex_key in self.explored_hexes:
                entity.draw(screen)
                
        for item in items:
            hex_key = (item.hex.x, item.hex.y, item.hex.z)
            if hex_key in self.explored_hexes:
                item.render(screen, self.map)
        
        # Apply the fog overlay
        screen.blit(self.fog_surface, (0, 0))

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
        
        # Initialize fog of war
        self.fog_of_war = FogOfWar(self.map, vision_radius=4)
        
        # Spawn initial entities
        self.spawn_survivors(20)
        self.spawn_items(20)
        
        self.background = pygame.Surface((WIDTH, HEIGHT))
        self.background.fill((0, 0, 0))
            
        # Initialize rescuer position on valid terrain
        valid_start = [h for h in self.map.hexes.keys() if h.terrain_type != 'water']
        if valid_start:
            self.rescuer.hexEntity = random.choice(valid_start)
            self.rescuer.position = self.rescuer._calculate_position()
        else:
            raise ValueError("No valid starting positions (no non-water hexes)")

    def spawn_survivors(self, count):
        """Spawn survivors at random locations, strictly avoiding water terrain"""
        valid_hexes = [hex_coord for hex_coord in self.map.hexes.keys() 
                    if hex_coord.terrain_type != 'water']
        
        count = min(count, len(valid_hexes))
        
        for _ in range(count):
            hex_coords = random.choice(valid_hexes)
            valid_hexes.remove(hex_coords)
            
            survivor = Survivor(
                self.map,
                color=SURVIVOR_COLOR,
                speed=1,
                ai_type=random.choice(['wander', 'chase'])
            )
            survivor.hexEntity = hex_coords
            survivor.position = survivor._hex_to_screen()
            self.survivors.append(survivor)

    def spawn_items(self, count):
        """Spawn random items at random locations, avoiding water"""
        valid_hexes = [hex_coord for hex_coord in self.map.hexes.keys() 
                    if hex_coord.terrain_type != 'water']
        
        item_types = [
            ("Medkit", "weapon", 15),
            ("Knife", "weapon", 10),
            ("Food", "food", 20),
            ("Water", "food", 15)
        ]
        
        for _ in range(min(count, len(valid_hexes))):
            hex_coords = random.choice(valid_hexes)
            valid_hexes.remove(hex_coords)
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
                            self.items.remove(item)
                
                # Item drop (D key)
                elif event.key == pygame.K_d:
                    pass
                
                # Fog of war toggle (F key)
                elif event.key == pygame.K_f:
                    self.fog_of_war.toggle()

    def draw(self):
        """Draw all game elements"""
        self.screen.blit(self.background, (0, 0))
        
        # Draw hex grid
        for h in self.map.hexes.values():
            vertices, color = self.map.draw_hex(h, self.rescuer.hexEntity)
            pygame.draw.polygon(self.screen, color, vertices)
            pygame.draw.polygon(self.screen, (255, 255, 255), vertices, 1)
        
        # Update fog of war with rescuer's position
        self.fog_of_war.update(self.rescuer.hexEntity)
        
        if self.fog_of_war.active:
            # Draw entities and items through fog of war
            self.fog_of_war.apply_fog(self.screen, self.survivors + [self.rescuer], self.items)
        else:
            # Draw everything normally
            for survivor in self.survivors:
                survivor.draw(self.screen)
                survivor.render_status(self.screen)
                
            for item in self.items:
                item.render(self.screen, self.map)
            self.rescuer.draw(self.screen)  
    def update(self):
        """Update game state"""
        dt = self.clock.get_time() / 1000.0
        
        # Update rescuer
        self.rescuer.update(dt)
        
        # Update survivors
        for survivor in self.survivors[:]:
            player_for_ai = type('', (), {'hex': self.rescuer.hexEntity})()
            survivor.update(dt, player_for_ai)
            
            # Check for dead survivors
            if not survivor.is_alive():
                self.survivors.remove(survivor)
                if len(self.survivors) == 0:
                    self.game_over()
        
        # Item pickup logic
        for survivor in self.survivors:
            for item in self.items[:]:
                if (item.hex.x == survivor.hexEntity.x and 
                    item.hex.y == survivor.hexEntity.y and 
                    item.hex.z == survivor.hexEntity.z):
                    if survivor.pick_item(item):
                        self.items.remove(item)

    def game_over(self):
        """Display game over screen"""
        self.running = False
        
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        
        font_large = pygame.font.SysFont(None, 72)
        font_small = pygame.font.SysFont(None, 36)
        
        text1 = font_large.render("GAME OVER", True, (255, 0, 0))
        text2 = font_small.render("All survivors have perished", True, (255, 255, 255))
        text3 = font_small.render("Press any key to exit", True, (255, 255, 255))
        
        self.screen.blit(overlay, (0, 0))
        self.screen.blit(text1, (WIDTH//2 - text1.get_width()//2, HEIGHT//2 - 100))
        self.screen.blit(text2, (WIDTH//2 - text2.get_width()//2, HEIGHT//2))
        self.screen.blit(text3, (WIDTH//2 - text3.get_width()//2, HEIGHT//2 + 50))
        
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                elif event.type == pygame.KEYDOWN:
                    waiting = False
        
        pygame.quit()
        sys.exit()
         
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