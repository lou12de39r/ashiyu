"""Footprint geometry library (KiCad coordinates: mm, y-down).

Pad tuple fields:
  num, kind ('smd'|'thru'|'np'), shape ('rect'|'roundrect'|'circle'|'oval'),
  x, y, w, h, drill (None | float | (dw, dh))
Sources:
  - SKRA switch / TS-1928-B / USB-C : user's KiCad 10 "Assemble Alps Silent" project
  - R/C/LED 0603, SOD-123, SOT-23(-5/-6), JST SH, PCM12 : KiCad official library geometry
  - MDBT50Q : Adafruit ItsyBitsy nRF52840 (production-proven Eagle package), y flipped
"""

def _box(x1, y1, x2, y2, layer, w):
    return [(layer, x1, y1, x2, y1, w), (layer, x2, y1, x2, y2, w),
            (layer, x2, y2, x1, y2, w), (layer, x1, y2, x1, y1, w)]

FP = {}

# ---------------------------------------------------------------- key switch
FP['SW_ALPS_SKRA_6.2mm'] = dict(
    descr='ALPS SKRACAE010 6.2x6.2x3.5mm tact switch, key cell 18.5x18mm',
    attr='smd',
    pads=[('1', 'smd', 'rect', -2.875, -2, 2.75, 1, None),
          ('1', 'smd', 'rect', 2.875, -2, 2.75, 1, None),
          ('2', 'smd', 'rect', -2.875, 2, 2.75, 1, None),
          ('2', 'smd', 'rect', 2.875, 2, 2.75, 1, None)],
    lines=[('F.SilkS', -3.25, -3.1, 3.25, -3.1, 0.12), ('F.SilkS', -3.25, 3.1, 3.25, 3.1, 0.12),
           ('F.SilkS', -3.25, -1.25, -3.25, 1.25, 0.12), ('F.SilkS', 3.25, -1.25, 3.25, 1.25, 0.12)]
          + _box(-9.25, -9.0, 9.25, 9.0, 'Dwgs.User', 0.15)
          + _box(-4.5, -3.35, 4.5, 3.35, 'F.CrtYd', 0.05)
          + _box(-3.1, -3.1, 3.1, 3.1, 'F.Fab', 0.1),
    circles=[('Dwgs.User', -7.55, -7.3, 2.0), ('Dwgs.User', -7.55, 7.3, 2.0),
             ('Dwgs.User', 7.55, -7.3, 2.0), ('Dwgs.User', 7.55, 7.3, 2.0)],
    ref_at=(0, -4.1), val_at=(0, 4.2), ref_size=0.8)


def _two(name, descr, px, w, h, shape, crt, silk=None):
    pads = [('1', 'smd', shape, -px, 0, w, h, None), ('2', 'smd', shape, px, 0, w, h, None)]
    lines = _box(-crt[0], -crt[1], crt[0], crt[1], 'F.CrtYd', 0.05)
    if silk:
        lines += silk
    FP[name] = dict(descr=descr, attr='smd', pads=pads, lines=lines, circles=[],
                    ref_at=(0, -1.45), val_at=(0, 1.45), ref_size=0.8)


_two('R_0603', 'Resistor 0603 (1608 metric)', 0.825, 0.8, 0.95, 'roundrect', (1.48, 0.73),
     [('F.SilkS', -0.237, -0.5225, 0.237, -0.5225, 0.12), ('F.SilkS', -0.237, 0.5225, 0.237, 0.5225, 0.12)])
_two('C_0603', 'Capacitor 0603 (1608 metric)', 0.775, 0.9, 0.95, 'roundrect', (1.48, 0.73),
     [('F.SilkS', -0.14, -0.51, 0.14, -0.51, 0.12), ('F.SilkS', -0.14, 0.51, 0.14, 0.51, 0.12)])
# LED: pad1 = cathode
_two('LED_0603', 'LED 0603 (1608 metric), pad1=K', 0.7875, 0.875, 0.95, 'roundrect', (1.48, 0.73),
     [('F.SilkS', 0.8, -0.735, -1.485, -0.735, 0.12), ('F.SilkS', -1.485, -0.735, -1.485, 0.735, 0.12),
      ('F.SilkS', -1.485, 0.735, 0.8, 0.735, 0.12)])
# SOD-123: pad1 = cathode
_two('D_SOD-123', 'SOD-123, pad1=K', 1.65, 0.9, 1.2, 'rect', (2.35, 1.15),
     [('F.SilkS', -2.36, -1.0, 1.65, -1.0, 0.12), ('F.SilkS', -2.36, -1.0, -2.36, 1.0, 0.12),
      ('F.SilkS', -2.36, 1.0, 1.65, 1.0, 0.12)])

