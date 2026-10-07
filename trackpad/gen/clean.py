"""(KiCad python) remove dangling tracks reported by DRC json; usage: clean.py board drc.json"""
import sys, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); d = json.load(open(sys.argv[2]))
pts = []
for v in d['violations']:
    if v['type'] in ('track_dangling', 'via_dangling'):
        for it in v['items']:
            pts.append((it['pos']['x'], it['pos']['y'], it['description']))
T = b.Tracks(); rm = []
for i in range(len(T)):
    t = T[i]
    for x, y, desc in pts:
        if t.GetClass() == 'PCB_VIA':
            p = t.GetPosition()
            if 'Via' in desc and abs(p.x / 1e6 - x) < 0.01 and abs(p.y / 1e6 - y) < 0.01:
                rm.append(t); break
        else:
            s, e = t.GetStart(), t.GetEnd()
            if 'Track' in desc and any(abs(q.x / 1e6 - x) < 0.01 and abs(q.y / 1e6 - y) < 0.01 for q in (s, e, t.GetCenter() if hasattr(t, 'GetCenter') else s)):
                rm.append(t); break
for t in rm:
    b.Remove(t)
pcbnew.SaveBoard(sys.argv[1], b)
print('removed', len(rm))
