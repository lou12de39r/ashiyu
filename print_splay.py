"""1:1 print sheets to compare the frozen layout with a splayed variant (each half turned by ANG about its top-inner
corner: columns point towards the elbows, gap wider at the bottom).  Paper test only - nothing else uses this.

usage: python3 print_splay.py [ANG=6]
writes: layout_splay{ANG}_print_A4x2.pdf (two A4 landscape pages, tape at the centre line),
        layout_v20_print_A4x2.pdf (same tiling for the current layout), layout_splay{ANG}_print_A3.pdf,
        docs/layout_splay{ANG}_compare.png
"""
import json, math, sys, copy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.transforms as mt
from matplotlib.patches import FancyBboxPatch, Polygon
from matplotlib.backends.backend_pdf import PdfPages
plt.rcParams['font.family'] = 'Noto Sans CJK JP'

ANG = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
L = json.load(open('layout_v20.json'))
PX, PY = L['pitch']
W, H = L['outline']
CX = W / 2
CAP = 1.44


def splay(keys, ang):
    out = copy.deepcopy(keys)
    main = [k for k in out if k['kind'] != 'mouse']
    left = [k for k in main if k['cx'] < CX]
    right = [k for k in main if k['cx'] > CX]
    for side, ks, sgn in (('L', left, 1), ('R', right, -1)):
        if not ks:
            continue
        flat = [k for k in ks if k['rot_deg'] == 0 and k['kind'] != 'bt']
        if sgn > 0:
            px = max(k['cx'] + k['w_u'] * PX / 2 for k in flat)
        else:
            px = min(k['cx'] - k['w_u'] * PX / 2 for k in flat)
        py = min(k['cy'] - k['h_u'] * PY / 2 for k in flat)
        a = math.radians(sgn * ang)
        for k in ks:
            dx, dy = k['cx'] - px, k['cy'] - py
            k['cx'] = px + dx * math.cos(a) - dy * math.sin(a)
            k['cy'] = py + dx * math.sin(a) + dy * math.cos(a)
            k['rot_deg'] = k['rot_deg'] + sgn * ang
    return out


def corners(k, grow=0.0):
    w = k['w_u'] * PX - CAP + 2 * grow
    h = k['h_u'] * PY - CAP + 2 * grow
    a = math.radians(k['rot_deg'])
    pts = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        x, y = sx * w / 2, sy * h / 2
        pts.append((k['cx'] + x * math.cos(a) - y * math.sin(a), k['cy'] + x * math.sin(a) + y * math.cos(a)))
    return pts


def hull(pts):
    pts = sorted(set(pts))
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def draw(ax, keys, title, colour='k'):
    tp = L['trackpad']
    ax.add_patch(FancyBboxPatch((tp['x'], tp['y']), tp['w'], tp['h'], boxstyle='round,pad=0,rounding_size=4',
                                fc='#eeeeee', ec=colour, lw=0.5))
    for k in keys:
        w = k['w_u'] * PX - CAP
        h = k['h_u'] * PY - CAP
        tr = mt.Affine2D().rotate_deg_around(k['cx'], k['cy'], k['rot_deg']) + ax.transData
        ax.add_patch(FancyBboxPatch((k['cx'] - w / 2, k['cy'] - h / 2), w, h, boxstyle='round,pad=0,rounding_size=1.2',
                                    fc='none', ec=colour, lw=0.45, transform=tr))
        ax.text(k['cx'], k['cy'], k['label'].split(' ')[0], ha='center', va='center',
                fontsize=6 if k['h_u'] >= 1 and k['w_u'] >= 1 else 4.2, rotation=-k['rot_deg'], color=colour)
    pts = [p for k in keys for p in corners(k, 3.0)]
    ax.add_patch(Polygon(hull(pts), closed=True, fc='none', ec=colour, lw=0.5, ls='--'))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


def page(pdf, keys, title, xlo, xhi, note):
    PW, PH = 297.0, 210.0
    fig = plt.figure(figsize=(PW / 25.4, PH / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    y0 = -40
    ax.set_xlim(xlo, xlo + PW)
    ax.set_ylim(y0 + PH, y0)
    ax.axis('off')
    draw(ax, keys, title)
    ax.plot([CX, CX], [y0 + 22, y0 + PH - 8], color='#c00', lw=0.4, ls=(0, (4, 3)))
    for yy in (0, 60, 120):
        ax.plot([CX - 4, CX + 4], [yy, yy], color='#c00', lw=0.5)
    sx = xlo + 12
    ax.plot([sx, sx + 100], [y0 + PH - 14, y0 + PH - 14], 'k-', lw=0.8)
    ax.text(sx + 50, y0 + PH - 17, '100 mm（定規で確認）', ha='center', fontsize=7)
    ax.text(xlo + 12, y0 + 6, title + '　' + note, fontsize=7.5, va='center')
    pdf.savefig(fig)
    plt.close(fig)


def two_pages(keys, title, fn):
    xs = [p[0] for k in keys for p in corners(k, 3.0)]
    with PdfPages(fn) as pdf:
        page(pdf, keys, title + '（1/2 左）', min(xs) - 8, None or 0, '赤い点線で右ページと重ねて貼る。実際のサイズ／100% で印刷')
        page(pdf, keys, title + '（2/2 右）', max(xs) + 8 - 297, 0, '赤い点線で左ページと重ねて貼る。実際のサイズ／100% で印刷')


cur = L['keys']
spl = splay(L['keys'], ANG)
two_pages(cur, '現行 v20（水平・開きなし）', 'layout_v20_print_A4x2.pdf')
two_pages(spl, f'左右を {ANG:g}° 開いた版', f'layout_splay{ANG:g}_print_A4x2.pdf')

# A3 single sheet
fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
bx = draw(ax, spl, '')
ax.set_xlim((bx[0] + bx[1]) / 2 - 210, (bx[0] + bx[1]) / 2 + 210)
ax.set_ylim((bx[2] + bx[3]) / 2 + 148.5, (bx[2] + bx[3]) / 2 - 148.5)
ax.axis('off')
ax.plot([bx[0], bx[0] + 100], [bx[3] + 15, bx[3] + 15], 'k-', lw=0.8)
ax.text(bx[0] + 50, bx[3] + 20, '100 mm（定規で確認）', ha='center', fontsize=7)
fig.savefig(f'layout_splay{ANG:g}_print_A3.pdf')
plt.close(fig)

# comparison picture
fig, axs = plt.subplots(1, 2, figsize=(16, 4.6))
for ax, ks, t in ((axs[0], cur, '現行 v20'), (axs[1], spl, f'左右を {ANG:g}° 開いた版')):
    b = draw(ax, ks, t)
    ax.set_xlim(-20, W + 20)
    ax.set_ylim(H + 25, -10)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f'{t}　外形の目安 {b[1] - b[0]:.0f} × {b[3] - b[2]:.0f} mm', fontsize=11)
fig.savefig(f'docs/layout_splay{ANG:g}_compare.png', dpi=110, bbox_inches='tight')
for ks, t in ((cur, 'current'), (spl, 'splay')):
    xs = [p[0] for k in ks for p in corners(k, 3.0)]
    ys = [p[1] for k in ks for p in corners(k, 3.0)]
    print(t, 'bbox %.1f x %.1f mm' % (max(xs) - min(xs), max(ys) - min(ys)))