FP['SOT-23'] = dict(descr='SOT-23-3', attr='smd',
    pads=[('1', 'smd', 'rect', -1, -0.95, 0.9, 0.8, None), ('2', 'smd', 'rect', -1, 0.95, 0.9, 0.8, None),
          ('3', 'smd', 'rect', 1, 0, 0.9, 0.8, None)],
    lines=_box(-1.7, -1.75, 1.7, 1.75, 'F.CrtYd', 0.05)
          + [('F.SilkS', 0.76, 1.58, 0.76, 0.65, 0.12), ('F.SilkS', 0.76, -1.58, 0.76, -0.65, 0.12),
             ('F.SilkS', 0.76, -1.58, -1.4, -1.58, 0.12), ('F.SilkS', 0.76, 1.58, -0.7, 1.58, 0.12)],
    circles=[], ref_at=(0, -2.5), val_at=(0, 2.5), ref_size=0.8)

for n, cnt in (('SOT-23-5', 5), ('SOT-23-6', 6)):
    if cnt == 5:
        pos = [(-1.1375, -0.95), (-1.1375, 0), (-1.1375, 0.95), (1.1375, 0.95), (1.1375, -0.95)]
    else:
        pos = [(-1.1375, -0.95), (-1.1375, 0), (-1.1375, 0.95), (1.1375, 0.95), (1.1375, 0), (1.1375, -0.95)]
    FP[n] = dict(descr=n, attr='smd',
        pads=[(str(i + 1), 'smd', 'roundrect', x, y, 1.325, 0.6, None) for i, (x, y) in enumerate(pos)],
        lines=_box(-2.05, -1.7, 2.05, 1.7, 'F.CrtYd', 0.05)
              + [('F.SilkS', 0, -1.56, 0.8, -1.56, 0.12), ('F.SilkS', 0, 1.56, 0.8, 1.56, 0.12),
                 ('F.SilkS', 0, 1.56, -0.8, 1.56, 0.12), ('F.SilkS', 0, -1.56, -1.675, -1.56, 0.12)],
        circles=[], ref_at=(0, -2.5), val_at=(0, 2.5), ref_size=0.8)

FP['JST_SH_SM02B-SRSS-TB'] = dict(descr='JST SH 1.0mm 2pin horizontal SMD (SM02B-SRSS-TB)', attr='smd',
    pads=[('1', 'smd', 'roundrect', -0.5, -2, 0.6, 1.55, None), ('2', 'smd', 'roundrect', 0.5, -2, 0.6, 1.55, None),
          ('MP', 'smd', 'roundrect', -1.8, 1.875, 1.2, 1.8, None), ('MP', 'smd', 'roundrect', 1.8, 1.875, 1.2, 1.8, None)],
    lines=_box(-2.9, -3.28, 2.9, 3.28, 'F.CrtYd', 0.05) + _box(-2, -1.675, 2, 2.575, 'F.Fab', 0.1)
          + [('F.SilkS', -1.06, 2.685, 1.06, 2.685, 0.12), ('F.SilkS', -2.11, -0.865, -2.11, 0.715, 0.12),
             ('F.SilkS', 2.11, -0.865, 2.11, 0.715, 0.12)],
    circles=[], ref_at=(0, -4.0), val_at=(0, 4.0), ref_size=0.8)

# Slide switch: C&K PCM12SMTR, land pattern = KiCad SW_SPDT_PCM12
FP['SW_SPDT_PCM12'] = dict(descr='C&K PCM12SMTR SPDT slide switch, right angle', attr='smd',
    pads=[('', 'np', 'circle', -1.5, 0.33, 0.9, 0.9, 0.9), ('', 'np', 'circle', 1.5, 0.33, 0.9, 0.9, 0.9),
          ('1', 'smd', 'rect', -2.25, -1.43, 0.7, 1.5, None), ('2', 'smd', 'rect', 0.75, -1.43, 0.7, 1.5, None),
          ('3', 'smd', 'rect', 2.25, -1.43, 0.7, 1.5, None),
          ('MP', 'smd', 'rect', -3.65, 1.43, 1.0, 0.8, None), ('MP', 'smd', 'rect', 3.65, 1.43, 1.0, 0.8, None),
          ('MP', 'smd', 'rect', 3.65, -0.78, 1.0, 0.8, None), ('MP', 'smd', 'rect', -3.65, -0.78, 1.0, 0.8, None)],
    lines=[('F.CrtYd', -4.4, -2.45, 4.4, -2.45, 0.05), ('F.CrtYd', 4.4, -2.45, 4.4, 2.1, 0.05),
           ('F.CrtYd', 4.4, 2.1, 1.65, 2.1, 0.05), ('F.CrtYd', 1.65, 2.1, 1.65, 3.4, 0.05),
           ('F.CrtYd', 1.65, 3.4, -1.65, 3.4, 0.05), ('F.CrtYd', -1.65, 3.4, -1.65, 2.1, 0.05),
           ('F.CrtYd', -1.65, 2.1, -4.4, 2.1, 0.05), ('F.CrtYd', -4.4, 2.1, -4.4, -2.45, 0.05)]
          + _box(-3.35, -1.6, 3.35, 1.6, 'F.Fab', 0.1)
          + [('F.SilkS', -1.4, 1.73, 1.4, 1.73, 0.12), ('F.SilkS', -1.4, -1.73, -0.2, -1.73, 0.12)],
    circles=[], ref_at=(0, -3.3), val_at=(0, 4.2), ref_size=0.8)

