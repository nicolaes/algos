import sys
import math
from dataclasses import dataclass
from typing import Tuple

# Convert neutral units and attack enemy ones
dirs = [(-1,0),(1,0),(0,-1),(0,1)]
grid = fixed_grid = {}
RANGE = 6
my_id = int(input())  # 0 - you are the first player, 1 - you are the second player
W, H = [int(i) for i in input().split()]
for i in range(H):
    for j, c in enumerate(input()):
        loc = j, i
        fixed_grid[loc] = c

@dataclass
class Unit:
    id: int
    x: int
    y: int
    loc: Tuple[int, int]
    friend: bool
    enemy: bool
    neutral: bool
    mob: bool # not leader
    hp: int
mock_unit = Unit(0,0,0,(0,0),False,False,False,False,0)

def range_to(l1, l2):
    x1, y1 = l1
    x2, y2 = l2
    return abs(x2 - x1) + abs(y2 - y1)

def moves_of(loc):
    x, y = loc
    for dx, dy in dirs:
        target = x + dx, y + dy
        if target in grid and grid[target] == '.': yield target


# game loop
while True:
    units = {}; grid = fixed_grid.copy()
    my_lead = mock_unit; their_lead = mock_unit; my_mobs = []; their_mobs = []
    for i in range(int(input())):
        unit_id, unit_type, hp, x, y, owner = [int(j) for j in input().split()]
        unit = Unit(id=unit_id, mob=unit_type==0, x=x, y=y, loc=(x,y), friend=owner==my_id, enemy=owner==(1-my_id), neutral=owner==2, hp=hp)
        if not unit.mob:
            if unit.friend: my_lead = unit
            else: their_lead = unit
        else:
            if unit.friend: my_mobs.append(unit)
            else: their_mobs.append(unit)
        grid[unit.loc] = unit_id
        units[unit_id] = unit

    priorities = []

    for m in their_mobs:
        # 1 Defend leader
        range_to_lead = range_to(my_lead.loc, m.loc)
        if range_to_lead < RANGE:
            run_to = max(moves_of(my_lead.loc), lambda loc: range_to(loc, m.loc))
            priorities.append((10 - range_to_lead, f"{my_lead.id} MOVE {my_lead.x} {my_lead.y}"))
    
    for m in my_mobs:
        # 2 Attack enemy leader
        range_to_lead = range_to(their_lead.loc, m.loc)

    

    # WAIT | unitId MOVE x y | unitId SHOOT target| unitId CONVERT target
    print("WAIT")
