"""Independent DRC-lite: clearance, connectivity, edge clearance, antenna keepout.
Not a replacement for KiCad DRC - a gate so we never hand over obviously broken copper."""
import math
from collections import defaultdict

import design as D

CLR = 0.15          # copper-copper
CLR_SAME_FP = 0.1   # pad-pad inside one footprint (module pads are 0.4 apart by design)
EDGE = 0.3
HOLE_CLR = 0.2


def seg_seg(p1, p2, q1, q2):
    def dot(a, b): return a[0] * b[0] + a[1] * b[1]
    def sub(a, b): return (a[0] - b[0], a[1] - b[1])
    d1, d2, r = sub(p2, p1), sub(q2, q1), sub(p1, q1)
    a, e, f_ = dot(d1, d1), dot(d2, d2), dot(d2, r)
    if a < 1e-12 and e < 1e-12:
        return math.dist(p1, q1)
    if a < 1e-12:
        s, t = 0.0, min(max(f_ / e, 0), 1)
    else:
        c = dot(d1, r)
        if e < 1e-12:
            t, s = 0.0, min(max(-c / a, 0), 1)
        else:
            b = dot(d1, d2)
            den = a * e - b * b
            s = min(max((b * f_ - c * e) / den, 0), 1) if den > 1e-12 else 0.0
            t = (b * s + f_) / e
            if t < 0:
                t, s = 0.0, min(max(-c / a, 0), 1)
            elif t > 1:
                t, s = 1.0, min(max((b - c) / a, 0), 1)
    cp = (p1[0] + d1[0] * s, p1[1] + d1[1] * s)
    cq = (q1[0] + d2[0] * t, q1[1] + d2[1] * t)
    # proper crossing => 0
    return math.dist(cp, cq)


def pt_rect(p, r):
    dx = max(r[0] - p[0], 0, p[0] - r[2])
    dy = max(r[1] - p[1], 0, p[1] - r[3])
    return math.hypot(dx, dy)


def seg_rect(a, b, r):
    # inside / crossing test via Liang-Barsky
    x0, y0 = a
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    ok = True
    for p, q in ((-dx, x0 - r[0]), (dx, r[2] - x0), (-dy, y0 - r[1]), (dy, r[3] - y0)):
        if abs(p) < 1e-12:
            if q < 0:
                ok = False
                break
        else:
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
    if ok and t0 <= t1:
        return 0.0
    corners = [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]
    d = min(pt_rect(a, r), pt_rect(b, r))
    for i in range(4):
        d = min(d, seg_seg(a, b, corners[i], corners[(i + 1) % 4]))
    return d


def rect_rect(r, s):
    dx = max(s[0] - r[2], r[0] - s[2], 0)
    dy = max(s[1] - r[3], r[1] - s[3], 0)
    return math.hypot(dx, dy)


class Obj:
    __slots__ = ('kind', 'layers', 'net', 'a', 'b', 'rad', 'rect', 'owner', 'desc')

    def bbox(self):
        if self.kind == 'rect':
            return self.rect
        return (min(self.a[0], self.b[0]) - self.rad, min(self.a[1], self.b[1]) - self.rad,
                max(self.a[0], self.b[0]) + self.rad, max(self.a[1], self.b[1]) + self.rad)


def dist(o, p):
    if o.kind == 'rect' and p.kind == 'rect':
        return rect_rect(o.rect, p.rect)
    if o.kind == 'rect':
        o, p = p, o
    if p.kind == 'rect':
        return seg_rect(o.a, o.b, p.rect) - o.rad
    return seg_seg(o.a, o.b, p.a, p.b) - o.rad - p.rad


