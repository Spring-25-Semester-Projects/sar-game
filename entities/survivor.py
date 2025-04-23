import pygame
from pygame.math import Vector2

TILE_SIZE = 32
MAX_RISK  = 100.0

class Tile:
    def __init__(self, x, y, risk=0.0):
        self.pos = (x * TILE_SIZE, y * TILE_SIZE)
        self.risk = risk
        self.neighbors = []

class Grid:
    def __init__(self, width, height, default_risk=0.0):
        self.width  = width
        self.height = height
        self.tiles  = [
            [Tile(x, y, default_risk) for y in range(height)]
            for x in range(width)
        ]
        for x in range(width):
            for y in range(height):
                t = self.tiles[x][y]
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        t.neighbors.append(self.tiles[nx][ny])

    def get_neighbors(self, tile):
        return tile.neighbors

class Survivor(pygame.sprite.Sprite):
    def __init__(self, start_tile, grid, risk_map, speed=100):
        super().__init__()

        raw = pygame.image.load("assets/imgs/survivor.jpeg").convert_alpha()
        raw = pygame.transform.scale(raw, (TILE_SIZE, TILE_SIZE))

        mask_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(
            mask_surf,
            (255, 255, 255, 255),
            (TILE_SIZE // 2, TILE_SIZE // 2),
            TILE_SIZE // 2
        )

        raw.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.image = raw

        self.rect   = self.image.get_rect(topleft=start_tile.pos)
        self.radius = TILE_SIZE // 2
        self.mask   = pygame.mask.from_surface(self.image)

        self.grid         = grid
        self.current_tile = start_tile
        self.speed        = speed
        self.moving       = False
        self.target_pos   = Vector2(self.rect.topleft)
        self.risk_map     = risk_map
        self.risk         = 0.0

    def update(self, dt):
        if self.moving:
            self._move_towards_target(dt)
        else:
            self._choose_next_tile()
        self._update_risk()

    def _move_towards_target(self, dt):
        pos  = Vector2(self.rect.topleft)
        step = self.speed * dt
        new_pos = pos.move_towards(self.target_pos, step)
        self.rect.topleft = (round(new_pos.x), round(new_pos.y))

        if self.rect.topleft == (round(self.target_pos.x), round(self.target_pos.y)):
            self.moving = False
            for tile in self.grid.get_neighbors(self.current_tile) + [self.current_tile]:
                if tile.pos == self.target_pos:
                    self.current_tile = tile
                    break

    def _choose_next_tile(self):
        neighbors = self.grid.get_neighbors(self.current_tile)
        valid     = [t for t in neighbors if t in self.risk_map]
        if not valid:
            return
        next_tile      = min(valid, key=lambda t: self.risk_map.get(t, float('inf')))
        self.target_pos = Vector2(next_tile.pos)
        self.moving     = True

    def _update_risk(self):
        self.risk += self.risk_map.get(self.current_tile, 0.0)
        if self.risk >= MAX_RISK:
            self.kill()


class Weapon:
    def __init__(self, name, damage):
        self.name = name
        self.damage = damage

class ExtendedSurvivor(Survivor):
    def __init__(self, start_tile, grid, risk_map, speed=100, max_health=100, max_stamina=100, stamina_regen=10, vision_radius=3):
        super().__init__(start_tile, grid, risk_map, speed)
        self.max_health = max_health
        self.health = max_health
        self.inventory = []
        self.status_effects = {}
        self.max_stamina = max_stamina
        self.stamina = max_stamina
        self.stamina_regen = stamina_regen
        self.weapon = None
        self.waypoints = []
        self.vision_radius = vision_radius

    def take_damage(self, amount):
        self.health = max(self.health - amount, 0)
        if self.health <= 0:
            self.kill()

    def heal(self, amount):
        self.health = min(self.health + amount, self.max_health)

    def add_item(self, item):
        self.inventory.append(item)

    def remove_item(self, item):
        if item in self.inventory:
            self.inventory.remove(item)

    def equip_weapon(self, weapon):
        self.weapon = weapon

    def attack(self, target):
        if self.weapon and target in self.grid.get_neighbors(self.current_tile):
            try:
                target.take_damage(self.weapon.damage)
            except AttributeError:
                pass  
    def apply_status(self, name, duration, effect_fn):
        self.status_effects[name] = {"duration": duration, "effect": effect_fn}

    def _process_statuses(self, dt):
        to_remove = []
        for name, info in self.status_effects.items():
            info["effect"](self, dt)
            info["duration"] -= dt
            if info["duration"] <= 0:
                to_remove.append(name)
        for name in to_remove:
            del self.status_effects[name]

    def _regen_stamina(self, dt):
        self.stamina = min(self.stamina + self.stamina_regen * dt, self.max_stamina)

    def sprint(self, multiplier, duration):
        orig_speed = self.speed
        def sprint_effect(surv, dt):
            if surv.stamina > 0:
                surv.speed = orig_speed * multiplier
                surv.stamina = max(surv.stamina - dt * (multiplier - 1) * 5, 0)
            else:
                surv.speed = orig_speed
        self.apply_status(f"sprint_{id(self)}", duration, sprint_effect)

    def set_waypoints(self, tile_list):
        self.waypoints = tile_list.copy()

    def _follow_waypoints(self):
        if not self.moving and self.waypoints:
            next_tile = self.waypoints.pop(0)
            self.target_pos = Vector2(next_tile.pos)
            self.moving = True

    def get_visible_tiles(self):
        vis = []
        x0 = self.current_tile.pos[0] // TILE_SIZE
        y0 = self.current_tile.pos[1] // TILE_SIZE
        for x in range(max(0, x0 - self.vision_radius), min(self.grid.width, x0 + self.vision_radius + 1)):
            for y in range(max(0, y0 - self.vision_radius), min(self.grid.height, y0 + self.vision_radius + 1)):
                if abs(x - x0) + abs(y - y0) <= self.vision_radius:
                    vis.append(self.grid.tiles[x][y])
        return vis

    def find_nearest_safe_zone(self):
        safe_tiles = [t for col in self.grid.tiles for t in col if getattr(t, 'safe_zone', False)]
        if not safe_tiles:
            return None
        return min(safe_tiles,
                   key=lambda t: abs(t.pos[0] - self.current_tile.pos[0]) + abs(t.pos[1] - self.current_tile.pos[1]))

    def go_to_safe_zone(self):
        dest = self.find_nearest_safe_zone()
        if dest:
            self.set_waypoints([dest])

    def update(self, dt):
        super().update(dt)
        self._process_statuses(dt)
        self._regen_stamina(dt)
        if self.waypoints:
            self._follow_waypoints()

    def draw(self, surface):

        surface.blit(self.image, self.rect.topleft)

        bar_w, bar_h = TILE_SIZE, 5
        ratio = self.health / self.max_health if self.max_health else 0
        x, y = self.rect.x, self.rect.y - bar_h - 2
        pygame.draw.rect(surface, (100,100,100), (x, y, bar_w, bar_h))
        pygame.draw.rect(surface, (0,255,0), (x, y, bar_w * ratio, bar_h))

        sy = y + bar_h + 1
        s_ratio = self.stamina / self.max_stamina if self.max_stamina else 0
        pygame.draw.rect(surface, (100,100,100), (x, sy, bar_w, bar_h))
        pygame.draw.rect(surface, (0,0,255), (x, sy, bar_w * s_ratio, bar_h))
