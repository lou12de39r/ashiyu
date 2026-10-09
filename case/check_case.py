"""Section views of the assembled case (CI): top frame, bottom plate, PCB, part blocks, ACC keycaps, custom caps.

usage: python check_case.py <dir with built STEP + stack.json> <ACC_Keycaps dir>
Writes section_*.png and checks.txt (interference volumes between keycaps / frame / part blocks).
"""
import json, math, os, sys
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
D, ACC = sys.argv[1], sys.argv[2]
I = json.load(open(os.path.join(HERE, 'case_inputs.json')))
S = json.load(open(os.path.join(D, 'stack.json')))
Z_PT, Z_PB = S['Z_PT'], S['Z_PB']
log = open(os.path.join(D, 'checks.txt'), 'w')


def p(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    log.write(s + '\n')


top = cq.importers.importStep(os.path.join(D, 'tomtho_mk2_top_frame.step')).val()
bot = cq.importers.importStep(os.path.join(D, 'tomtho_mk2_bottom_plate.step')).val()
cap05 = cq.importers.importStep(os.path.join(D, 'tomtho_mk2_keycap_0.5u_x_0.5u.step')).val()
accs = {}
for name, key, cxy in (('ACC_1u.step', (1.0, 1.0), (8.25, -8.0)), ('ACC_0.5u.step', (1.0, 0.5), (8.25, -3.5)),
                       ('ACC_1.25u.step', (1.25, 1.0), (10.5, -8.0))):
    sh = cq.importers.importStep(os.path.join(ACC, name)).val()
    accs[key] = sh.translate(cq.Vector(-cxy[0], -cxy[1], 0))
caps = []
for k in I['keys']:
    key = (k['w_u'], k['h_u'])
    sh = accs.get(key, cap05)
    sh = sh.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), -k['rot_deg']).translate(cq.Vector(k['cx'], -k['cy'], Z_PT + 4.5))
    caps.append((k, sh))
pcb = cq.Workplane('XY').workplane(offset=Z_PB).center((I['board'][0] + I['board'][2]) / 2, -(I['board'][1] + I['board'][3]) / 2) \
    .rect(I['board'][2] - I['board'][0], I['board'][3] - I['board'][1]).extrude(I['pcb_t']).val()
blocks = []
sw_body = {}
for q in I['parts']:
    if q['ref'].startswith('H'):
        continue
    x0, y0, x1, y1 = q['bbox']
    h = q['h']
    if q['fp'] == 'SW_ALPS_SKRA_6.2mm':      # body 6.2 square to 2.8, actuator d 2.8 to 3.4 (LCSC STEP)
        b = cq.Workplane('XY').workplane(offset=Z_PT).center(q['x'], -q['y']).rect(6.2, 6.2).extrude(2.8) \
            .faces('>Z').workplane().circle(1.4).extrude(0.6)
        b = b.rotate((q['x'], -q['y'], 0), (q['x'], -q['y'], 1), q['rot'])
    else:
        b = cq.Workplane('XY').workplane(offset=Z_PT).center((x0 + x1) / 2, -(y0 + y1) / 2).rect(x1 - x0 - 0.5, y1 - y0 - 0.5).extrude(h)
    blocks.append((q['ref'], b.val()))
    if q['fp'] == 'SW_ALPS_SKRA_6.2mm':      # switch body without the actuator (the actuator is meant to be pushed)
        sw_body[q['ref']] = cq.Workplane('XY').workplane(offset=Z_PT).center(q['x'], -q['y']).rect(6.2, 6.2).extrude(2.8) \
            .rotate((q['x'], -q['y'], 0), (q['x'], -q['y'], 1), q['rot']).val()

# --- interference checks (volumes, mm3)
def inter(a, b):
    try:
        return a.intersect(b).Volume()
    except Exception:
        return -1


bad = 0
for k, c in caps:
    for nm, other in (('top frame', top), ('bottom', bot)):
        v = inter(c, other)
        if v > 0.01:
            bad += 1
            p(f'INTERFERENCE cap "{k["label"]}" x {nm}: {v:.3f} mm3')
    bbc = c.BoundingBox()
    for ref, b in blocks:
        bb = b.BoundingBox()
        if bb.xmax < bbc.xmin or bb.xmin > bbc.xmax or bb.ymax < bbc.ymin or bb.ymin > bbc.ymax:
            continue
        v = inter(c, b)
        if v > 0.01:
            bad += 1
            p(f'INTERFERENCE cap "{k["label"]}" x {ref}: {v:.3f} mm3')
# keycaps pressed 1.0 mm (full SKRA travel) against part blocks other than their own switch
for k, c in caps:
    cp = c.translate(cq.Vector(0, 0, -1.0))
    bbc = cp.BoundingBox()
    for ref, b in blocks:
        bb = b.BoundingBox()
        if bb.xmax < bbc.xmin or bb.xmin > bbc.xmax or bb.ymax < bbc.ymin or bb.ymin > bbc.ymax:
            continue
        if ref in sw_body:
            # switches: the cap can only travel until its nub (0.1 above the actuator at rest) has pushed the actuator
            # flush with the body (actuator top 3.4 -> body top 2.8), i.e. 0.7 mm.  Only the body counts there.
            b = sw_body[ref]
            v = inter(c.translate(cq.Vector(0, 0, -0.7)), b)
        else:
            v = inter(cp, b)
        if v > 0.01:
            bad += 1
            p(f'PRESSED cap "{k["label"]}" hits {ref}: {v:.3f} mm3')
