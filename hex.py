class Center:
    def __init__(self, q=0, r=0):
        self.q, self.r = q, r
    
    def __eq__(self, other):
        if not isinstance(other, Center):
            return NotImplemented
        
        return (self.q, self.r) == (other.q, other.r)
    
    def __iter__(self):
        return iter((self.q,self.r))
    
    def __repr__(self):
        return f"{{q={self.q},r={self.r}}}."

class Hex:
    def __init__(self, x=0, y=0, z=0):
        self.x, self.y, self.z = x, y, z

    def __eq__(self, other):
        if not isinstance(other, Hex):
            return NotImplemented
        return (self.x, self.y, self.z) == (other.x, other.y, other.z)

    def __hash__(self):
        hq = hash(self.x)
        hr = hash(self.y)

        return hq ^ (hr + 0x9e3779b9 + ((hq << 6) & 0xFFFFFFFFFFFFFFFF) + (hq >> 2))
    
    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def __repr__(self):
        return f"{{x={self.x}, y={self.y}, z={self.z}}}::({hash(self):#x})"