import sys
from dataclasses import dataclass
from collections import deque
import random
from typing import Union
import time

def log(*args):
    print(*args, file=sys.stderr, flush=True)

MAX_TIME = 0.040

ME = 1
OPP = 0
NONE = -1

@dataclass(frozen=True)
class Pos:
    x: int
    y: int
    def __add__(self, other): return Pos(self.x + other.x, self.y + other.y)

@dataclass
class Tile:
    x: int
    y: int
    p: Pos
    scrap_amount: int
    owner: int
    units: int # not yet assigned
    recycler: bool
    can_build: bool
    can_spawn: bool
    in_range_of_recycler: bool

XY = Union[Tile, Pos]

RECYCLER_AREA = [(0,0),(-1,0),(1,0),(0,-1),(0,1)]
MOVES = [Pos(x, y) for x,y in [(-1,0),(1,0),(0,-1),(0,1)]]

def dist(ax, ay, bx, by):
    return abs(ax - bx) + abs(ay - by)

def sq_dist(ax, ay, bx, by):
    return (ax - bx)**2 + (ay - by)**2

def tile_richness(t: Tile):
    r = 0
    for px, py in RECYCLER_AREA:
        p = Pos(t.x+px, t.y+py)
        if p in grid:
            t = grid[p]
            r += t.scrap_amount // 2 if t.in_range_of_recycler else t.scrap_amount
    return r

def unit_count(tiles: list[Tile]):
    return sum(t.units for t in tiles)

def closest_tiles_to(l: list[Tile], p: XY):
    # by_steps = {Pos(t.x, t.y): (t, s) for t in l if (s:=steps_to(t, p)) < W*H}
    by_steps = {Pos(t.x, t.y): (t, s) for t in l if (s:=sq_dist(t.x, t.y, p.x, p.y)) < W*H}
    while by_steps:
        closest = min(by_steps, key=lambda p: by_steps[p][1])
        yield by_steps[closest][0]
        del by_steps[closest]

def steps_to(f: XY, t: XY, grid): # BFS
    queue = deque[tuple[int, XY]]([(0, f)])
    visited: set[Pos] = {Pos(f.x, f.y)}
    while len(queue) > 0:
        step_count, n = queue.popleft()
        if n==t: return step_count
        
        for m in MOVES:
            nxt_pos = Pos(n.x + m.x, n.y + m.y)
            if nxt_pos not in grid: continue

            nxt = grid[nxt_pos]
            if nxt_pos not in visited and not nxt.recycler and nxt.scrap_amount > 0:
                visited.add(nxt_pos)
                queue.append((step_count + 1, nxt))
    return W*H

PERF_START = time.perf_counter()
def perf_milestone(s):
    return
    log(s, int((time.perf_counter() - PERF_START)*1000), 'ms')
OVT = lambda: time.perf_counter() - PERF_START >= MAX_TIME

W, H = [int(i) for i in input().split()]

