import sys


def log(*args):
    print(*args, file=sys.stderr, flush=True)


input_list = []; orig_input = input
def input(): input_list.append(orig_input()); return input_list[-1]


for i in input_list: log(i)
