"""Tiny 2-layer A* maze router for individual fix-up connections (0.05mm grid)."""
import heapq
import math
import numpy as np

import design as D
import check as C
import fillsim as F

RES = 0.05


def _mask(objs, layer, grow, win, net):
    x0, y0, x1, y1 = win
    nx, ny = int((x1 - x0) / RES) + 1, int((y1 - y0) / RES) + 1
    m = np.zeros((ny, nx), bool)
    for o in objs:
        if o.net == net:
            continue
        if layer not in o.layers and o.net != '<hole>':
            continue
        bb = o.bbox()
        if bb[2] < x0 - 2 or bb[0] > x1 + 2 or bb[3] < y0 - 2 or bb[1] > y1 + 2:
            continue
        F._paint(m, o, grow + (0.05 if o.net == '<hole>' else 0), x0, y0)
    # board edge / keepout
    bx1, by1, bx2, by2 = D.BOARD
    xs = x0 + np.arange(nx) * RES
    ys = y0 + np.arange(ny) * RES
    X, Y = np.meshgrid(xs, ys)
    m |= (X < bx1 + 0.3 + grow) | (X > bx2 - 0.3 - grow) | (Y < by1 + 0.3 + grow) | (Y > by2 - 0.3 - grow)
    ax1, ay1, ax2, ay2 = D.ANT_KEEPOUT
    m |= (X > ax1 - grow) & (X < ax2 + grow) & (Y < ay2 + grow)
    return m


def route(tracks, vias, net, src, dst_pts, w=0.3, clr=0.16, margin=6.0, via_cost=40):
    """src: (x,y) on F.Cu (pad centre). dst_pts: list of (x,y,layer) acceptable targets."""
    objs = C.build(tracks, vias)
    xs = [src[0]] + [p[0] for p in dst_pts]
    ys = [src[1]] + [p[1] for p in dst_pts]
    win = (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)
    tm = {L: _mask(objs, L, clr + w / 2, win, net) for L in ('F.Cu', 'B.Cu')}
    vr = D.VIA[0] / 2
    vm = _mask(objs, 'F.Cu', clr + vr + 0.05, win, net) | _mask(objs, 'B.Cu', clr + vr + 0.05, win, net)
    padobjs = [o for o in objs if o.owner in D.PARTS and o.net == net]
    vm |= _mask(padobjs, 'F.Cu', vr + 0.25, win, '__none__') & ~_mask([], 'F.Cu', 0, win, '__none__')
    xs_ = win[0] + np.arange(vm.shape[1]) * RES
    ys_ = win[1] + np.arange(vm.shape[0]) * RES
    XX, YY = np.meshgrid(xs_, ys_)
    for ref in ('U1',):
        p = D.PARTS[ref]
        vm |= (np.abs(XX - p['x']) < 5.25 + vr + 0.1) & (np.abs(YY - p['y']) < 7.75 + vr + 0.1)
    x0, y0 = win[0], win[1]
    ny, nx = tm['F.Cu'].shape

    def cell(x, y):
        return int(round((y - y0) / RES)), int(round((x - x0) / RES))
    s = (0,) + cell(*src)
    goals = {}
    for (x, y, L) in dst_pts:
        j, i = cell(x, y)
        goals[(0 if L == 'F.Cu' else 1, j, i)] = True
    # allow start/goal cells even if inside own-net copper (mask excludes own net already)
    gl = list(goals)

    def h(n):
        return min(math.hypot(n[1] - g[1], n[2] - g[2]) for g in gl)
    openl = [(h(s), 0.0, s, None)]
    came = {}
    best = {s: 0.0}
    dirs = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    L = ('F.Cu', 'B.Cu')
    found = None
    it = 0
    while openl:
        f_, g, n, par = heapq.heappop(openl)
        if n in came:
            continue
        came[n] = par
        if n in goals:
            found = n
            break
        it += 1
        if it > 2_000_000:
            break
        l, j, i = n
        for dj, di, c in dirs:
            jj, ii = j + dj, i + di
            if not (0 <= jj < ny and 0 <= ii < nx) or tm[L[l]][jj, ii]:
                continue
            nn = (l, jj, ii)
            ng = g + c
            if ng < best.get(nn, 1e18):
                best[nn] = ng
                heapq.heappush(openl, (ng + h(nn), ng, nn, n))
        if not vm[j, i]:
            nn = (1 - l, j, i)
            ng = g + via_cost
            if ng < best.get(nn, 1e18):
                best[nn] = ng
                heapq.heappush(openl, (ng + h(nn), ng, nn, n))
    if not found:
        return None
    path = []
    n = found
    while n:
        path.append(n)
        n = came[n]
    path.reverse()
    # string-pull each single-layer run
    def clear(l, a, b):
        n = int(max(abs(a[1] - b[1]), abs(a[2] - b[2])) * 2) + 1
        for k in range(n + 1):
            jj = int(round(a[1] + (b[1] - a[1]) * k / n))
            ii = int(round(a[2] + (b[2] - a[2]) * k / n))
            if tm[L[l]][jj, ii]:
                return False
        return True
    runs, cur = [], [path[0]]
    for a, b in zip(path, path[1:]):
        if a[0] != b[0]:
            runs.append(cur)
            cur = [b]
        else:
            cur.append(b)
    runs.append(cur)
    newpath = []
    for run in runs:
        k = 0
        out = [run[0]]
        while k < len(run) - 1:
            m = len(run) - 1
            while m > k + 1 and not clear(run[k][0], run[k], run[m]):
                m -= 1
            out.append(run[m])
            k = m
        newpath += out
    path = newpath
    # convert to segments, merge collinear
    newt, newv = [], []
    pts = [(path[0][0], x0 + path[0][2] * RES, y0 + path[0][1] * RES)]
    for a, b in zip(path, path[1:]):
        if a[0] != b[0]:
            newv.append((x0 + a[2] * RES, y0 + a[1] * RES, net))
        pts.append((b[0], x0 + b[2] * RES, y0 + b[1] * RES))
    seg_start = pts[0]
    prev = pts[0]
    pdir = None
    for p in pts[1:]:
        if p[0] != prev[0]:
            if (seg_start[1], seg_start[2]) != (prev[1], prev[2]):
                newt.append((L[prev[0]], seg_start[1], seg_start[2], prev[1], prev[2], w, net))
            seg_start, prev, pdir = p, p, None
            continue
        if (seg_start[1], seg_start[2]) != (prev[1], prev[2]):
            newt.append((L[prev[0]], seg_start[1], seg_start[2], prev[1], prev[2], w, net))
        seg_start = prev
        prev = p
    if (seg_start[1], seg_start[2]) != (prev[1], prev[2]):
        newt.append((L[prev[0]], seg_start[1], seg_start[2], prev[1], prev[2], w, net))
    # exact start point
    if newt:
        l0, xa, ya, xb, yb, ww, nn = newt[0]
        newt[0] = (l0, src[0], src[1], xb, yb, ww, nn) if abs(xa - src[0]) < 0.06 and abs(ya - src[1]) < 0.06 else newt[0]
    return newt, newv
