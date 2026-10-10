"""Collect everything the case needs from the layout and the finished PCB -> case_inputs.json.

Run locally with KiCad's python (needs pcbnew):  /opt/kicad/AppDir/bin/python3 export_inputs.py
The CadQuery builder (build_case.py, run in CI) reads only case_inputs.json.
Coordinates: layout / KiCad mm, origin at the rear-left corner of the layout outline, +y towards the user.
"""
import json, math, os, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'gen'))
import design as D  # noqa: E402

L = json.load(open(os.path.join(HERE, '..', 'layout_v20.json')))
PX, PY = L['pitch']

# Part heights above the PCB top (mm).  From the LCSC STEP models where available (case CI, measure2.txt),
# datasheets otherwise.  Anything >= PLATE_GAP - 0.4 gets a pocket in the underside of the plate.
HEIGHT = {
    'USB_C_HRO_TYPE-C-31-M-12': 3.31,    # LCSC STEP
    'JST_SH_SM02B-SRSS-TB': 2.95,        # JST SH side entry (datasheet)
    'Raytac_MDBT50Q': 2.2,               # Raytac MDBT50Q-1MV2 datasheet (10 x 15.5 x 2.2)
    'SW_TS-1928-B': 1.5,
    'FPC_0.5mm_6P_HC': 1.2,
    'SW_ALPS_SKRA_6.2mm': 3.4,
    'SW_SPDT_PCM12': 1.9,                # LCSC STEP
    'LED_0603': 0.7, 'R_0603': 0.5, 'C_0603': 0.9, 'LED_XL-2012_Bicolor': 0.8,   # LCSC STEP
    'D_SOD-123': 1.1, 'SOT-23': 1.1, 'SOT-23-5': 1.2, 'SOT-23-6': 1.6,           # LCSC STEP
}
DEFAULT_H = 1.2

# ACC keycap plate holes (ClickBoard Tenkey case: cap body + 0.14 per side)
def hole(k):
    if (k['w_u'], k['h_u']) == (1.25, 1.0):
        return 21.0, 16.0
    if (k['w_u'], k['h_u']) == (0.5, 0.5):
        return 7.25, 7.0          # custom flange cap (not an ACC part)
    return k['w_u'] * PX - 2.0, k['h_u'] * PY - 2.0


def leg_centres(k):
    """ACC keycap leg zones (r 2.0 keep-out, Salicylic-acid3 footprints): corners minus 1.7 mm."""
    if (k['w_u'], k['h_u']) == (0.5, 0.5):
        return []
    ox, oy = k['w_u'] * PX / 2 - 1.7, k['h_u'] * PY / 2 - 1.7
    r = math.radians(k['rot_deg'])
    out = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            lx, ly = sx * ox, sy * oy
            out.append((k['cx'] + lx * math.cos(r) - ly * math.sin(r), k['cy'] + lx * math.sin(r) + ly * math.cos(r)))
    return out


def dist_hole(px, py, k):
    w, h = hole(k)
    r = math.radians(k['rot_deg'])
    dx, dy = px - k['cx'], py - k['cy']
    lx = dx * math.cos(r) + dy * math.sin(r)
    ly = -dx * math.sin(r) + dy * math.cos(r)
    ex, ey = max(abs(lx) - w / 2, 0), max(abs(ly) - h / 2, 0)
    return math.hypot(ex, ey) if (ex or ey) else -min(w / 2 - abs(lx), h / 2 - abs(ly))


board = pcbnew.LoadBoard(os.path.join(HERE, '..', 'tomtho_mk2.kicad_pcb'))
parts = []
fps = board.GetFootprints()
for i in range(len(fps)):
    f = fps[i]
    ref = f.GetReference()
    fpn = str(f.GetFPID().GetLibItemName())
    cy = f.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if not cy.IsEmpty() else f.GetBoundingBox(False)
    parts.append({'ref': ref, 'fp': fpn, 'x': f.GetPosition().x / 1e6, 'y': f.GetPosition().y / 1e6,
                  'rot': f.GetOrientationDegrees(),
                  'bbox': [bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6],
                  'h': HEIGHT.get(fpn, DEFAULT_H)})


def dist_parts(px, py, skip=()):
    m = 99.0
    for p in parts:
        if p['ref'] in skip or p['ref'].startswith('H'):
            continue
        x0, y0, x1, y1 = p['bbox']
        m = min(m, math.hypot(max(x0 - px, 0, px - x1), max(y0 - py, 0, py - y1)))
    return m


# plate support posts (1.2 x 1.2): in the vertical webs between horizontally neighbouring keys, clear of keycap
# holes, keycap leg zones and parts; then thinned out to one per ~30 mm
keys = [k for k in L['keys'] if k['rot_deg'] == 0]
cands = []
for a in keys:
    for b in keys:
        if b['cx'] <= a['cx'] or not (15 < b['cx'] - a['cx'] < 21):
            continue
        x = (a['cx'] + a['w_u'] * PX / 2 + b['cx'] - b['w_u'] * PX / 2) / 2
        y0 = max(a['cy'] - a['h_u'] * PY / 2, b['cy'] - b['h_u'] * PY / 2)
        y1 = min(a['cy'] + a['h_u'] * PY / 2, b['cy'] + b['h_u'] * PY / 2)
        if y1 - y0 < 9:
            continue
        y = (y0 + y1) / 2
        ok = all(dist_hole(x, y, k) >= 0.35 + 0.6 * 0 for k in L['keys']) \
            and all(math.hypot(x - lx, y - ly) >= 2.0 + 0.85 for k in L['keys'] for lx, ly in leg_centres(k)) \
            and dist_parts(x, y) >= 0.9
        if ok:
            cands.append((x, y))
posts = []
for c in sorted(cands):
    if all(math.hypot(c[0] - p[0], c[1] - p[1]) > 30 for p in posts):
        posts.append(c)

out = {
    'outline': L['outline'], 'outline_r': 5.0, 'pitch': [PX, PY],
    'board': list(D.BOARD), 'board_r': D.CORNER_R, 'pcb_t': 1.2,
    'keys': [dict(k, hole=list(hole(k))) for k in L['keys']],
    'leds': L['leds'],
    'trackpad': L['trackpad'],
    'screws': [list(s) for s in D.SCREWS],
    'posts': [list(p) for p in posts],
    'battery': list(D.BATTERY_AREA),
    'slots': [list(s) for s in D.SLOTS],
    'parts': parts,
    'switch_centres': [[p['x'], p['y'], p['rot']] for p in parts if p['fp'] == 'SW_ALPS_SKRA_6.2mm'],
}
for ref in ('J1', 'SW101', 'SW102', 'J2', 'U1', 'J3'):
    out[ref] = next(p for p in parts if p['ref'] == ref)
json.dump(out, open(os.path.join(HERE, 'case_inputs.json'), 'w'), indent=1, ensure_ascii=False)
print(len(out['keys']), 'keys', len(posts), 'posts', len(out['screws']), 'screws', len(parts), 'parts')
