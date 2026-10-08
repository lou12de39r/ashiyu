"""Foam (PORON) template for the bottom plate: fills the pockets between the support islands / ribs, leaves the
LiPo pocket and the battery-lead path free.  Runs in CI after build_case.py.

Method: section the bottom plate just under the PCB, rasterise the material at 0.05 mm, take the free area inside
the board outline minus keep-outs, erode it by CLR, trace the outlines.
Outputs: poron_3mm.dxf (outlines, mm, +y away from the user), poron_3mm_A4.pdf (1:1, A4 landscape), poron_3mm.png
usage: python poron.py <dir with tomtho_mk2_bottom_plate.step + stack.json>
"""
import json, os, sys
import numpy as np
import cadquery as cq
from PIL import Image, ImageDraw
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import contourpy

D = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
I = json.load(open(os.path.join(HERE, 'case_inputs.json')))
S = json.load(open(os.path.join(D, 'stack.json')))
bot = cq.importers.importStep(os.path.join(D, 'tomtho_mk2_bottom_plate.step')).val()
Z = S['Z_PB'] - 0.6
CLR = 0.5          # foam pulled back from every wall / island
RES = 0.05         # mm per pixel

bx0, by0, bx1, by1 = I['board']
W = int((bx1 - bx0) / RES) + 1
H = int((by1 - by0) / RES) + 1


def px(x, y):      # layout mm -> pixel
    return ((x - bx0) / RES, (y - by0) / RES)


img = Image.new('L', (W, H), 0)     # 255 = material
dr = ImageDraw.Draw(img)
sec = bot.intersect(cq.Face.makePlane(1000, 1000, basePnt=(0, 0, Z), dir=(0, 0, 1)))
for f in sec.Faces():
    vs, tris = f.tessellate(0.01)
    P = [px(v.x, -v.y) for v in vs]
    for t in tris:
        dr.polygon([P[i] for i in t], fill=255)
mat = np.array(img) > 0
free = ~mat
# board outline (rounded corners ignored: the rim is solid there anyway) and keep-outs
bat = I['battery']
sl = I['slots'][0]
keep = [(bat[0] - 1.0, bat[1] - 1.0, bat[2] + 1.0, bat[3] + 1.0),
        (bat[2] - 6.0, sl[1] - 1.5, bat[2] - 1.0, bat[1]),
        (bat[2] - 6.0, sl[1] - 1.5, sl[2] + 2.0, sl[3] + 1.5)]
for x0, y0, x1, y1 in keep:
    a, b = px(x0, y0), px(x1, y1)
    free[max(0, int(a[1])):int(b[1]) + 1, max(0, int(a[0])):int(b[0]) + 1] = False
free[:1, :] = free[-1:, :] = False
free[:, :1] = free[:, -1:] = False
r = int(round(CLR / RES))
yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
er = ndimage.binary_erosion(free, structure=(xx ** 2 + yy ** 2) <= r * r)
lab, n = ndimage.label(er)
sizes = ndimage.sum(er, lab, range(1, n + 1)) * RES * RES
keepl = [i + 1 for i, s in enumerate(sizes) if s > 20]           # drop slivers under 20 mm2
er = np.isin(lab, keepl)
print('foam pieces:', len(keepl), 'area cm2: %.1f' % (er.sum() * RES * RES / 100))

gen = contourpy.contour_generator(z=er.astype(float))
lines = gen.lines(0.5)
polys = [np.column_stack([bx0 + l[:, 0] * RES, by0 + l[:, 1] * RES]) for l in lines if len(l) > 8]


def simplify(p, tol=0.03):
    keep = [p[0]]
    for q in p[1:-1]:
        if np.hypot(*(q - keep[-1])) > tol * 4:
            keep.append(q)
    keep.append(p[-1])
    return np.array(keep)


polys = [simplify(p) for p in polys]
# DXF R12, POLYLINE per outline; y flipped so the drawing is seen from above with the rear edge at the top
with open(os.path.join(D, 'poron_3mm.dxf'), 'w') as fh:
    fh.write('0\nSECTION\n2\nENTITIES\n')
    for p in polys:
        fh.write('0\nPOLYLINE\n8\nPORON\n66\n1\n70\n1\n')
        for x, y in p:
            fh.write(f'0\nVERTEX\n8\nPORON\n10\n{x:.3f}\n20\n{-y:.3f}\n')
        fh.write('0\nSEQEND\n')
    fh.write('0\nENDSEC\n0\nEOF\n')

W_MM, H_MM = 297, 210
fig = plt.figure(figsize=(W_MM / 25.4, H_MM / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(-8.5, W_MM - 8.5)
ax.set_ylim(-H_MM + 40, 40)
ax.set_aspect('equal')
ax.axis('off')
from matplotlib.path import Path
from matplotlib.patches import PathPatch
verts, codes = [], []
for p in polys:
    q = np.column_stack([p[:, 0], -p[:, 1]])
    verts += list(q) + [q[0]]
    codes += [Path.MOVETO] + [Path.LINETO] * (len(q) - 1) + [Path.CLOSEPOLY]
ax.add_patch(PathPatch(Path(verts, codes), fc='#f2e6c9', ec='k', lw=0.4))
ax.plot([bx0, bx1, bx1, bx0, bx0], [-by0, -by0, -by1, -by1, -by0], color='#999', lw=0.4, ls='--')
ax.plot([0, 100], [25, 25], 'k-', lw=1.2)
ax.text(50, 27, '100 mm  (print at 100 % / actual size and check with a ruler)', ha='center', fontsize=7)
ax.text(0, -122, 'tomtho-slim mk2  PORON 3.0 mm, seen from above (rear edge at the top). Dashed: PCB outline. '
        'LiPo pocket and lead path left free.', fontsize=6.5)
fig.savefig(os.path.join(D, 'poron_3mm_A4.pdf'))
fig.savefig(os.path.join(D, 'poron_3mm.png'), dpi=110)
