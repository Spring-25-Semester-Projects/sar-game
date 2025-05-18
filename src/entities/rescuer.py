from src.entities.mock_entity import *
from collections import defaultdict, Counter
import heapq
import random
import numpy as np
import time

class Rescuer(Entity):
    def __init__(self, map):
        super().__init__(map)

        sprite_img = pygame.image.load("sar-game-8-field-of-view/assets/Females/F_03.png").convert_alpha()
        self.sprite_sheet = SpriteSheet(sprite_img)
        self.animation_list = []
        self.animation_steps = 3  # Using only 3 front-facing frames
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.animation_cooldown = 200

        # Initialize animation frames - use the front-facing frames only
        for x in range(self.animation_steps):
            self.animation_list.append(self.sprite_sheet.get_img(x, 17, 17, 2.75, (0, 0, 0)))


        self.resources = float('inf')  # Set to a reasonable initial value 
        self.stats = [self.points, self.resources]
        self.inventory = {}
        self.target_path = []
        self.costs = None  # Will be set from the game class
        
        # Anti-loop measures
        self.visit_count = Counter()  # Track how many times each hex has been visited
        self.visit_history = []       # Track the recent path taken
        self.history_size = 10        # Number of recent steps to track
        self.last_exploration_time = time.time()  # Time tracking for exploration
        self.stuck_threshold = 3      # How many repeated visits before considering "stuck"
        self.exploration_boost = 1.0  # Dynamic exploration boost (increases when stuck)
        
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
        visit_count = self.visit_count[hex]
        
        # Exponential penalty for frequently visited hexes
        if visit_count >= self.stuck_threshold:
            return visit_count * self.exploration_boost * 2.0
        
        # Minor penalty for recently visited hexes
        if hex in self.visit_history:
            return 1.0 * self.exploration_boost
            
        return 0
    
    def expectimax_decision(self, survivor_hex, visited_hexes, costs):
        """
        Enhanced expectimax approach that accounts for survivor's possible movements.
        - Considers the cost of each path
        - Takes into account the probability of the survivor moving
        - Evaluates multiple possible future states
        - Now includes anti-loop protection
        """
        # Increase exploration boost over time when no new tiles visited
        current_time = time.time()
        time_since_last_exploration = current_time - self.last_exploration_time
        
        # If we're getting stuck in loops, increase the exploration boost
        if time_since_last_exploration > 5.0:  # 5 seconds without finding new tiles
            self.exploration_boost = min(5.0, self.exploration_boost + 0.5)
        else:
            self.exploration_boost = max(1.0, self.exploration_boost - 0.1)  # Slowly decrease back to normal
            
        if survivor_hex is None:
            return self.explore_decision(visited_hexes, costs)
        
        # Maximum depth for expectimax search
        max_depth = 2
        
        # Initial path to survivor using A*
        base_path = self.a_star_pathfinding(self.hexEntity, survivor_hex, costs)
        
        if not base_path:
            # No path found, explore instead
            return self.explore_decision(visited_hexes, costs)
        
        # Store the base path for visualization
        self.target_path = base_path
        
        # If we're already next to the survivor, just go to them
        if len(base_path) <= 2:
            return base_path[1] if len(base_path) > 1 else None
        
        # Get possible next moves for the rescuer
        neighbors = self.map.neighbor_hex(self.hexEntity)
        valid_moves = [n for n in neighbors if n is not None and costs[n] != float('-inf')]
        
        if not valid_moves:
            return None
        
        # Evaluate each possible move using expectimax
        best_score = float('-inf')
        best_move = None
        
        for move in valid_moves:
            # Calculate score for this move using expectimax
            score = self._expectimax_score(
                move,                # Rescuer's position after this move
                survivor_hex,        # Current survivor position
                costs,               # Map costs
                1,                   # Current depth (starting at 1 after the first move)
                max_depth,           # Maximum depth to search
                visited_hexes        # Visited hexes
            )
            
            # Apply visit penalty for anti-loop protection
            visit_penalty = self._calculate_visit_penalty(move)
            score -= visit_penalty
            
            # Update best move if this one is better
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move if best_move else base_path[1]
    
    def _expectimax_score(self, rescuer_pos, survivor_pos, costs, depth, max_depth, visited_hexes):
        """
        Recursive helper function for expectimax calculation.
        
        Args:
            rescuer_pos: The rescuer's position
            survivor_pos: The survivor's current position
            costs: Map costs
            depth: Current search depth
            max_depth: Maximum search depth
            visited_hexes: Set of hexes already visited
            
        Returns:
            Numeric score representing the expected utility of this state
        """
        # Base case: maximum depth reached or rescuer found survivor
        if depth >= max_depth or rescuer_pos == survivor_pos:
            # Terminal state evaluation
            if rescuer_pos == survivor_pos:
                return 1000  # Large reward for finding survivor
            
            # Evaluate based on distance and cost
            distance_score = -self.hex_distance(rescuer_pos, survivor_pos) * 10
            cost_score = -costs[rescuer_pos] if costs[rescuer_pos] != float('-inf') else -100
            
            # Higher reward for unvisited tiles to encourage exploration
            exploration_score = 15 if rescuer_pos not in visited_hexes else 0
            
            # Add a novelty bonus for hexes not in recent history
            novelty_bonus = 10 if rescuer_pos not in self.visit_history else 0
            
            return distance_score + cost_score + exploration_score + novelty_bonus
        
        # Rescuer's turn (max node)
        if depth % 2 == 1:
            # Get possible moves for rescuer
            neighbors = self.map.neighbor_hex(rescuer_pos)
            valid_moves = [n for n in neighbors if n is not None and costs[n] != float('-inf')]
            
            if not valid_moves:
                return -1000  # Very bad if rescuer has no valid moves
            
            # Choose the best move (max value)
            best_score = float('-inf')
            for move in valid_moves:
                score = self._expectimax_score(move, survivor_pos, costs, depth + 1, max_depth, visited_hexes)
                best_score = max(best_score, score)
                
            return best_score
        
        # Survivor's turn (chance node)
        else:
            # Get possible moves for survivor
            neighbors = self.map.neighbor_hex(survivor_pos)
            valid_moves = [n for n in neighbors if n is not None and costs[n] != float('-inf')]
            
            if not valid_moves:
                valid_moves = [survivor_pos]  # Survivor stays in place if no valid moves
            
            # Calculate expected value across all possible survivor moves
            # Assume survivor has 75% chance to move randomly and 25% chance to stay still
            total_score = 0
            
            # Score for staying still (25% chance)
            stay_score = self._expectimax_score(rescuer_pos, survivor_pos, costs, depth + 1, max_depth, visited_hexes)
            total_score += 0.25 * stay_score
            
            # Score for random movement (75% chance distributed among valid moves)
            move_probability = 0.75 / len(valid_moves) if valid_moves else 0
            for move in valid_moves:
                if move != survivor_pos:  # Skip the case where survivor stays still (already calculated)
                    score = self._expectimax_score(rescuer_pos, move, costs, depth + 1, max_depth, visited_hexes)
                    total_score += move_probability * score
            
            return total_score
    
    def explore_decision(self, visited_hexes, costs):
        """
        Decide which direction to move for exploration.
        Prioritize unvisited hexes with lower cost, avoiding loops.
        """
        neighbors = self.map.neighbor_hex(self.hexEntity)
        valid_neighbors = [n for n in neighbors if n is not None and costs[n] != float('-inf')]
        
        if not valid_neighbors:
            return None
        
        # Check if we're in a potential loop (revisiting same hexes)
        current_pos = self.hexEntity
        is_looping = self._detect_loop()
        
        # Prioritize unvisited neighbors
        unvisited = [n for n in valid_neighbors if n not in visited_hexes]
        
        if unvisited:
            # Found new territories to explore - reset exploration metrics
            self.last_exploration_time = time.time()
            self.exploration_boost = 1.0
            
            # Sort by cost (prefer lower cost tiles)
            unvisited.sort(key=lambda x: costs[x])
            return unvisited[0]  # Choose the lowest cost unvisited neighbor
        
        # All neighbors visited - need to choose based on other factors
        if is_looping:
            # We're in a loop - find the least visited neighbor
            visit_counts = [(n, self.visit_count[n]) for n in valid_neighbors]
            least_visited = min(visit_counts, key=lambda x: x[1])[0]
            return least_visited
        else:
            # Not in a loop yet - use normal cost-based decision
            valid_neighbors.sort(key=lambda x: costs[x] + self._calculate_visit_penalty(x))
            return valid_neighbors[0]
    
    def _detect_loop(self):
        """Detect if we're stuck in a loop by analyzing recent movement patterns"""
        if len(self.visit_history) < self.history_size:
            return False
            
        # Check for repeating patterns in the last N moves
        # Simple detection: if we've revisited the same hex more than threshold times recently
        recent_positions = self.visit_history[-self.history_size:]
        position_counts = Counter(recent_positions)
        
        # If any position appears more than threshold times in recent history
        return any(count >= self.stuck_threshold for count in position_counts.values())
    
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
    
    def move_with_ai(self, survivor_hex, visited_hexes, costs):
        """Use AI to determine the next move"""
        # Update visit statistics
        current_pos = self.hexEntity
        self.visit_count[current_pos] += 1
        
        # Add to visit history and maintain history size
        self.visit_history.append(current_pos)
        if len(self.visit_history) > self.history_size:
            self.visit_history.pop(0)
            
        # Make decision with updated statistics
        target_hex = self.expectimax_decision(survivor_hex, visited_hexes, costs)
        direction = self.get_direction_to_hex(target_hex)
        
        if direction:
            return self.move(direction)
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
    
    def seek(self, survivor_hex=None, visited_hexes=None, costs=None):
        """Search for survivor using expectimax decision making"""
        if survivor_hex and visited_hexes and costs:
            next_hex = self.expectimax_decision(survivor_hex, visited_hexes, costs)
            return self.get_direction_to_hex(next_hex)
        return None
    
    def add_item(self, item_type):
        """Add an item to inventory"""
        if item_type in self.inventory:
            self.inventory[item_type] += 1
        else:
            self.inventory[item_type] = 1
    
    def use_item(self, item_type):
        """Use an item from inventory"""
        if item_type in self.inventory and self.inventory[item_type] > 0:
            # Handle item effects (could be resources, health, etc.)
            self.inventory[item_type] -= 1
            
            # Remove from inventory if count is 0
            if self.inventory[item_type] <= 0:
                del self.inventory[item_type]
            
            return True
        return False

    def __repr__(self):
        return f"Entity={type(self).__name__}. Health={self.points}, Resources={self.resources}."
