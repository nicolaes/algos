import sys
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Union
import queue

def log(*args):
    print(*args, file=sys.stderr, flush=True)

###############################################################
Loc = Tuple[int, int]
ROCK, PAPER, SCISSORS, DEAD = 'ROCK', 'PAPER', 'SCISSORS', 'DEAD'

@dataclass
class Pac:
    id: int
    mine: bool
    x: int = 0
    y: int = 0
    type_id: Union[ROCK, PAPER, SCISSORS, DEAD] = 'DEAD'  # ROCK PAPER SCISSORS
    speed_turns_left: int = 0
    ability_cooldown: int = 0

###############################################################

me: Dict[int, Pac] = {}
they: Dict[int, Pac] = {}

# width: size of the grid
# height: top left corner is (x=0, y=0)
grid = set()
grid_pellets: Dict[Loc, int] = {}
width, height = [int(i) for i in input().split()]
def init_grid():
    for i in range(height):
        row = input()  # one line of the grid: space " " is floor, pound "#" is wall
        for j, map_point in enumerate(row):
            if map_point == ' ':
                loc = (j, i)
                grid.add(loc)
                grid_pellets[loc] = 1


all_pac_locs: Set[Loc] = set()
def init_round():
    # game loop
    all_pac_locs.clear()

    input() # my_score, opponent_score = [int(i) for i in input().split()]

    visible_pac_count = int(input())  # all your pacs and enemy pacs in sight
    for _ in range(visible_pac_count):
        inputs = input().split()
        pac_id = int(inputs[0])  # pac number (unique within a team)
        mine = inputs[1] != "0"  # true if this pac is yours
        x = int(inputs[2])  # position in the grid
        y = int(inputs[3])  # position in the grid
        type_id = inputs[4]  # ROCK PAPER SCISSORS DEAD
        speed_turns_left = int(inputs[5])  # unused in wood leagues
        ability_cooldown = int(inputs[6])  # unused in wood leagues

        loc: Loc = x, y
        all_pac_locs.add(loc)
        grid_pellets[loc] = 0

        pac_dict = me if mine else they
        if type_id == 'DEAD':
            if pac_id in pac_dict:
                del pac_dict[pac_id]
        else:
            if pac_id not in pac_dict:
                pac_dict[pac_id] = Pac(pac_id, mine)
            pac = pac_dict[pac_id]

            pac.x = x
            pac.y = y
            pac.type_id = type_id
            pac.ability_cooldown = ability_cooldown
            pac.speed_turns_left = speed_turns_left
    
    visible_pellet_count = int(input())  # all pellets in sight
    for i in range(visible_pellet_count):
        # value: amount of points this pellet is worth
        x, y, value = [int(j) for j in input().split()]
        loc = x, y
        grid_pellets[loc] = value * 2
    

###############################################################

def on_edge(x, y):
    return x == 0 or y == 0 or x == (width - 1) or y == (height - 1)

def apply_direction(x, y, dir):
    dx, dy = dir
    return (x + dx) % width, (y + dy) % height

def best_direction_for_steps(x: int, y: int, steps: int) -> Loc:
    global grid, grid_pellets

    # Find most points in {steps} steps
    directions: Dict[str, Loc] = {
        '<': (-1, 0), 
        '>': (1, 0), 
        '^': (0, -1), 
        'v': (0, 1)
    }

    loc = x, y
    frontier: queue.PriorityQueue[Tuple[float, Loc]] = queue.PriorityQueue()
    frontier.put((0, loc))

    points_so_far: Dict[Loc, int] = {}
    points_so_far[loc] = 0
    path_to_loc: Dict[Loc, str] = {}
    path_to_loc[loc] = ''

    first_step = True
    best_path: str = ''
    while not frontier.empty():
        _, current_loc = frontier.get()
        cx, cy = current_loc

        step_count = len(path_to_loc[current_loc])
        if step_count >= steps:
            best_path = path_to_loc[current_loc]
            break

        for next_step in directions:
            next_loc: Loc = apply_direction(cx, cy, directions[next_step])
            if next_loc not in grid: continue
        
            # Avoid collisions on first step
            if step_count < 2 and next_loc in all_pac_locs and next_loc != loc:
                continue

            new_points: int = points_so_far[current_loc]
            # If we didn't pass through here before (and ate the points)
            if next_loc not in points_so_far:
                new_points -= grid_pellets[next_loc]

            # if new route or with more points
            if next_loc not in points_so_far or new_points < points_so_far[next_loc]:
                points_so_far[next_loc] = new_points
                path_to_loc[next_loc] = path_to_loc[current_loc] + next_step
                
                priority = new_points + len(path_to_loc[next_loc]) / (steps + 1)
                frontier.put((priority, next_loc))
        
        if first_step:
            first_step = False
    
    if len(best_path) == 0:
        return loc
    
    for dir in best_path[:1]:
        dx, dy = directions[dir]
        x = (x + dx) % width
        y = (y + dy) % height
    return x, y


###############################################################
# Grab the pellets as fast as you can!
init_grid()

# game loop
while True:
    init_round()

    # Write an action using print
    commands: List[str] = []
    for pac_id in me:
        pac = me[pac_id]
        if pac.speed_turns_left == 0 and pac.ability_cooldown == 0:
            commands.append(f"SPEED {pac_id}")
        else:
            tx, ty = best_direction_for_steps(pac.x, pac.y, 100)
            commands.append(f"MOVE {pac_id} {tx} {ty}")

    print('|'.join(commands))
    
