"""(KiCad python) finish the mk2 trackpad: hand-solder friendly QFN pads, rotate 90 deg so it is 49 (x) x 43 (y),
move the origin, add attribution silk.  usage: finish.py in out"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM
EXT = float(sys.argv[3]) if len(sys.argv) > 3 else 0.35
# 1) lengthen the IQS550 perimeter pads outwards by 0.35 mm (hotplate / hot-air friendly, easier to inspect)
F = b.Footprints()
for i in range(len(F)):
    f = F[i]
    if f.GetReference() != 'U1':
        continue
    c = f.GetPosition(); P = f.Pads()
    for j in range(len(P)):
        p = P[j]
        if p.GetNumber() in ('49', ''):
            continue
        s = p.GetSize(); q = p.GetPosition()
        dx, dy = q.x - c.x, q.y - c.y
        if abs(dx) > abs(dy):            # left / right rows
            long_ax = 'x'
        else:
            long_ax = 'y'
        ext = mm(EXT)
        # pad size is in pad-local coordinates; perimeter pads are rotated so their long side points outward
        p.SetSize(pcbnew.VECTOR2I(s.x + (ext if s.x > s.y else 0), s.y + (ext if s.y > s.x else 0)))
        if long_ax == 'x':
            p.SetPosition(pcbnew.VECTOR2I(q.x + (ext // 2 if dx > 0 else -ext // 2), q.y))
        else:
            p.SetPosition(pcbnew.VECTOR2I(q.x, q.y + (ext // 2 if dy > 0 else -ext // 2)))
# 2) rotate everything 90 deg CCW about the board centre, then move the top-left corner to (100, 100)
bb = b.GetBoardEdgesBoundingBox(); ctr = bb.GetCenter()
ang = pcbnew.EDA_ANGLE(90.0, pcbnew.DEGREES_T)

def each(coll):
    return [coll[i] for i in range(len(coll))]
for it in each(b.Footprints()) + each(b.Tracks()) + each(b.Drawings()) + each(b.Zones()):
    it.Rotate(ctr, ang)
bb = b.GetBoardEdgesBoundingBox()
dv = pcbnew.VECTOR2I(mm(100) - bb.GetLeft(), mm(100) - bb.GetTop())
for it in each(b.Footprints()) + each(b.Tracks()) + each(b.Drawings()) + each(b.Zones()):
    it.Move(dv)
# 3) attribution / title on the back silk
bb = b.GetBoardEdgesBoundingBox()
t = pcbnew.PCB_TEXT(b)
t.SetText('tomtho-slim mk2 trackpad 49x43 / 10Tx x 10Rx')
t.SetLayer(b.GetLayerID('B.SilkS')); t.SetTextSize(pcbnew.VECTOR2I(mm(0.7), mm(0.7))); t.SetTextThickness(mm(0.12))
t.SetMirrored(True)
t.SetPosition(pcbnew.VECTOR2I(bb.GetRight() - mm(14), bb.GetTop() + mm(6)))
b.Add(t)
pcbnew.SaveBoard(sys.argv[2], b)
bb = b.GetBoardEdgesBoundingBox()
print('board', round(bb.GetWidth() / 1e6, 2), 'x', round(bb.GetHeight() / 1e6, 2))
