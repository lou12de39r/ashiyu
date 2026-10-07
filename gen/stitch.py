"""Place a short stub + via next to GND pads so the B.Cu pour picks them up."""
import math
import design as D
import check as C

VIA_R = D.VIA[0] / 2


def _obstacles(tracks, vias):
    objs = C.build(tracks, vias)
    return [o for o in objs if o.net != 'GND']


def _ok_via(x, y, obs):
    bx1, by1, bx2, by2 = D.BOARD
    if min(x - bx1, y - by1, bx2 - x, by2 - y) < VIA_R + 0.5:
        return False
    ax1, ay1, ax2, ay2 = D.ANT_KEEPOUT
    if C.pt_rect((x, y), (ax1, ay1 - 1, ax2, ay2)) < VIA_R + 0.3:
        return False
    v = C.Obj()
    v.kind, v.a, v.b, v.rad, v.layers = 'cap', (x, y), (x, y), VIA_R, ('F.Cu', 'B.Cu')
    for o in obs:
        bb = o.bbox()
        if bb[0] - 1 > x or bb[2] + 1 < x or bb[1] - 1 > y or bb[3] + 1 < y:
            continue
        lim = 0.25 if o.net == '<hole>' else 0.2
        if C.dist(v, o) < lim:
            return False
    return True


def _ok_stub(a, b, w, obs, owner):
    ax1, ay1, ax2, ay2 = D.ANT_KEEPOUT
    if C.seg_rect(a, b, (ax1, ay1 - 1, ax2, ay2)) - w / 2 < 0.02:
        return False
    s = C.Obj()
    s.kind, s.a, s.b, s.rad, s.layers = 'cap', a, b, w / 2, ('F.Cu',)
    for o in obs:
        if 'F.Cu' not in o.layers and o.net != '<hole>':
            continue
        if C.dist(s, o) < 0.17:
            return False
    return True


def stitch(tracks, vias, pads, w=0.3, rmax=4.0):
    """pads: list of (ref, num). returns (new_tracks, new_vias, failures)"""
    tracks, vias = list(tracks), list(vias)
    fails = []
    for ref, num in pads:
        p = D.PARTS[ref]
        hits = [h for h in D.pad_world(p) if h[0] == num]
        best = None
        obs = _obstacles(tracks, vias)
        for h in hits:
            _, kind, shape, X, Y, W, H, _, _ = h
            step = 0.2
            n = int(rmax / step)
            for i in range(-n, n + 1):
                for j in range(-n, n + 1):
                    x, y = X + i * step, Y + j * step
                    d = math.hypot(x - X, y - Y)
                    if d > rmax or d < 0.5 or (best and d >= best[0]):
                        continue
                    if not _ok_via(x, y, obs):
                        continue
                    if not _ok_stub((X, Y), (x, y), w, obs, ref):
                        continue
                    best = (d, X, Y, x, y)
        if best:
            _, X, Y, x, y = best
            tracks.append(('F.Cu', X, Y, x, y, w, 'GND'))
            vias.append((x, y, 'GND'))
        else:
            fails.append((ref, num))
    return tracks, vias, fails


def gnd_pads():
    out = []
    for ref, p in D.PARTS.items():
        for num, net in p['nets'].items():
            if net == 'GND' and not ref.startswith('TP'):
                out.append((ref, num))
    return sorted(set(out))


def stitch_grid(tracks, vias, region, pitch=2.5, min_sep=2.0):
    """Drop GND stitching vias on free grid points inside region (x1,y1,x2,y2)."""
    tracks, vias = list(tracks), list(vias)
    obs = _obstacles(tracks, vias)
    gv = [(x, y) for (x, y, n) in vias if n == 'GND']
    x1, y1, x2, y2 = region
    y = y1
    added = 0
    while y <= y2:
        x = x1
        while x <= x2:
            if all(math.hypot(x - a, y - b) >= min_sep for a, b in gv) and _ok_via(x, y, obs):
                # do not sit on GND pads' thermal ring either
                vias.append((x, y, 'GND'))
                gv.append((x, y))
                added += 1
            x += pitch
        y += pitch
    return tracks, vias, added
