"""Z-buffer preview renderer for binary STLs (numpy only).  Places keycaps on the layout.

usage: python3 render_zbuf.py out.png elev azim W H  <scene.json>
scene.json: {"meshes": [{"stl": path, "color": "#rrggbb", "gloss": 0..1,
                          "place": [[x, y, z, rot_deg], ...]   (optional; default identity)}],
             "light": [x, y, z]}
"""
import json, sys
import numpy as np
import matplotlib.colors as mc
from PIL import Image


def load(path):
    with open(path, 'rb') as f:
        f.read(80)
        n = np.frombuffer(f.read(4), np.uint32)[0]
        d = np.frombuffer(f.read(int(n) * 50), dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    return d['v'].astype(np.float64)


def main():
    out, elev, azim, W, H, scene = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
    S = json.load(open(scene))
    tris, cols, gloss = [], [], []
    for m in S['meshes']:
        t0 = load(m['stl'])
        for (x, y, z, r) in m.get('place', [[0, 0, 0, 0]]):
            a = np.radians(r)
            R = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
            tt = t0 @ R.T + np.array([x, y, z])
            if 'tilt' in m:                       # rotate about the X axis through (Y = y0, z = 0), then lift
                ang, y0, z0 = m['tilt']
                c, s_ = np.cos(np.radians(ang)), np.sin(np.radians(ang))
                Y, Zc = tt[..., 1] - y0, tt[..., 2].copy()
                tt[..., 1] = y0 + Y * c - Zc * s_
                tt[..., 2] = z0 + Y * s_ + Zc * c
            tris.append(tt)
            cols.append(np.tile(mc.to_rgb(m['color']), (len(t0), 1)))
            gloss.append(np.full(len(t0), m.get('gloss', 0.2)))
    T = np.concatenate(tris)
    C = np.concatenate(cols)
    G = np.concatenate(gloss)
    e, a = np.radians(elev), np.radians(azim)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.sin(e), np.cos(e)], [0, -np.cos(e), np.sin(e)]])
    M = Rx @ Rz
    P = T @ M.T                                     # view coords: x right, y up, z towards the viewer
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = nrm / (ln + 1e-12)
    view = M.T @ np.array([0, 0, 1.0])              # towards the viewer, world coords
    flip = (nrm @ view) < 0
    nrm[flip] *= -1                                  # two-sided lighting
    L = np.array(S.get('light', [-0.4, 0.5, 0.75]), float)
    L /= np.linalg.norm(L)
    diff = np.clip(nrm @ L, 0, 1)
    Hh = L + view
    Hh /= np.linalg.norm(Hh)
    spec = np.clip(nrm @ Hh, 0, 1) ** 40
    shade = C * (0.30 + 0.70 * diff[:, None]) + (G * spec)[:, None] * 0.9
    shade = np.clip(shade, 0, 1)
    # screen mapping
    xy = P[:, :, :2]
    lo, hi = xy.reshape(-1, 2).min(0), xy.reshape(-1, 2).max(0)
    pad = 0.04
    s = min(W * (1 - 2 * pad) / (hi[0] - lo[0]), H * (1 - 2 * pad) / (hi[1] - lo[1]))
    off = np.array([W / 2, H / 2]) - s * (lo + hi) / 2
    sx = xy[:, :, 0] * s + off[0]
    sy = H - (xy[:, :, 1] * s + off[1])
    zz = P[:, :, 2]
    zbuf = np.full((H, W), -np.inf)
    img = np.ones((H, W, 3))
    bg = np.linspace(1.0, 0.86, H)[:, None, None] * np.array([0.95, 0.95, 0.96])
    img[:] = bg
    x0 = np.clip(np.floor(sx.min(1)).astype(int), 0, W - 1)
    x1 = np.clip(np.ceil(sx.max(1)).astype(int), 0, W - 1)
    y0 = np.clip(np.floor(sy.min(1)).astype(int), 0, H - 1)
    y1 = np.clip(np.ceil(sy.max(1)).astype(int), 0, H - 1)
    for i in np.argsort(zz.mean(1)):
        if x1[i] < x0[i] or y1[i] < y0[i]:
            continue
        X, Y = np.meshgrid(np.arange(x0[i], x1[i] + 1) + 0.5, np.arange(y0[i], y1[i] + 1) + 0.5)
        ax, ay, bx, by, cx, cy = sx[i, 0], sy[i, 0], sx[i, 1], sy[i, 1], sx[i, 2], sy[i, 2]
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9:
            continue
        w0 = ((by - cy) * (X - cx) + (cx - bx) * (Y - cy)) / den
        w1 = ((cy - ay) * (X - cx) + (ax - cx) * (Y - cy)) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        z = w0 * zz[i, 0] + w1 * zz[i, 1] + w2 * zz[i, 2]
        sub = zbuf[y0[i]:y1[i] + 1, x0[i]:x1[i] + 1]
        upd = inside & (z > sub)
        sub[upd] = z[upd]
        img[y0[i]:y1[i] + 1, x0[i]:x1[i] + 1][upd] = shade[i]
    Image.fromarray((img * 255).astype(np.uint8)).save(out)


main()
