"""tomtho-slim mk2 case: top frame + bottom plate (+ custom 0.5u x 0.5u keycaps), CadQuery.  Runs in CI.

Reads case_inputs.json (export_inputs.py, from the finished PCB).  Writes STEP + STL for JLC3DP and preview PNGs.

Heights (z = 0 at the bottom of the case):
  bottom plate   0 .. Z_PB         floor 1.0 under the LiPo pocket (3.0 cell + 0.3)
  PCB            Z_PB .. Z_PT      1.2 mm
  plate          Z_PT+3.0 .. Z_PT+5.0   (as the ClickBoard Tenkey case: ACC keycap hooks catch under the plate)
  keycap top     Z_PT+6.0
Plan coordinates: X = layout x, Y = -layout y (so the STL is the right way up), mm.

usage: python build_case.py <out dir> [ACC_Keycaps dir for the preview]
"""
import json, math, os, sys
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'out')
ACC = sys.argv[2] if len(sys.argv) > 2 else ''
os.makedirs(OUT, exist_ok=True)
I = json.load(open(os.path.join(HERE, 'case_inputs.json')))

# ------------------------------------------------------------------ parameters
WALL = 1.8            # side wall, outside the PCB clearance
PCB_CLR = 0.3         # PCB edge to wall
FLOOR = 1.0
BAT_T, BAT_CLR = 3.0, 0.3
PCB_T = I['pcb_t']
Z_PB = FLOOR + BAT_T + BAT_CLR          # PCB bottom = seam between the two parts
Z_PT = Z_PB + PCB_T                     # PCB top
PLATE_B = Z_PT + 3.0
PLATE_T = Z_PT + 5.0
TP_SKIN = 1.0                           # plate over the trackpad (TPS43 is optimised for a 1 mm overlay)
HOLE_R = 0.8                            # keycap hole corner radius
KEY_CLR = float(os.environ.get('KEY_CLR', '0'))   # extra clearance per side on keycap holes (e.g. 0.1 for MJF)
HOLE_CHAMFER = 0.5                      # 45 deg lead-in at the top of each keycap hole
BOSS_D, PILOT_D = 4.6, 1.6              # M2 self-tapping into the top frame
SCREW_CLR_D, HEAD_D, HEAD_DEPTH = 2.4, 4.4, 1.6
TOP_CHAMFER = 1.0

W, H = I['outline']
R0 = I['outline_r']
bx0, by0, bx1, by1 = I['board']
BR = I['board_r']


def Y(y):
    return -y


def rrect(x0, y0, x1, y1, r):
    """Rounded rectangle in layout coords -> Workplane sketch on XY (Y flipped)."""
    return (cq.Sketch().rect(x1 - x0, y1 - y0).vertices().fillet(r)), ((x0 + x1) / 2, Y((y0 + y1) / 2))


def slab(x0, y0, x1, y1, r, z0, z1):
    sk, (cx, cy) = rrect(x0, y0, x1, y1, r)
    return cq.Workplane('XY').workplane(offset=z0).center(cx, cy).placeSketch(sk).extrude(z1 - z0)


def box(cx, cy, w, h, z0, z1, rot=0.0, r=0.0):
    """Box centred at layout (cx, cy), rotated by the layout angle rot (clockwise-positive, y down)."""
    wp = cq.Workplane('XY').workplane(offset=z0)
    if r > 0:
        s = cq.Sketch().rect(w, h).vertices().fillet(r)
        solid = wp.placeSketch(s).extrude(z1 - z0)
    else:
        solid = wp.rect(w, h).extrude(z1 - z0)
    return solid.rotate((0, 0, 0), (0, 0, 1), -rot).translate((cx, Y(cy), 0))


def cyl(cx, cy, d, z0, z1):
    return cq.Workplane('XY').workplane(offset=z0).center(cx, Y(cy)).circle(d / 2).extrude(z1 - z0)


def tapered_hole(cx, cy, w, h, rot, z0, depth, grow):
    """Lead-in: w x h at z0 growing by `grow` per side at z0 + depth."""
    wp = cq.Workplane('XY').workplane(offset=z0)
    s0 = wp.rect(w, h).workplane(offset=depth).rect(w + 2 * grow, h + 2 * grow).loft()
    return s0.rotate((0, 0, 0), (0, 0, 1), -rot).translate((cx, Y(cy), 0))


case_out = (-WALL - PCB_CLR + bx0, -WALL - PCB_CLR + by0, bx1 + PCB_CLR + WALL, by1 + PCB_CLR + WALL)
case_r = BR + PCB_CLR + WALL
inner = (bx0 - PCB_CLR, by0 - PCB_CLR, bx1 + PCB_CLR, by1 + PCB_CLR)
inner_r = BR + PCB_CLR

