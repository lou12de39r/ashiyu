"""Keycap files for tomtho-slim mk2, based on Salicylic-acid3's ACC (Acid Caps ClickProfile) keycaps.  Runs in CI.

ACC keycaps (https://github.com/Salicylic-acid3/ACC_Keycaps) are CC BY-NC 4.0 (c) Salicylic_acid3.
Changes made here: re-centred, converted to STL, combined on print sprues, thumb caps domed (dish filled);
the 0.5u x 0.5u cap is our own design.
The outputs are therefore under CC BY-NC 4.0 as well (non-commercial use only).

usage: python keycaps.py <ACC_Keycaps dir> <out dir> <dir with tomtho_mk2_keycap_0.5u_x_0.5u.step>
"""
import json, os, sys
import cadquery as cq

ACC, OUT, CASE = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
I = json.load(open(os.path.join(HERE, 'case_inputs.json')))

# ACC files: (name, body centre in the file's XY) - measured: body x 0.14..16.36 (1u) etc., z top = +1.5
TYPES = {
    '1u':       ('ACC_1u.step',      (8.25, -8.0)),
    '1u_home':  ('ACC_1u_Home.step', (8.25, -8.0)),
    '1.25u':    ('ACC_1.25u.step',   (10.5, -8.0)),
    '1u_x_0.5u': ('ACC_0.5u.step',    (8.25, -3.5)),
}
caps = {}
for key, (fn, (cx, cy)) in TYPES.items():
    s = cq.importers.importStep(os.path.join(ACC, fn)).val().translate(cq.Vector(-cx, -cy, 0))
    caps[key] = s
caps['0.5u_x_0.5u'] = cq.importers.importStep(os.path.join(CASE, 'tomtho_mk2_keycap_0.5u_x_0.5u.step')).val()

# Thumb caps: the ACC cap with its dish (~0.45 mm deep) filled and the top made a gentle dome.  Walls, hooks, nub and
# edge rounding stay ACC; the part above local z = 0 is raised by LIFT so the dome's edges sit near the other caps' rims.
# The dome peaks LIFT above the old rim height and is SAG lower at the middle of each top edge (ellipsoid: same sag in
# x and y), so corners end about 2*SAG lower.
SAG = 0.4
LIFT = 0.3
TOPZ = 1.49 + LIFT


def domed(acc):
    up = acc.intersect(cq.Solid.makeBox(60, 40, 3, pnt=cq.Vector(-30, -20, 0))).translate(cq.Vector(0, 0, LIFT))
    acc = acc.fuse(up).clean()
    sec = cq.Workplane('XY').add(acc).section(TOPZ).faces().vals()
    outer = max((f.outerWire() for f in sec), key=lambda w: cq.Face.makeFromWires(w).Area())
    fill = cq.Solid.extrudeLinear(cq.Face.makeFromWires(outer), cq.Vector(0, 0, -0.7))
    body = acc.fuse(fill).clean()
    bb = outer.BoundingBox()
    a, b = max(-bb.xmin, bb.xmax), max(-bb.ymin, bb.ymax)       # half sizes of the flat top
    R = (b * b + SAG * SAG) / (2 * SAG)
    ell = cq.Solid.makeSphere(R, angleDegrees1=-90, angleDegrees2=90).transformGeometry(
        cq.Matrix([[a / b, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]])).translate(cq.Vector(0, 0, TOPZ - R))
    out = body.intersect(ell).clean()
    try:                                                      # soften the crease where the dome meets the edge rounding
        top = max((f for f in out.Faces() if f.Center().z > 0.8), key=lambda f: f.Area())
        out = out.fillet(0.3, top.Edges())
    except Exception as e:
        print('thumb fillet skipped:', e)
    print(f'domed: top {2*a:.2f} x {2*b:.2f}, R {R:.1f}, sag {SAG}, lift {LIFT}, peak z {TOPZ:.2f}')
    return out


caps['1u_thumb'] = domed(caps['1u'])
caps['1.25u_thumb'] = domed(caps['1.25u'])

# "this way up" mark: a filled triangle engraved into the underside of every cap, pointing to the rear of the board
# (+Y here; layout y is negated when the caps are placed).  Away from the nub, the switch and the corner hooks.
# 0.5 mm deep (JLC3DP guide: engraved details >= 0.8 mm wide; the filled triangle is 3 mm), top skin kept >= 0.6 mm.
def up_mark(shape, cx, cy, side=3.0, depth=0.5):
    h = side * 3 ** 0.5 / 2
    pts = [(cx - side / 2, cy - h / 3), (cx + side / 2, cy - h / 3), (cx, cy + 2 * h / 3)]
    col = cq.Workplane('XY').workplane(offset=-4.0).polyline(pts).close().extrude(8.0).val()
    mat = shape.intersect(col)
    bb = mat.BoundingBox()
    d = min(depth, bb.zmax - bb.zmin - 0.6)
    cut = cq.Workplane('XY').workplane(offset=bb.zmin - 0.2).polyline(pts).close().extrude(0.2 + d).val()
    print(f'up mark at ({cx}, {cy}): underside z {bb.zmin:.2f}, top z {bb.zmax:.2f}, depth {d:.2f}')
    return shape.cut(cut).clean()