FP['SW_TS-1928-B'] = dict(descr='XKB TS-1928-B 2.8x1.95x0.6mm tact switch', attr='smd',
    pads=[('1', 'smd', 'rect', -1.55, -0.6, 0.6, 0.6, None), ('1', 'smd', 'rect', 1.55, -0.6, 0.6, 0.6, None),
          ('2', 'smd', 'rect', -1.55, 0.6, 0.6, 0.6, None), ('2', 'smd', 'rect', 1.55, 0.6, 0.6, 0.6, None)],
    lines=[('F.SilkS', -0.9, -1.15, 0.9, -1.15, 0.12), ('F.SilkS', -0.9, 1.15, 0.9, 1.15, 0.12)]
          + _box(-2.1, -1.25, 2.1, 1.25, 'F.CrtYd', 0.05),
    circles=[], ref_at=(0, -2.0), val_at=(0, 2.0), ref_size=0.8)

FP['USB_C_HRO_TYPE-C-31-M-12'] = dict(descr='HRO TYPE-C-31-M-12 USB-C receptacle (USB2.0)', attr='smd',
    pads=[('S1', 'thru', 'oval', 4.32, 1.05, 1.0, 1.6, (0.6, 1.2)), ('', 'np', 'circle', 2.89, -2.6, 0.65, 0.65, 0.65),
          ('S1', 'thru', 'oval', -4.32, 1.05, 1.0, 1.6, (0.6, 1.2)), ('', 'np', 'circle', -2.89, -2.6, 0.65, 0.65, 0.65),
          ('S1', 'thru', 'oval', -4.32, -3.13, 1.0, 2.1, (0.6, 1.7)), ('S1', 'thru', 'oval', 4.32, -3.13, 1.0, 2.1, (0.6, 1.7)),
          ('A6', 'smd', 'rect', -0.25, -4.045, 0.3, 1.45, None), ('B5', 'smd', 'rect', 1.75, -4.045, 0.3, 1.45, None),
          ('A8', 'smd', 'rect', 1.25, -4.045, 0.3, 1.45, None), ('B6', 'smd', 'rect', 0.75, -4.045, 0.3, 1.45, None),
          ('A7', 'smd', 'rect', 0.25, -4.045, 0.3, 1.45, None), ('B7', 'smd', 'rect', -0.75, -4.045, 0.3, 1.45, None),
          ('A5', 'smd', 'rect', -1.25, -4.045, 0.3, 1.45, None), ('B8', 'smd', 'rect', -1.75, -4.045, 0.3, 1.45, None),
          ('A12', 'smd', 'rect', 3.25, -4.045, 0.6, 1.45, None), ('B4', 'smd', 'rect', 2.45, -4.045, 0.6, 1.45, None),
          ('A4', 'smd', 'rect', -2.45, -4.045, 0.6, 1.45, None), ('A1', 'smd', 'rect', -3.25, -4.045, 0.6, 1.45, None),
          ('B12', 'smd', 'rect', -3.25, -4.045, 0.6, 1.45, None), ('B9', 'smd', 'rect', -2.45, -4.045, 0.6, 1.45, None),
          ('A9', 'smd', 'rect', 2.45, -4.045, 0.6, 1.45, None), ('B1', 'smd', 'rect', 3.25, -4.045, 0.6, 1.45, None)],
    lines=_box(-5.32, -5.27, 5.32, 4.15, 'F.CrtYd', 0.05) + _box(-4.47, -3.65, 4.47, 3.65, 'F.Fab', 0.1)
          + [('F.SilkS', -4.7, 2.0, -4.7, 3.2, 0.12), ('F.SilkS', -4.7, -1.9, -4.7, 0.1, 0.12),
             ('F.SilkS', 4.7, 2.0, 4.7, 3.2, 0.12), ('F.SilkS', 4.7, -1.9, 4.7, 0.1, 0.12),
             ('Dwgs.User', -5.0, 3.65, 5.0, 3.65, 0.1)],
    circles=[], ref_at=(0, -5.9), val_at=(0, 5.1), ref_size=0.8)

