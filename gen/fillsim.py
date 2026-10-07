"""Approximate KiCad zone fill for the two GND pours and check that every GND pad
ends up in one connected copper body.  Raster 0.05 mm."""
import numpy as np
from scipy import ndimage

import design as D
import check as C

RES = 0.05
ZCLR = 0.25        # zone clearance to other nets
EDGE = 0.5         # zone to board edge
MINW = 0.2         # zone min thickness
THERM = 0.3        # thermal gap


def _grid():
    x1, y1, x2, y2 = D.BOARD
    nx = int((x2 - x1) / RES) + 1
    ny = int((y2 - y1) / RES) + 1
    return x1, y1, nx, ny


def _disk(r):
    n = int(np.ceil(r / RES))
    yy, xx = np.mgrid[-n:n + 1, -n:n + 1]
    return (xx * xx + yy * yy) * RES * RES <= r * r + 1e-9


def _paint(mask, o, grow, x0, y0):
    bx1, by1, bx2, by2 = o.bbox()
    bx1 -= grow; by1 -= grow; bx2 += grow; by2 += grow
    i1, i2 = max(0, int((bx1 - x0) / RES)), min(mask.shape[1] - 1, int((bx2 - x0) / RES) + 1)
    j1, j2 = max(0, int((by1 - y0) / RES)), min(mask.shape[0] - 1, int((by2 - y0) / RES) + 1)
    if i2 < i1 or j2 < j1:
        return
    xs = x0 + np.arange(i1, i2 + 1) * RES
    ys = y0 + np.arange(j1, j2 + 1) * RES
    X, Y = np.meshgrid(xs, ys)
    if o.kind == 'rect':
        r = o.rect
        dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
        dy = np.maximum(np.maximum(r[1] - Y, Y - r[3]), 0)
        d = np.hypot(dx, dy)
        sel = d <= grow + 1e-9
    else:
        ax, ay = o.a
        bx, by = o.b
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy
        if L2 < 1e-12:
            t = np.zeros_like(X)
        else:
            t = np.clip(((X - ax) * vx + (Y - ay) * vy) / L2, 0, 1)
        d = np.hypot(X - (ax + t * vx), Y - (ay + t * vy))
        sel = d <= o.rad + grow + 1e-9
    mask[j1:j2 + 1, i1:i2 + 1] |= sel


def simulate(tracks, vias, verbose=True, png=None):
    x0, y0, nx, ny = _grid()
    objs = C.build(tracks, vias)
    layers = ('F.Cu', 'B.Cu')
    fill = {}
    gndcu = {}
    for L in layers:
        blocked = np.zeros((ny, nx), bool)
        g = np.zeros((ny, nx), bool)
        for o in objs:
            if L not in o.layers and not (o.net == '<hole>'):
                continue
            if o.net == 'GND':
                _paint(g, o, 0.0, x0, y0)
                # thermal relief gap around pads (vias are solid-connected in KiCad by default -> treat as solid)
                if o.owner in D.PARTS:
                    _paint(blocked, o, THERM, x0, y0)
            else:
                _paint(blocked, o, ZCLR if o.net != '<hole>' else 0.3, x0, y0)
        # board edge
        e = int(EDGE / RES)
        blocked[:e, :] = blocked[-e:, :] = True
        blocked[:, :e] = blocked[:, -e:] = True
        ax1, ay1, ax2, ay2 = D.ANT_KEEPOUT
        blocked[max(0, int((ay1 - 1 - y0) / RES)):int((ay2 - y0) / RES) + 1,
                int((ax1 - x0) / RES):int((ax2 - x0) / RES) + 1] = True
        free = ~blocked
        # min thickness: opening with disk of MINW/2
        k = _disk(MINW / 2)
        free = ndimage.binary_opening(free, structure=k)
        fill[L] = free
        gndcu[L] = g
    # thermal spokes: a GND pad connects if the fill exists just outside its thermal gap
    ring_hits = []
    pad_objs = [o for o in objs if o.net == 'GND' and o.owner in D.PARTS]
    body = {L: fill[L] | gndcu[L] for L in layers}
    # add spoke connection pixels: pad dilated by THERM+RES touching fill => merge
    for o in pad_objs:
        for L in o.layers:
            if L not in layers:
                continue
            m = np.zeros((ny, nx), bool)
            _paint(m, o, THERM + 2 * RES, x0, y0)
            if (m & fill[L]).sum() * RES * RES >= 0.4 * 0.1:  # at least one 0.4mm spoke landing
                body[L] |= m & (fill[L] | gndcu[L] | (m & ~fill[L] & ~_other(o, objs, L, x0, y0, ny, nx)))
                ring_hits.append((o.desc, L))
    lab = {}
    offs = 0
    for L in layers:
        l, n = ndimage.label(body[L])
        l[l > 0] += offs
        lab[L] = l
        offs += n
    parent = list(range(offs + 1))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def at(L, x, y):
        return lab[L][int(round((y - y0) / RES)), int(round((x - x0) / RES))]

    for o in objs:
        if o.net == 'GND' and len(o.layers) >= 2 and 'F.Cu' in o.layers and 'B.Cu' in o.layers:
            cx, cy = (o.a if o.kind != 'rect' else ((o.rect[0] + o.rect[2]) / 2, (o.rect[1] + o.rect[3]) / 2))
            a, b = at('F.Cu', cx, cy), at('B.Cu', cx, cy)
            if a and b:
                parent[find(a)] = find(b)
    comps = {}
    for o in pad_objs:
        L = o.layers[0]
        cx, cy = ((o.rect[0] + o.rect[2]) / 2, (o.rect[1] + o.rect[3]) / 2) if o.kind == 'rect' else o.a
        lb = at(L, cx, cy)
        comps.setdefault(find(lb) if lb else -1, []).append(o.desc)
    main = max(comps, key=lambda k: len(comps[k]))
    isolated = [d for k, v in comps.items() if k != main for d in v]
    global LAST
    LAST = dict(comps=comps, main=main, body=body, fill=fill, gndcu=gndcu, lab=lab, x0=x0, y0=y0)
    if verbose:
        print(f'GND pads: {len(pad_objs)}, components: {len(comps)}, isolated: {isolated}')
        for L in layers:
            print(L, 'fill area %.0f mm2' % (fill[L].sum() * RES * RES))
    if png:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(2, 1, figsize=(26, 19))
        for ax, L in zip(axs, layers):
            ax.imshow(np.where(body[L], 1, 0) + np.where(gndcu[L], 1, 0), cmap='viridis', interpolation='nearest',
                      extent=(x0, x0 + nx * RES, y0 + ny * RES, y0))
            ax.set_title(L + ' GND pour (sim)')
        fig.savefig(png, dpi=70)
        plt.close(fig)
    return isolated


def _other(o, objs, L, x0, y0, ny, nx):
    # cells occupied by other-net copper near pad (spoke cannot cross them)
    m = np.zeros((ny, nx), bool)
    bx1, by1, bx2, by2 = o.bbox()
    for p in objs:
        if p is o or p.net == 'GND' or L not in p.layers:
            continue
        q1 = p.bbox()
        if q1[2] < bx1 - 1 or q1[0] > bx2 + 1 or q1[3] < by1 - 1 or q1[1] > by2 + 1:
            continue
        _paint(m, p, ZCLR, x0, y0)
    return m
