class Center:
    def __init__(self, q=0, r=0):
        self.q, self.r = q, r

class Hex:
    def __init__(self, x=0, y=0, z=0):
        self.x, self.y, self.z = x, y, z

    def __hash__(self):
        hq = hash(self.x)
        hr = hash(self.y)

        return hq ^ (hr + 0x9e3779b9 + ((hq << 6) & 0xFFFFFFFFFFFFFFFF) + (hq >> 2))
