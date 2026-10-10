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
TP_MOD = (43.0, 40.0, 1.0, 1.0)         # TPS43 module itself (no cover plate: touched directly): w, h, PCB t, corner r
TP_CLR = 0.15                           # pocket clearance per side
TP_LIP_W, TP_LIP_T = 1.0, 0.5           # frame lip over the module edge (width, thickness)
HOLE_R = float(os.environ.get('HOLE_R', '1.8'))   # keycap hole corner radius (largest that clears the ACC corner hooks: hole_radius_test.py)
KEY_CLR = float(os.environ.get('KEY_CLR', '0'))   # extra clearance per side on keycap holes (e.g. 0.1 for MJF)
HOLE_CHAMFER = 0.5                      # 45 deg lead-in at the top of each keycap hole
BOSS_D = 5.2                            # boss round each Tadpole rod (sits on the PCB top)
ROD_D, ROD_TOP = 3.0, None              # Tadpole Pin D3.0: d3.0 (+0.05) blind hole in the top frame (ROD_TOP set below)
CUP_D, CUP_WALL = 4.8, 1.0              # cup in the bottom tray round the Tadpole bulge (bulge 3.1 tall under the PCB)
TRAY_CLR = 0.15                         # bottom tray to skirt, per side
FLOAT = 0.4                             # bottom-tray supports stop this far under the PCB (the PCB floats on the Tadpoles)
TOP_CHAMFER = 1.5                       # 45 deg chamfer round the top edge (ClickBoard style, no ring)

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


def rr_wire(w, h, r, z):
    f = cq.Sketch().rect(w, h).vertices().fillet(r)._faces.Faces()[0]
    return f.outerWire().translate(cq.Vector(0, 0, z))


def tapered_hole(cx, cy, w, h, rot, z0, depth, grow):
    """Lead-in with rounded corners: w x h (corner HOLE_R) at z0, growing by `grow` per side at z0 + depth."""
    s = cq.Solid.makeLoft([rr_wire(w, h, HOLE_R, z0), rr_wire(w + 2 * grow, h + 2 * grow, HOLE_R + grow, z0 + depth)], True)
    return cq.Workplane('XY').add(s).rotate((0, 0, 0), (0, 0, 1), -rot).translate((cx, Y(cy), 0))


case_out = (-WALL - PCB_CLR + bx0, -WALL - PCB_CLR + by0, bx1 + PCB_CLR + WALL, by1 + PCB_CLR + WALL)
case_r = BR + PCB_CLR + WALL
inner = (bx0 - PCB_CLR, by0 - PCB_CLR, bx1 + PCB_CLR, by1 + PCB_CLR)
inner_r = BR + PCB_CLR

# ================================================================== top frame
# Screwless: the frame's outer wall (skirt) runs down to the desk; the bottom tray fits inside it from below and clicks
# in with 8 hidden spring clips.  From the side the case is one piece; the only seam is on the underside.
top = slab(*case_out, case_r, 0, PLATE_T).faces('>Z').edges().chamfer(TOP_CHAMFER)
top = top.faces('<Z').edges().chamfer(0.3)
top = top.cut(slab(*inner, inner_r, -0.1, PLATE_B))

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
# trackpad (no cover plate): the TPS43 module goes in FROM BELOW (before the PCB) and its top face is touched directly
# through a window 1.0 mm smaller per side; the 1.0 x 0.5 mm lip holds it, so it cannot fall out.  Sensor face 0.5 mm
# below the top (a frame you can feel).  The module's own 3M 468 tape sticks it to the lip; a PORON block (about 4 mm: 5.1 mm
# from the rib tops to the module PCB, minus its underside parts) on the tray's cross ribs presses it up from below.  Window edge rounded by a 0.3 mm chamfer.
_pw, _ph, _pt, _pr = TP_MOD
add_cut(box(tpc[0], tpc[1], _pw - 2 * TP_LIP_W, _ph - 2 * TP_LIP_W, PLATE_T - TP_LIP_T - 0.1, PLATE_T + 0.2, r=_pr + 1.0))
add_cut(cq.Workplane('XY').add(cq.Solid.makeLoft([rr_wire(_pw - 2 * TP_LIP_W, _ph - 2 * TP_LIP_W, _pr + 1.0, PLATE_T - 0.3),
        rr_wire(_pw - 2 * TP_LIP_W + 0.62, _ph - 2 * TP_LIP_W + 0.62, _pr + 1.31, PLATE_T + 0.01)], True))
        .translate((tpc[0], Y(tpc[1]), 0)))
