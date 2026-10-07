"""tomtho-slim mk2 : 65 keys, roBa-style half stagger, centre Azoteq TPS43 trackpad module (FPC),
ALPS SKRA 6.2mm, 18.5x18 pitch, nRF52840 (Raytac MDBT50Q-1MV2) on board, LiPo + USB-C, ZMK.

Single source of truth for parts and nets.  Key positions come from ../layout_v20.json.
All coordinates: KiCad mm, y-down, origin = rear-left corner of the case outline.
"""
import json
import math
import os
from fplib import FP

HERE = os.path.dirname(os.path.abspath(__file__))
L = json.load(open(os.path.join(HERE, '..', 'layout_v20.json')))
W, H = L['outline']
BOARD = (0.6, 0.6, W - 0.6, H - 0.6)          # PCB = case outline minus 0.6 mm wall clearance
TP = L['trackpad']
FX0 = TP['free_area_x']                         # 114.0: left edge of the centre free area (fixed by the keys)

# ------------------------------------------------------------------ matrix (6 rows x 12 cols, COL2ROW)
MATRIX = {
    0: ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-'],
    1: ['Tab', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '['],
    2: ['Ctl', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', "'", ']'],
    3: ['⇧', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/', 'Ent'],
    4: ['Fn', 'Ctrl', 'Win', '変換 L6', 'Space L2', '無変換 L3', 'BS', 'Enter L1', 'Del', '←', '↑', '→'],
    5: ['BT 切替', None, None, None, None, 'mL', 'mM', 'mR', None, None, '↓', None],
}
MOUSE = {'L': 'mL', 'M': 'mM', 'R': 'mR'}
NROWS, NCOLS = 6, 12


def key_name(k):
    return MOUSE[k['label']] if k['kind'] == 'mouse' else k['label']


def rot(x, y, a):
    a = math.radians(a)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


PARTS = {}


def add(ref, fp, value, x, y, r, nets, sym, lcsc='', desc='', mpn='', bom=True, dnp=False):
    assert fp in FP, fp
    assert ref not in PARTS, f'duplicate reference {ref}'
    PARTS[ref] = dict(ref=ref, fp=fp, value=value, x=x, y=y, rot=r, nets=nets, sym=sym,
                      lcsc=lcsc, desc=desc, mpn=mpn, bom=bom, dnp=dnp)


# --- keys: SW n / D n, numbered in matrix order (row-major)
where = {}
for k in L['keys']:
    where[key_name(k)] = k
CELLS = []                      # (n, r, c, name)
n = 0
for r in range(NROWS):
    for c in range(NCOLS):
        name = MATRIX[r][c]
        if name is None:
            continue
        assert name in where, name
        n += 1
        CELLS.append((n, r, c, name))
        k = where[name]
        a = -k['rot_deg']                       # KiCad rotation is CCW-positive, layout is CW-positive (y-down)
        add(f'SW{n}', 'SW_ALPS_SKRA_6.2mm', 'SKRAAWE010', k['cx'], k['cy'], a,
            {'1': f'COL{c}', '2': f'K{r}_{c}'}, 'SW_Push', 'C202383',
            f'key "{name}" - ALPS SKRA 6.2mm tact', 'SKRAAWE010')
        if name in ('↑', '↓'):                  # stacked 0.5u keys: diode beside the switch, not below it
            dx, dy, da = 6.6, 0.0, 90
        else:
            dx, dy = rot(0, 5.0, a)
            da = a + 180
        add(f'D{n}', 'D_SOD-123', '1N4148W', k['cx'] + dx, k['cy'] + dy, da,
            {'1': f'ROW{r}', '2': f'K{r}_{c}'}, 'D', 'C81598', 'Switching diode', '1N4148W')
assert n == len(L['keys']) == 65, n
NKEYS = n

# --- MCU module in the free area between "5" and "6", antenna at the rear edge
U1X = FX0 + 24.2            # 138.2: module centred in the free area between "5" and "6"
U1Y = 0.6 + 8.05                # antenna edge on the board's rear edge
MCU_PINS = {
    # outer pads: matrix
    '3': 'ROW0', '4': 'ROW1', '6': 'ROW2', '8': 'ROW3', '10': 'ROW4', '12': 'ROW5',
    '14': 'COL0', '16': 'COL1', '20': 'COL2', '22': 'COL3', '24': 'COL4', '26': 'COL5',
    '48': 'COL6', '46': 'COL7', '44': 'COL8', '41': 'COL9', '39': 'COL10', '37': 'COL11',
    # inner pads: LEDs (left) and trackpad (right)
    '5': 'LED_BT1', '7': 'LED_BT2', '9': 'LED_BT3', '11': 'LED_PWR_G', '13': 'LED_PWR_R',
    '36': 'TP_SDA', '38': 'TP_SCL', '42': 'TP_RDY', '43': 'TP_RST',
    # system
    '40': 'RESET', '51': 'SWDIO', '53': 'SWCLK', '35': 'USB_DP', '34': 'USB_DN',
    '28': 'VDD', '30': 'VDDH', '32': 'VBUS',
    '1': 'GND', '2': 'GND', '15': 'GND', '33': 'GND', '55': 'GND',
}
PIN_NAMES = {'1': 'GND', '2': 'GND', '3': 'P1.10', '4': 'P1.11', '5': 'P1.12', '6': 'P1.13', '7': 'P1.14',
             '8': 'P1.15', '9': 'P0.03/AIN1', '10': 'P0.29/AIN5', '11': 'P0.02/AIN0', '12': 'P0.31/AIN7',
             '13': 'P0.28/AIN4', '14': 'P0.30/AIN6', '15': 'GND', '16': 'P0.27', '17': 'P0.00/XL1',
             '18': 'P0.01/XL2', '19': 'P0.26', '20': 'P0.04/AIN2', '21': 'P0.05/AIN3', '22': 'P0.06',
             '23': 'P0.07', '24': 'P0.08', '25': 'P1.08', '26': 'P1.09', '27': 'P0.11', '28': 'VDD',
             '29': 'P0.12', '30': 'VDDH', '31': 'DCCH', '32': 'VBUS', '33': 'GND', '34': 'D-', '35': 'D+',
             '36': 'P0.14', '37': 'P0.13', '38': 'P0.16', '39': 'P0.15', '40': 'P0.18/RESET', '41': 'P0.17',
             '42': 'P0.19', '43': 'P0.21', '44': 'P0.20', '45': 'P0.23', '46': 'P0.22', '47': 'P1.00',
             '48': 'P0.24', '49': 'P0.25', '50': 'P1.02', '51': 'SWDIO', '52': 'P0.09/NFC1', '53': 'SWDCLK',
             '54': 'P0.10/NFC2', '55': 'GND', '56': 'P1.04', '57': 'P1.06', '58': 'P1.07', '59': 'P1.05',
             '60': 'P1.03', '61': 'P1.01'}
add('U1', 'Raytac_MDBT50Q', 'MDBT50Q-1MV2', U1X, U1Y, 0, dict(MCU_PINS), 'MDBT50Q', 'C5118826',
    'nRF52840 BLE module, chip antenna, TELEC certified', 'MDBT50Q-1MV2')

FX = FX0                        # 114.0  free area: x 113.5..163.5, y 0.6..28.2 (trackpad starts at 28.7)
# module decoupling, right of the module
add('C2', 'C_0603', '10uF', U1X + 7.4, 5.0, 90, {'1': 'VDDH', '2': 'GND'}, 'C', 'C19702', '10V X5R', 'CL10A106KP8NNNC')
add('C3', 'C_0603', '100nF', U1X + 9.2, 5.0, 90, {'1': 'VDDH', '2': 'GND'}, 'C', 'C14663', '50V X7R', 'CC0603KRX7R9BB104')
add('C4', 'C_0603', '4.7uF', U1X + 7.4, 9.0, 90, {'1': 'VDD', '2': 'GND'}, 'C', 'C19666', '16V X5R', 'CL10A475KO8NNNC')
add('C5', 'C_0603', '100nF', U1X + 9.2, 9.0, 90, {'1': 'VDD', '2': 'GND'}, 'C', 'C14663', '50V X7R', 'CC0603KRX7R9BB104')
add('C1', 'C_0603', '4.7uF', U1X + 7.4, 13.0, 90, {'1': 'VBUS', '2': 'GND'}, 'C', 'C19666', '16V X5R', 'CL10A475KO8NNNC')

# reset + SWD pads, below the module
add('SW66', 'SW_TS-1928-B', 'RESET', U1X, 19.6, 0, {'1': 'RESET', '2': 'GND'}, 'SW_Push', 'C1121891',
    'Reset (double-tap = UF2 bootloader)', 'TS-1928-B')
for i, net in enumerate(['SWDIO', 'SWCLK', 'GND', 'VDD']):
    add(f'TP{i + 1}', 'TestPoint_Pad_D1.0mm', net, U1X - 3.81 + i * 2.54, 24.0, 0, {'1': net}, 'TestPoint', bom=False,
        desc='SWD pad for first bootloader flash')

# USB-C (top mount, rear edge) + ESD
add('J1', 'USB_C_HRO_TYPE-C-31-M-12', 'USB-C', FX + 6.0, 0.6 + 3.65, 180,
    {'A1': 'GND', 'B1': 'GND', 'A12': 'GND', 'B12': 'GND', 'A4': 'VBUS', 'B4': 'VBUS', 'A9': 'VBUS', 'B9': 'VBUS',
     'A5': 'CC1', 'B5': 'CC2', 'A6': 'USB_DP', 'B6': 'USB_DP', 'A7': 'USB_DN', 'B7': 'USB_DN', 'S1': 'GND'},
    'USB_C', 'C165948', 'USB2.0 Type-C receptacle, top mount (sits in the free area under the case top)', 'TYPE-C-31-M-12')
add('R1', 'R_0603', '5.1k', FX + 2.0, 12.0, 90, {'1': 'CC1', '2': 'GND'}, 'R', 'C23186', 'CC pull-down', '0603WAF5101T5E')
add('R2', 'R_0603', '5.1k', FX + 10.0, 12.0, 90, {'1': 'CC2', '2': 'GND'}, 'R', 'C23186', 'CC pull-down', '0603WAF5101T5E')
add('U2', 'SOT-23-6', 'USBLC6-2SC6', FX + 6.0, 12.0, 0,
    {'1': 'USB_DP', '6': 'USB_DP', '3': 'USB_DN', '4': 'USB_DN', '5': 'VBUS', '2': 'GND'},
    'USBLC6', 'C7519', 'USB ESD protection', 'USBLC6-2SC6')

# charger (MCP73831, 100 mA)
add('U3', 'SOT-23-5', 'MCP73831', FX + 6.0, 17.0, 0,
    {'1': 'CHG_STAT', '2': 'GND', '3': 'VBAT', '4': 'VBUS', '5': 'PROG'}, 'MCP73831', 'C424093',
    'Li-Po charger 4.2V', 'MCP73831T-2ACI/OT')
add('C6', 'C_0603', '4.7uF', FX + 2.0, 17.0, 90, {'1': 'VBUS', '2': 'GND'}, 'C', 'C19666', '16V X5R', 'CL10A475KO8NNNC')
add('C7', 'C_0603', '4.7uF', FX + 10.0, 17.0, 90, {'1': 'VBAT', '2': 'GND'}, 'C', 'C19666', '16V X5R', 'CL10A475KO8NNNC')
add('R3', 'R_0603', '4.7k', FX + 6.0, 20.2, 0, {'1': 'PROG', '2': 'GND'}, 'R', 'C23162', 'Ichg = 1000V/4.7k = 213mA (0.2-0.5C for an 800-1000 mAh cell)',
    '0603WAF4701T5E')

# load-sharing power path (Microchip AN1149 style)
add('D66', 'D_SOD-123', 'B5819W', FX + 15.5, 12.0, 90, {'1': 'VSYS', '2': 'VBUS'}, 'D_Schottky', 'C8598',
    'VBUS -> VSYS', 'B5819W SL')
add('Q1', 'SOT-23', 'AO3401A', FX + 15.0, 18.0, 0, {'1': 'VBUS', '2': 'VSYS', '3': 'VBAT'}, 'PMOS', 'C15127',
    'Battery -> VSYS when no USB', 'AO3401A')
add('R5', 'R_0603', '100k', FX + 15.0, 21.5, 0, {'1': 'VBUS', '2': 'GND'}, 'R', 'C25803', 'Q1 gate pull-down',
    '0603WAF1003T5E')
# power switch (rear edge, right of the module) + battery connector (LiPo sits under the PCB)
add('SW67', 'SW_SPDT_PCM12', 'POWER', FX + 41.0, 0.6 + 2.6, 180, {'1': 'VDDH', '2': 'VSYS'},
    'SW_SPDT', 'C221841', 'Power slide switch (pin3 = OFF, open)', 'PCM12SMTR')
add('J2', 'JST_SH_SM02B-SRSS-TB', 'BATTERY', FX + 5.0, 24.6, 90, {'1': 'VBAT', '2': 'GND'}, 'Conn_02', 'C160402',
    'LiPo 1S (protected cell), check polarity!', 'SM02B-SRSS-TB(LF)(SN)')

# charge LED (red, VBUS powered, on while charging) - top right, next to the power LED
add('R4', 'R_0603', '1k', W - 14.0, 10.0, 90, {'1': 'VBUS', '2': 'LED_CHG_A'}, 'R', 'C21190', 'LED resistor',
    '0603WAF1001T5E')
add('LED1', 'LED_0603', 'RED', W - 14.0, 6.5, 90, {'1': 'CHG_STAT', '2': 'LED_CHG_A'}, 'LED', 'C2286',
    'Charge indicator (on while charging)', 'KT-0603R')

# indicator LEDs: bicolour XL-2012SURSYGC (1=R- 2=R+ 3=YG- 4=YG+), both anodes on VDD, cathodes sunk by GPIO via 1k
LEDS = L['leds']
_led = {e['name']: e for e in LEDS}
LED_RES = 'C21190'
for i in range(3):
    e = _led[f'BT{i + 1}']
    add(f'LED{2 + i}', 'LED_XL-2012_Bicolor', 'XL-2012SURSYGC', e['cx'], e['cy'], 0,
        {'2': 'VDD', '4': 'VDD', '3': f'LED_BT{i + 1}_K'}, 'LED_Dual_CA', 'C965847',
        f'BT{i + 1} profile LED (yellow-green die used, red unused)', 'XL-2012SURSYGC')
    add(f'R{6 + i}', 'R_0603', '1k', e['cx'], e['cy'] + 2.6, 0, {'1': f'LED_BT{i + 1}_K', '2': f'LED_BT{i + 1}'},
        'R', LED_RES, 'LED current ~1 mA', '0603WAF1001T5E')
e = _led['PWR']
add('LED5', 'LED_XL-2012_Bicolor', 'XL-2012SURSYGC', e['cx'], e['cy'], 0,
    {'2': 'VDD', '4': 'VDD', '1': 'LED_PWR_RK', '3': 'LED_PWR_GK'}, 'LED_Dual_CA', 'C965847',
    'Power / battery LED (green = OK, red = <20 %)', 'XL-2012SURSYGC')
add('R9', 'R_0603', '1k', e['cx'] - 1.2, e['cy'] + 2.6, 90, {'1': 'LED_PWR_GK', '2': 'LED_PWR_G'}, 'R', LED_RES,
    'LED current ~1 mA', '0603WAF1001T5E')
add('R10', 'R_0603', '1k', e['cx'] + 1.2, e['cy'] + 2.6, 90, {'1': 'LED_PWR_RK', '2': 'LED_PWR_R'}, 'R', LED_RES,
    'LED current ~1 mA', '0603WAF1001T5E')

# trackpad module connector (FPC 6P 0.5 mm) + I2C pull-ups
# Azoteq TPS43-201A-S (43 x 40, 1.0 t PCB, IQS572, ZIF J1 on its underside) is stuck with its own 3M 468 adhesive to
# the underside of the case-top window.  Its underside parts hang into a cut-out of this board, so the pad surface can
# sit flush with the case top.  J3 is just left of the cut-out.  TPS43 J1 pinout (datasheet table 2.1):
# 1 RDY, 2 NRST, 3 GND, 4 VDDHI, 5 SCL, 6 SDA  -> J3 uses the same numbering.  The FFC type (A = same side /
# B = opposite sides) is chosen once the position and contact side of the module's ZIF are measured: pin 1 must
# reach pin 1 (a mirrored cable swaps GND and VDD).
TP_CUT = (TP['x'] - 0.5, TP['y'] - 0.5, TP['x'] + TP['w'] + 0.5, TP['y'] + TP['h'] + 0.5)
TPJ = (TP_CUT[0], TP['y'] + TP['h'] / 2 - 2.0)
add('J3', 'FPC_0.5mm_6P_HC', 'TRACKPAD', TP_CUT[0] - 2.3, TPJ[1], 90,
    {'1': 'TP_RDY', '2': 'TP_RST', '3': 'GND', '4': 'VDD', '5': 'TP_SCL', '6': 'TP_SDA', 'MP': 'GND'},
    'Conn_FPC6', 'C5213729', 'To Azoteq TPS43 trackpad module (FFC 6P 0.5 mm)', 'HC-FPC-05-10-6RLTAG')
add('R11', 'R_0603', '4.7k', TP_CUT[0] - 2.6, TPJ[1] - 4.6, 90, {'1': 'VDD', '2': 'TP_SDA'}, 'R', 'C23162',
    'I2C pull-up', '0603WAF4701T5E')
add('R12', 'R_0603', '4.7k', TP_CUT[0] - 2.6, TPJ[1] + 4.6, 90, {'1': 'VDD', '2': 'TP_SCL'}, 'R', 'C23162',
    'I2C pull-up', '0603WAF4701T5E')

# mounting holes (between key columns; checked against key positions at PCB stage)
for i, (x, y) in enumerate([(39.0, 58.0), (W - 39.0, 58.0), (FX0 - 2.0, 4.0), (FX0 + 49.0 + 2.0, 4.0),
                            (W / 2, H - 8.0)]):
    add(f'H{i + 1}', 'MountingHole_2.2mm_M2', 'M2', x, y, 0, {}, 'MountingHole', bom=False)

POWER_NETS = {'VBUS', 'VSYS', 'VBAT', 'VDDH', 'VDD'}

# ------------------------------------------------------------------ board-level geometry for the PCB writer / router
VIA = (0.6, 0.3)
CORNER_R = 4.4
ANT_KEEPOUT = (U1X - 6.2, BOARD[1], U1X + 6.2, U1Y - 3.95)           # no copper on either layer
MODULE_FCU_KEEPOUT = (U1X - 2.5, U1Y - 3.5, U1X + 2.5, U1Y + 5.6)     # no F.Cu tracks under the module centre
BATTERY_AREA = (22.0, 34.0, 92.0, 74.0)                                # LiPo under the PCB (B side), 70 x 40 max
SLOTS = [(112.4, 21.6, 113.6, 27.6), TP_CUT]                            # battery lead pass-through, trackpad cut-out
SILK_RECTS = [('B.SilkS',) + BATTERY_AREA]
SILK_TEXTS = [
    ('B.SilkS', 57.0, 54.0, 'LiPo 1S  (<= 3.0 t x 40 x 70)', 1.5),
    ('B.SilkS', 57.0, 57.5, 'lead -> slot -> J2 (pin1 = +)', 1.0),
    ('B.SilkS', 200.0, 54.0, 'tomtho-slim mk2', 2.5),
    ('B.SilkS', 200.0, 58.0, 'nRF52840 MDBT50Q / TPS43 / ZMK / 18.5x18', 1.2),
    ('B.SilkS', 200.0, 61.0, 'JLCJLCJLCJLC', 1.0),
    ('F.SilkS', U1X - 3.81 + 3.81, 25.9, 'DIO CLK GND VDD', 0.8),
    ('F.SilkS', FX + 41.0, 7.4, 'ON   OFF', 0.8),
    ('F.SilkS', FX + 2.4, 27.6, '+', 1.0),
]
TRACKS, VIAS = [], []
for _r in ('C2', 'C3', 'C4', 'C5', 'R9', 'R10', 'U2', 'H3', 'H4'):
    PARTS[_r]['ref_fab'] = True                     # crowded spots: reference on F.Fab instead of silk

# inner-row module pads cannot escape between the outer pads (0.4 mm gaps): short F.Cu stub inward to a via
ESC_PADS = ['5', '7', '9', '11', '13', '36', '38', '40', '42', '43']


def escapes():
    t, v = [], []
    for num in ESC_PADS:
        net = MCU_PINS[num]
        X, Y = next((h[3], h[4]) for h in pad_world(PARTS['U1']) if h[0] == num)
        vx = X + (0.75 if X < U1X else -0.75)
        t.append(('F.Cu', X, Y, vx, Y, 0.2, net))
        v.append((vx, Y, net))
    return t, v


def pad_world(part):
    fp = FP[part['fp']]
    for (num, kind, shape, x, y, w, h, drill) in fp['pads']:
        dx, dy = rot(x, y, part['rot'])
        W_, H_ = (h, w) if part['rot'] % 180 == 90 else (w, h)
        net = part['nets'].get(num, '') if num else ''
        yield num, kind, shape, part['x'] + dx, part['y'] + dy, W_, H_, drill, net


def all_nets():
    s = set()
    for p in PARTS.values():
        s.update(v for v in p['nets'].values() if v)
    return sorted(s)


if __name__ == '__main__':
    print(len(PARTS), 'parts', len(all_nets()), 'nets', NKEYS, 'keys')
    used = [v for v in MCU_PINS.values() if v not in ('GND',)]
    print('MCU pins used:', len(MCU_PINS), 'GPIO signals:', sum(1 for v in MCU_PINS.values()
          if v.startswith(('ROW', 'COL', 'LED', 'TP_'))))
