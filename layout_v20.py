import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'Noto Sans CJK JP'
from matplotlib.patches import FancyBboxPatch, Rectangle
PX, PY, M, WEDGE = 18.5, 18.0, 2.0, 11.0   # rear strip holds the 0.5u BT keys
DROP = 0.25
TPW = 43.0                            # Azoteq TPS43-201A-S (43 x 40 mm)
TPH = 40.0
G = (49.0 + 2.0) / PX                 # centre gap kept from v20 (2.76u); keys do not move
R1 = 6 + G                            # right block start
keys = []
# column stagger = roBa offsets x0.5, measured from the pinky column (negative = towards the rear)
SL = [0.0, 0.0, -0.185, -0.308, -0.242, -0.176]      # outer, Q, W, E, R, T
SR = [-0.176, -0.242, -0.308, -0.185, 0.0, 0.0]  # Y, U, I, O, P, outer
SH = SL[3] - SL[5]          # shift every non-thumb key down so the 3/8 tops meet the trackpad top (+0.132u)
SL = [v - SH for v in SL]; SR = [v - SH for v in SR]
ROT = {}
def k(xu, yu, t, kind='k', w=1.0, h=1.0, r=0.0):
    keys.append((xu, yu, t, kind, w, h))
    if r: ROT[len(keys) - 1] = r
for c, t in enumerate(['`', '1', '2', '3', '4', '5']): k(c, SL[c], t, 'new')
k(0, -0.5, 'BT\n切替', 'bt', 0.5, 0.5)
for c, t in enumerate(['6', '7', '8', '9', '0', '-']): k(R1 + c, SR[c], t, 'new')
Lr = [['Tab','Q','W','E','R','T'], ['Ctl','A','S','D','F','G'], ['⇧','Z','X','C','V','B']]
Rr = [['Y','U','I','O','P','['], ['H','J','K','L',"'",']'], ['N','M',',','.','/','Ent']]
for r in range(3):
    for c in range(6):
        k(c, r + 1 + SL[c], Lr[r][c], 'new' if c == 0 else 'k')
        k(R1 + c, r + 1 + SR[c], Rr[r][c], 'new' if c == 5 else 'k')
for c, t in zip(range(3), ('Fn', 'Ctrl', 'Win')): k(c, 4 + SL[c], t, 'mod')   # Alt removed
TW = 1.25
# roBa thumb fan x0.5: rotation 0 / 4.5 / 10 deg, drop 0 / 0.046 / 0.192 u (outer -> inner), 0.06u gaps
TR = [0.0, 4.5, 10.0]; TD = [0.0, 0.046, 0.192]; TG = 0.04
import math
def lowest(yc_u, w, r):   # lowest corner (mm) of a key whose centre is at yc_u
    a = math.radians(abs(r)); return WEDGE + yc_u * PY + (w * PX - 1.2) / 2 * math.sin(a) + (PY - 1) / 2 * math.cos(a)
T0 = 4 + DROP
while max(lowest(T0 + TD[i] + 0.5, TW, TR[i]) for i in range(3)) > WEDGE + (4 + DROP + 1) * PY - 0.5: T0 -= 0.01
# inner edge pushed in as far as a 2 mm gap between the tilted inner keys' top corners allows,
# so the outer thumb key covers about half of the C / comma key
CEN = (7 + R1 - 1) / 2
_sh = 9 * math.sin(math.radians(TR[2])) - (TW * PX - 1.2) / 2 * (1 - math.cos(math.radians(TR[2])))
XI = CEN - (1.0 + _sh) / PX
lx = [XI - TW * (3 - i) - TG * (2 - i) for i in range(3)]
for i, t in enumerate(('変換\nL6', 'Space\nL2', '無変換\nL3')): k(lx[i], T0 + TD[i], t, 'thumb', TW, 1.0, TR[i])
right_th = R1 - 1
for i, (t, kind) in enumerate(zip(('BS', 'Enter\nL1', 'Del'), ('thumb', 'thumb', 'addth'))):
    j = 2 - i   # mirror: BS is the innermost
    k(2 * CEN - XI + (TW + TG) * i, T0 + TD[j], t, kind, TW, 1.0, -TR[j])