# ================================================================== top frame
top = slab(*case_out, case_r, Z_PB, PLATE_T).faces('>Z').edges().chamfer(TOP_CHAMFER)
top = top.cut(slab(*inner, inner_r, Z_PB - 0.1, PLATE_B))

cut = None


def add_cut(s):
    global cut
    cut = s if cut is None else cut.union(s)


# keycap holes + lead-in
for k in I['keys']:
    w, h = k['hole'][0] + 2 * KEY_CLR, k['hole'][1] + 2 * KEY_CLR
    add_cut(box(k['cx'], k['cy'], w, h, PLATE_B - 0.2, PLATE_T + 0.2, k['rot_deg'], HOLE_R))
    add_cut(tapered_hole(k['cx'], k['cy'], w, h, k['rot_deg'], PLATE_T - HOLE_CHAMFER, HOLE_CHAMFER + 0.01, HOLE_CHAMFER))

# plate thinned around the 0.5u x 0.5u keys (flange caps, see below)
for k in I['keys']:
    if (k['w_u'], k['h_u']) == (0.5, 0.5):
        add_cut(box(k['cx'], k['cy'], 8.8, 8.6, PLATE_B - 0.2, Z_PT + 4.3))

# LED windows (1.8 square, as the Tenkey case) with light shrouds added below
for e in I['leds']:
    add_cut(box(e['cx'], e['cy'], 1.8, 1.8, PLATE_B - 0.2, PLATE_T + 0.2))

# trackpad pocket from below: TPS43 (43 x 40 x 1.0 PCB) stuck to a 1.0 mm skin
tp = I['trackpad']
tpc = (tp['x'] + tp['w'] / 2, tp['y'] + tp['h'] / 2)
add_cut(box(tpc[0], tpc[1], tp['w'] + 0.6, tp['h'] + 0.6, PLATE_B - 0.2, PLATE_T - TP_SKIN, r=1.0))

# shallow groove round the touch area so a finger can feel its edge (skin stays 1.0 mm over the pad itself)
add_cut(box(tpc[0], tpc[1], tp['w'] + 1.6, tp['h'] + 1.6, PLATE_T - 0.4, PLATE_T + 0.2, r=2.0)
        .cut(box(tpc[0], tpc[1], tp['w'], tp['h'], PLATE_T - 0.5, PLATE_T + 0.3, r=1.6)))

# reset pin hole over SW66
add_cut(cyl(I['SW66']['x'], I['SW66']['y'], 1.6, PLATE_B - 0.2, PLATE_T + 0.2))

