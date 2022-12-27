from __future__ import annotations
import dataclasses
import sys
from collections import deque
from typing import Dict, List, Set, Tuple, Union
from dataclasses import dataclass, field
import datetime
from queue import PriorityQueue

def log(*args):
    print(*args, file=sys.stderr, flush=True)

# REMOVE IN CODINGAME
input_stack = deque()
with open('few_clones.txt') as file_object:
    input_stack = deque(file_object.read().split('\n'))
input = lambda: input_stack.popleft()
# REMOVE IN CODINGAME

# nb_floors: number of floors
# width: width of the area
# nb_rounds: maximum number of rounds
# exit_floor: floor on which the exit is found
# exit_pos: position of the exit on its floor
# nb_total_clones: number of generated clones
# nb_additional_elevators: number of additional elevators that you can build
# nb_elevators: number of elevators
nb_floors, width, nb_rounds, exit_floor, exit_pos, nb_total_clones, nb_additional_elevators, nb_elevators = [int(i) for i in input().split()]
nb_floors = exit_floor + 1

# exit floors
exits: Dict[int, Set[int]] = {}
for i in range(nb_floors):
    exits[i] = set()
exits[exit_floor].add(exit_pos)

# elevators
for i in range(nb_elevators):
    # elevator_floor: floor on which this elevator is found
    # elevator_pos: position of the elevator on its floor
    elevator_floor, elevator_pos = [int(j) for j in input().split()]
    exits[elevator_floor].add(elevator_pos)

# how many elevators left to optimize the path
nb_spare_elevators = \
    nb_additional_elevators - sum([not exits[f] for f in range(nb_floors - 1)])

######################################################################################
# Optimize map

# search neighbors
neighbor_el_pos_cache = {}
def neighbor_el_pos(
    floor: int, pos: int
) -> Tuple[Union[int, None], Union[int, None]]:
    loc = floor, pos
    if loc in neighbor_el_pos_cache:
        return neighbor_el_pos_cache[loc]

    to_left, to_right = None, None
    for el_pos in sorted(list(exits[floor])):
        if el_pos > pos:
            to_right = el_pos
            break
        if el_pos < pos:
            to_left = el_pos

    neighbor = to_left, to_right

    neighbor_el_pos_cache[loc] = neighbor
    return neighbor

# allowed limits for each floor
# force elevators for the narrow upper intervals
forced_elevators: Dict[int, int] = {}
allowed_limits: Dict[int, Tuple[int, int]] = {}
l_limit = r_limit = exit_pos # start by allowing any pos, with exit being required
for f in range(nb_floors - 1, -1, -1):
    prev_l, prev_r = l_limit, r_limit

    # look for neighbors of required_pos
    # allow first layer of wrapping elevators (drones can't jump over elevators)
    l_limit, next_after_left = neighbor_el_pos(f, l_limit)
    pref_before_right, r_limit = neighbor_el_pos(f, r_limit)

    # if no elevators in the previous interval
    if f != nb_floors - 1 and nb_spare_elevators > 0 and (
        next_after_left and prev_r and next_after_left > prev_r or
        pref_before_right and prev_l and pref_before_right < prev_l
    ):
        forced_elevators[f] = exit_pos
        nb_spare_elevators -= 1


    if l_limit is None:
        l_limit = 0
    if r_limit is None:
        r_limit = width - 1
        if l_limit == 0: break # stop imposing limits
    
    allowed_limits[f] = l_limit, r_limit

# List of elevators including forced ones
exits_incl_forced = {f: elevators.copy() for f, elevators in exits.items()}
for f in forced_elevators:
    exits_incl_forced[f].add(forced_elevators[f])
    
# log('forced_elevators', forced_elevators)
# log('allowed_limits', allowed_limits)

###################################################################################### 

CLONE_COST = 3
Loc = Tuple[int, int] # floor / pos
LocWParent = Tuple[int, int, bool, Union[Tuple, None]]

@dataclass(order=True)
class KeyPos:
    cost: int = field(compare=False) # rounds to go up through this ELEVATOR
    priority: int
    floor: int = field(compare=False) # floor elevator is on
    pos: int = field(compare=False)
    goes_right: bool = field(compare=False) # clone is going right when reaching this
    parent: None = field(default = None, compare = False)
    spare_elevators: int = field(default = nb_spare_elevators, compare = False)
    clones_remaining: int = field(default = nb_total_clones, compare = False)

### KeyPos builders vvv

def go_to_elevator(crt: KeyPos, next_pos: int, using_spare_el = False):
    nxt = dataclasses.replace(crt)
    nxt.parent = crt

    # Position and orientation
    nxt.floor += 1
    nxt.pos = next_pos
    if nxt.pos != crt.pos:
        nxt.goes_right = (nxt.pos > crt.pos)

    # Cost and priority
    nxt.cost += cost_to_gate(crt, next_pos)
    if nxt.goes_right != crt.goes_right:
        nxt.cost += CLONE_COST
    nxt.priority = nxt.cost + dist_to_exit(crt, nxt.pos)

    # Game state
    if nxt.goes_right != crt.goes_right:
        nxt.clones_remaining -= 1

    # New elevator
    if nxt.pos not in exits:
        # Cost and priority
        nxt.cost += CLONE_COST
        nxt.priority += CLONE_COST
        
        # Game state
        nxt.clones_remaining -= 1
        if using_spare_el: nxt.spare_elevators -= 1
    
    return nxt

