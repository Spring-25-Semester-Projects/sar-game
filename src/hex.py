class Center:
    def __init__(self, q=0, r=0):
        self.q, self.r = q, r

class Hex:
    def __init__(self, x=0, y=0, z=0, terrain_type='normal'):
        self.x, self.y, self.z = x, y, z
        self.terrain_type = terrain_type
        self.cost = self._get_terrain_cost()
    
    def _get_terrain_cost(self):
        costs = {
            'plain': 1,
            'forest': 3,
            'mountain': 6,
            'water': float('inf')
        }
        return costs.get(self.terrain_type, 1)
    
    def __hash__(self):
        hq = hash(self.x)
        hr = hash(self.y)

        return hq ^ (hr + 0x9e3779b9 + ((hq << 6) & 0xFFFFFFFFFFFFFFFF) + (hq >> 2))
    
    def eq(self, other):
        if not isinstance(other, Hex):
            return False
        return self.x == other.x and self.y == other.y and self.z == other.z