# clearances of the small keys (0.5u wide or tall) to their own switch: nub to actuator at rest, cap underside to
# switch body when pressed 1.0 mm (negative = overlap)
for k, c in caps:
    if k['w_u'] >= 1.0 and k['h_u'] >= 1.0:
        continue
    bbc = c.BoundingBox()
    own = min(sw_body, key=lambda r: (sw_body[r].Center().x - (bbc.xmin + bbc.xmax) / 2) ** 2
              + (sw_body[r].Center().y - (bbc.ymin + bbc.ymax) / 2) ** 2)
    body = sw_body[own]
    near = c.intersect(cq.Workplane('XY').workplane(offset=Z_PT).center(body.Center().x, body.Center().y)
                       .rect(7.0, 7.0).extrude(6.0).val())
    low = near.BoundingBox().zmin - Z_PT                 # lowest point of the cap over its switch, above the PCB
    rest = near.cut(cq.Workplane('XY').workplane(offset=Z_PT).center(body.Center().x, body.Center().y)
                    .circle(1.8).extrude(6.0).val())
    other = rest.BoundingBox().zmin - Z_PT if rest.Volume() > 1e-6 else float('nan')
    p(f'small key "{k["label"]}" ({own}): nub bottom {low:.2f} above PCB (actuator top 3.40, gap {low - 3.40:.2f}); '
      f'lowest other part over the switch {other:.2f} (body top 2.80, room {other - 2.80:.2f}; '
      f'the cap travels at most {low - 2.80:.2f} before the actuator bottoms)')
for ref, b in blocks:
    for nm, other in (('top frame', top), ('bottom', bot)):
        v = inter(b, other)
        if v > 0.01:
            bad += 1
            p(f'INTERFERENCE part {ref} x {nm}: {v:.3f} mm3')
for nm, other in (('top frame', top), ('bottom', bot)):        # the PCB itself (plain slab, no holes)
    v = inter(pcb, other)
    if v > 0.01:
        bad += 1
        p(f'INTERFERENCE PCB x {nm}: {v:.3f} mm3')
p('interferences:', bad)


# --- section pictures
def sec(shape, axis, value):
    """Section faces, triangulated -> list of triangles in (h, z)."""
    if axis == 'y':
        pl = cq.Face.makePlane(1000, 1000, basePnt=(0, value, 0), dir=(0, 1, 0))
    else:
        pl = cq.Face.makePlane(1000, 1000, basePnt=(value, 0, 0), dir=(1, 0, 0))
    try:
        s = shape.intersect(pl)
    except Exception:
        return []
    out = []
    for f in s.Faces():
        vs, tris = f.tessellate(0.02)
        P = [(v.x, v.z) if axis == 'y' else (-v.y, v.z) for v in vs]
        out += [[P[i] for i in t] for t in tris]
    return out


def view(axis, value, lo, hi, name, title):
    fig, ax = plt.subplots(figsize=(14, 3.2))
    groups = [(top, '#5b7fbf'), (bot, '#9a9a9a'), (pcb, '#2f8f4f')]
    groups += [(b, '#e39b2d') for _, b in blocks]
    groups += [(c, '#c0392b') for _, c in caps]
    for shape, col in groups:
        bb = shape.BoundingBox()
        if axis == 'y' and not (bb.ymin <= value <= bb.ymax):
            continue
        if axis == 'x' and not (bb.xmin <= value <= bb.xmax):
            continue
        for poly in sec(shape, axis, value):
            ax.add_patch(Polygon(poly, closed=True, fc=col, ec=col, lw=0.2))
    ax.set_xlim(lo, hi)
    ax.set_ylim(-1, 13)
    ax.set_aspect('equal')
    ax.grid(True, lw=0.2)
    ax.set_title(title, fontsize=9)
    fig.savefig(os.path.join(D, f'section_{name}.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)


key = {k['label']: k for k in I['keys']}
g = key['G']
view('y', -g['cy'], -3, 282, 'row_G', f'section through row A..L (layout y = {g["cy"]:.1f}), z up, mm')
view('y', -g['cy'], 90, 170, 'row_G_zoom', 'zoom: G / trackpad / H')
bt = key['BT 切替']
view('x', bt['cx'], -2, 40, 'BT', 'section through the BT key (custom flange cap), rear at left')
view('x', I['J1']['x'], -3, 35, 'USB', 'section through the USB-C receptacle')
view('x', 138.5, -3, 112, 'centre', 'section through the centre (MCU, trackpad, M key, front screw)')
th = key['Space L2']
view('x', th['cx'], 60, 112, 'thumb', 'section through a thumb key')
up = key['↑']
view('x', up['cx'], 60, 112, 'arrows', 'section through the up / down keys')
log.close()
