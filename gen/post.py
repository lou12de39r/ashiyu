"""routed.pkl -> drop zero-length segments, add GND stitching vias over the board -> routed_final.pkl"""
import pickle, sys
import design as D
import stitch as ST

pitch = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
t, v = pickle.load(open('routed.pkl', 'rb'))
t = [x for x in t if (round(x[1], 3), round(x[2], 3)) != (round(x[3], 3), round(x[4], 3))]
x1, y1, x2, y2 = D.BOARD
# keep stitching vias away from rotated (thumb) keys: the clearance checker treats pads as axis-aligned
rotp = [(q['x'], q['y']) for q in D.PARTS.values() if q['rot'] % 90]
_ok = ST._ok_via
ST._ok_via = lambda x, y, obs: _ok(x, y, obs) and all((x - a) ** 2 + (y - b) ** 2 > 6.0 ** 2 for a, b in rotp)
drop = set()
import os
if os.path.exists('drop_vias.txt'):
    drop = {tuple(map(float, l.split())) for l in open('drop_vias.txt') if l.strip()}
# escape vias the router did not use (nothing on B.Cu reaches them): drop the via and the F.Cu stubs ending on it
def _at(seg, x, y):
    return any(abs(seg[i] - x) < 0.02 and abs(seg[i + 1] - y) < 0.02 for i in (1, 3))
_dead = [x for x in v if x[2] != 'GND' and not any(s[0] == 'B.Cu' and s[6] == x[2] and _at(s, x[0], x[1]) for s in t)]
for x in _dead:
    t = [s for s in t if not (s[6] == x[2] and _at(s, x[0], x[1]))]
v = [x for x in v if x not in _dead]
print('unused escape vias dropped', len(_dead), _dead)
t, v, n = ST.stitch_grid(t, v, (x1 + 1.5, y1 + 1.5, x2 - 1.5, y2 - 1.5), pitch=pitch, min_sep=pitch * 0.6)
v = [x for x in v if not (x[2] == 'GND' and (round(x[0], 2), round(x[1], 2)) in drop)]
print('stitching vias added', n, 'dropped', len(drop))
pickle.dump((t, v), open('routed_final.pkl', 'wb'))