for key in ('1u', '1u_home', '1.25u', '1u_thumb', '1.25u_thumb'):
    caps[key] = up_mark(caps[key], 0.0, 4.2)
caps['1u_x_0.5u'] = up_mark(caps['1u_x_0.5u'], 4.2, 0.0, side=2.4)   # inside the recess beside the nub


def export(shape, name):
    cq.exporters.export(shape, os.path.join(OUT, name + '.step'))
    cq.exporters.export(shape, os.path.join(OUT, name + '.stl'), tolerance=0.01, angularTolerance=0.1)
    b = shape.BoundingBox()
    print(f'{name}: {b.xlen:.2f} x {b.ylen:.2f} x {b.zlen:.2f} mm, volume {shape.Volume():.0f} mm3')


for key, s in caps.items():
    export(s, f'keycap_{key}')

# how many of each the mk2 layout needs (F / J get the homing cap)
need = {'1u': 0, '1u_home': 2, '1.25u': 0, '1u_x_0.5u': 0, '0.5u_x_0.5u': 0, '1u_thumb': 0, '1.25u_thumb': 0}
for k in I['keys']:
    t = {(1.0, 1.0): '1u', (1.25, 1.0): '1.25u', (1.0, 0.5): '1u_x_0.5u', (0.5, 0.5): '0.5u_x_0.5u'}[(k['w_u'], k['h_u'])]
    if k['kind'] in ('thumb', 'addth'):
        t += '_thumb'
    need[t] += 1
need['1u'] -= 2
print('needed:', need)


def sprue(items, cols, px, py, name):
    """Caps on a grid, joined by small bars at mid-side (clear of the corner hooks), skirt level z -1.4..-0.6."""
    body = None
    pos = []
    for n, key in enumerate(items):
        i, j = n % cols, n // cols
        x, y = i * px, -j * py
        pos.append((x, y, key))
        c = caps[key].translate(cq.Vector(x, y, 0))
        body = c if body is None else body.fuse(c)
    bb = {k: caps[k].BoundingBox() for k in set(items)}
    for x, y, key in pos:
        for x2, y2, key2 in pos:
            if (abs(x2 - x - px) < 1e-6 and abs(y2 - y) < 1e-6):          # right neighbour
                a, b = x + bb[key].xmax - 0.6, x2 + bb[key2].xmin + 0.6
                body = body.fuse(cq.Workplane('XY').workplane(offset=-1.4).center((a + b) / 2, y).rect(b - a, 1.0).extrude(0.8).val())
            if (abs(y2 - y + py) < 1e-6 and abs(x2 - x) < 1e-6):          # lower neighbour
                a, b = y + bb[key].ymin + 0.6, y2 + bb[key2].ymax - 0.6
                body = body.fuse(cq.Workplane('XY').workplane(offset=-1.4).center(x, (a + b) / 2).rect(1.0, a - b).extrude(0.8).val())
    export(body.clean(), name)


SP = 1.1   # ~10 % spares: the ClickBoard author saw about 1 in 10 printed caps fail on burrs
n1 = int(need['1u'] * SP + 0.999)
# split in two: one 57-cap sprue is a ~45 MB STL, over the 30 MB file limit of the chat it is handed over in
na = (n1 + 1) // 2
sprue(['1u'] * na, 8, 19.0, 18.5, f'print_sprue_1u_x{na}_a')
sprue(['1u'] * (n1 - na), 8, 19.0, 18.5, f'print_sprue_1u_x{n1 - na}_b')
if need['1.25u']:
    sprue(['1.25u'] * (need['1.25u'] + 1), 4, 23.5, 18.5, f"print_sprue_1.25u_x{need['1.25u'] + 1}")
# thumb caps are always printed (no ACC part): 1.25u + 1 spare, 1u + 2 spares
th = ['1.25u_thumb'] * (need['1.25u_thumb'] + 1) + ['1u_thumb'] * (need['1u_thumb'] + 2)
sprue(th, 3, 23.5, 18.5, f"print_sprue_thumb_1.25u_x{need['1.25u_thumb'] + 1}_1u_x{need['1u_thumb'] + 2}")
sprue(['1u_x_0.5u'] * (need['1u_x_0.5u'] + 1), 3, 19.0, 10.0, f"print_sprue_1u_x_0.5u_x{need['1u_x_0.5u'] + 1}")
sprue(['1u_home'] * (need['1u_home'] + 1), 3, 19.0, 18.5, f"print_sprue_1u_home_x{need['1u_home'] + 1}")
mixed = None
json.dump({'needed': need, 'sprue_1u': n1, 'spares': '1u +10 %, others +1, thumb 1u +2; 0.5u x 0.5u: see the case sprue (x6)'}, open(os.path.join(OUT, 'keycaps.json'), 'w'), indent=1)
open(os.path.join(OUT, 'LICENSE.txt'), 'w').write(
    'Keycap models derived from ACC Keycaps by Salicylic_acid3 (https://github.com/Salicylic-acid3/ACC_Keycaps),\n'
    'licensed CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/).\n'
    'Changes: re-centred, converted to STL, combined on print sprues for tomtho-slim mk2; thumb caps have the dish filled\n'
    'and a domed top; 0.5u x 0.5u flange cap is new.\n'
    'Non-commercial use only.\n')
