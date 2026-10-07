"""(KiCad python) Derive the mk2 trackpad (49 x 43 mm, 10 Tx x 10 Rx) from GR-Trackpad65 (MIT, geek-rabb1t):
keep Tx5..Tx14 (x >= XCUT), drop Tx0..Tx4 and the PCBA rails, move the Rx series resistors that fall off the board.
Usage: python3 crop.py in.kicad_pcb out.kicad_pcb"""
import sys, pcbnew

XCUT, X1, Y0, Y1, R = 157.0, 200.0, 40.0, 89.0, 1.2
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
DROP_NETS = {f'/TX{k}' for k in range(0, 5)}
MOVE = {'R12': (161.2, 51.2, 180), 'R11': (161.2, 54.5, 180), 'R10': (161.2, 56.0, 180), 'R9': (161.2, 58.9, 180)}
RER = {'/RX6', '/RX7', '/RX8', '/RX9', 'Net-(U1-Rx6A)', 'Net-(U1-Rx7A)', 'Net-(U1-Rx8A)', 'Net-(U1-Rx9A)'}


def cx(item):
    return item.GetBoundingBox().GetCenter().x / 1e6


rm = []
F = b.Footprints()
for i in range(len(F)):
    f = F[i]
    ref = f.GetReference()
    if ref == 'REF**':
        rm.append(f)
    elif ref in MOVE:
        x, y, a = MOVE[ref]
        f.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        f.SetOrientationDegrees(a)
T = b.Tracks()
for i in range(len(T)):
    t = T[i]
    nm = t.GetNetname()
    if nm in DROP_NETS or (nm in RER and t.GetClass() != 'PCB_VIA' and b.GetLayerName(t.GetLayer()) == 'B.Cu'):
        rm.append(t)
    elif t.GetClass() == 'PCB_VIA' and nm in RER:
        rm.append(t)
    elif t.GetClass() == 'PCB_VIA':
        p = t.GetPosition()
        if p.x / 1e6 < XCUT + 0.5:
            rm.append(t)
        elif nm == '' and p.x / 1e6 < XCUT + 3.0 and (p.y / 1e6 < Y0 + 2.0 or p.y / 1e6 > Y1 - 2.0):
            rm.append(t)                     # frame vias that would sit in the new rounded corners
    else:
        s, e = t.GetStart().x / 1e6, t.GetEnd().x / 1e6
        if min(s, e) < XCUT + 0.3:
            rm.append(t)
D = b.Drawings()
for i in range(len(D)):
    d = D[i]
    L = b.GetLayerName(d.GetLayer())
    if L == 'Edge.Cuts':
        rm.append(d); continue
    sh = pcbnew.Cast_to_PCB_SHAPE(d) if d.GetClass() == 'PCB_SHAPE' else None
    if sh is not None and sh.GetNetname() in DROP_NETS:
        rm.append(d); continue
    bb = d.GetBoundingBox()
    if bb.GetLeft() / 1e6 < XCUT + 0.15:
        rm.append(d)
Z = b.Zones()
for i in range(len(Z)):
    z = Z[i]
    bb = z.GetBoundingBox()
    if bb.GetWidth() < mm(5) and bb.GetLeft() / 1e6 < XCUT + 0.15:
        rm.append(z)
for it in rm:
    b.Remove(it)
# new outline: rounded rectangle
def seg(a, c):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(b.GetLayerID('Edge.Cuts'))
    s.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); s.SetEnd(pcbnew.VECTOR2I(mm(c[0]), mm(c[1]))); s.SetWidth(mm(0.1)); b.Add(s)
def arc(c, a0):
    import math
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(b.GetLayerID('Edge.Cuts')); s.SetWidth(mm(0.1))
    pts = [(c[0] + R * math.cos(math.radians(a0 + d)), c[1] + R * math.sin(math.radians(a0 + d))) for d in (0, 45, 90)]
    s.SetArcGeometry(*[pcbnew.VECTOR2I(mm(x), mm(y)) for x, y in pts]); b.Add(s)
x0, x1, y0, y1 = XCUT, X1, Y0, Y1
seg((x0 + R, y0), (x1 - R, y0)); seg((x1, y0 + R), (x1, y1 - R)); seg((x1 - R, y1), (x0 + R, y1)); seg((x0, y1 - R), (x0, y0 + R))
arc((x1 - R, y0 + R), 270); arc((x1 - R, y1 - R), 0); arc((x0 + R, y1 - R), 90); arc((x0 + R, y0 + R), 180)
pcbnew.SaveBoard(sys.argv[2], b)
print('removed', len(rm))
