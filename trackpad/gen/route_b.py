"""Single-layer (B.Cu) routing of the trackpad reconnections with Freerouting, using a purpose-built DSN.
Rx7..9 get a pre-placed via onto their F.Cu Rx line (same x as the original Rx4/Rx5 vias).
Usage: python3 route_b.py board.kicad_pcb"""
import sys, os, json, subprocess, math
B = os.path.abspath(sys.argv[1]); W = os.path.join(os.path.dirname(B), 'work'); os.makedirs(W, exist_ok=True)
KPY = '/opt/kicad/AppDir/bin/python3'
RXV = {'/RX6': (158.54, 71.56), '/RX7': (162.66, 76.26), '/RX8': (158.5, 80.96), '/RX9': (158.5, 85.66)}
TGT = set(RXV) | {f'Net-(U1-Rx{k}A)' for k in (6, 7, 8, 9)}
dump = f'''
import pcbnew, json
b = pcbnew.LoadBoard({B!r}); o = {{'pads': [], 'trk': [], 'vias': [], 'edge': None}}
F = b.Footprints()
for i in range(len(F)):
    f = F[i]; P = f.Pads()
    for j in range(len(P)):
        p = P[j]
        if not p.IsOnLayer(b.GetLayerID('B.Cu')):
            continue
        q = p.GetPosition(); s = p.GetSize()
        o['pads'].append((f.GetReference(), p.GetNumber(), p.GetNetname(), q.x/1e6, q.y/1e6, s.x/1e6, s.y/1e6, p.GetOrientationDegrees()))
T = b.Tracks()
for i in range(len(T)):
    t = T[i]
    if t.GetClass() == 'PCB_VIA':
        q = t.GetPosition(); o['vias'].append((q.x/1e6, q.y/1e6, t.GetNetname()))
    elif b.GetLayerName(t.GetLayer()) == 'B.Cu':
        s, e = t.GetStart(), t.GetEnd(); o['trk'].append((s.x/1e6, s.y/1e6, e.x/1e6, e.y/1e6, t.GetWidth()/1e6, t.GetNetname()))
bb = b.GetBoardEdgesBoundingBox(); o['edge'] = (bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6)
json.dump(o, open({W + "/bgeo.json"!r}, 'w'))
'''
subprocess.run([KPY, '-c', dump], capture_output=True)
g = json.load(open(W + '/bgeo.json'))
um = lambda v: f'{v * 1000:.1f}'
x1, y1, x2, y2 = g['edge']; x1 += 0.35; y1 += 0.35; x2 -= 0.35; y2 -= 0.35
o = ['(pcb tp_b\n (parser (string_quote ")(space_in_quoted_tokens on))\n (resolution um 10)\n (unit um)\n (structure\n',
     '  (layer B.Cu (type signal))\n',
     f'  (boundary (path pcb 0 {um(x1)} {um(-y1)} {um(x2)} {um(-y1)} {um(x2)} {um(-y2)} {um(x1)} {um(-y2)} {um(x1)} {um(-y1)}))\n']
CL = 0.0
for (ref, num, net, x, y, w, h, a) in g['pads']:
    if net in TGT:
        continue
    r = math.hypot(w, h) / 2 if a % 90 else None
    if r:
        o.append(f'  (keepout "" (circle B.Cu {um(2 * r + CL)} {um(x)} {um(-y)}))\n')
    else:
        if a % 180 == 90:
            w, h = h, w
        o.append(f'  (keepout "" (rect B.Cu {um(x - w / 2 - CL / 2)} {um(-y - h / 2 - CL / 2)} {um(x + w / 2 + CL / 2)} {um(-y + h / 2 + CL / 2)}))\n')
for (ax, ay, bx, by, w, net) in g['trk']:
    if net in TGT:
        continue
    o.append(f'  (keepout "" (path B.Cu {um(w + CL)} {um(ax)} {um(-ay)} {um(bx)} {um(-by)}))\n')
