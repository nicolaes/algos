from dataclasses import field
from queue import PriorityQueue
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import matplotlib.pyplot as plt

cost_history = []

flatten = lambda a: [c for l in a for c in l]
DIRS = {'L':(-1,0),'R':(1,0),'U':(0,-1),'D':(0,1)}
Board = List[int]

def loopover(mixed_up_board: List[List[str]], solved_board: List[List[str]]) -> Optional[List[str]]:
    target_idx = {s: i for i, s in enumerate(flatten(solved_board))}
    a = [target_idx[c] for c in flatten(mixed_up_board)]
    H, W = len(mixed_up_board), len(mixed_up_board[0])
    moves = [f'{d}{i}' for d in 'LR' for i in range(H)] + [f'{d}{i}' for d in 'UD' for i in range(W)]
    lines, cols = [set(range(W*l, W*(l+1))) for l in range(H)], [set(range(c, W*H, W)) for c in range(W)]
    
    @dataclass(order=True)
    class Step:
        cost: int
        board: Board = field(compare=False)
        steps: str = field(compare=False)

    
    signature = lambda bo: ' '.join(map(str, bo))
    target_sig = signature(range(0, W*H))

    # diff = lambda bo: sum([abs((i//W) - (tile//W)) + abs((i%W) - (tile%W)) for i, tile in enumerate(bo)]) # 0.9s solving time
    # diff = lambda bo: 1
    # row_diff ^ 2 + col_diff ^ 2
    # abs(row_diff) + abs(col_diff)
    # daca se misca toata lina / coloana o data: sa masoare cat de diferite sunt liniile coloanele
    # e.g. numarul de elemente lipsa din linie / coloana
    
    diff = lambda bo: sum([len(set(bo[W*l : W*(l+1)]) - lines[l]) for l in range(H)]) + \
            sum([len(set(bo[c : W*H : W]) - cols[c]) for c in range(W)]) # 3.2s solving time
    # diff = lambda bo: sum([a!=b for a,b in zip(bo, range(W*H))])**2
    if signature(a) == target_sig: return []
    
    i = 0

    # A*
    winning_steps = ''
    visited = set()
    q: PriorityQueue[Step] = PriorityQueue()
    q.put(Step(diff(a), a, ''))
    visited.add(signature(a))
    while not q.empty():
        crt = q.get()

        i += 1
        if i % 100 == 0: cost_history.append(crt.cost)
        if i > 200000:
            print(len(visited))
            break
        
        for m in moves:
            # Do the move
            next_bo = crt.board.copy()
            move(next_bo, m, W, H)

            # Stop if place already visited
            next_sig = signature(next_bo)
            if next_sig in visited: continue
            
            # Diff to target board
            next_diff = diff(next_bo)
            next_steps = crt.steps + m
            if next_diff == 0:
                winning_steps = next_steps
                q = PriorityQueue()
                break
            
            # Next step
            q.put(Step(
                len(next_steps) // 2 + next_diff,
                next_bo,
                next_steps
            ))
            visited.add(next_sig)

    res = [winning_steps[i:i+2] for i in range(0, len(winning_steps), 2)]
    return res

def move(a: Board, m, W, H):
    ds, ns = m; n = int(ns)

    # Ln = range(W*n, W*(n+1)-1, 1)
    # Rn = range(W*(n+1)-1, W*n-1, -1)
    # Un = range(n, W*(H-1)+n, W)
    # Dn = range(W*(H-1)+n, n, -W)
    if ds in 'LR': start, end, step = W*n, W*(n+1)-1, 1
    if ds in 'UD': start, end, step = n, W*(H-1)+n, W
    if ds in 'RD': start, end, step = end, start, -step
    for i in range(start, end, step): a[i], a[i+step] = a[i+step], a[i]

def pretty(a):
    for i in range(H): print(a[W*i:W*(i+1)])

def check(a_init: List[List[str]], b_init: List[List[str]], moves: List[str]):
    H, W = len(a_init), len(a_init[0])
    a, b = map(flatten, [a_init, b_init])

    # print(pretty(a))
    # for m in moves: move(a, m, W, H); print(pretty(a))
    
    return sum([ai!=bi for ai, bi in zip(a, b)]) == 0

from cw_test import test
def run_test(start, end, unsolvable):
    def board(str):
        return [list(row) for row in str.split('\n')]
    moves = loopover(board(start), board(end))
    print('moves', moves)
    if unsolvable:
        test.assert_equals(moves, None, 'Unsolvable configuration')
    else:
        test.assert_equals(check(board(start), board(end), moves), True)

# run_test('12\n34', '12\n34',  False)
# run_test('42\n31', '12\n34', False)
# run_test('425\n631', '123\n456', False)
# run_test('012\n345\n678', '012\n345\n678', False)
# run_test('120\n345\n678', '012\n345\n678', False)
# run_test('210\n345\n678', '012\n345\n678', False)
# run_test('ACDBE\nFGHIJ\nKLMNO\nPQRST', 'ABCDE\nFGHIJ\nKLMNO\nPQRST', False)
run_test('ACDBE\nFGHIJ\nKLMNO\nPQRST\nUVWXY', 'ABCDE\nFGHIJ\nKLMNO\nPQRST\nUVWXY', False)
# run_test('ABCDE\nKGHIJ\nPLMNO\nFQRST\nUVWXY', 'ABCDE\nFGHIJ\nKLMNO\nPQRST\nUVWXY', False)
# run_test('CWMFJ\nORDBA\nNKGLY\nPHSVE\nXTQUI', 'ABCDE\nFGHIJ\nKLMNO\nPQRST\nUVWXY', False)
# run_test('WCMDJ\nORFBA\nKNGLY\nPHVSE\nTXQUI', 'ABCDE\nFGHIJ\nKLMNO\nPQRST\nUVWXY', True)
# run_test('WCMDJ0\nORFBA1\nKNGLY2\nPHVSE3\nTXQUI4\nZ56789', 'ABCDEF\nGHIJKL\nMNOPQR\nSTUVWX\nYZ0123\n456789', False)
