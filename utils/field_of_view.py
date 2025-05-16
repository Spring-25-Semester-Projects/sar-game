import numpy as np
from src.hex import Hex, Center
from src.map import Map

class Line:
    def __init__(self, v0 : Hex = Hex(), *args : Hex):
       self.v0 = v0
       self.vertices = args
    
    def __iter__(self):
        yield self.v0
        yield from self.vertices

def calculate_angle(p1, p2):

    return np.arctan2(np.linalg.norm(np.cross(p1, p2)), np.dot(p1,p2)) # ? arctan(||p1 x p2||/(p1 · p2)) ± pi

def findReflexVertex(line : Line):

    line = np.array([[*h] for h in list(line)])
    
    reflexVertices = []
    
    for i in range(len(line)):
        v1 = line[i-1] - line[i]
        v2 = line[(i+1) % len(line)] - line[i]
        
        if calculate_angle(v1,v2) >= (np.pi/2):
            reflexVertices.append(line[i])
    
    return reflexVertices

# TODO: Algorithm:
# * IF V_k in Line then:
# *     IF isReflexVertex(V_k):
# *         ReportReflexVertex(V_k) // We also have that V_k is to said to be _reflex_ to P

def B_linecast(entity_hex : Hex, map : Map, limit=-1):
    center = Center(entity_hex.x,entity_hex.z)

    def draw_lines(q,r):
        dcenter = np.array([abs(q - center.q),abs(r - center.r)])
        step = np.array([(+1 if q > center.q else -1),(+1 if r > center.r else -1)])

        if dcenter[0] > dcenter[1]:
            error = dcenter[0] / 2
            steps = dcenter[0]
            Nerror = dcenter[1]
            Perror = dcenter[0]

            primary_step = lambda x,z: np.array([x + step[0], z])
            secondary_step = lambda x,z: np.array([x, z + step[1]])
        else:
            error = dcenter[1] / 2
            steps = dcenter[1]
            Nerror = dcenter[0]
            Perror = dcenter[1]

            primary_step   = lambda x,z: np.array([x, z + step[1]])
            secondary_step = lambda x,z: np.array([x + step[0], z])
            
            p1,p2 = center.q,center.r
            for i in range(steps):
                p1,p2 = primary_step(p1,p2)

                error -= Nerror

                if error < 0:
                    p1,p2 = secondary_step(p1,p2)
                    
                    error += Perror

                if limit >= 0 and map.hex_distance(Hex(center.q,0,-center.q), Hex(p1,0,-p1)) > limit:
                    return

    def cast():
        for x in range(map.min_x, map.max_x):
            draw_lines(x, map.min_z)
            draw_lines(x, map.max_z - 1)
            
        for z in range(map.min_z + 1, map.max_z - 1):
            draw_lines(map.min_x, z)
            draw_lines(map.max_x - 1, z)