# pockets in the underside of the plate over tall parts
for p in I['parts']:
    if p['h'] > (PLATE_B - Z_PT) - 0.4 and not p['fp'].startswith('SW_ALPS'):
        x0, y0, x1, y1 = p['bbox']
        add_cut(box((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0 + 1.0, y1 - y0 + 1.0, PLATE_B - 0.2,
                    Z_PT + p['h'] + 0.4))

top = top.cut(cut)

# light shrouds around the LEDs (stop 1.0 above the PCB, clear of the 0603 resistors)
add = None
for e in I['leds']:
    s = box(e['cx'], e['cy'], 3.4, 3.4, Z_PT + 1.0, PLATE_B + 0.01).cut(box(e['cx'], e['cy'], 2.4, 2.4, Z_PT, PLATE_B + 0.02))
    add = s if add is None else add.union(s)
# screw bosses (sit on the PCB top) and plate posts
for x, y in I['screws']:
    add = add.union(cyl(x, y, BOSS_D, Z_PT, PLATE_B + 0.01))
for x, y in I['posts']:
    add = add.union(box(x, y, 1.4, 1.4, Z_PT, PLATE_B + 0.01))
top = top.union(add)
for x, y in I['screws']:
    top = top.cut(cyl(x, y, PILOT_D, Z_PT - 0.1, PLATE_T - 0.8))

# rear wall openings: USB-C (notch, open at the top: a 6 mm plug overmold leaves no wall above it) and the
# power-switch lever slot.  Both only through the wall.
j1, sw = I['J1'], I['SW67']
wy0, wy1 = case_out[1] - 1.0, inner[1] + 0.5
top = top.cut(box(j1['x'], (wy0 + wy1) / 2, 12.4, wy1 - wy0, Z_PT - 1.6, PLATE_T + 1.0))
top = top.cut(box(sw['x'], (wy0 + wy1) / 2, 9.6, wy1 - wy0, Z_PT - 0.1, Z_PT + 2.2))

# ================================================================== bottom plate
bot = slab(*case_out, case_r, 0, Z_PB)
# lightening pocket over the whole inside (floor 1.0), then support islands added back
pocket = slab(inner[0] + 2.5, inner[1] + 2.5, inner[2] - 2.5, inner[3] - 2.5, max(inner_r - 2.5, 1.0), FLOOR, Z_PB + 0.1)
bot = bot.cut(pocket)
isl = None


def add_isl(s):
    global isl
    isl = s if isl is None else isl.union(s)


bat = I['battery']
bat_box = (bat[0] - 0.5, bat[1] - 0.5, bat[2] + 0.5, bat[3] + 0.5)
for x, y, rot in I['switch_centres']:
    if bat_box[0] - 4 < x < bat_box[2] + 4 and bat_box[1] - 4 < y < bat_box[3] + 4:
        continue                                   # over the LiPo: the cell itself carries the PCB
    add_isl(box(x, y, 7.0, 7.0, FLOOR - 0.01, Z_PB, -rot))
for x, y in I['screws']:
    add_isl(cyl(x, y, 6.5, FLOOR - 0.01, Z_PB))
# solid under the USB-C / MCU / power switch area (plug and switch forces)
add_isl(box(j1['x'], 8.0, 16.0, 14.0, FLOOR - 0.01, Z_PB))
add_isl(box(sw['x'], 6.0, 10.0, 10.0, FLOOR - 0.01, Z_PB))
add_isl(box(I['SW66']['x'], I['SW66']['y'], 8.0, 6.0, FLOOR - 0.01, Z_PB))
bot = bot.union(isl)
# LiPo pocket (the lead runs inside the lightening pocket to the pass-through slot near J2: no islands on the way)
bot = bot.cut(box((bat_box[0] + bat_box[2]) / 2, (bat_box[1] + bat_box[3]) / 2, bat_box[2] - bat_box[0],
                  bat_box[3] - bat_box[1], FLOOR, Z_PB + 0.1, r=1.0))
# screws: clearance + counterbore from below
for x, y in I['screws']:
    bot = bot.cut(cyl(x, y, SCREW_CLR_D, -0.1, Z_PB + 0.1)).cut(cyl(x, y, HEAD_D, -0.1, HEAD_DEPTH))
# USB-C notch continues 0.4 into the bottom rim
bot = bot.cut(box(j1['x'], (wy0 + wy1) / 2, 12.4, wy1 - wy0, Z_PT - 1.6, Z_PB + 0.1))

# ================================================================== custom 0.5u x 0.5u keycap (BT, M)
# No ACC part exists, and hooks do not fit (the SKRA body, 6.2 square up to 2.8 mm, fills the 7 mm hole).
# Flange type instead: the plate is thinned to 0.8 mm around these two keys (pocket from below up to PCB+4.2);
# the cap is dropped in from below before the PCB, its flange (PCB+3.8..4.2) stops under the pocket ceiling.
# Flange to switch body: 1.0 mm = the switch's full travel.  Local z = 0 at PCB+4.5 (same as the ACC caps).
CW, CH = 7.25 - 0.28, 7.0 - 0.28
cap = cq.Workplane('XY').workplane(offset=-0.3).rect(CW, CH).extrude(1.8).edges('|Z').fillet(1.0).edges('>Z').chamfer(0.5)
cap = cap.union(cq.Workplane('XY').workplane(offset=-0.7).rect(8.6, 8.4).extrude(0.4))      # flange
cap = cap.union(cq.Workplane('XY').workplane(offset=-1.0).circle(1.25).extrude(0.31))       # nub on the switch

# ================================================================== export
def export(shape, name):
    cq.exporters.export(shape, os.path.join(OUT, name + '.step'))
    cq.exporters.export(shape, os.path.join(OUT, name + '.stl'), tolerance=0.02, angularTolerance=0.1)
    bb = shape.val().BoundingBox()
    print(f'{name}: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.2f} mm, volume {shape.val().Volume() / 1000:.1f} cm3')


export(top, 'tomtho_mk2_top_frame')
export(bot, 'tomtho_mk2_bottom_plate')
export(cap, 'tomtho_mk2_keycap_0.5u_x_0.5u')
json.dump({'Z_PB': Z_PB, 'Z_PT': Z_PT, 'PLATE_B': PLATE_B, 'PLATE_T': PLATE_T, 'KEYCAP_TOP': Z_PT + 6.0,
           'outline': [case_out[2] - case_out[0], case_out[3] - case_out[1]]},
          open(os.path.join(OUT, 'stack.json'), 'w'), indent=1)
print('stack', Z_PB, Z_PT, PLATE_B, PLATE_T, 'keycap top', Z_PT + 6.0)
