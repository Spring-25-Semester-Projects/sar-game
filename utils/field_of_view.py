import numpy as np
from src.hex import Hex, Center
from src.map import Map
from config import SEGEMENT

class Line:
    def __init__(self, v0 : Hex = Hex(), *args : Hex):
       self.v0 = v0
       self.vertices = args
    
    def __iter__(self):
        yield self.v0
        yield from self.vertices

class Chain:
    def __init__(self, c0 : Line, *args : Line):
        self.c0 = c0
        self.lines = args
    
    def __iter__(self):
        yield self.c0
        yield from self.lines

def calculate_angle(p1, p2):

    return np.arctan2(np.linalg.norm(np.cross(p1, p2)), np.dot(p1,p2)) # ? arctan(||p1 x p2||/(p1 · p2)) ± pi

def ReportReflexVertex(chain : Chain):
    reflexVertices = []

    for line in chain:

        line = np.array([[*h] for h in list(line)])
        
        for i in range(len(line)):
            v1 = line[i-1] - line[i]
            v2 = line[(i+1) % len(line)] - line[i]
            
            if calculate_angle(v1,v2) >= (np.pi/2):
                reflexVertices.append(line[i])
        
    return reflexVertices

def B_linecast(p : Hex, Q: Hex, map : Map, costs, limit=-1):
    pcenter = Center(p.x,p.z)
    Qcenter = Center(Q.x, Q.z)

    dcenter = np.array([abs(Qcenter.q - pcenter.q), abs(Qcenter.r - pcenter.r)])
    step = np.array([+1 if Qcenter.q > pcenter.q else -1 if Qcenter.q < pcenter.q else 0, +1 if Qcenter.r > pcenter.r else -1 if Qcenter.r < pcenter.r else 0])

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
            
    p1,p2 = pcenter.q,pcenter.r
    path = []

        # Special case: purely horizontal line
    if dcenter[1] == 0:
        for q in range(pcenter.q + step[0], Qcenter.q + step[0], step[0]):
            h = Hex(q, pcenter.r, -q - pcenter.r)
            if limit >= 0 and map.hex_distance(p, h) > limit:
                break
            if not map.hexes.get(h):
                break
            if costs[h] == float('inf'):
                continue
            path.append(h)
        return path

    # Special case: purely vertical line
    if dcenter[0] == 0:
        for r in range(pcenter.r + step[1], Qcenter.r + step[1], step[1]):
            h = Hex(pcenter.q, r, -pcenter.q - r)
            if limit >= 0 and map.hex_distance(p, h) > limit:
                break
            if not map.hexes.get(h):
                break
            if costs[h] == float('inf'):
                continue
            path.append(h)
        return path
            
    for i in range(steps):
        p1,p2 = primary_step(p1,p2)

        if dcenter[1] == 0:
            for q in range(pcenter.q + step[0], Qcenter.q + step[0], step[0]):
                h = Hex(q, pcenter.r, -q - pcenter.r)
                if limit >= 0 and map.hex_distance(p, h) > limit:
                    break
                if not map.hexes.get(h):
                    break
                if costs[h] == float('inf'):
                    continue

                path.append(h)

    # Special case: purely vertical line
        if dcenter[0] == 0:
            for r in range(pcenter.r + step[1], Qcenter.r + step[1], step[1]):
                h = Hex(pcenter.q, r, -pcenter.q - r)
                if limit >= 0 and map.hex_distance(p, h) > limit:
                    break
                if not map.hexes.get(h):
                    break
                if costs[h] == float('inf'):
                    continue
                
                path.append(h)
            

        error -= Nerror

        if error < 0:
            p1,p2 = secondary_step(p1,p2)
                    
            error += Perror
                
        h = Hex(p1, p2, -p1-p2)

        if limit >= 0 and map.hex_distance(p,h) > limit:
            break

        if not map.hexes.get(h):
            break

        if costs[h] == float('inf'):
            continue

        path.append(h)
    
    return path

def field_of_view(p: Hex, map: Map, costs, limit=-1):
    visible = {}

    fhorizon = []
    for x in range(map.min_x, map.max_x):
        for z in (map.min_z, map.max_z-1):
            Q = Hex(x, z, -x-z)
            ray = B_linecast(p, Q, map, costs, limit)

            if ray:
                for h in ray:
                    visible[h] = True

                fhorizon.append(ray[-1])
    
    for z in range(map.min_z+1, map.max_z-1):
        for x in (map.min_x, map.max_x-1):
            Q = Hex(x, z, -x-z)
            ray = B_linecast(p, Q, map, costs, limit)

            if ray:
                for h in ray:
                    visible[h] = True

                fhorizon.append(ray[-1])
    
    seen = set()
    horizon = []
    for h in fhorizon:
        if h not in seen:
            seen.add(h)
            horizon.append(h)

    chunks = [horizon[i:i+SEGEMENT] for i in range(0, len(horizon), SEGEMENT)]
    lines = [Line(*chunk) for chunk in chunks if len(chunk) > 1]
    
    chain = Chain(lines[0], *lines[1:]) if lines else Chain(Line(p))
    
    reflex_vertices = ReportReflexVertex(chain)

    for Q in reflex_vertices:
        ray = B_linecast(p, Hex(Q[0],Q[1],-Q[1]-Q[0]), map, costs, limit)
        if ray:
            for h in ray:
                visible[h] = True

    return visible