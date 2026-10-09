"""Route the unconnected nets of the cropped trackpad with Freerouting.
Electrode polygons (gr_poly with nets) are not exported by KiCad's DSN writer, so they are injected as F.Cu keepouts.
Usage: python3 route_tp.py board.kicad_pcb"""
import sys, subprocess, os, json
B = os.path.abspath(sys.argv[1]); W = os.path.join(os.path.dirname(B), 'work')
os.makedirs(W, exist_ok=True)
KPY = '/opt/kicad/AppDir/bin/python3'
RER = ['/RX7', '/RX8', '/RX9']
dump = f'''
import pcbnew, json
b = pcbnew.LoadBoard({B!r})
pcbnew.ExportSpecctraDSN(b, {W + "/tp.dsn"!r})
out = []
D = b.Drawings()
for i in range(len(D)):
    d = D[i]
    if d.GetClass() != 'PCB_SHAPE' or b.GetLayerName(d.GetLayer()) != 'F.Cu':
        continue
    s = pcbnew.Cast_to_PCB_SHAPE(d)
    if s.GetNetname() in {RER!r}:
        continue
    poly = s.GetPolyShape() if s.GetShape() == pcbnew.SHAPE_T_POLY else None
    if poly is None or poly.OutlineCount() == 0:
        bb = s.GetBoundingBox(); out.append([(bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()), (bb.GetRight(), bb.GetBottom()), (bb.GetLeft(), bb.GetBottom())]); continue
    o = poly.Outline(0)
    out.append([(o.CPoint(k).x, o.CPoint(k).y) for k in range(o.PointCount())])
json.dump(out, open({W + "/polys.json"!r}, 'w'))
'''
subprocess.run([KPY, '-c', dump], capture_output=True)
polys = json.load(open(W + '/polys.json'))
dsn = open(W + '/tp.dsn').read()
ko = []
for p in polys:
    pts = ' '.join(f'{x / 1000:.1f} {-y / 1000:.1f}' for x, y in p + [p[0]])
    ko.append(f'    (keepout "" (polygon F.Cu 0 {pts}))\n')
i = dsn.index('    (via "Via', dsn.index('(structure'))
dsn = dsn[:i] + ''.join(ko) + dsn[i:]
open(W + '/tp_ko.dsn', 'w').write(dsn)
print('keepouts', len(ko))
for attempt in range(3):
    if os.path.exists(W + '/tp.ses'):
        os.remove(W + '/tp.ses')
    r = subprocess.run(['java', '-jar', '/opt/kicad/freerouting.jar', '-de', W + '/tp_ko.dsn', '-do', W + '/tp.ses', '-mp', '20',
                        '-mt', '1'], capture_output=True, text=True, timeout=500)
    if os.path.exists(W + '/tp.ses') and os.path.getsize(W + '/tp.ses') > 100:
        break
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gen'))
from pcbio import read_ses
t, v = read_ses(W + '/tp.ses')
nets = set(RER) | {f'Net-(U1-Rx{k}A)' for k in (7, 8, 9)}
t = [x for x in t if x[6] in nets]; v = [x for x in v if x[2] in nets]
print('new tracks', len(t), 'vias', len(v))
json.dump({'t': t, 'v': v}, open(W + '/new.json', 'w'))
imp = f'''
import pcbnew, json
b = pcbnew.LoadBoard({B!r})
d = json.load(open({W + "/new.json"!r}))
mm = pcbnew.FromMM
for (L, x1, y1, x2, y2, w, n) in d['t']:
    tr = pcbnew.PCB_TRACK(b); tr.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1))); tr.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    tr.SetWidth(mm(w)); tr.SetLayer(b.GetLayerID(L)); tr.SetNet(b.FindNet(n)); b.Add(tr)
for (x, y, n) in d['v']:
    vi = pcbnew.PCB_VIA(b); vi.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); vi.SetWidth(mm(0.45)); vi.SetDrill(mm(0.2))
    vi.SetNet(b.FindNet(n)); b.Add(vi)
pcbnew.SaveBoard({B!r}, b)
print('ok')
'''
r = subprocess.run([KPY, '-c', imp], capture_output=True, text=True)
print(r.stdout.strip()[-200:], r.stderr.strip()[-300:] if 'Error' in r.stderr else '')