for (x, y, net) in g['vias']:
    if net in TGT:
        continue
    o.append(f'  (keepout "" (circle B.Cu {um(0.45 + CL)} {um(x)} {um(-y)}))\n')
o.append('  (via "Via450")\n  (rule (width 130) (clearance 130))\n )\n (placement\n')
pins = {}
k = 0
for (ref, num, net, x, y, w, h, a) in g['pads']:
    if net in TGT:
        k += 1; o.append(f'  (component P{k} (place P{k} {um(x)} {um(-y)} front 0))\n'); pins.setdefault(net, []).append((f'P{k}', w, h, a))
for net, (x, y) in RXV.items():
    k += 1; o.append(f'  (component P{k} (place P{k} {um(x)} {um(-y)} front 0))\n'); pins.setdefault(net, []).append((f'P{k}', 0.45, 0.45, 0))
o.append(' )\n (library\n')
for net, L in pins.items():
    for (c, w, h, a) in L:
        if a % 180 == 90:
            w, h = h, w
        o.append(f'  (image {c} (pin S{c} 1 0 0))\n  (padstack S{c} (shape (rect B.Cu {um(-w / 2)} {um(-h / 2)} {um(w / 2)} {um(h / 2)})))\n')
o.append('  (padstack "Via450" (shape (circle B.Cu 450)) (attach off))\n )\n (network\n')
for net, L in pins.items():
    o.append(f'  (net "{net}" (pins {" ".join(c + "-1" for c, *_ in L)}))\n')
o.append('  (class c1 ' + ' '.join(f'"{n}"' for n in pins) + ' (circuit (use_via "Via450")) (rule (width 130) (clearance 130)))\n )\n (wiring)\n)\n')
open(W + '/b.dsn', 'w').write(''.join(o))
print('pins', {n: len(v) for n, v in pins.items()})
for attempt in range(4):
    if os.path.exists(W + '/b.ses'):
        os.remove(W + '/b.ses')
    subprocess.run(['java', '-jar', '/opt/kicad/freerouting.jar', '-de', W + '/b.dsn', '-do', W + '/b.ses', '-mp', '60', '-mt', '1'],
                   capture_output=True, text=True, timeout=600)
    if os.path.exists(W + '/b.ses') and os.path.getsize(W + '/b.ses') > 50:
        break
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gen'))
from pcbio import read_ses
t, v = read_ses(W + '/b.ses')
print('routed segments', len(t), 'vias', len(v), {n for *_, n in t})
json.dump({'t': t, 'v': [(x, y, n) for n, (x, y) in RXV.items()]}, open(W + '/new.json', 'w'))
imp = f'''
import pcbnew, json
b = pcbnew.LoadBoard({B!r}); d = json.load(open({W + "/new.json"!r})); mm = pcbnew.FromMM
TG = set({sorted(TGT)!r}); T = b.Tracks(); rm = []
for i in range(len(T)):
    t = T[i]
    if t.GetNetname() in TG and (t.GetClass() == 'PCB_VIA' or b.GetLayerName(t.GetLayer()) == 'B.Cu'):
        rm.append(t)
for t in rm:
    b.Remove(t)
for (L, x1, y1, x2, y2, w, n) in d['t']:
    tr = pcbnew.PCB_TRACK(b); tr.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1))); tr.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    tr.SetWidth(mm(w)); tr.SetLayer(b.GetLayerID('B.Cu')); tr.SetNet(b.FindNet(n)); b.Add(tr)
for (x, y, n) in d['v']:
    vi = pcbnew.PCB_VIA(b); vi.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); vi.SetWidth(mm(0.45)); vi.SetDrill(mm(0.2))
    vi.SetNet(b.FindNet(n)); b.Add(vi)
pcbnew.SaveBoard({B!r}, b)
'''
subprocess.run([KPY, '-c', imp], capture_output=True)
