"""(KiCad python) fix F.Cu Rx stubs left at the cut: shorten to the new via where one exists, otherwise delete"""
import sys, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); d = json.load(open(sys.argv[2])); mm = pcbnew.FromMM
dang = []
for v in d['violations']:
    if v['type'] == 'track_dangling':
        it = v['items'][0]; dang.append((it['pos']['x'], it['pos']['y']))
T = b.Tracks(); vias = []
for i in range(len(T)):
    t = T[i]
    if t.GetClass() == 'PCB_VIA':
        vias.append((t.GetPosition().x / 1e6, t.GetPosition().y / 1e6, t.GetNetname()))
rm = []
for i in range(len(T)):
    t = T[i]
    if t.GetClass() == 'PCB_VIA' or b.GetLayerName(t.GetLayer()) != 'F.Cu':
        continue
    s, e = t.GetStart(), t.GetEnd()
    for x, y in dang:
        for q, other in ((s, e), (e, s)):
            if abs(q.x / 1e6 - x) < 0.02 and abs(q.y / 1e6 - y) < 0.02:
                hit = [v for v in vias if v[2] == t.GetNetname() and abs(v[1] - y) < 0.02 and min(q.x, other.x) / 1e6 <= v[0] <= max(q.x, other.x) / 1e6]
                if hit:
                    np_ = pcbnew.VECTOR2I(mm(hit[0][0]), q.y)
                    if q == s: t.SetStart(np_)
                    else: t.SetEnd(np_)
                else:
                    rm.append(t)
seen = []
for t in rm:
    if any(t is z for z in seen): continue
    seen.append(t)
    b.Remove(t)
pcbnew.SaveBoard(sys.argv[1], b)
print('trimmed/removed', len(dang), len(rm))
