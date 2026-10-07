"""Exterior concept render of tomtho-slim mk2 from layout_v20.json (painter's algorithm, not the final case CAD)."""
import json, math, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.family'] = 'Noto Sans CJK JP'
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
L = json.load(open(os.path.join(HERE, '..', 'layout_v20.json')))
PX, PY = L['pitch']; W, H = L['outline']
CASE_T, CAP_B, CAP_T = 6.3, 6.6, 9.7
COL = dict(case='#dcd8d0', key='#f6f3ec', new='#f6f3ec', mod='#bfc4cc', thumb='#e3a98b', addth='#e3a98b',
           mouse='#9fb0c8', bt='#9fb0c8', half='#bfc4cc', pad='#2a2e35')
LIGHT = np.array([-0.4, 0.5, 0.77]); LIGHT /= np.linalg.norm(LIGHT)


def rrect(cx, cy, w, h, r, rot=0.0, n=5):
    pts = []
    for (sx, sy, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ccx, ccy = sx * (w / 2 - r), sy * (h / 2 - r)
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    # layout y points to the user; world Y points away from the user
    return [(cx + x * c - y * s, -(cy + x * s + y * c)) for x, y in pts]


class Cam:
    def __init__(self, yaw, pitch):
        self.yaw, self.pitch = math.radians(yaw), math.radians(pitch)

    def p(self, x, y, z):
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        X = x * cy - y * sy; Y = x * sy + y * cy
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        return X, z * cp + Y * sp, Y * cp - z * sp          # screen x, screen y, depth (bigger = farther)

    def view(self):
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        return np.array([-sy * cp, -cy * cp, sp])            # vector toward the viewer (world)


def solid(poly, z0, z1, inset=0.0):
    cx = sum(p[0] for p in poly) / len(poly); cy = sum(p[1] for p in poly) / len(poly)
    T = [(cx + (x - cx) * (1 - inset), cy + (y - cy) * (1 - inset)) for x, y in poly]
    faces = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]; ta, tb = T[i], T[(i + 1) % len(T)]
        faces.append([(a[0], a[1], z0), (b[0], b[1], z0), (tb[0], tb[1], z1), (ta[0], ta[1], z1)])
    faces.append([(x, y, z1) for x, y in T])
    return faces


def draw_obj(ax, cam, faces, color, ec=(0, 0, 0, 0.18), lw=0.3):
    base = np.array(matplotlib.colors.to_rgb(color)); v = cam.view()
    allp = np.array([q for f in faces for q in f]); cen = allp.mean(axis=0)
    items = []
    for f in faces:
        n = np.cross(np.subtract(f[1], f[0]), np.subtract(f[2], f[0]))
        nn = np.linalg.norm(n)
        if nn == 0:
            continue
        n /= nn
        mid = np.mean(f, axis=0)
        if np.dot(n, mid - cen) < 0:
            n = -n                                          # make every normal point outward
        if all(abs(q[2] - f[0][2]) < 1e-9 for q in f):
            n = np.array([0, 0, 1.0])                      # top face
        if np.dot(n, v) <= 0:
            continue                                        # back face
        k = 0.62 + 0.38 * max(0, np.dot(n, LIGHT))
        pts = [cam.p(*q) for q in f]
        items.append((np.mean([q[2] for q in pts]), [(q[0], q[1]) for q in pts], np.clip(base * k, 0, 1)))
    for d, pts, c in sorted(items, key=lambda t: -t[0]):
        ax.add_patch(Polygon(pts, closed=True, fc=c, ec=ec, lw=lw))


def render(ax, cam, title):
    draw_obj(ax, cam, solid(rrect(W / 2, H / 2, W, H, 5.0), 0, CASE_T), COL['case'], lw=0.5)
    tp = L['trackpad']
    draw_obj(ax, cam, solid(rrect(tp['x'] + tp['w'] / 2, tp['y'] + tp['h'] / 2, tp['w'], tp['h'], 3.0), CASE_T, CASE_T + 0.3),
             COL['pad'])
    for e in L['leds']:
        draw_obj(ax, cam, solid(rrect(e['cx'], e['cy'], 1.6, 1.6, 0.7), CASE_T, CASE_T + 0.05),
                 '#53c565' if e['name'] != 'CHG' else '#ff6a3d', ec='none')
    caps = []
    for k in L['keys']:
        w = k['w_u'] * PX - 1.44; h = k['h_u'] * PY - 1.44
        poly = rrect(k['cx'], k['cy'], w, h, 1.3, k['rot_deg'])
        caps.append((cam.p(k['cx'], -k['cy'], CAP_B)[2], poly, COL.get(k['kind'], COL['key'])))
    for d, poly, col in sorted(caps, key=lambda t: -t[0]):
        draw_obj(ax, cam, solid(poly, CAP_B, CAP_T, inset=0.05), col)
    ax.set_aspect('equal'); ax.autoscale_view(); ax.axis('off')
    ax.set_title(title, fontsize=12)


for name, cam, size in (('exterior_top.png', Cam(0, 90), (16, 6.6)), ('exterior_oblique.png', Cam(-18, 38), (16, 8.5))):
    fig = plt.figure(figsize=size, facecolor='white')
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    render(ax, cam, '')
    out = os.path.join(HERE, '..', 'docs', name)
    fig.savefig(out, dpi=130, facecolor='white')
    plt.close(fig)
    print(out)
