"""(run with KiCad python) list GND zone fill outlines that contain no GND via / pad -> isolated islands"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
pts = {'F.Cu': [], 'B.Cu': []}
vias = []
padpos = {'F.Cu': [], 'B.Cu': []}
T = b.Tracks()
for t in (T[i] for i in range(len(T))):
    if t.GetNetname() == 'GND' and t.GetClass() == 'PCB_VIA':
        vias.append(t.GetPosition())
F = b.Footprints()
for fp in (F[i] for i in range(len(F))):
    PD = fp.Pads()
    for p in (PD[j] for j in range(len(PD))):
        if p.GetNetname() == 'GND':
            for L in pts:
                if p.IsOnLayer(b.GetLayerID(L)):
                    padpos[L].append((fp.GetReference() + '.' + p.GetNumber(), p.GetPosition()))
Z = b.Zones()
for z in (Z[i] for i in range(len(Z))):
    if z.GetNetname() != 'GND':
        continue
    for L in ('F.Cu', 'B.Cu'):
        lid = b.GetLayerID(L)
        if not z.IsOnLayer(lid):
            continue
        ps = z.GetFilledPolysList(lid)
        for i in range(ps.OutlineCount()):
            ol = ps.Outline(i)
            bb = ol.BBox()
            hv = [v for v in vias if bb.Contains(pcbnew.VECTOR2I(v)) and ps.Contains(pcbnew.VECTOR2I(v), i)]
            hp = [n for n, p in padpos[L] if bb.Contains(pcbnew.VECTOR2I(p)) and ps.Contains(pcbnew.VECTOR2I(p), i)]
            if not hv:
                print(L, 'island without via, pads', hp, 'bbox', round(bb.GetLeft() / 1e6, 2), round(bb.GetTop() / 1e6, 2),
                      round(bb.GetRight() / 1e6, 2), round(bb.GetBottom() / 1e6, 2), 'area', round(ol.Area() / 1e12, 2))