add_cut(box(tpc[0], tpc[1], _pw + 2 * TP_CLR, _ph + 2 * TP_CLR, PLATE_B - 0.2, PLATE_T - TP_LIP_T, r=_pr + TP_CLR))

# reset button over SW101: a printed plunger (dropped in from below, flange under the plate) pressed by a fingertip.
# SW101 = XKB TS-1928-B, 0.6 mm tall, 160 gf, so an accidental brush does not reset it.  Plunger top 0.2 below the
# plate surface, in a 4.8 mm hole with a 0.4 mm lead-in.
RST = (I['SW101']['x'], I['SW101']['y'])
add_cut(cyl(RST[0], RST[1], 4.8, PLATE_B - 0.2, PLATE_T + 0.2))
add_cut(cq.Workplane('XY').workplane(offset=PLATE_T - 0.4).center(RST[0], Y(RST[1])).circle(2.4)
        .workplane(offset=0.41).circle(2.81).loft())

# pockets in the underside of the plate over tall parts
for p in I['parts']:
    if p['h'] > (PLATE_B - Z_PT) - 0.4 and not p['fp'].startswith('SW_ALPS'):
        x0, y0, x1, y1 = p['bbox']
        add_cut(box((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0 + 1.0, y1 - y0 + 1.0, PLATE_B - 0.2,
                    Z_PT + p['h'] + 0.4))

top = top.cut(cut)

# light shrouds around the LEDs (stop 1.0 above the PCB, clear of the 0603 resistors); walls 0.8 for printing
add = None
for e in I['leds']:
    s = box(e['cx'], e['cy'], 4.0, 4.0, Z_PT + 1.0, PLATE_B + 0.01).cut(box(e['cx'], e['cy'], 2.4, 2.4, Z_PT, PLATE_B + 0.02))
    add = s if add is None else add.union(s)
# Tadpole bosses (sit on the PCB top) and plate posts
for x, y in I['screws']:
    add = add.union(cyl(x, y, BOSS_D, Z_PT, PLATE_B + 0.01))
for x, y in I['posts']:
    add = add.union(box(x, y, 1.4, 1.4, Z_PT, PLATE_B + 0.01))
top = top.union(add)
# Tadpole rod holes: d3.0 blind, up to 0.8 under the top surface.  The rod stands 5.0 above a 1.5 mm plate in the
# GEONWORKS drawing, i.e. 5.3 above our 1.2 mm PCB: trim about 1.1 mm off each rod tip (silicone, a cutter does it).
ROD_TOP = PLATE_T - 0.8
for x, y in I['screws']:
    top = top.cut(cyl(x, y, ROD_D, Z_PT - 0.1, ROD_TOP))

# rear wall openings: USB-C (notch, open at the top: a 6 mm plug overmold leaves no wall above it) and the
# power-switch lever slot.  Both only through the wall.
j1, sw = I['J1'], I['SW102']
wy0, wy1 = case_out[1] - 1.0, inner[1] + 0.5
top = top.cut(box(j1['x'], (wy0 + wy1) / 2, 12.4, wy1 - wy0, Z_PT - 1.6, PLATE_T + 1.0))
top = top.cut(box(sw['x'], (wy0 + wy1) / 2, 9.6, wy1 - wy0, Z_PT - 0.1, Z_PT + 2.2))

# ================================================================== bottom tray (inside the skirt)
tray = (inner[0] + TRAY_CLR, inner[1] + TRAY_CLR, inner[2] - TRAY_CLR, inner[3] - TRAY_CLR)
TRAY_TOP = Z_PB - FLOAT
bot = slab(*tray, inner_r - TRAY_CLR, 0, TRAY_TOP)
# lightening pocket over the whole inside (floor 1.0), then support islands added back
pocket = slab(inner[0] + 2.5, inner[1] + 2.5, inner[2] - 2.5, inner[3] - 2.5, max(inner_r - 2.5, 1.0), FLOOR, TRAY_TOP + 0.1)
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
    add_isl(box(x, y, 7.0, 7.0, FLOOR - 0.01, TRAY_TOP, -rot))
for x, y in I['screws']:
    add_isl(cyl(x, y, CUP_D + 2 * CUP_WALL, FLOOR - 0.01, TRAY_TOP))
# ribs between neighbouring switch islands: turn the 1.0 mm floor into small panels (JLC3DP asks for 2 mm walls at
# 200 mm scale; a ribbed 1.0 mm floor is far stiffer than a plain one)
sc = [(x, y) for x, y, rot in I['switch_centres']
      if not (bat_box[0] - 4 < x < bat_box[2] + 4 and bat_box[1] - 4 < y < bat_box[3] + 4)]
for i, (xa, ya) in enumerate(sc):
    for xb, yb in sc[i + 1:]:
        d = math.hypot(xb - xa, yb - ya)
        if d < 21.0:
            ang = math.degrees(math.atan2(yb - ya, xb - xa))      # layout frame, y down = clockwise-positive
            add_isl(box((xa + xb) / 2, (ya + yb) / 2, d, 1.5, FLOOR - 0.01, TRAY_TOP, ang))
# cross ribs under the trackpad area (no switches there to carry islands)
tx0, ty0 = tp['x'] - 0.5, tp['y'] - 0.5
for f in (0.33, 0.67):
    add_isl(box(tx0 + f * (tp['w'] + 1), tpc[1], 1.5, tp['h'] + 1, FLOOR - 0.01, TRAY_TOP))
    add_isl(box(tpc[0], ty0 + f * (tp['h'] + 1), tp['w'] + 1, 1.5, FLOOR - 0.01, TRAY_TOP))
# solid under the USB-C / MCU / power switch area (plug and switch forces)
add_isl(box(j1['x'], 8.0, 16.0, 14.0, FLOOR - 0.01, TRAY_TOP))
add_isl(box(sw['x'], 6.0, 10.0, 10.0, FLOOR - 0.01, TRAY_TOP))
add_isl(box(I['SW101']['x'], I['SW101']['y'], 8.0, 6.0, FLOOR - 0.01, TRAY_TOP))
bot = bot.union(isl)
# LiPo pocket (the lead runs inside the lightening pocket to the pass-through slot near J2: no islands on the way)
bot = bot.cut(box((bat_box[0] + bat_box[2]) / 2, (bat_box[1] + bat_box[3]) / 2, bat_box[2] - bat_box[0],
                  bat_box[3] - bat_box[1], FLOOR, Z_PB + 0.1, r=1.0))
# Tadpole cups: d4.8 down to the floor (bulge bottom 0.2 above it)
for x, y in I['screws']:
    bot = bot.cut(cyl(x, y, CUP_D, FLOOR, TRAY_TOP + 0.1))
# rubber-foot recesses (YAHATA Slim Flex mini pad, d6 mm): d6.6 x 0.5 deep, centred under switch islands (solid above).
# 4 front (1.5 mm hard pads) + 4 rear (3.0 mm hard pads): rear stands 1.5 mm higher -> about 1.2 deg tilt.
FOOT_D, FOOT_DEPTH = 6.6, 0.5
FEET = ['Ctrl', '無変換 L3', 'BS', '→', '`', '5', '6', '-']
for lab in FEET:
    k = next(k for k in I['keys'] if k['label'] == lab)
    bot = bot.cut(cyl(k['cx'], k['cy'], FOOT_D, -0.1, FOOT_DEPTH))
    print(f'foot recess under "{lab}" at ({k["cx"]:.1f}, {k["cy"]:.1f})')
# hidden spring clips: a 10 mm horizontal beam (1.0 thick, 2.0 tall) freed in the tray rim, with a double-ramp bump
# (0.55 out) that clicks into a groove in the skirt's inner face.  Interference 0.4 -> bending strain ~0.6 %.
# Pull the tray straight down to open (the ramps work both ways).
CLIP_L, CLIP_T, CLIP_Z, BUMP_H, BUMP_L = 10.0, 1.0, (1.6, 3.6), 0.55, 3.0
CLIPS = [('front', x) for x in (30.0, 100.0, 177.0, 247.0)] + [('rear', x) for x in (70.0, 207.0)] + \
        [('left', 54.0), ('right', 54.0)]


def clip_frame(side, pos):
    """origin on the tray's outer face, local +v = outward normal, +u along the wall, as (point, rotation deg)."""
    if side == 'front':
        return (pos, Y(tray[3])), 180.0
    if side == 'rear':
        return (pos, Y(tray[1])), 0.0
    if side == 'left':
        return (tray[0], Y(pos)), 90.0
    return (tray[2], Y(pos)), -90.0


def place(sol, side, pos):
    (px, py), rot = clip_frame(side, pos)
    return sol.rotate((0, 0, 0), (0, 0, 1), rot).translate((px, py, 0))


def lbox(u0, u1, v0, v1, z0, z1):
    return cq.Workplane('XY').box(u1 - u0, v1 - v0, z1 - z0, centered=False).translate((u0, v0, z0))


for side, pos in CLIPS:
    rim = 2.5 - TRAY_CLR + 0.2                                   # rim thickness (to the lightening pocket) + a bit
    bot = bot.cut(place(lbox(-CLIP_L / 2 - 0.8, CLIP_L / 2 + 0.8, -rim, 0.1, FLOOR, TRAY_TOP + 0.1), side, pos))
    beam = lbox(-CLIP_L / 2 - 0.81, CLIP_L / 2, -CLIP_T, 0.0, CLIP_Z[0], CLIP_Z[1])
    root = lbox(-CLIP_L / 2 - 2.0, -CLIP_L / 2 - 0.8, -rim, 0.0, FLOOR - 0.01, TRAY_TOP)   # rebuilt root block
    z0, z1 = CLIP_Z[0] + 0.3, CLIP_Z[1] - 0.3
    bump = (cq.Workplane('YZ').polyline([(0.0, z0), (BUMP_H, z0 + BUMP_H), (BUMP_H, z1 - BUMP_H), (0.0, z1)]).close()
            .extrude(BUMP_L).translate((CLIP_L / 2 - BUMP_L - 0.5, 0, 0)))
    bot = bot.union(place(beam.union(root).union(bump), side, pos))
    # groove in the skirt (top frame) opposite the bump
    top = top.cut(place(lbox(CLIP_L / 2 - BUMP_L - 0.8, CLIP_L / 2 - 0.2, TRAY_CLR - 0.01, TRAY_CLR + BUMP_H + 0.1,
                             z0 - 0.15, z1 + 0.15), side, pos))

# ================================================================== custom 0.5u x 0.5u keycap (BT, M)
# No ACC part exists, and hooks do not fit (the SKRA body, 6.2 square up to 2.8 mm, fills the 7 mm hole).
# Flange type instead: the plate is thinned to 0.8 mm around these two keys (pocket from below up to PCB+4.2);
# the cap is dropped in from below before the PCB, its flange (PCB+3.6..4.2) stops under the pocket ceiling.
# Flange to switch body: 0.8 mm (the cap can travel at most 0.7 before the actuator bottoms).  Local z = 0 at PCB+4.5 (same as the ACC caps).
CW, CH = 7.25 - 0.28, 7.0 - 0.28
cap = cq.Workplane('XY').workplane(offset=-0.3).rect(CW, CH).extrude(1.8).edges('|Z').fillet(1.7).edges('>Z').chamfer(0.5)
# flange: corners rounded r2.5 = hole corner r1.8 + 0.7 overlap, so it overlaps the plate evenly all round (like ACC)
# (built from a rounded 2D outline: the earlier box + edge fillet came out with square corners)
# 0.6 thick (was 0.4: under JLC3DP's 0.5 mm minimum wall); grown downwards, still 0.8 above the switch body (travel <= 0.7)
flange = cq.Workplane('XY').workplane(offset=-0.9).sketch().rect(8.6, 8.4).vertices().fillet(2.5).finalize().extrude(0.6)
cap = cap.union(flange)
assert not cap.val().isInside(cq.Vector(4.1, 4.0, -0.5)), 'flange corners not rounded'
assert cap.val().isInside(cq.Vector(4.0, 0.0, -0.5)), 'flange missing'
cap = cap.union(cq.Workplane('XY').workplane(offset=-1.0).circle(1.25).extrude(0.31))       # nub on the switch
# "this way up" mark: filled triangle (side 2.0) engraved 0.4 deep into the flange underside, pointing to the rear (+Y)
_h = 2.0 * 3 ** 0.5 / 2
cap = cap.cut(cq.Workplane('XY').workplane(offset=-1.0).polyline([(-1.0, 2.1 - _h / 3), (1.0, 2.1 - _h / 3), (0.0, 2.1 + 2 * _h / 3)])
              .close().extrude(0.5))

# ================================================================== export
def export(shape, name):
    cq.exporters.export(shape, os.path.join(OUT, name + '.step'))
    cq.exporters.export(shape, os.path.join(OUT, name + '.stl'), tolerance=0.02, angularTolerance=0.1)
    bb = shape.val().BoundingBox()
    print(f'{name}: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.2f} mm, volume {shape.val().Volume() / 1000:.1f} cm3')


export(top, 'tomtho_mk2_top_frame')
export(bot, 'tomtho_mk2_bottom_plate')
export(cap, 'tomtho_mk2_keycap_0.5u_x_0.5u')
# the same cap x 6 on a sprue (one 3D-print part: a single 8.6 mm cap is under JLC3DP's minimum part size)
pitch = 13.0
sprue = None
for i in range(3):
    for j in range(2):
        c = cap.translate((i * pitch, j * pitch, 0))
        sprue = c if sprue is None else sprue.union(c)
for j in range(2):                                   # bars along x at flange level, between caps
    sprue = sprue.union(cq.Workplane('XY').workplane(offset=-0.9).center(pitch, j * pitch)
                        .rect(2 * pitch - 8.0, 1.2).extrude(0.6))
for i in range(3):                                   # bars along y
    sprue = sprue.union(cq.Workplane('XY').workplane(offset=-0.9).center(i * pitch, pitch / 2)
                        .rect(1.2, pitch - 8.0).extrude(0.6))
# reset plunger, same local z as the caps (0 = PCB + 4.5): stem ends 0.1 mm above the switch (0.6 mm tall).
# Stem 3.0 mm across (was 2.0) so it covers the whole 1.95 x 2.8 switch top even with ~0.5 mm of play/tilt/offset.
plunger = (cq.Workplane('XY').workplane(offset=-1.5).circle(2.2).extrude(1.8).faces('>Z').edges().fillet(0.4)
           .union(cq.Workplane('XY').workplane(offset=-2.1).circle(3.3).extrude(0.6))   # flange 0.6 thick
           .union(cq.Workplane('XY').workplane(offset=-3.8).circle(1.5).extrude(1.9)))
export(plunger, 'tomtho_mk2_reset_plunger')
for j in range(2):                                   # two plungers (one spare) on the same sprue
    sprue = sprue.union(plunger.translate((3 * pitch, j * pitch, 0)))
    sprue = sprue.union(cq.Workplane('XY').workplane(offset=-0.9).center(2 * pitch + (4.3 + pitch - 2.2) / 2, j * pitch)
                        .rect(pitch - 4.3 - 2.2 + 1.0, 1.2).extrude(0.6))
export(sprue, 'tomtho_mk2_keycap_0.5u_x6_reset_x2_sprue')   # 0.5u x 0.5u caps x6 + reset plungers x2
json.dump({'Z_PB': Z_PB, 'Z_PT': Z_PT, 'PLATE_B': PLATE_B, 'PLATE_T': PLATE_T, 'KEYCAP_TOP': Z_PT + 6.0,
           'outline': [case_out[2] - case_out[0], case_out[3] - case_out[1]]},
          open(os.path.join(OUT, 'stack.json'), 'w'), indent=1)
print('stack', Z_PB, Z_PT, PLATE_B, PLATE_T, 'keycap top', Z_PT + 6.0)
