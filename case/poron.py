"""Foam (PORON) template for the bottom plate: fills the pockets between the support islands / ribs, leaves the
LiPo pocket and the battery-lead path free.  Runs in CI after build_case.py.

Outputs: poron_3mm.dxf (cut outline, mm), poron_3mm_A4.pdf (1:1 on A4 landscape), poron_3mm.png
usage: python poron.py <dir with tomtho_mk2_bottom_plate.step + stack.json>
"""
import json, os, sys
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path

D = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
I = json.load(open(os.path.join(HERE, 'case_inputs.json')))
S = json.load(open(os.path.join(D, 'stack.json')))
bot = cq.importers.importStep(os.path.join(D, 'tomtho_mk2_bottom_plate.step')).val()
Z = S['Z_PB'] - 0.6                         # a level inside the pockets
CLR = 0.5                                   # foam pulled back from every wall / island

bx0, by0, bx1, by1 = I['board']
air = cq.Workplane('XY').workplane(offset=Z - 0.05).center((bx0 + bx1) / 2, -(by0 + by1) / 2) \
    .rect(bx1 - bx0, by1 - by0).extrude(0.1).val().cut(bot)
# keep-outs: LiPo pocket (+1 mm) and the lead path to the pass-through slot by J2
bat = I['battery']
sl = I['slots'][0]
keep = [(bat[0] - 1.0, bat[1] - 1.0, bat[2] + 1.0, bat[3] + 1.0),
        (bat[2] - 6.0, sl[1] - 1.5, bat[2] - 1.0, bat[1]),          # up from the battery's rear-right corner
        (bat[2] - 6.0, sl[1] - 1.5, sl[2] + 2.0, sl[3] + 1.5)]      # across to the slot
for x0, y0, x1, y1 in keep:
    air = air.cut(cq.Workplane('XY').workplane(offset=Z - 1).center((x0 + x1) / 2, -(y0 + y1) / 2)
                  .rect(x1 - x0, y1 - y0).extrude(2).val())
# shrink by CLR (offset faces inwards), drop slivers
faces = []
for f in cq.Workplane('XY').add(air).faces('<Z').vals():
    try:
        g = f.outerWire().offset2D(-CLR, 'intersection')
        inner = [w.offset2D(CLR, 'intersection') for w in f.innerWires()]
        for w in g:
            ff = cq.Face.makeFromWires(w, [x for ws in inner for x in ws])
            if ff.Area() > 25:
                faces.append(ff)
    except Exception:
        pass
print('foam pieces:', len(faces), 'area cm2: %.1f' % (sum(f.Area() for f in faces) / 100))
wp = cq.Workplane('XY')
for f in faces:
    wp = wp.add(f)
cq.exporters.export(wp, os.path.join(D, 'poron_3mm.dxf'))


def draw(ax):
    for f in faces:
        for w in [f.outerWire()] + f.innerWires():
            pts = [v.toTuple() for v in w.Vertices()]
            ed = []
            for e in w.Edges():
                ed += [e.positionAt(t / 12).toTuple() for t in range(13)]
            xs = [p[0] for p in ed]
            ys = [p[1] for p in ed]
            ax.plot(xs, ys, 'k-', lw=0.4)


W_MM, H_MM = 297, 210
fig = plt.figure(figsize=(W_MM / 25.4, H_MM / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(-8.5, W_MM - 8.5)
ax.set_ylim(-H_MM + 40, 40)
ax.set_aspect('equal')
ax.axis('off')
draw(ax)
ax.plot([0, 100], [25, 25], 'k-', lw=1.2)
ax.text(50, 27, '100 mm (check with a ruler: print at 100 %)', ha='center', fontsize=7)
ax.text(0, -125, 'tomtho-slim mk2 - PORON 3.0 mm (pockets between the support islands; LiPo pocket and lead path left free)',
        fontsize=7)
fig.savefig(os.path.join(D, 'poron_3mm_A4.pdf'))
fig.savefig(os.path.join(D, 'poron_3mm.png'), dpi=110)