for c, t in ((R1 + 3, '←'), (R1 + 5, '→')): k(c, 4 - SH, t, 'mod')   # arrow cluster kept flat
k(R1 + 4, 4 - SH, '↑', 'half', 1.0, 0.5); k(R1 + 4, 4.5 - SH, '↓', 'half', 1.0, 0.5)
BY = 3.5 + SL[5]                                      # L/R bottom flush with the B/N row bottom (4.0u)
bx = 6 + (G - 2.5) / 2
k(bx, BY, 'L', 'mouse', 1.0, 0.5); k(bx + 1.5, BY, 'R', 'mouse', 1.0, 0.5)
k(bx + 1.0, BY, 'M', 'mouse', 0.5, 0.5)       # 0.5u x 0.5u, flush with L/R
W = (R1 + 6) * PX + 2 * M
H = WEDGE + (4 + DROP + 1) * PY + M
fig = plt.figure(figsize=(15, 9.8))
ax = fig.add_axes([0.02, 0.28, 0.96, 0.68])
ax.add_patch(FancyBboxPatch((0, 0), W, H, boxstyle='round,pad=0,rounding_size=5', fc='#e9e6df', ec='#555', lw=1.2))
ax.add_patch(Rectangle((0.6, 0.6), W - 1.2, WEDGE - 0.6, fc='#cfd8e3', ec='none'))


col = {'k': '#ffffff', 'mod': '#eef2f7', 'thumb': '#fde8c8', 'new': '#e3f1e3', 'mouse': '#e6e0f5', 'add': '#ffd9d9', 'opt': '#f4f4f4', 'addth': '#ffd9a8', 'half': '#ffd9d9', 'bt': '#cfe3ff'}
for idx, (xu, yu, t, kind, w, h) in enumerate(keys):
    x = M + xu * PX; y = WEDGE + yu * PY
    import matplotlib.transforms as mt
    tr = mt.Affine2D().rotate_deg_around(x + w * PX / 2, y + h * PY / 2, ROT.get(idx, 0)) + ax.transData
    ax.add_patch(FancyBboxPatch((x + 0.6, y + 0.5), w * PX - 1.2, h * PY - 1, boxstyle='round,pad=0,rounding_size=1.5',
                                fc=col[kind], ec='#888', lw=0.8, ls='--' if kind == 'opt' else '-', transform=tr))
    ax.text(x + w * PX / 2, y + h * PY / 2, t, ha='center', va='center', fontsize=(8.5 if len(t) < 5 else 6.5) if w > 0.6 else 5.5, family='Noto Sans CJK JP', rotation=-ROT.get(idx, 0), rotation_mode='anchor')
