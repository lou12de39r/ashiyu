import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
from matplotlib.collections import LineCollection

import design as D
from fplib import FP


def render(tracks, vias, out, window=None, dpi=200, title=''):
    x1, y1, x2, y2 = window or D.BOARD
    w = (x2 - x1)
    h = (y2 - y1)
    fig = plt.figure(figsize=(min(24, w / 10 + 1), min(24, w / 10 + 1) * h / w + 0.6))
    ax = fig.add_axes([0.01, 0.01, 0.98, 0.94])
    ax.set_facecolor('#0b2a1a')
    bx1, by1, bx2, by2 = D.BOARD
    ax.add_patch(FancyBboxPatch((bx1, by1), bx2 - bx1, by2 - by1, boxstyle='round,pad=0,rounding_size=1',
                                fc='#123f27', ec='#e8e83a', lw=1.2))
    ax1, ay1, ax2, ay2 = D.ANT_KEEPOUT
    ax.add_patch(Rectangle((ax1, ay1), ax2 - ax1, ay2 - ay1, fc='none', ec='#ff66ff', lw=1, ls='--', hatch='//'))
    bx1, by1, bx2, by2 = D.BATTERY_AREA
    ax.add_patch(Rectangle((bx1, by1), bx2 - bx1, by2 - by1, fc='none', ec='#dddddd', lw=0.8, ls=':'))
    ax.text((bx1 + bx2) / 2, (by1 + by2) / 2, 'LiPo area', color='#dddddd', ha='center', va='center', fontsize=8)
    # B.Cu tracks under F
    for layer, col in (('B.Cu', '#3b7dff'), ('F.Cu', '#ff4a3b')):
        segs = [((t[1], t[2]), (t[3], t[4])) for t in tracks if t[0] == layer]
        lws = [t[5] for t in tracks if t[0] == layer]
        if segs:
            # width in data units -> points
            ppd = ax.get_window_extent().width / (x2 - x1) * 72 / fig.dpi
            ax.add_collection(LineCollection(segs, colors=col, linewidths=[max(0.3, lw * ppd) for lw in lws],
                                             alpha=0.85 if layer == 'F.Cu' else 0.75, capstyle='round'))
    for ref, p in D.PARTS.items():
        fp = FP[p['fp']]
        for (num, kind, shape, X, Y, W, H, drill, net) in D.pad_world(p):
            if kind == 'np':
                ax.add_patch(Circle((X, Y), W / 2, fc='black', ec='#999999', lw=0.3))
                continue
            col = '#ffb000' if kind == 'thru' else '#d23c2c'
            if shape == 'circle':
                ax.add_patch(Circle((X, Y), W / 2, fc=col, ec='none'))
            else:
                ax.add_patch(Rectangle((X - W / 2, Y - H / 2), W, H, fc=col, ec='none'))
        if p['fp'] in ('Raytac_MDBT50Q', 'USB_C_HRO_TYPE-C-31-M-12', 'SW_SPDT_PCM12', 'JST_SH_SM02B-SRSS-TB'):
            pass
        lbl = ref
        if not ref.startswith(('SW', 'D')) or ref in ('D55', 'SW55', 'SW56'):
            ax.text(p['x'], p['y'], lbl, color='white', fontsize=4.5, ha='center', va='center', zorder=10)
    for (x, y, n) in vias:
        ax.add_patch(Circle((x, y), D.VIA[0] / 2, fc='#c8c8c8', ec='none', zorder=5))
        ax.add_patch(Circle((x, y), D.VIA[1] / 2, fc='black', ec='none', zorder=6))
    # module outline
    ax.add_patch(Rectangle((D.U1X - 5.25, D.U1Y - 7.75), 10.5, 15.5, fc='none', ec='white', lw=0.6))
    ax.set_xlim(x1, x2)
    ax.set_ylim(y2, y1)
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    fig.suptitle(title, fontsize=10)
    fig.savefig(out, dpi=dpi)
    plt.close(fig)


if __name__ == '__main__':
    render(D.TRACKS, D.VIAS, sys.argv[1] if len(sys.argv) > 1 else '/tmp/r.png')
