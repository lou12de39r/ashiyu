"""Rough PNG/PDF preview of the generated schematic (for review without KiCad)."""
import sys
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.family'] = 'Noto Sans CJK JP'
import matplotlib.pyplot as plt
from pcbio import _tok, _parse


def main(path, out, window=None):
    tree = _parse(_tok(open(path).read()))
    libs = {}
    fig = plt.figure(figsize=(46.8, 33.1))
    ax = fig.add_axes([0.01, 0.01, 0.98, 0.98])
    for n in tree[1:]:
        if isinstance(n, list) and n[0] == 'lib_symbols':
            for s in n[1:]:
                libs[s[1]] = s
    for n in tree[1:]:
        if not isinstance(n, list):
            continue
        if n[0] == 'symbol':
            lid = next(x for x in n if isinstance(x, list) and x[0] == 'lib_id')[1]
            at = next(x for x in n if isinstance(x, list) and x[0] == 'at')
            X, Y, R = float(at[1]), float(at[2]), int(float(at[3]))
            s = libs[lid]

            def T(x, y):
                x, y = float(x), -float(y)
                for _ in range((R // 90) % 4):
                    x, y = y, -x
                return X + x, Y + y
            for sub in s[2:]:
                if not (isinstance(sub, list) and sub[0] == 'symbol'):
                    continue
                for g in sub[2:]:
                    if not isinstance(g, list):
                        continue
                    if g[0] == 'rectangle':
                        a = T(g[1][1], g[1][2]); b = T(g[2][1], g[2][2])
                        ax.plot([a[0], b[0], b[0], a[0], a[0]], [a[1], a[1], b[1], b[1], a[1]], 'k-', lw=0.6)
                    elif g[0] == 'polyline':
                        pts = [T(p[1], p[2]) for p in g[1][1:]]
                        ax.plot([p[0] for p in pts], [p[1] for p in pts], 'k-', lw=0.6)
                    elif g[0] == 'circle':
                        c = T(g[1][1], g[1][2])
                        ax.add_patch(plt.Circle(c, float(g[2][1]), fill=False, lw=0.5))
                    elif g[0] == 'pin':
                        at2 = next(x for x in g if isinstance(x, list) and x[0] == 'at')
                        ln = float(next(x for x in g if isinstance(x, list) and x[0] == 'length')[1])
                        px, py, a = float(at2[1]), float(at2[2]), int(at2[3])
                        dx, dy = {0: (ln, 0), 180: (-ln, 0), 90: (0, ln), 270: (0, -ln)}[a]
                        p1, p2 = T(px, py), T(px + dx, py + dy)
                        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#a00', lw=0.6)
                        nm = next(x for x in g if isinstance(x, list) and x[0] == 'name')[1]
                        if nm not in ('~', '1', '2', 'K', 'A', 'GND', 'pwr') or lid.endswith(('USB_C', 'Conn_02')):
                            ha = 'left' if a == 0 else 'right' if a == 180 else 'center'
                            off = {0: 0.6, 180: -0.6}.get(a, 0)
                            ax.text(p2[0] + off, p2[1], nm, fontsize=3.2, ha=ha, va='center', color='#004')
            for pr in n:
                if isinstance(pr, list) and pr[0] == 'property' and pr[1] in ('Reference', 'Value'):
                    eff = str(pr)
                    if 'hide' in eff:
                        continue
                    pa = next(x for x in pr if isinstance(x, list) and x[0] == 'at')
                    ax.text(float(pa[1]), float(pa[2]), pr[2], fontsize=3.5 if pr[1] == 'Value' else 4,
                            color='#060' if pr[1] == 'Value' else '#000', ha='left', va='center')
        elif n[0] == 'label':
            at = n[2]
            a = int(float(at[3]))
            ha = 'left' if a in (0, 90) else 'right'
            ax.text(float(at[1]), float(at[2]), n[1], fontsize=3.5, color='#0050c0', ha=ha, va='bottom',
                    rotation=a if a in (90, 270) else 0, rotation_mode='anchor')
        elif n[0] == 'wire':
            p = n[1]
            ax.plot([float(p[1][1]), float(p[2][1])], [float(p[1][2]), float(p[2][2])], color='#080', lw=0.7)
        elif n[0] == 'no_connect':
            x, y = float(n[1][1]), float(n[1][2])
            ax.plot([x - 0.6, x + 0.6], [y - 0.6, y + 0.6], 'b-', lw=0.5)
            ax.plot([x - 0.6, x + 0.6], [y + 0.6, y - 0.6], 'b-', lw=0.5)
        elif n[0] == 'text':
            at = next(x for x in n if isinstance(x, list) and x[0] == 'at')
            ax.text(float(at[1]), float(at[2]), n[1].replace('\\n', '\n'), fontsize=5.5, ha='left', va='top',
                    color='#333')
    x1, y1, x2, y2 = window or (0, 0, 594, 420)
    ax.set_xlim(x1, x2)
    ax.set_ylim(y2, y1)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.savefig(out, dpi=110 if not window else 220)
    plt.close(fig)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
