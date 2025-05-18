from src.entities.mock_entity import Entity, Hex
from collections import defaultdict, Counter
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

        self.resources = float('inf') # Set to a reasonable initial value 
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
        
        # Naive Bayes variables for survivor movement prediction
        self.survivor_move_history = []  # Track survivor's recent movements
        self.survivor_position_history = []  # Track survivor's positions
        self.survivor_last_seen_position = None
        self.survivor_last_seen_time = 0  # Track when survivor was last spotted
        self.survivor_direction_counts = Counter()  # Count movement directions
        self.survivor_terrain_prefs = defaultdict(Counter)  # Terrain preferences by cost
        self.laplace_smoothing = 1.0  # Smoothing factor for Naive Bayes
        
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
    
    def update_survivor_model(self, current_survivor_pos):
        """Update the Naive Bayes model with new survivor observation"""
        # Only update if we have valid data
        if current_survivor_pos is None:
            return
            
        # If this is the first observation
        if self.survivor_last_seen_position is None:
            self.survivor_last_seen_position = current_survivor_pos
            self.survivor_position_history.append(current_survivor_pos)
            self.survivor_last_seen_time = time.time()
            return
            
        # Only update if the position has changed (movement occurred)
        if current_survivor_pos != self.survivor_last_seen_position:
            # Determine which direction the survivor moved
            neighbors = self.map.neighbor_hex(self.survivor_last_seen_position)
            for i, neighbor in enumerate(neighbors):
                if neighbor == current_survivor_pos:
                    directions = ["SS", "SE", "SW", "NN", "NE", "NW"]
                    moved_direction = directions[i]
                    self.survivor_direction_counts[moved_direction] += 1
                    self.survivor_move_history.append(moved_direction)
                    
                    # Update terrain preference (if costs are available)
                    if self.costs and current_survivor_pos in self.costs:
                        cost = self.costs[current_survivor_pos]
                        if cost != float('-inf'):  # Don't count blocked tiles
                            self.survivor_terrain_prefs[moved_direction][cost] += 1
                    
                    # Limit history size
                    if len(self.survivor_move_history) > 20:
                        self.survivor_move_history.pop(0)
                    break
            
            # Update position history
            self.survivor_position_history.append(current_survivor_pos)
            if len(self.survivor_position_history) > 20:
                self.survivor_position_history.pop(0)
                
            # Update last seen data
            self.survivor_last_seen_position = current_survivor_pos
            self.survivor_last_seen_time = time.time()
    
    def predict_survivor_movement_probs(self, current_pos, valid_moves):
        """
        Use Naive Bayes to predict the probabilities of the survivor's next movement.
        Returns a dictionary mapping each possible move to its probability.
        """
        # If we have no history, use uniform distribution
        if not self.survivor_move_history:
            # Equal probability for all valid moves including staying
            num_options = len(valid_moves) + 1  # +1 for staying in place
            stay_prob = 1.0 / num_options
            move_prob = 1.0 / num_options
            
            probs = {current_pos: stay_prob}
            for move in valid_moves:
                if move != current_pos:  # Avoid double counting staying in place
                    probs[move] = move_prob
            return probs
        
        # Calculate prior probabilities based on movement history
        total_moves = sum(self.survivor_direction_counts.values()) + len(self.survivor_direction_counts) * self.laplace_smoothing
        
        # Initialize uniform probabilities first (fallback)
        probs = {}
        
        # Process each possible move
        neighbors = self.map.neighbor_hex(current_pos)
        directions = ["SS", "SE", "SW", "NN", "NE", "NW"]
        
        # First calculate raw probabilities based on direction history
        raw_probs = {}
        for i, neighbor in enumerate(neighbors):
            if neighbor is None or neighbor not in valid_moves:
                continue
                
            direction = directions[i]
            
            # Get direction probability (with Laplace smoothing)
            dir_count = self.survivor_direction_counts[direction] + self.laplace_smoothing
            dir_prob = dir_count / total_moves
            
            # Get terrain preference probability if we have data
            terrain_prob = 1.0
            if self.costs and neighbor in self.costs:
                cost = self.costs[neighbor]
                if cost != float('-inf'):
                    # Calculate how often survivor chose this cost for this direction
                    cost_count = self.survivor_terrain_prefs[direction][cost] + self.laplace_smoothing
                    total_cost_counts = sum(self.survivor_terrain_prefs[direction].values()) + \
                                     len(self.survivor_terrain_prefs[direction]) * self.laplace_smoothing
                    if total_cost_counts > 0:
                        terrain_prob = cost_count / total_cost_counts
            
            # Combined probability using Naive Bayes (direction and terrain are independent features)
            raw_probs[neighbor] = dir_prob * terrain_prob
        
        # Calculate staying probability - inverse correlation with movement activity
        # More movement history = less likely to stay still
        move_activity = min(0.9, len(self.survivor_move_history) / 20)  # Cap at 90%
        stay_prob = 1.0 - move_activity
        raw_probs[current_pos] = stay_prob
        
        # Normalize probabilities
        total_prob = sum(raw_probs.values())
        if total_prob > 0:
            for pos, prob in raw_probs.items():
                probs[pos] = prob / total_prob
        else:
            # Fallback to uniform if calculations failed
            even_prob = 1.0 / len(raw_probs)
            for pos in raw_probs:
                probs[pos] = even_prob
                
        return probs
    
    def expectimax_decision(self, survivor_hex, visited_hexes, costs):
        """
        Enhanced expectimax approach that accounts for survivor's possible movements.
        - Considers the cost of each path
        - Uses Naive Bayes to predict survivor movement
        - Evaluates multiple possible future states
        - Now includes anti-loop protection
        """
        # Update the survivor model with current observation
        self.update_survivor_model(survivor_hex)
        
        # Increase exploration boost over time when no new tiles visited
        current_time = time.time()
        time_since_last_exploration = current_time - self.last_exploration_time
        
        # If we're getting stuck in loops, increase the exploration boost
        if time_since_last_exploration > 3.0:  # 5 seconds without finding new tiles
            self.exploration_boost = min(3.0, self.exploration_boost + 0.5)
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
        Recursive helper function for expectimax calculation with Naive Bayes probabilities.
        
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
        
        # Survivor's turn (chance node) - Now using Naive Bayes probabilities
        else:
            # Get possible moves for survivor
            neighbors = self.map.neighbor_hex(survivor_pos)
            valid_moves = [n for n in neighbors if n is not None and costs[n] != float('-inf')]
            
            if not valid_moves:
                valid_moves = [survivor_pos]  # Survivor stays in place if no valid moves
            
            # Calculate movement probabilities using Naive Bayes
            valid_moves.append(survivor_pos)  # Include staying in place as an option
            move_probs = self.predict_survivor_movement_probs(survivor_pos, valid_moves)
            
            # Calculate expected value across all possible survivor moves
            total_score = 0
            
            for move, probability in move_probs.items():
                score = self._expectimax_score(rescuer_pos, move, costs, depth + 1, max_depth, visited_hexes)
                total_score += probability * score
            
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