# ---------------------------------------------------------------- MDBT50Q
# Eagle package "MDBT50" (Adafruit). (pad, x, y, rot) ; R90/R270 => 0.4 wide x 0.6 tall
_md = [('1', -4.65, 3.75, 0), ('2', -4.65, 2.65, 180), ('3', -4.65, 1.85, 0), ('4', -4.65, 0.25, 0),
       ('5', -3.75, -0.15, 0), ('6', -4.65, -0.55, 180), ('7', -3.75, -0.95, 0), ('8', -4.65, -1.35, 0),
       ('9', -3.75, -1.75, 0), ('10', -4.65, -2.15, 0), ('11', -3.75, -2.55, 0), ('12', -4.65, -2.95, 0),
       ('13', -3.75, -3.35, 0), ('14', -4.65, -3.75, 0),
       ('15', -4.8, -7.15, 270), ('16', -4.0, -7.15, 270), ('17', -3.2, -7.15, 270), ('18', -2.4, -7.15, 90),
       ('19', -2.0, -6.25, 270), ('20', -1.6, -7.15, 90), ('21', -1.2, -6.25, 270), ('22', -0.8, -7.15, 90),
       ('23', -0.4, -6.25, 270), ('24', 0.0, -7.15, 90), ('25', 0.4, -6.25, 270), ('26', 0.8, -7.15, 90),
       ('27', 1.2, -6.25, 270), ('28', 1.6, -7.15, 90), ('29', 2.0, -6.25, 270), ('30', 2.4, -7.15, 90),
       ('31', 3.2, -7.15, 270), ('32', 4.0, -7.15, 270), ('33', 4.8, -7.15, 270),
       ('34', 4.65, -6.15, 180), ('35', 4.65, -5.35, 180), ('36', 3.75, -4.95, 180), ('37', 4.65, -4.55, 180),
       ('38', 3.75, -4.15, 180), ('39', 4.65, -3.75, 180), ('40', 3.75, -3.35, 180), ('41', 4.65, -2.95, 180),
       ('42', 3.75, -2.55, 180), ('43', 3.75, -1.75, 180), ('44', 4.65, -1.35, 180), ('45', 3.75, -0.95, 180),
       ('46', 4.65, -0.55, 180), ('47', 3.75, -0.15, 180), ('48', 4.65, 0.25, 180), ('49', 3.75, 0.65, 180),
       ('50', 3.75, 1.45, 180), ('51', 4.65, 1.85, 180), ('52', 3.75, 2.25, 180), ('53', 4.65, 2.65, 180),
       ('54', 3.75, 3.05, 180), ('55', 4.65, 3.75, 180),
       ('56', -2.0, -0.55, 270), ('57', -1.2, -0.55, 270), ('58', -0.4, -0.55, 270), ('59', 0.4, -0.55, 270),
       ('60', 1.2, -0.55, 270), ('61', 2.0, -0.55, 270)]
_mdpads = []
for n, ex, ey, r in _md:
    w, h = (0.4, 0.6) if r in (90, 270) else (0.6, 0.4)
    _mdpads.append((n, 'smd', 'rect', ex, -ey, w, h, None))
FP['Raytac_MDBT50Q'] = dict(
    descr='Raytac MDBT50Q-1MV2 nRF52840 module 10.5x15.5x2.05mm (chip antenna toward -Y)',
    attr='smd', pads=_mdpads,
    lines=_box(-5.25, -7.75, 5.25, 7.75, 'F.SilkS', 0.12) + _box(-5.25, -7.75, 5.25, 7.75, 'F.Fab', 0.1)
          + _box(-5.6, -8.0, 5.6, 7.95, 'F.CrtYd', 0.05)
          + _box(-6.2, -7.75, 6.2, -3.95, 'Cmts.User', 0.1),
    circles=[], ref_at=(0, 9.0), val_at=(0, 2.0), ref_size=0.8,
    texts=[('Cmts.User', 0, -5.85, 'ANTENNA: NO COPPER', 0.6)])

