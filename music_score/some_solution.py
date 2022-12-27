import re

(w, h), img_cols = map(int, input().split()), input().split()
img_cols = ''.join(c*int(n) for c,n in zip(img_cols[::2], img_cols[1::2]))
img_cols = [''.join(img_cols[x::w]) for x in range(w)]

STAFF = re.compile('W(B+?)B?W')
staff, notes = [], []

# recognize stuff and notes
for col_index, column in enumerate(img_cols):
    line_spans = (m.span(1) for m in STAFF.finditer(column))
    if not staff:
        staff = [sum(line_span)/2 for line_span in line_spans]
        if staff:
            note_spacing = (staff[-1]-staff[0])/8
            def full_staff():
                yield staff[0]-note_spacing
                for a,b in zip(staff,staff[1:]):
                    yield from (a, (a+b)/2)
                yield from (staff[-1]+i*note_spacing for i in (0,1,2))
            staff = tuple(full_staff())
    else:
        a,b = max(line_spans, key = lambda x: x[1]-x[0], default=(0,0))
        if b-a > note_spacing*3:
            if notes and notes[-1][0][1]+1==col_index:
                (l,r),(u,d) = notes[-1]
                notes[-1] = (l,col_index), (max(u,a), min(d,b))
            else:
                notes+=[((col_index,col_index), (a,b))]

# notes' generator
def note_by_note():
    for (l,r),(u,d) in notes:
        for x,y,yi in (l-1,u-1,u+1), (r+1,u-1,u+1), (l-1,d+1,d-1), (r+1,d+1,d-1):
            if img_cols[x][y]=='B':
                note = 'GFEDCBAGFEDC'[min(range(len(staff)), key=lambda i: abs(staff[i]-yi))]
                yield note + 'HQ'[img_cols[x][yi]=='B']
                break
    
print(' '.join(note_by_note()))