tx = M + 6 * PX + (G * PX - TPW) / 2
ty = WEDGE + (1 + SL[5]) * PY + 0.5          # trackpad top = top of T / Y
gx = M + 6 * PX + 1.0                          # left edge of the free area (fixed, independent of the pad size)
ax.add_patch(FancyBboxPatch((tx, ty), TPW, TPH, boxstyle='round,pad=0,rounding_size=4', fc='#d9dde3', ec='#556', lw=1.2))
ax.text(tx + TPW / 2, ty + TPH - 8, f'TPS43 trackpad {TPW:.0f} × {TPH:.0f}', ha='center', va='center', fontsize=8.5)
# electronics hidden under the trackpad (top side of main PCB)
ax.add_patch(Rectangle((gx + 19, 0.3), 10.5, 15.5, fc='#4a7c59', ec='k', alpha=0.85)); ax.text(gx + 24.2, 8, 'nRF\n52840', ha='center', va='center', fontsize=6, color='w')
ax.add_patch(Rectangle((gx + 19, -0.2), 10.5, 3.8, fc='none', ec='#c33', ls='--')); ax.text(gx + 24.2, -2.5, 'antenna at rear edge', ha='center', fontsize=6.5, color='#c33')
ax.add_patch(Rectangle((gx + 1, 17), 47, ty - 19, fc='none', ec='#556', ls=':')); ax.text(gx + 12, 17 + (ty - 19) / 2, 'charger / ESD\n/ power', ha='center', va='center', fontsize=6.5)
ax.add_patch(Rectangle((gx + 4, -1.0), 9, 7.3, fc='#999', ec='k')); 
ax.add_patch(Rectangle((M + 1*PX, WEDGE + 1.2*PY), 4*PX, 2.2*PY, fc='none', ec='#b07d00', ls='--', lw=1.2))
ax.text(M + 3*PX, WEDGE + 2.3*PY + 14, 'LiPo under the PCB\n(e.g. 3 × 40 × 70 mm)', ha='center', fontsize=8, color='#8a6d1d')
n = len(keys)
from matplotlib.patches import Circle
LY = WEDGE / 2 + 1.0
for i, c in enumerate(('#22c55e', '#22c55e', '#22c55e')):
    lx = M + 0.5 * PX + 4 + 4.5 * i
    ax.add_patch(Circle((lx, LY), 1.1, fc=c, ec='k', lw=0.5)); ax.text(lx, LY + 3.2, str(i + 1), ha='center', fontsize=6)

ax.text(gx + 8.5, 3, 'USB-C', ha='center', va='center', fontsize=5.5, color='w')
from matplotlib.patches import Wedge
px_ = W - 8
ax.add_patch(Wedge((px_, LY), 1.2, 90, 270, fc='#22c55e', ec='k', lw=0.5)); ax.add_patch(Wedge((px_, LY), 1.2, 270, 90, fc='#ef4444', ec='k', lw=0.5))
ax.text(px_, LY + 3.4, '電源', ha='center', fontsize=6)
ax.add_patch(Circle((px_ - 6, LY), 1.1, fc='#f59e0b', ec='k', lw=0.5)); ax.text(px_ - 6, LY + 3.4, '充電', ha='center', fontsize=6)
for (xu, yu, t, kind, w, h) in keys:
    pass
ax.set_xlim(-5, W + 5); ax.set_ylim(H + 5, -5); ax.set_aspect('equal'); ax.axis('off')
ax.set_title('\n' + f'roBa-style v20 (trackpad top = T / Y top)  –  {n} keys  ≈ {W:.0f} × {H:.0f} mm   trackpad TPS43 {TPW:.0f}×{TPH:.0f}', fontsize=11)
ax2 = fig.add_axes([0.04, 0.03, 0.92, 0.2])
Hk = H
ax2.fill([0, Hk, Hk, 0], [3, 3, 4.2, 4.2], color='#3a7d44')
ax2.fill([0, Hk, Hk, 0], [4.2, 4.2, 9.4, 9.4], color='#ddd')
ax2.fill([8, 70, 70, 8], [0.5, 0.5, 3.0, 3.0], color='#f2c14e')
ax2.fill([0, Hk, Hk, 0], [0, 0, 0.5, 0.5], color='#999')
ax2.text(39, 1.6, 'LiPo 3 mm', ha='center', va='center', fontsize=8)
ax2.annotate('total ≈ 9.7 mm (bottom 0.5 + LiPo 3 + PCB 1.2 + switch 3.5 + keycap ~1.5)', (Hk*0.6, 9.4), (Hk*0.35, 13), fontsize=8, arrowprops=dict(arrowstyle='->'))
ax2.set_xlim(-3, Hk + 3); ax2.set_ylim(-1, 15); ax2.set_aspect('equal'); ax2.axis('off'); ax2.set_title('Side section (rear ← → front)', fontsize=9)
fig.savefig('roba_ortho_v20.png', dpi=120, bbox_inches='tight')
print(n, round(W,1), round(H,1), round(G, 2), 'T0', round(T0,3), 'outer L', round(XI-3*TW-2*TG,3), 'outer R end', round(2*CEN-XI+3*TW+2*TG,3), 'comma ctr', round(R1+2.5,3))