FP['TestPoint_Pad_D1.0mm'] = dict(descr='SMD test pad 1.0mm', attr='smd',
    pads=[('1', 'smd', 'circle', 0, 0, 1.0, 1.0, None)],
    lines=[], circles=[('F.CrtYd', 0, 0, 0.75)], ref_at=(0, -1.3), val_at=(0, 1.3), ref_size=0.8)

FP['MountingHole_2.2mm_M2'] = dict(descr='M2 mounting hole, NPTH 2.2mm', attr='exclude_from_pos_files exclude_from_bom',
    pads=[('', 'np', 'circle', 0, 0, 2.2, 2.2, 2.2)],
    lines=[], circles=[('Cmts.User', 0, 0, 2.0), ('F.CrtYd', 0, 0, 2.25)],
    ref_at=(0, -3.0), val_at=(0, 3.0), ref_size=0.8)


FP['Tadpole_D3.0_NPTH'] = dict(descr='Tadpole Pin D3.0 mount: NPTH 3.1mm', attr='exclude_from_pos_files exclude_from_bom',
    pads=[('', 'np', 'circle', 0, 0, 3.1, 3.1, 3.1)],
    lines=[], circles=[('Cmts.User', 0, 0, 2.4), ('F.CrtYd', 0, 0, 2.6)],
    ref_at=(0, -3.4), val_at=(0, 3.4), ref_size=0.8)


# ------------------------------------------------------------------ mk2 additions: footprints converted from the
# LCSC/EasyEDA data fetched by CI (.github/workflows/lcsc.yml -> gen/lcsc/*.kicad_mod).  Edge.Cuts lines are dropped
# here (the USB-C notch is drawn into the board outline by pcbio).
import os as _os
import re as _re

_LCSC = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'lcsc')


def _from_kicad_mod(fname, descr, rename=None, keep=('F.SilkS', 'F.CrtYd', 'F.Fab')):
    t = open(_os.path.join(_LCSC, fname)).read()
    pads, lines, edge = [], [], []
    for m in _re.finditer(r'\(pad (\S+) (smd|thru_hole) (\w+) \(at ([-\d.]+) ([-\d.]+)[^)]*\) \(size ([\d.]+) ([\d.]+)\)'
                          r'[^\n]*', t):
        num, kind, shape, x, y, w, h = m.groups()
        num = (rename or {}).get(num, num)
        drill = None
        d = _re.search(r'\(drill oval ([\d.]+) ([\d.]+)\)', m.group(0))
        if d:
            drill = (round(float(d.group(1)), 3), round(float(d.group(2)), 3))
        else:
            d = _re.search(r'\(drill ([\d.]+)\)', m.group(0))
            drill = float(d.group(1)) if d else None
        pads.append((num, 'smd' if kind == 'smd' else 'thru', shape, float(x), float(y), float(w), float(h), drill))
    for m in _re.finditer(r'\(fp_line \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(layer ([\w.]+)\) \(width ([\d.]+)\)', t):
        x1, y1, x2, y2, layer, w = m.groups()
        seg = (layer, float(x1), float(y1), float(x2), float(y2), max(0.05, float(w)))
        if layer == 'Edge.Cuts':
            edge.append(seg)
        elif layer in keep:
            lines.append(seg if layer != 'F.SilkS' else seg[:5] + (0.12,))
    return dict(descr=descr, attr='smd', pads=pads, lines=lines, circles=[], ref_at=(0, -3.0), val_at=(0, 3.0),
                ref_size=0.8, edge=edge)


FP['USB_C_SHOUHAN_16P_CB1.6'] = _from_kicad_mod(
    'USB-C-SMD_SHOU_TYPE-C-16P-CB1.6.kicad_mod',
    'SHOU HAN TYPE-C 16P CB1.6 073 mid-mount USB-C (LCSC C2906290, EasyEDA footprint); needs board notch',
    rename={'25': 'S1', '26': 'S1', '27': 'S1', '28': 'S1'})
FP['LED_XL-2012_Bicolor'] = _from_kicad_mod(
    'LED-SMD_4P-L2.0-W1.3-RD-TL.kicad_mod',
    'XINGLIGHT XL-2012SURSYGC bicolour LED (C965847): 1=R- 2=R+ 3=YG- 4=YG+')
FP['LED_XL-2012_Bicolor']['ref_at'] = (0, -1.6)
FP['FPC_0.5mm_6P_HC'] = _from_kicad_mod(
    'FPC-SMD_6P-P0.50_HCTL_HC-FPC-05-10-6RLTAG.kicad_mod',
    'HCTL HC-FPC-05-10-6RLTAG 0.5mm 6P FPC, bottom contact (C5213729); 7/8 = mounting',
    rename={'7': 'MP', '8': 'MP'})
