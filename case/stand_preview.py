"""Concept mesh for a separate tilt stand (bounce base) + scene for render_zbuf.py.  Preview only.
usage: python3 stand_preview.py <out dir> <angle deg> <scene_in.json>"""
import json, math, sys
import numpy as np
OUT, ANG, SCENE = sys.argv[1], float(sys.argv[2]), sys.argv[3]
I = json.load(open('case_inputs.json'))
bx0, by0, bx1, by1 = I['board']
CL, WALL = 0.3, 3.3   # preview only (build_case: 3.6 sides/rear, 4.6 front)
X0, Y0, X1, Y1 = bx0 - CL - WALL, by0 - CL - WALL, bx1 + CL + WALL, by1 + CL + WALL   # keyboard outline (layout)
R = 10.0                                   # = build_case CORNER_R
t = math.tan(math.radians(ANG))
H_FRONT, LIP, RIM_W, GAP = 2.0, 1.6, 2.2, 0.4


def rrect(x0, y0, x1, y1, r, n=10):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return [(x, -y) for x, y in pts]          # to STL coords (Y up = towards the rear)


YF = -Y1                                       # front edge of the keyboard in STL coords


def ztop(Y):                                  # sloped surface the keyboard sits on
    return H_FRONT + (Y - YF) * t


tris = []


def quad(a, b, c, d):
    tris.extend([[a, b, c], [a, c, d]])


outer = rrect(X0 - GAP - RIM_W, Y0 - GAP - RIM_W, X1 + GAP + RIM_W, Y1 + GAP + RIM_W, R + GAP + RIM_W)
inner = rrect(X0 - GAP, Y0 - GAP, X1 + GAP, Y1 + GAP, R + GAP)
cxy = (sum(p[0] for p in outer) / len(outer), sum(p[1] for p in outer) / len(outer))
n = len(outer)
for i in range(n):
    (ax, ay), (bx, by) = outer[i], outer[(i + 1) % n]
    (ix, iy), (jx, jy) = inner[i], inner[(i + 1) % n]
    # bottom
    tris.append([(cxy[0], cxy[1], 0), (bx, by, 0), (ax, ay, 0)])
    # outer wall up to rim top
    quad((ax, ay, 0), (bx, by, 0), (bx, by, ztop(by) + LIP), (ax, ay, ztop(ay) + LIP))
    # rim top
    quad((ax, ay, ztop(ay) + LIP), (bx, by, ztop(by) + LIP), (jx, jy, ztop(jy) + LIP), (ix, iy, ztop(iy) + LIP))
    # rim inner wall down to the seat
    quad((ix, iy, ztop(iy) + LIP), (jx, jy, ztop(jy) + LIP), (jx, jy, ztop(jy)), (ix, iy, ztop(iy)))
    # seat (sloped)
    ci = (sum(p[0] for p in inner) / n, sum(p[1] for p in inner) / n)
    tris.append([(ix, iy, ztop(iy)), (jx, jy, ztop(jy)), (ci[0], ci[1], ztop(ci[1]))])
T = np.array(tris, dtype='<f4')
rec = np.zeros(len(T), dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
rec['v'] = T
open(f'{OUT}/stand.stl', 'wb').write(b'\0' * 80 + np.uint32(len(T)).tobytes() + rec.tobytes())
print('stand rear height %.1f mm, front %.1f mm' % (ztop(-Y0 + GAP + RIM_W) + LIP, H_FRONT + LIP))
# scene: keyboard rotated by ANG about the front-bottom edge, sitting on the seat
S = json.load(open(SCENE))
a = math.radians(ANG)
for m in S['meshes']:
    m['tilt'] = [ANG, YF, H_FRONT]
S['meshes'].insert(0, {'stl': f'{OUT}/stand.stl', 'color': '#3b3d42', 'gloss': 0.15})
json.dump(S, open(f'{OUT}/scene_stand.json', 'w'))
