# Custom input source
from collections import deque

current_filename = None
input_stack = deque()
def init_data(filename):
    global input_stack, current_filename
    current_filename = filename
    with open(filename) as file_object:
        input_stack = deque(file_object.read().split('\n'))
    return

def input():
    global input_stack, current_filename
    if not input_stack or input_stack[0] == '':
        init_data(current_filename)
        raise Exception('End of input')
    return input_stack.popleft()