def build(tracks, vias):
    objs = []

    def mk(kind, layers, net, owner, desc, a=None, b=None, rad=0, rect=None):
        o = Obj()
        o.kind, o.layers, o.net, o.owner, o.desc, o.a, o.b, o.rad, o.rect = kind, layers, net, owner, desc, a, b, rad, rect
        objs.append(o)
        return o

    for ref, p in D.PARTS.items():
        for (num, kind, shape, X, Y, W, H, drill, net) in D.pad_world(p):
            if kind == 'np':
                mk('cap', ('F.Cu', 'B.Cu', 'HOLE'), '<hole>', ref, f'{ref} NPTH', (X, Y), (X, Y), W / 2)
                continue
            layers = ('F.Cu',) if kind == 'smd' else ('F.Cu', 'B.Cu')
            netn = net or f'<nc:{ref}:{num}>'
            if shape in ('circle',):
                mk('cap', layers, netn, ref, f'{ref}.{num}', (X, Y), (X, Y), W / 2)
            elif shape == 'oval':
                if H >= W:
                    mk('cap', layers, netn, ref, f'{ref}.{num}', (X, Y - (H - W) / 2), (X, Y + (H - W) / 2), W / 2)
                else:
                    mk('cap', layers, netn, ref, f'{ref}.{num}', (X - (W - H) / 2, Y), (X + (W - H) / 2, Y), H / 2)
            else:
                mk('rect', layers, netn, ref, f'{ref}.{num}', rect=(X - W / 2, Y - H / 2, X + W / 2, Y + H / 2))
    for i, (layer, x1, y1, x2, y2, w, net) in enumerate(tracks):
        mk('cap', (layer,), net, f'trk{i}', f'track {net} {layer} ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})',
           (x1, y1), (x2, y2), w / 2)
    for i, (x, y, net) in enumerate(vias):
        mk('cap', ('F.Cu', 'B.Cu'), net, f'via{i}', f'via {net} ({x:.2f},{y:.2f})', (x, y), (x, y), D.VIA[0] / 2)
    return objs


def run(tracks, vias, verbose=True):
    objs = build(tracks, vias)
    grid = defaultdict(list)
    G = 2.0
    for i, o in enumerate(objs):
        x1, y1, x2, y2 = o.bbox()
        for gx in range(int(x1 // G) - 1, int(x2 // G) + 2):
            for gy in range(int(y1 // G) - 1, int(y2 // G) + 2):
                grid[(gx, gy)].append(i)
    errors = []
    parent = list(range(len(objs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    checked = set()
    for cell, ids in grid.items():
        for ii in range(len(ids)):
            for jj in range(ii + 1, len(ids)):
                i, j = ids[ii], ids[jj]
                if (i, j) in checked:
                    continue
                checked.add((i, j))
                o, p = objs[i], objs[j]
                common = set(o.layers) & set(p.layers)
                hole = '<hole>' in (o.net, p.net)
                if not common and not hole:
                    continue
                d = dist(o, p)
                if o.net == p.net and not hole:
                    if d <= 1e-4 and common - {'HOLE'}:
                        parent[find(i)] = find(j)
                    continue
                if hole and o.net == p.net:
                    continue
                if o.owner == p.owner and o.kind == 'rect' and p.kind == 'rect':
                    lim = CLR_SAME_FP
                elif hole:
                    lim = HOLE_CLR
                else:
                    lim = CLR
                if o.owner == p.owner and hole:
                    continue
                if d < lim - 1e-4:
                    errors.append(f'CLEARANCE {d:.3f}<{lim}: {o.desc}  <->  {p.desc}')
    # pads with the same number inside one part are internally connected
    first = {}
    for i, o in enumerate(objs):
        if o.owner in D.PARTS and not o.net.startswith('<'):
            k = (o.owner, o.desc)
            if k in first:
                parent[find(i)] = find(first[k])
            else:
                first[k] = i
    # connectivity
    groups = defaultdict(set)
    for i, o in enumerate(objs):
        if o.net.startswith('<'):
            continue
        groups[o.net].add(find(i))
    unrouted = {n: len(g) for n, g in groups.items() if len(g) > 1}
    # dangling stubs: count islands that contain no pad
    for n, g in groups.items():
        for root in g:
            members = [objs[i] for i in range(len(objs)) if objs[i].net == n and find(i) == root]
            if not any(m.owner in D.PARTS for m in members):
                errors.append(f'ISLAND without pad on {n}: {members[0].desc}')
    # edge clearance & keepout
    bx1, by1, bx2, by2 = D.BOARD
    ax1, ay1, ax2, ay2 = D.ANT_KEEPOUT
    for o in objs:
        if o.net.startswith('<hole') or o.owner.startswith('H'):
            continue
        x1, y1, x2, y2 = o.bbox()
        m = min(x1 - bx1, y1 - by1, bx2 - x2, by2 - y2)
        if m < EDGE and not (o.owner in ('J1', 'SW56')):
            errors.append(f'EDGE {m:.3f}: {o.desc}')
        if not o.owner in D.PARTS and o.kind == 'cap':
            if seg_rect(o.a, o.b, (ax1, ay1, ax2, ay2)) - o.rad < 0.0:
                errors.append(f'ANTENNA KEEPOUT: {o.desc}')
    if verbose:
        for e in errors[:60]:
            print(e)
        print(f'{len(errors)} errors; unrouted nets: {len(unrouted)}', dict(sorted(unrouted.items())))
    return errors, unrouted


if __name__ == '__main__':
    run(D.TRACKS, D.VIAS)