# game loop
first_loop = True
while True:
    grid: dict[Pos, Tile] = {}
    all_tiles: list[Tile] = []

    my_matter, opp_matter = [int(i) for i in input().split()]

    my_recyclers: list[Tile] = []
    opp_recyclers: list[Tile] = []

    for y in range(H):
        for x in range(W):
            # owner: 1 = me, 0 = foe, -1 = neutral
            # recycler, can_build, can_spawn, in_range_of_recycler: 1 = True, 0 = False
            scrap_amount, owner, units, recycler, can_build, can_spawn, in_range_of_recycler = [int(k) for k in input().split()]
            if scrap_amount == 0: continue

            p = Pos(x, y)
            tile = Tile(x, y, p, scrap_amount, owner, units, recycler == 1, can_build == 1, can_spawn == 1, in_range_of_recycler == 1)

            all_tiles.append(tile)
            grid[p] = tile

            # RECYCLERS
            if tile.recycler:
                if tile.owner == ME:
                    my_recyclers.append(tile)
                elif tile.owner == OPP:
                    opp_recyclers.append(tile)
    
    PERF_START = time.perf_counter()

    # FIRST LOOP
    if first_loop:
        all_richest_tiles = sorted(all_tiles, key=tile_richness)
        pass

    # OUTSIDE ISLAND-LOGIC
    recyclers_to_build = len(opp_recyclers) - len(my_recyclers) + 1
    actions = []
        
    # DFS of tiles to reveals islands
    island_id = 0
    island_visited: set[Pos] = set()
    for t in all_tiles:
        if t.p in island_visited: continue
        island_tiles: list[Tile] = [t]; i = 0; island_id += 1
        island_visited.add(t.p)
        while i < len(island_tiles):
            c = island_tiles[i]; i += 1
            for m in MOVES:
                nxt_pos = m+c
                if nxt_pos in island_visited or nxt_pos not in grid: continue
                island_visited.add(nxt_pos)
                island_tiles.append(grid[nxt_pos])

        # ISLAND-BASED OPS
        my_units: list[Tile] = []
        opp_units: list[Tile] = []
        opp_tiles: list[Tile] = []
        opp_empty: list[Tile] = []
        my_tiles: list[Tile] = []
        neutral_tiles: list[Tile] = []

        for tile in island_tiles:
            # NON-RECYCLERS
            if tile.owner == ME:
                my_tiles.append(tile)
                if tile.units > 0:
                    my_units.append(tile)
            elif tile.owner == OPP:
                opp_tiles.append(tile)
                if tile.units > 0:
                    opp_units.append(tile)
                else:
                    opp_empty.append(tile)
            else:
                neutral_tiles.append(tile)
        # log(f'> STARTING ISLAND {island_id} - {len(island_tiles)} tiles')
        

        perf_milestone('NEW RECYCLERS')
        new_recyclers = []
        any_opp_in_range = False
        for o in opp_units:
            if next((m for m in my_units if steps_to(m, o, grid) < W*H), None):
                any_opp_in_range = True
                break
        if any_opp_in_range:
            richest_tiles = sorted(my_tiles, key=tile_richness)
            while my_matter >= 10 and recyclers_to_build > 0 and len(richest_tiles):
                my_matter -= 10
                recyclers_to_build -= 1
                new_recyclers.append(richest_tiles.pop())
        

        perf_milestone('NEW ROBOTS')
        robots_to_build = unit_count(opp_units) - unit_count(my_units) + 1
        target_list = opp_units if len(opp_units) > 0 else opp_tiles
        new_robots: dict[Pos, int] = {}
        if len(target_list) > 0:
            ox = sum([u.x for u in target_list]) // len(target_list)
            oy = sum([u.y for u in target_list]) // len(target_list)
            tiles_towards_opp = sorted(my_tiles, key=lambda t: dist(t.x, t.y, ox, oy), reverse=True)
            while my_matter >= 10 and robots_to_build > 0 and len(tiles_towards_opp):
                my_matter -= 10
                robots_to_build -= 1
                t = tiles_towards_opp.pop()
                new_robots[t.p] = new_robots[t.p]+1 if t.p in new_robots else 1


        perf_milestone('EXPANSION ROBOTS')
        border_opp: list[Pos] = []
        border_neutral: list[Pos] = []
        visited = set()
        for t in my_tiles:
            if t.p in visited: continue
            visited.add(t.p)

            near_opp, near_neutral = False, False
            for m in MOVES:
                nbr_p = Pos(t.x + m.x, t.y + m.y)
                if nbr_p in visited or nbr_p not in grid: continue

                nbr = grid[nbr_p]
                if nbr.owner == OPP:
                    near_opp = True
                    break
                elif nbr.owner == NONE:
                    near_neutral = True
                    break
                
            if near_opp: border_opp.append(t.p)
            elif near_neutral: border_neutral.append(t.p)

        while my_matter >= 20 and (border_neutral or border_opp):
            p = random.choice(border_neutral or border_opp)
            my_matter -= 10
            new_robots[p] = new_robots[p]+1 if p in new_robots else 1

        # MUTARILE TALE SI ALE INAMICULUI:
        # OC inamicul captureaza spatiu (cu puterea X)
        # OE captureaza un neutru
        # IE tu capturezi neutru
        # IC tu capturezi oponent
        # N nu e nicio schimbare
        # D robotul decedeaza

        # Tile status
        # tile_status: dict[Pos, str] = {}
        # for u in my_tiles:
        #     f = Pos(u.x, u.y)
        #     status = None
        #     for m in u_moves:
        #         p = Pos(u.x+m.x, u.y+m.y)
        #         if p not in p_grid: continue
                
        #         new_pos = p_grid[p]
        #         if new_pos in opp_tiles:
        #             log('poti captura oponent cu puterea', new_pos.units)
        #         elif new_pos in neutral_tiles:
        #             log('poti captura neutru')

        # MOVEMENT
        movement: list[tuple[Pos, XY, int]] = [] # from/to/dispatch_amount
            

        perf_milestone('ADVANCE')
        for opp_tile in sorted(opp_units, key=lambda t: t.units, reverse=True):
            units_to_counter = opp_tile.units + 1
            for r in closest_tiles_to(my_units, opp_tile): # perf breaker
                if OVT(): break
                while units_to_counter > 0:
                    # Dispatch counters
                    dispatched_amount = min(units_to_counter, r.units)
                    units_to_counter -= dispatched_amount
                    r.units -= dispatched_amount

                    movement.append((r.p, opp_tile, dispatched_amount))

                    if r.units == 0: break
                if units_to_counter == 0: break


        perf_milestone('SCOUT')
        def scout_outwards(f: Tile):
            queue = deque[tuple[int, Tile]]([(0, f)])
            visited: set[Pos] = {Pos(f.x, f.y)}
            crossed_robots: set[Pos] = {Pos(f.x, f.y)}
            
            while len(queue) > 0:
                step_count, n = queue.popleft()
                if n in opp_empty or n in neutral_tiles: return n, crossed_robots
                
                for m in MOVES:
                    nxt_pos = Pos(n.x + m.x, n.y + m.y)
                    if nxt_pos not in grid: continue

                    nxt = grid[nxt_pos]
                    if nxt_pos not in visited and not nxt.recycler and nxt.scrap_amount > 0:
                        visited.add(nxt_pos)
                        if nxt.units > 0 and nxt.owner == ME: crossed_robots.add(nxt_pos)
                        queue.append((step_count + 1, nxt))
            return None, crossed_robots

        for r in my_units:
            if OVT(): break
            if r.units == 0: continue

            # if robots remain, scout
            scout_towards_p, crossed_robots = scout_outwards(r)
            if scout_towards_p:
                movement.append((r.p, scout_towards_p, r.units))
                r.units = 0
            for p in crossed_robots:
                # assign crossed robots to same direction (if any)
                if scout_towards_p:
                    movement.append((p, scout_towards_p, grid[p].units))
                grid[p].units = 0


        perf_milestone('ACTIONS')
        for p in new_robots:
            actions.append('SPAWN {} {} {}'.format(new_robots[p], p.x, p.y))

        for tile in my_tiles:
            if tile.can_build:
                should_build = tile in new_recyclers
                if should_build:
                    actions.append('BUILD {} {}'.format(tile.x, tile.y))

        for r, to_pos, dispatched_amount in movement:
            actions.append('MOVE {} {} {} {} {}'.format(dispatched_amount, r.x, r.y, to_pos.x, to_pos.y))

    print(';'.join(actions) if len(actions) > 0 else 'WAIT')


# TODO
# fix "trying to move null units"
# precompute best recycler spots
# add A* to steps_to
# increase time limit from 40ms
# build > 1 robot for coutering
# reuse Tile objects

# Rank 26.12: 822/1767 silver league
