from src.entities.mock_entity import Entity, Hex
from collections import defaultdict
from config import CONST_RESCUER_SPRITE_PATH
from src.hex import Hex
import heapq
import random
import numpy as np
import time

class Rescuer(Entity):
    def __init__(self, map):
        # Call parent constructor with the specific sprite path
        super().__init__(map, sprite_path=CONST_RESCUER_SPRITE_PATH)
        
        # Set the rescuer to start at the top of the map (two hexes higher)
        max_x = int(map.max_x)
        min_z = int(map.min_z)
        # Start position adjusted to be two hexes higher
        self.hexEntity = self._find_spawn_position(map, max_x, min_z)
        self.position = self.entity_position()

        self.resources = 500  # Set to a reasonable initial value
        self.stats = [self.points, self.resources]
        self.target_hex = None  # Store target destination
        self.current_path = []  # Store current A* path
        self.costs = None       # Will be set from the game class
        self.reached_target = False  # Flag to indicate if target has been reached
        
        # Anti-loop measures
        self.visit_count = {}   # Track how many times each hex has been visited
        self.visit_history = [] # Track the recent path taken
        self.history_size = 10  # Number of recent steps to track
    
    def _find_spawn_position(self, map, x, z):
            """Find a valid hex at the bottom right of the map, ensuring neighbors are in view"""
            # Calculate coordinates for bottom right area
            max_z = int(map.max_z) - 3  # Move a few hexes in from the edge
            min_x = int(map.min_x) + 3  # Move a few hexes in from the edge
            
            # Try to find a hex in the bottom right area (with buffer from edge)
            for dx in range(6):
                for dz in range(6):
                    test_hex = Hex(min_x+dx, -(min_x+dx)-(max_z-dz), max_z-dz)
                    if test_hex in map.hexes:
                        # Check if all neighbors are in the map
                        all_neighbors_exist = True
                        for neighbor in map.neighbor_hex(test_hex):
                            if neighbor is None:
                                all_neighbors_exist = False
                                break
                        
                        if all_neighbors_exist:
                            return map.hexes[test_hex]
            
            # Fall back to any valid hex in bottom right region
            for dx in range(10):
                for dz in range(10):
                    test_hex = Hex(min_x+dx, -(min_x+dx)-(max_z-dz), max_z-dz)
                    if test_hex in map.hexes:
                        return map.hexes[test_hex]
            
            # Fall back to original position if all else fails
            corner_hex = Hex(min_x, -min_x-max_z, max_z)
            if corner_hex in map.hexes:
                return map.hexes[corner_hex]
            
            # If still not found, search anywhere
            for hex in map.hexes.values():
                neighbors = map.neighbor_hex(hex)
                if None not in neighbors:
                    return hex
            
    def replinsh(self, vl):
        self.resources += vl
    
    def hex_distance(self, hex1, hex2):
        """Calculate the distance between two hex tiles"""
        return self.map.hex_distance(hex1, hex2)
    
    def a_star_pathfinding(self, start_hex, goal_hex, costs):
        """A* pathfinding algorithm for hex grid with anti-loop protection"""
        # Initialize the open and closed sets
        open_set = []
        closed_set = set()
        
        # Add the starting node to the open set
        # (f_score, tiebreaker, hex)
        heapq.heappush(open_set, (0, id(start_hex), start_hex))
        
        # Create dictionaries to store g_score, f_score and came_from
        g_score = defaultdict(lambda: float('inf'))
        g_score[start_hex] = 0
        
        f_score = defaultdict(lambda: float('inf'))
        f_score[start_hex] = self.hex_distance(start_hex, goal_hex)
        
        # Dictionary to reconstruct the path
        came_from = {}
        
        while open_set:
            # Get the node with lowest f_score
            _, _, current_hex = heapq.heappop(open_set)
            
            # Check if we reached the goal
            if current_hex == goal_hex:
                # Reconstruct path
                path = []
                while current_hex in came_from:
                    path.append(current_hex)
                    current_hex = came_from[current_hex]
                path.append(start_hex)
                return list(reversed(path))
            
            # Add current node to closed set
            closed_set.add(current_hex)
            
            
            # Check all neighbors
            for neighbor in self.map.neighbor_hex(current_hex):
                # Skip if None or in closed set
                if neighbor is None or neighbor in closed_set:
                    continue
                
                # Skip if cost is infinite (blocked tile)
                if costs[neighbor] == float('-inf'):
                    continue
                
                # Apply anti-loop factor to the cost calculation
                visit_penalty = self._calculate_visit_penalty(neighbor)
                
                # Calculate the g_score for this neighbor with visit penalty
                tentative_g = g_score[current_hex] + costs[neighbor] + visit_penalty
                
                # Skip if this path is worse
                if tentative_g >= g_score[neighbor]:
                    continue
                
                # This path is better, record it
                came_from[neighbor] = current_hex
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + self.hex_distance(neighbor, goal_hex)
                
                # Add to open set if not already there
                # Use id(neighbor) as a tiebreaker to prevent comparing Hex objects directly
                if neighbor not in [h for _, _, h in open_set]:
                    heapq.heappush(open_set, (f_score[neighbor], id(neighbor), neighbor))
        
        # No path found
        return []
    
    def _calculate_visit_penalty(self, hex):
        """Calculate penalty for visiting a frequently visited hex"""
        visit_count = self.visit_count.get(hex, 0)
        
        # Exponential penalty for frequently visited hexes
        if visit_count >= 3:  # Threshold for considering a tile "frequently visited"
            return visit_count * 2.0
        
        # Minor penalty for recently visited hexes
        if hex in self.visit_history:
            return 1.0
            
        return 0
    
    def set_random_target(self, visited_hexes, costs):
        """
        Set target in the upper right area of the screen
        """
        # Get the max x coordinate for upper right
        max_x = int(self.map.max_x)
        min_z = int(self.map.min_z)
        
        # Try to find a valid hex in the upper right area (within a 5x5 grid from corner)
        valid_targets = []
        for dx in range(5):
            for dz in range(5):
                test_hex = Hex(max_x-dx, -(max_x-dx)-(min_z+dz), min_z+dz)
                if test_hex in self.map.hexes and costs[self.map.hexes[test_hex]] != float('-inf'):
                    valid_targets.append(self.map.hexes[test_hex])
        
        # If we found valid targets in the upper right, choose one randomly
        if valid_targets:
            self.target_hex = random.choice(valid_targets)
            # Calculate initial path to target
            self.current_path = self.a_star_pathfinding(self.hexEntity, self.target_hex, costs)
            self.reached_target = False
            return True
            
        # If no valid hex found in the upper right, fall back to the original method
        valid_targets = []
        for hex in self.map.hexes.values():
            if hex not in visited_hexes and costs[hex] != float('-inf'):
                valid_targets.append(hex)
        
        # If we've visited all valid hexes, just use any walkable hex
        if not valid_targets:
            valid_targets = [hex for hex in self.map.hexes.values() if costs[hex] != float('-inf')]
        
        # Select a random target
        if valid_targets:
            self.target_hex = random.choice(valid_targets)
            # Calculate initial path to target
            self.current_path = self.a_star_pathfinding(self.hexEntity, self.target_hex, costs)
            self.reached_target = False
            return True
        
        return False
    
    def get_direction_to_hex(self, target_hex):
        """Convert a target hex to a direction command (NN, NE, etc.)"""
        if target_hex is None:
            return None
            
        neighbors = self.map.neighbor_hex(self.hexEntity)
        
        # Find the index of the target hex in neighbors
        for i, neighbor in enumerate(neighbors):
            if neighbor == target_hex:
                # Map index to direction
                directions = ["SS", "SE", "SW", "NN", "NE", "NW"]
                return directions[i]
                
        return None
    
    def move_with_astar(self, visited_hexes, costs):
        """Use A* to determine and execute the next move"""
        # Update visit statistics for current position
        current_pos = self.hexEntity
        if current_pos in self.visit_count:
            self.visit_count[current_pos] += 1
        else:
            self.visit_count[current_pos] = 1
        
        # Add to visit history and maintain history size
        self.visit_history.append(current_pos)
        if len(self.visit_history) > self.history_size:
            self.visit_history.pop(0)
        
        # If we reached the target or don't have a target, get a new one
        if self.target_hex is None or self.reached_target or current_pos == self.target_hex:
            success = self.set_random_target(visited_hexes, costs)
            if not success:
                return None  # No valid targets available
            
            if current_pos == self.target_hex:
                self.reached_target = True
                return None  # Already at target
        
        # If current path is empty or invalid, recalculate
        if not self.current_path or len(self.current_path) < 2:
            self.current_path = self.a_star_pathfinding(current_pos, self.target_hex, costs)
            
            # If still no path, try new target
            if not self.current_path or len(self.current_path) < 2:
                self.set_random_target(visited_hexes, costs)
                return None
        
        # Get next hex in path
        next_hex = self.current_path[1] if len(self.current_path) > 1 else None
        
        # Convert hex to direction and move
        direction = self.get_direction_to_hex(next_hex)
        
        if direction:
            result = self.move(direction)
            
            # Update path - remove the hex we just moved to
            if result is not None and len(self.current_path) > 1:
                self.current_path.pop(0)
                
            # Check if we reached target
            if self.hexEntity == self.target_hex:
                self.reached_target = True
                
            return result
            
        return None
    
    def move(self, move_dir):
        """Override the parent move method to reduce resources when moving"""
        result = super().move(move_dir)
        if result is not None:
            # Reduce resources when moving based on tile cost
            hex_moved_to = self.hexEntity
            
            # Use self.costs instead of an undefined costs variable
            if self.costs is not None:
                move_cost = max(1, self.costs[hex_moved_to] if self.costs[hex_moved_to] != float('-inf') else 1)
            else:
                move_cost = 1  # Default cost if costs not set
                
            self.resources = max(0, self.resources - move_cost)
        
        return result