### KeyPos builders ^^^

def is_elevator_disallowed(floor: int, pos: int, goes_right: bool):
    return floor + 1 in allowed_limits and (
        pos <= allowed_limits[floor + 1][0] or 
        pos >= allowed_limits[floor + 1][1]
    )

def cost_to_gate(crt: KeyPos, next_pos: int):
    return abs(next_pos - crt.pos) + 1 #+ (nb_floors - crt.floor) + abs(next_pos - exit_pos)

def dist_to_exit(crt: KeyPos, next_pos: int):
    return (nb_floors - crt.floor) + abs(next_pos - exit_pos)

# plan 1: search fastest path; if no elevator ignore it
# (one will be build just above best one)
def bfs_a_star(init_floor: int, init_pos: int, init_right: bool):
    root = KeyPos(0, 0, init_floor - 1, init_pos, True)

    q: PriorityQueue[KeyPos] = PriorityQueue()
    q.put(root)

    visited = set()

    while not q.empty():
        crt = q.get()

        if is_elevator_disallowed(crt.floor, crt.pos, crt.goes_right):
            continue
        if crt.clones_remaining < 0: continue
        # if crt.cost > nb_rounds: continue

        # visit = (crt.floor, crt.pos, crt.goes_right)
        # if visit in visited:
        #     log(visit, crt)
        # visited.add(visit)

    
        if crt.floor == exit_floor and crt.pos == exit_pos:
            elevator_chain: Dict[int, int] = {}
            while crt is not None:
                elevator_chain[crt.floor] = crt.pos
                crt = crt.parent

            log('exit', crt.cost)
            log('elevator_chain', elevator_chain)
            return None

            return elevator_chain

        next_floor = crt.floor + 1
        if next_floor >= nb_floors: continue

        # Next level options
        next_neighbors = neighbor_el_pos(next_floor, crt.pos)
        if crt.pos in exits[next_floor]:
            # elevator exactly above
            # can only reach neighbor when changing direction
            if crt.goes_right:
                next_neighbors = next_neighbors[0], crt.pos
            else:
                next_neighbors = crt.pos, next_neighbors[1]

        # forced elevator
        if next_floor in forced_elevators:
            if forced_elevators[next_floor] not in next_neighbors:
                continue

            q.put(go_to_elevator(crt, forced_elevators[next_floor]))
            continue

        # search through neighbors
        elevator_found = False
        for next_pos in next_neighbors:
            if next_pos is None: continue
            
            elevator_found = True
            q.put(go_to_elevator(crt, next_pos))
        
        # Try with a new elevator: forced, empty floor or to optimize
        if not elevator_found: # empty floor
            q.put(go_to_elevator(crt, crt.pos))
            pass
            
        # for path optimization
        elif crt.spare_elevators > 0:
            if crt.floor < nb_floors - 2:
                # only do this when 2+ more levels up
                two_levels_above = exits_incl_forced[next_floor + 1]
                
                # log(next_floor, crt.pos, '->', *next_neighbors)
                l_limit, r_limit = next_neighbors
                if l_limit is None: l_limit = -1
                if r_limit is None: r_limit = width

                for pos in two_levels_above:
                    if pos > l_limit and pos < r_limit and pos != crt.pos:
                        q.put(go_to_elevator(crt, pos - 1, True))
                        q.put(go_to_elevator(crt, pos, True))
                        q.put(go_to_elevator(crt, pos + 1, True))
            
            q.put(go_to_elevator(crt, crt.pos, True))

# issue: there is a limit of clones to use for direction switches
# plan 2: A* + add more extra-elevator options

######################################################################################

# game loop
blocked_first = False
optimal_exits = None
first_run = True
while True:
    inputs = input().split()
    clone_floor = int(inputs[0])  # floor of the leading clone
    clone_pos = int(inputs[1])  # position of the leading clone on its floor
    direction = inputs[2]  # direction of the leading clone: LEFT or RIGHT

    # log(clone_floor, clone_pos, direction)

    # No clone yet
    if direction == 'NONE':
        print('WAIT')
        continue

    # search best run
    if first_run:
        optimal_exits = bfs_a_star(clone_floor, clone_pos, direction == 'RIGHT')
        # log('optimal_exits', optimal_exits)
        first_run = False
    if not optimal_exits:
        break

    # No elevator
    if (
        optimal_exits[clone_floor] not in exits[clone_floor] and
        optimal_exits[clone_floor] == clone_pos
    ):
        print('ELEVATOR')
        exits[clone_floor].add(clone_pos)
        continue

    is_dir_correct = False
    exit_dir = \
        'LEFT' if optimal_exits[clone_floor] <= clone_pos else 'RIGHT'
    is_dir_correct = (
        exit_dir == direction or
        clone_pos == optimal_exits[clone_floor]
    )
    
    # Write an action using print
    print('WAIT' if is_dir_correct else 'BLOCK')
