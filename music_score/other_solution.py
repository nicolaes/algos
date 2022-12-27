import sys
import math
import numpy as np
from itertools import groupby

w, h = [int(i) for i in input().split()]
image = input()

img = []
it = image.split()
for k,v in zip(it[::2], it[1::2]):
    img += [1 if k=='W' else 0]*int(v)
img = np.array(img).reshape(h, w)

# import matplotlib.pyplot as plt
# plt.imshow(img)

# get start of grid lines
for x in range(w):
    if not img[:,x].all():
        break

linemask = img[:,x]==1

# pixels below lines
lines = []
for y in range(1,h):
    if img[y-1,x]==0 and img[y,x]==1:
        lines.append(y)
        
# add 6th line to lines and mask
lines.append(lines[-1]+lines[2]-lines[1])
linemask[lines[4]:lines[5]] = linemask[lines[2]:lines[3]]


# get note tail positions on x axis
tailwidth = 0
tails = []
v = 0
for c,g in groupby((np.sum(img[lines[0]:lines[4]+1:lines[2]-lines[1]], axis=0)>3)):
    ln = len(list(g))
    if c == False:
        if tailwidth==0:
            tailwidth = ln
        tails.append(v)
    v += ln

notes = ['G', 'F', 'E', 'D', 'C', 'B', 'A', 'G', 'F', 'E', 'D', 'C']
res = []

# loop each note by tail position
for t in tails:
    vert = t-1
    p = np.where((img[:,vert] == 0) & linemask)[0]
    # chech tail direction
    if len(p)==0:
        vert = t+tailwidth
        p = np.where((img[:,vert] == 0) & linemask)[0]
    for i in range(6):
        if lines[i] > p[0]:
            res.append('%s%s' % (notes[2*i+(lines[i] < p[-1])],
                                       ['Q','H'][img[(p[0]+p[-1])//2,vert]]))
            break

print(' '.join(res))