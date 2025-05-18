import numpy as np
from src.entities.mock_entity import *

class Survivor(Entity):
    def __init__(self, map):
        super().__init__(map)

        # ! THIS IS ONLY FOR TESTING, DEFAUT SPAWN POSITION IS BASED ON SEED
        self.hexEntity = map.hexes[Hex(-12,6,6)]
        self.position = self.entity_position()

        self.stamina = 100
        self.hunger = 0
        self.stats = [self.points, self.stamina, self.hunger]
        self.sane = True # Well, for now.
        
        # Override sprite image for survivor
        sprite_img = pygame.image.load("sar-game-8-field-of-view/assets/Females/F_10.png").convert_alpha()
        self.sprite_sheet = SpriteSheet(sprite_img)
        self.animation_list = []
        self.animation_steps = 3  # Using only 3 front-facing frames
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.animation_cooldown = 200
        
        # Initialize animation frames - use the front-facing frames only
        for x in range(self.animation_steps):
            self.animation_list.append(self.sprite_sheet.get_img(x, 17, 17, 2.75, (0, 0, 0)))

    def eat(self, vl):
        self.stats = [self.stats[0], max(self.hunger - vl, 0), min(self.stamina + ((1/3) * vl), 100)]
        
    def decide(self):
        """Implements random movement decision logic based on sanity level"""
        if not self.sane:
            # When insane, picks completely random direction
            random_dir_index = np.random.randint(0, 6)
            directions = ["NN", "NE", "NW", "SS", "SE", "SW"]
            random_dir = directions[random_dir_index]
            return self.move(random_dir)
        else:
            # When sane, will implement more advanced behavior later with minimax
            return None
    
    def move(self, move_dir):
        """Override the parent move method to track stamina and hunger"""
        result = super().move(move_dir)
        if result is not None:
            # Randomly decrease stamina and increase hunger when moving
            if np.random.random() < 0.3:  # 30% chance
                self.stamina = max(0, self.stamina - 2)
                self.hunger = min(100, self.hunger + 1)
                
            # If stamina reaches 0 or hunger reaches 100, survivor goes insane
            if self.stamina <= 0 or self.hunger >= 100:
                self.sane = False
        
        return result
    
    def __repr__(self):
        return f"Entity={type(self).__name__}. Health={self.points}, Stamina={self.stamina}, Hunger={self.hunger}, Sane={self.sane}."
