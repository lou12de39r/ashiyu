"""Courtyard overlap / board-fit check with rotated rectangles (separating-axis test)."""
import math
import design as D
from fplib import FP


def crt(ref):
    p = D.PARTS[ref]
    fp = FP[p['fp']]
    c = [l for l in fp['lines'] if l[0] == 'F.CrtYd']
    if c:
        xs = [v for l in c for v in (l[1], l[3])]; ys = [v for l in c for v in (l[2], l[4])]
        x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
    else:
        r = max(cc[3] for cc in fp['circles'] if cc[0] == 'F.CrtYd')
        x1, y1, x2, y2 = -r, -r, r, r
    pts = []
    for (x, y) in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
        dx, dy = D.rot(x, y, p['rot'])
        pts.append((p['x'] + dx, p['y'] + dy))
    return pts


def axes(poly):
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % len(poly)]
        yield (-(y2 - y1), x2 - x1)


def overlap(a, b):
    for ax in list(axes(a)) + list(axes(b)):
        n = math.hypot(*ax)
        ax = (ax[0] / n, ax[1] / n)
        pa = [p[0] * ax[0] + p[1] * ax[1] for p in a]
        pb = [p[0] * ax[0] + p[1] * ax[1] for p in b]
        if max(pa) <= min(pb) + 1e-6 or max(pb) <= min(pa) + 1e-6:
            return False
    return True


def run(verbose=True):
    polys = {r: crt(r) for r in D.PARTS}
    bad = []
    refs = sorted(polys)
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            if overlap(polys[a], polys[b]):
                bad.append(('overlap', a, b))
    x1, y1, x2, y2 = D.BOARD
    edge_ok = {'J1', 'SW67'}          # parts allowed to hang over the rear edge
    for r, P in polys.items():
        if r in edge_ok:
            continue
        if min(p[0] for p in P) < x1 or max(p[0] for p in P) > x2 or min(p[1] for p in P) < y1 or max(p[1] for p in P) > y2:
            bad.append(('off-board', r, ''))
    if verbose:
        for b in bad:
            print(*b)
        print(len(bad), 'problems')
    return bad


if __name__ == '__main__':
    run()
