"""Loop-level numbers: plate holes of the ClickBoard Tenkey case, ACC leg/lip positions. Run in CI."""
import os, sys
import cadquery as cq
acc, casedir, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
f = open(os.path.join(out, 'measure2.txt'), 'w')
def p(*a):
    s = ' '.join(str(x) for x in a); print(s); f.write(s + '\n')
def loops(shape, z):
    pl = cq.Face.makePlane(400, 400, basePnt=(0, 0, z), dir=(0, 0, 1))
    sec = shape.intersect(pl)
    res = []
    for w in cq.Wire.combine(sec.Edges()):
        b = w.BoundingBox()
        res.append((round(b.xmin, 2), round(b.xmax, 2), round(b.ymin, 2), round(b.ymax, 2), round(b.xlen, 2), round(b.ylen, 2)))
    return sorted(res)
def vprobe(shape, x, y):
    """z intervals of material along a vertical line"""
    e = cq.Edge.makeLine(cq.Vector(x, y, -50), cq.Vector(x, y, 50))
    sec = shape.intersect(e)
    return [(round(ed.startPoint().z, 2), round(ed.endPoint().z, 2)) for ed in sec.Edges()]
tk = cq.importers.importStep(os.path.join(casedir, 'ClickBoard Tenkey', 'Clickboard Tenkey.step')).val()
for z in (-1.0, 1.0, 3.3, 4.0, 4.7, 4.95):
    L = loops(tk, z)
    p(f'tenkey z={z}: {len(L)} loops')
    for l in L:
        p('   ', l)
for x, y in ((47.75, -57.25), (29.5, -57.25), (47.75, -96.5), (2.0, -57.25), (5.0, -57.25), (10.0, -57.25), (47.75, -20.0)):
    p(f'tenkey probe x={x} y={y}:', vprobe(tk, x, y))
for fn in ('ACC_1u.step', 'ACC_0.5u.step', 'ACC_1.25u.step'):
    s = cq.importers.importStep(os.path.join(acc, fn)).val()
    for z in (-2.9, -2.25, -1.6, -1.4, -1.0, -0.5):
        p(f'{fn} z={z}:')
        for l in loops(s, z):
            p('   ', l)
f.close()
