"""Measure the reference STEP files (run in CI with CadQuery).

ACC keycaps (Salicylic-acid3/ACC_Keycaps, CC BY-NC 4.0) and the ClickBoard Tenkey case (Salicylic-acid3/Case_Data,
CC BY-NC 4.0) are only *measured* here, to get the hook / hole / height numbers for our own case.  They are cloned
at CI time and not stored in this repo.

usage: python measure_ref.py <ACC_Keycaps dir> <Case_Data dir> <out dir>
"""
import os, sys, math
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

acc, casedir, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
log = open(os.path.join(out, 'measure.txt'), 'w')


def p(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    log.write(s + '\n')


def bb(s):
    b = s.BoundingBox()
    return f'x {b.xmin:.2f}..{b.xmax:.2f} ({b.xlen:.2f})  y {b.ymin:.2f}..{b.ymax:.2f} ({b.ylen:.2f})  z {b.zmin:.2f}..{b.zmax:.2f} ({b.zlen:.2f})'


def edges_xy(shape, n=24):
    """Discretised edges -> list of polylines (3D points)."""
    lines = []
    for e in shape.Edges():
        try:
            pts = [e.positionAt(t / n) for t in range(n + 1)]
        except Exception:
            continue
        lines.append([(q.x, q.y, q.z) for q in pts])
    return lines


def section(shape, axis, value):
    """Planar section of a solid -> polylines in the plane's 2D coordinates."""
    if axis == 'z':
        pl = cq.Face.makePlane(400, 400, basePnt=(0, 0, value), dir=(0, 0, 1))
    elif axis == 'x':
        pl = cq.Face.makePlane(400, 400, basePnt=(value, 0, 0), dir=(1, 0, 0))
    else:
        pl = cq.Face.makePlane(400, 400, basePnt=(0, value, 0), dir=(0, 1, 0))
    sec = shape.intersect(pl)
    res = []
    for poly in edges_xy(sec):
        if axis == 'z':
            res.append([(a, b) for a, b, c in poly])
        elif axis == 'x':
            res.append([(b, c) for a, b, c in poly])
        else:
            res.append([(a, c) for a, b, c in poly])
    return res


def plot(polys, title, path, xlabel, ylabel):
    fig, ax = plt.subplots(figsize=(9, 7))
    for poly in polys:
        xs, ys = zip(*poly)
        ax.plot(xs, ys, 'k-', lw=0.6)
    ax.set_aspect('equal')
    ax.grid(True, lw=0.3)
    ax.minorticks_on()
    ax.grid(True, which='minor', lw=0.1)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    fig.savefig(path, dpi=130, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------- ACC keycaps
for fn in sorted(os.listdir(acc)):
    if not fn.lower().endswith('.step'):
        continue
    shp = cq.importers.importStep(os.path.join(acc, fn)).val()
    tag = fn[:-5]
    p('==', fn, 'solids', len(shp.Solids()), 'volume %.1f' % shp.Volume())
    p('  bbox', bb(shp))
    b = shp.BoundingBox()
    cx, cy = (b.xmin + b.xmax) / 2, (b.ymin + b.ymax) / 2
    # z slices: bounding box of each section and how many closed loops
    z = b.zmin + 0.05
    while z < b.zmax:
        polys = section(shp, 'z', z)
        if polys:
            xs = [q[0] for pl in polys for q in pl]
            ys = [q[1] for pl in polys for q in pl]
            p(f'  z={z:6.2f}: x {min(xs):7.2f}..{max(xs):7.2f}  y {min(ys):7.2f}..{max(ys):7.2f}  edges {len(polys)}')
        z += 0.25
    # pictures: plan sections at a few heights, and vertical sections through the centre and through a hook
    for frac in (0.05, 0.3, 0.6, 0.9):
        zz = b.zmin + frac * b.zlen
        plot(section(shp, 'z', zz), f'{tag} section z={zz:.2f}', os.path.join(out, f'{tag}_z{int(frac*100):02d}.png'), 'x', 'y')
    plot(section(shp, 'y', cy), f'{tag} section y={cy:.2f}', os.path.join(out, f'{tag}_ycen.png'), 'x', 'z')
    plot(section(shp, 'x', cx), f'{tag} section x={cx:.2f}', os.path.join(out, f'{tag}_xcen.png'), 'y', 'z')
    for frac in (0.12, 0.2):
        yy = b.ymin + frac * b.ylen
        plot(section(shp, 'y', yy), f'{tag} section y={yy:.2f}', os.path.join(out, f'{tag}_y{int(frac*100):02d}.png'), 'x', 'z')
        xx = b.xmin + frac * b.xlen
        plot(section(shp, 'x', xx), f'{tag} section x={xx:.2f}', os.path.join(out, f'{tag}_x{int(frac*100):02d}.png'), 'y', 'z')

# ---------------------------------------------------------------- ClickBoard Tenkey case
tk = os.path.join(casedir, 'ClickBoard Tenkey', 'Clickboard Tenkey.step')
asm = cq.importers.importStep(tk)
shp = asm.val() if len(asm.vals()) == 1 else cq.Compound.makeCompound(asm.vals())
p('== Tenkey', 'solids', len(shp.Solids()))
for i, s in enumerate(shp.Solids()):
    p(f'  solid {i}: vol {s.Volume():9.1f}  {bb(s)}')
b = shp.BoundingBox()
p('  all', bb(shp))
plot(edges_xy(shp, 8) and [[(a, b_) for a, b_, c in pl] for pl in edges_xy(shp, 8)], 'Tenkey top view (all edges)',
     os.path.join(out, 'tenkey_top.png'), 'x', 'y')
for frac in (0.25, 0.5, 0.75):
    yy = b.ymin + frac * b.ylen
    plot(section(shp, 'y', yy), f'Tenkey section y={yy:.2f}', os.path.join(out, f'tenkey_y{int(frac*100)}.png'), 'x', 'z')
    xx = b.xmin + frac * b.xlen
    plot(section(shp, 'x', xx), f'Tenkey section x={xx:.2f}', os.path.join(out, f'tenkey_x{int(frac*100)}.png'), 'y', 'z')
z = b.zmin + 0.05
while z < b.zmax:
    polys = section(shp, 'z', z)
    p(f'  tenkey z={z:6.2f}: edges {len(polys)}')
    z += 0.25
log.close()
