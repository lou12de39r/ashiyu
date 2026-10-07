"""1:1 print sheet (A4 landscape) from layout_v19.json. Print at 100% / actual size."""
import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.transforms as mt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
plt.rcParams['font.family'] = 'Noto Sans CJK JP'
L = json.load(open('layout_v19.json'))
PX, PY = L['pitch']; W, H = L['outline']
PW, PH = 297.0, 210.0
OX, OY = (PW - W) / 2, 38.0            # outline placement on the sheet (mm)
fig = plt.figure(figsize=(PW / 25.4, PH / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(-OX, PW - OX); ax.set_ylim(PH - OY, -OY); ax.axis('off')
ax.add_patch(FancyBboxPatch((0, 0), W, H, boxstyle='round,pad=0,rounding_size=5', fc='none', ec='k', lw=0.6))
tp = L['trackpad']
ax.add_patch(FancyBboxPatch((tp['x'], tp['y']), tp['w'], tp['h'], boxstyle='round,pad=0,rounding_size=4', fc='#eeeeee', ec='k', lw=0.5))
ax.text(tp['x'] + tp['w'] / 2, tp['y'] + tp['h'] / 2, f"trackpad\n{tp['w']:.0f} × {tp['h']:.1f}", ha='center', va='center', fontsize=7)
CAP = 1.44                               # ACC cap is ~1.44 mm smaller than the pitch cell
for kd in L['keys']:
    w = kd['w_u'] * PX - CAP; h = kd['h_u'] * PY - CAP
    tr = mt.Affine2D().rotate_deg_around(kd['cx'], kd['cy'], kd['rot_deg']) + ax.transData
    ax.add_patch(FancyBboxPatch((kd['cx'] - w / 2, kd['cy'] - h / 2), w, h, boxstyle='round,pad=0,rounding_size=1.2',
                                fc='none', ec='k', lw=0.4, transform=tr))
    ax.plot([kd['cx']], [kd['cy']], marker='+', ms=2.5, mew=0.3, color='#999')
    ax.text(kd['cx'], kd['cy'] + (2.6 if kd['h_u'] >= 1 else 0), kd['label'], ha='center', va='center',
            fontsize=6 if kd['h_u'] >= 1 and kd['w_u'] >= 1 else 4.2, rotation=-kd['rot_deg'], rotation_mode='anchor')
for e in L['leds']:
    ax.add_patch(Circle((e['cx'], e['cy']), 0.8, fc='none', ec='k', lw=0.4))
u = L['usb_c']; ax.add_patch(Rectangle((u['x'], 0), u['w'], 3, fc='none', ec='k', lw=0.4, ls='--')); ax.text(u['x'] + u['w'] / 2, 1.6, 'USB-C', ha='center', va='center', fontsize=4)
# scale check bars
sy = H + 14
ax.plot([0, 100], [sy, sy], 'k-', lw=0.8); [ax.plot([x, x], [sy - 1.5, sy + 1.5], 'k-', lw=0.6) for x in range(0, 101, 10)]
ax.text(50, sy + 4, '100 mm（定規で確認）', ha='center', va='top', fontsize=7)
ax.plot([W + 3, W + 3], [0, 50], 'k-', lw=0.8); ax.text(W + 4, 25, '50 mm', va='center', fontsize=6, rotation=-90)
ax.text(0, -26, 'tomtho-slim mk2 レイアウト v19　実寸印刷用', fontsize=10, va='top')
ax.text(0, -20, f'外形 {W:.1f} × {H:.1f} mm ／ ピッチ 18.5 × 18.0 ／ キー枠 = Acid Caps キーキャップ外形（目安） ／ ＋ = スイッチ中心',
        fontsize=6.5, va='top')
ax.text(0, -15, '印刷は「実際のサイズ／100%」で。下の100 mm の線を定規で測り、ずれていないか確認してから手を置いてください。', fontsize=6.5, va='top', color='#a00')
fig.savefig('layout_v19_print_A4.pdf')
fig.savefig('layout_v19_print_A4.png', dpi=110)
print('ok')
