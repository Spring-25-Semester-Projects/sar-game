import pygame
import sys
import os
import random
import numpy as np
from collections import defaultdict
from add.algorithms import PathfindingAlgorithms
from map import Map, Hex
from config import WIDTH, HEIGHT, FPS, OFFSET, SURVIVOR_COLOR, HEX_COLOR

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# extra to run the algo, delete if not needed

class RescueGame:
    def __init__(self, algorithm='bfs'):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Search and Rescue")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game map and entities
        self.map = Map(radius=30)
        self.rescuer_path = []
        self.path_lines = []
        self.survivors = []
        self.rescued_survivors = []
        self.fog_of_war = FogOfWar(self.map, vision_radius=3)
        
        # Algorithm selection
        self.algorithm = algorithm
        self.algorithms = PathfindingAlgorithms()
        
        # Initialize game state
        self.init_game()
        
    def init_game(self):
        # Place rescuer
        valid_start = [h for h in self.map.hexes.keys() if h.terrain_type != 'water']
        if valid_start:
            self.rescuer_hex = random.choice(valid_start)
            self.rescuer_position = self.hex_to_screen(self.rescuer_hex)
            self.rescuer_path = [self.rescuer_hex]
            self.fog_of_war.update(self.rescuer_hex)
        else:
            raise ValueError("No valid starting positions")
            
        # Spawn survivors
        self.spawn_survivors(5)
        
        # Build graph for pathfinding
        self.build_graph()
        
    def build_graph(self):
        self.graph = defaultdict(list)
        self.costs = {}
        
        for hex_coord in self.map.hexes:
            if hex_coord.terrain_type == 'water':
                continue
                
            neighbors = self.map.neighbor_hex(hex_coord)
            for neighbor_coords in neighbors:
                neighbor_hex = next((h for h in self.map.hexes.keys() 
                                   if h.x == neighbor_coords[0] and 
                                      h.y == neighbor_coords[1] and 
                                      h.z == neighbor_coords[2]), None)
                
                if neighbor_hex and neighbor_hex.terrain_type != 'water':
                    self.graph[hex_coord].append(neighbor_hex)
                    self.costs[(hex_coord, neighbor_hex)] = neighbor_hex.cost
                    
    def spawn_survivors(self, count):
        valid_hexes = [h for h in self.map.hexes.keys() 
                      if h.terrain_type != 'water' and 
                      h != self.rescuer_hex]
        
        for _ in range(min(count, len(valid_hexes))):
            hex_coords = random.choice(valid_hexes)
            valid_hexes.remove(hex_coords)
            
            survivor = {
                'hex': hex_coords,
                'position': self.hex_to_screen(hex_coords),
                'found': False,
                'health': 100
            }
            self.survivors.append(survivor)
            
    def hex_to_screen(self, hex_coord):
        center = self.map.hex_to_screen(hex_coord)
        return (center.q + OFFSET[0], center.r + OFFSET[1])
        
    def get_next_move(self):
        # Find unexplored hexes
        unexplored = [h for h in self.map.hexes.keys() 
                     if h.terrain_type != 'water' and 
                     (h.x, h.y, h.z) not in self.fog_of_war.explored_hexes]
        
        if not unexplored:
            return None
            
        # Find closest unexplored hex
        if self.algorithm == 'bfs':
            path = self.algorithms.bfs(self.graph, self.rescuer_hex, unexplored[0])
        elif self.algorithm == 'dfs':
            path = self.algorithms.dfs(self.graph, self.rescuer_hex, unexplored[0])
        elif self.algorithm == 'ucs':
            def cost_func(a, b):
                return self.costs.get((a, b), 1)
            path = self.algorithms.ucs(self.graph, self.rescuer_hex, unexplored[0], cost_func)
            
        if path and len(path) > 1:
            return path[1]
        return None
        
    def update(self):
        # Check for found survivors
        for survivor in self.survivors:
            hex_key = (survivor['hex'].x, survivor['hex'].y, survivor['hex'].z)
            if hex_key in self.fog_of_war.explored_hexes and not survivor['found']:
                survivor['found'] = True
                self.rescued_survivors.append(survivor)
                self.survivors.remove(survivor)
                
        # Check game over conditions
        if all(s['found'] for s in self.survivors + self.rescued_survivors):
            self.show_message("Rescued all!")
            return
            
        # Check for dead survivors
        for survivor in self.survivors[:]:
            survivor['health'] -= 0.1
            if survivor['health'] <= 0:
                self.survivors.remove(survivor)
                if not self.survivors and not self.rescued_survivors:
                    self.game_over()
                    return
                    
        # Move rescuer
        next_hex = self.get_next_move()
        if next_hex:
            self.rescuer_hex = next_hex
            self.rescuer_position = self.hex_to_screen(self.rescuer_hex)
            self.rescuer_path.append(self.rescuer_hex)
            self.fog_of_war.update(self.rescuer_hex)
            
            # Add line segment to path
            if len(self.rescuer_path) > 1:
                start_pos = self.hex_to_screen(self.rescuer_path[-2])
                end_pos = self.hex_to_screen(self.rescuer_hex)
                self.path_lines.append((start_pos, end_pos))
                
    def draw(self):
        self.screen.fill((0, 0, 0))
        
        # Draw hex grid
        for h in self.map.hexes.values():
            vertices, color = self.map.draw_hex(h, self.rescuer_hex)
            pygame.draw.polygon(self.screen, color, vertices)
            pygame.draw.polygon(self.screen, (255, 255, 255), vertices, 1)
        
        # Apply fog of war
        self.fog_of_war.apply_fog(self.screen)
        
        # Draw rescuer path
        for line in self.path_lines:
            pygame.draw.line(self.screen, (255, 0, 0), line[0], line[1], 2)
            
        # Draw rescuer
        pygame.draw.circle(self.screen, (0, 0, 255), self.rescuer_position, 10)
        
        # Draw survivors
        for survivor in self.survivors + self.rescued_survivors:
            if survivor['found'] or (survivor['hex'].x, survivor['hex'].y, survivor['hex'].z) in self.fog_of_war.explored_hexes:
                color = (0, 255, 0) if survivor['found'] else SURVIVOR_COLOR
                pygame.draw.circle(self.screen, color, survivor['position'], 8)
                
                # Draw health bar
                health_width = 15 * (survivor['health'] / 100)
                pygame.draw.rect(self.screen, (255, 0, 0), 
                                (survivor['position'][0] - 7, survivor['position'][1] - 15, 15, 3))
                pygame.draw.rect(self.screen, (0, 255, 0), 
                                (survivor['position'][0] - 7, survivor['position'][1] - 15, health_width, 3))
        
        pygame.display.flip()
        
    def show_message(self, message):
        font = pygame.font.SysFont(None, 72)
        text = font.render(message, True, (255, 255, 255))
        text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
        
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        
        self.screen.blit(overlay, (0, 0))
        self.screen.blit(text, text_rect)
        pygame.display.flip()
        
        pygame.time.wait(3000)
        self.running = False
        
    def game_over(self):
        self.show_message("Game Over")
        
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.algorithm = 'bfs'
                    elif event.key == pygame.K_2:
                        self.algorithm = 'dfs'
                    elif event.key == pygame.K_3:
                        self.algorithm = 'ucs'
                        
            self.update()
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

class FogOfWar:
    def __init__(self, map: Map, vision_radius=3):
        self.map = map
        self.vision_radius = vision_radius
        self.explored_hexes = set()
        
    def update(self, center_hex):
        self.explored_hexes.add((center_hex.x, center_hex.y, center_hex.z))
        
        for dx in range(-self.vision_radius, self.vision_radius + 1):
            for dy in range(max(-self.vision_radius, -dx - self.vision_radius), 
                          min(self.vision_radius, -dx + self.vision_radius) + 1):
                dz = -dx - dy
                self.explored_hexes.add((center_hex.x + dx, center_hex.y + dy, center_hex.z + dz))
                
    def apply_fog(self, screen):
        fog_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        for hex_coord in self.map.hexes:
            hex_key = (hex_coord.x, hex_coord.y, hex_coord.z)
            if hex_key not in self.explored_hexes:
                vertices, _ = self.map.draw_hex(hex_coord, None)
                pygame.draw.polygon(fog_surface, (0, 0, 0, 180), vertices)
                
        screen.blit(fog_surface, (0, 0))

if __name__ == "__main__":
    game = RescueGame(algorithm='bfs')
    game.run()