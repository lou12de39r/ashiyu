"""Schematic generator (KiCad 9/10 s-expression).  Netlist comes from design.PARTS, so it is
identical to the PCB by construction; symbol <-> footprint linkage uses the same UUIDs."""
import design as D
from pcbio import U, q, f, PROJECT, LIB, ROOT_UUID, REPO

FONT = '(effects (font (size 1.27 1.27)))'
FONT_H = '(effects (font (size 1.27 1.27)) (hide yes))'


def fnt(j=None, hide=False, size=1.27):
    s = f'(effects (font (size {f(size)} {f(size)}))'
    if j:
        s += f' (justify {j})'
    if hide:
        s += ' (hide yes)'
    return s + ')'


# ------------------------------------------------------------------ symbol library
SYMS = {}


def sym(name, pins, graphics, ref, desc, show_num=True, show_names=True, power=False, props=None):
    SYMS[name] = dict(pins=pins, graphics=graphics, ref=ref, desc=desc, show_num=show_num,
                      show_names=show_names, power=power, props=props or {})


def rect(x1, y1, x2, y2, fill='background'):
    return f'(rectangle (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width 0.254) (type default)) (fill (type {fill})))'


def poly(pts, fill='none', w=0.254):
    p = ' '.join(f'(xy {f(x)} {f(y)})' for x, y in pts)
    return f'(polyline (pts {p}) (stroke (width {f(w)}) (type default)) (fill (type {fill})))'


def circ(x, y, r, fill='none'):
    return f'(circle (center {f(x)} {f(y)}) (radius {f(r)}) (stroke (width 0.254) (type default)) (fill (type {fill})))'


# pins: (num, name, x, y, angle, length, etype)
sym('R', [('1', '~', 0, 3.81, 270, 1.27, 'passive'), ('2', '~', 0, -3.81, 90, 1.27, 'passive')],
    [rect(-1.016, -2.54, 1.016, 2.54, 'none')], 'R', 'Resistor', show_num=False, show_names=False)
sym('C', [('1', '~', 0, 3.81, 270, 2.794, 'passive'), ('2', '~', 0, -3.81, 90, 2.794, 'passive')],
    [poly([(-2.032, 0.762), (2.032, 0.762)], w=0.508), poly([(-2.032, -0.762), (2.032, -0.762)], w=0.508)],
    'C', 'Capacitor', show_num=False, show_names=False)
_dio = [poly([(-1.27, 1.27), (1.27, 1.27), (0, -1.27), (-1.27, 1.27)], 'none'), poly([(-1.27, -1.27), (1.27, -1.27)])]
sym('D', [('1', 'K', 0, -3.81, 90, 2.54, 'passive'), ('2', 'A', 0, 3.81, 270, 2.54, 'passive')],
    _dio, 'D', 'Diode (pin1=K)', show_num=False, show_names=False)
sym('D_Schottky', [('1', 'K', 0, -3.81, 90, 2.54, 'passive'), ('2', 'A', 0, 3.81, 270, 2.54, 'passive')],
    _dio + [poly([(-1.27, -1.27), (-1.27, -0.762)]), poly([(1.27, -1.27), (1.27, -1.778)])],
    'D', 'Schottky diode (pin1=K)', show_num=False, show_names=False)
sym('LED', [('1', 'K', 0, -3.81, 90, 2.54, 'passive'), ('2', 'A', 0, 3.81, 270, 2.54, 'passive')],
    _dio + [poly([(1.778, 0.508), (2.794, -0.508)]), poly([(2.286, 1.016), (3.302, 0)])],
    'LED', 'LED (pin1=K)', show_num=False, show_names=False)
sym('SW_Push', [('1', '1', -5.08, 0, 0, 2.54, 'passive'), ('2', '2', 5.08, 0, 180, 2.54, 'passive')],
    [circ(-2.032, 0, 0.508), circ(2.032, 0, 0.508), poly([(-2.54, 1.27), (2.54, 1.27)]),
     poly([(0, 1.27), (0, 3.048)])], 'SW', 'Push switch', show_num=False, show_names=False)
sym('SW_SPDT', [('2', 'C', -5.08, 0, 0, 2.54, 'passive'), ('1', 'A', 5.08, 2.54, 180, 2.54, 'passive'),
                ('3', 'B', 5.08, -2.54, 180, 2.54, 'passive')],
    [circ(-2.032, 0, 0.508), circ(2.032, 2.54, 0.508), circ(2.032, -2.54, 0.508), poly([(-1.524, 0.254), (1.778, 2.032)])],
    'SW', 'SPDT slide switch', show_names=False)
sym('PMOS', [('1', 'G', -5.08, 0, 0, 2.54, 'passive'), ('2', 'S', 2.54, 5.08, 270, 2.54, 'passive'),
             ('3', 'D', 2.54, -5.08, 90, 2.54, 'passive')],
    [poly([(-1.016, 1.778), (-1.016, -1.778)]), poly([(-2.54, 0), (-1.016, 0)]),
     poly([(-0.508, 1.778), (-0.508, -1.778)]), poly([(-0.508, 1.27), (2.54, 1.27), (2.54, 2.54)]),
     poly([(-0.508, -1.27), (2.54, -1.27), (2.54, -2.54)]), circ(0.5, 0, 2.8)],
    'Q', 'P-channel MOSFET (1=G 2=S 3=D)')
sym('TestPoint', [('1', '1', 0, 0, 90, 0, 'passive')], [circ(0, 1.27, 0.762)], 'TP', 'Test pad',
    show_num=False, show_names=False)
sym('MountingHole', [], [circ(0, 0, 1.27), circ(0, 0, 0.635)], 'H', 'Mounting hole', show_num=False)
sym('GND', [('1', 'GND', 0, 0, 270, 0, 'power_in')],
    [poly([(0, 0), (0, -1.27), (1.27, -1.27), (0, -2.54), (-1.27, -1.27), (0, -1.27)])], '#PWR', 'Ground',
    show_num=False, show_names=False, power=True)
sym('PWR_FLAG', [('1', 'pwr', 0, 0, 90, 0, 'power_out')],
    [poly([(0, 0), (0, 1.27), (-1.016, 1.905), (0, 2.54), (1.016, 1.905), (0, 1.27)])], '#FLG', 'Power flag',
    show_num=False, show_names=False, power=False)


def box(name, left, right, w, ref, desc, top=(), bottom=()):
    n = max(len(left), len(right), 1)
    h = n * 2.54
    pins = []
    for side, lst in (('L', left), ('R', right)):
        for k, (num, nm) in enumerate(lst):
            y = (n - 1) * 2.54 / 2 - k * 2.54
            if side == 'L':
                pins.append((num, nm, -w / 2 - 2.54, y, 0, 2.54, 'passive'))
            else:
                pins.append((num, nm, w / 2 + 2.54, y, 180, 2.54, 'passive'))
    sym(name, pins, [rect(-w / 2, h / 2 + 1.27, w / 2, -h / 2 - 1.27)], ref, desc)


# MDBT50Q: system pins left, GPIO right
_sys = ['28', '30', '31', '32', '35', '34', '51', '53', '40', '17', '18', '52', '54', '1', '2', '15', '33', '55']
_gpio = [p for p in sorted(D.PIN_NAMES, key=int) if p not in _sys]
_gpio.sort(key=lambda p: (D.PIN_NAMES[p].split('/')[0][:2], int(D.PIN_NAMES[p].split('/')[0].split('.')[1])))
box('MDBT50Q', [(p, D.PIN_NAMES[p]) for p in _sys], [(p, D.PIN_NAMES[p]) for p in _gpio], 20.32, 'U',
    'Raytac MDBT50Q-1MV2 nRF52840 module')
box('MCP73831', [('4', 'VDD'), ('1', 'STAT'), ('5', 'PROG')], [('3', 'VBAT'), ('2', 'VSS')], 12.7, 'U',
    'Li-Po charger')
box('USBLC6', [('1', 'I/O1'), ('3', 'I/O2'), ('5', 'VBUS')], [('6', 'I/O1'), ('4', 'I/O2'), ('2', 'GND')], 12.7, 'U',
    'USB ESD')
box('USB_C', [('A4', 'VBUS'), ('A9', 'VBUS'), ('B4', 'VBUS'), ('B9', 'VBUS'), ('A5', 'CC1'), ('B5', 'CC2'),
              ('A6', 'D+'), ('B6', 'D+'), ('A7', 'D-'), ('B7', 'D-'), ('A8', 'SBU1'), ('B8', 'SBU2')],
    [('A1', 'GND'), ('A12', 'GND'), ('B1', 'GND'), ('B12', 'GND'), ('S1', 'SHIELD')], 12.7, 'J',
    'USB 2.0 Type-C receptacle')
box('Conn_02', [('1', 'BAT+'), ('2', 'BAT-')], [], 7.62, 'J', 'JST SH 2-pin')
box('LED_Dual_CA', [('2', 'R+'), ('4', 'YG+')], [('1', 'R-'), ('3', 'YG-')], 10.16, 'LED',
    'Bicolour LED, common anode (XL-2012SURSYGC)')
box('Conn_FPC6', [('1', 'RDY'), ('2', 'RST'), ('3', 'GND'), ('4', 'VDD'), ('5', 'SCL'), ('6', 'SDA')],
    [('MP', 'MP')], 10.16, 'J', 'FPC 6P 0.5 mm')


def lib_symbols():
    o = ['\t(lib_symbols\n']
    for name, s in SYMS.items():
        flags = ''
        if s['power']:
            flags += ' (power)'
        if not s['show_num']:
            flags += ' (pin_numbers (hide yes))'
        flags += ' (pin_names (offset 0.508)' + ('' if s['show_names'] else ' (hide yes)') + ')'
        o.append(f'\t\t(symbol {q(LIB + ":" + name)}{flags} (exclude_from_sim no) (in_bom {"no" if s["power"] else "yes"}) '
                 f'(on_board {"no" if s["power"] else "yes"})\n')
        o.append(f'\t\t\t(property "Reference" {q(s["ref"])} (at 0 5.08 0) {fnt(hide=s["power"])})\n')
        o.append(f'\t\t\t(property "Value" {q(name)} (at 0 -5.08 0) {fnt()})\n')
        o.append(f'\t\t\t(property "Footprint" "" (at 0 0 0) {fnt(hide=True)})\n')
        o.append(f'\t\t\t(property "Datasheet" "~" (at 0 0 0) {fnt(hide=True)})\n')
        o.append(f'\t\t\t(property "Description" {q(s["desc"])} (at 0 0 0) {fnt(hide=True)})\n')
        o.append(f'\t\t\t(symbol {q(name + "_0_1")}\n')
        for g in s['graphics']:
            o.append(f'\t\t\t\t{g}\n')
        o.append('\t\t\t)\n')
        o.append(f'\t\t\t(symbol {q(name + "_1_1")}\n')
        for (num, nm, x, y, a, ln, et) in s['pins']:
            hide = ' (hide yes)' if s['power'] else ''
            o.append(f'\t\t\t\t(pin {et} line (at {f(x)} {f(y)} {a}) (length {f(ln)}){hide} (name {q(nm)} {FONT}) '
                     f'(number {q(num)} {FONT}))\n')
        o.append('\t\t\t)\n\t\t)\n')
    o.append('\t)\n')
    return ''.join(o)


# ------------------------------------------------------------------ placement
ITEMS = []
PWR_N = [0]


def pin_xy(symname, num, X, Y):
    for p in SYMS[symname]['pins']:
        if p[0] == num:
            return X + p[2], Y - p[3], p[4]
    raise KeyError((symname, num))


def label(net, x, y, pin_angle):
    # pin_angle: direction the pin points INTO the body; label must extend the other way
    out = {0: 180, 180: 0, 90: 270, 270: 90}[pin_angle]
    if net == 'GND':
        PWR_N[0] += 1
        rot = {270: 0, 90: 180, 180: 270, 0: 90}[out]  # GND graphic points away from the pin
        ITEMS.append(f'\t(symbol (lib_id {q(LIB + ":GND")}) (at {f(x)} {f(y)} {rot}) (unit 1) (exclude_from_sim no) '
                     f'(in_bom no) (on_board no) (dnp no) (uuid {q(U("pwr", PWR_N[0]))})\n'
                     f'\t\t(property "Reference" "#PWR{PWR_N[0]:03d}" (at {f(x)} {f(y + 6)} 0) {fnt(hide=True)})\n'
                     f'\t\t(property "Value" "GND" (at {f(x)} {f(y + 3.8)} 0) {fnt(size=1.0)})\n'
                     f'\t\t(property "Footprint" "" (at {f(x)} {f(y)} 0) {fnt(hide=True)})\n'
                     f'\t\t(property "Datasheet" "" (at {f(x)} {f(y)} 0) {fnt(hide=True)})\n'
                     f'\t\t(property "Description" "" (at {f(x)} {f(y)} 0) {fnt(hide=True)})\n'
                     f'\t\t(pin "1" (uuid {q(U("pwrpin", PWR_N[0]))}))\n'
                     f'\t\t(instances (project {q(PROJECT)} (path "/{ROOT_UUID}" (reference "#PWR{PWR_N[0]:03d}") (unit 1))))\n\t)\n')
        return
    just = {0: 'left bottom', 180: 'right bottom', 90: 'left bottom', 270: 'right bottom'}[out]
    ITEMS.append(f'\t(label {q(net)} (at {f(x)} {f(y)} {out}) {fnt(just)} (uuid {q(U("lbl", net, x, y))}))\n')


def noconn(x, y):
    ITEMS.append(f'\t(no_connect (at {f(x)} {f(y)}) (uuid {q(U("nc", x, y))}))\n')


def wire(a, b):
    ITEMS.append(f'\t(wire (pts (xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])})) (stroke (width 0) (type default)) '
                 f'(uuid {q(U("w", a, b))}))\n')


def text(t, x, y, size=1.5):
    t = t.replace('\\n', '\n')
    ITEMS.append(f'\t(text {q(t).replace(chr(10), "\\n")} (exclude_from_sim no) (at {f(x)} {f(y)} 0) '
                 f'{fnt("left top", size=size)} (uuid {q(U("text", t[:40], x, y))}))\n')


def place(ref, X, Y, nets_override=None, labels=True, wired=()):
    p = D.PARTS[ref]
    sname = p['sym']
    s = SYMS[sname]
    lcsc = p.get('lcsc', '')
    inbom = 'yes' if p['bom'] else 'no'
    pins_out = []
    o = [f'\t(symbol (lib_id {q(LIB + ":" + sname)}) (at {f(X)} {f(Y)} 0) (unit 1) (exclude_from_sim no) '
         f'(in_bom {inbom}) (on_board yes) (dnp no) (uuid {q(U("sym", ref))})\n']
    ys = [pp[3] for pp in s['pins']] or [0]
    xs = [pp[2] for pp in s['pins']] or [0]
    if sname in ('R', 'C', 'D', 'D_Schottky', 'LED'):
        rp, vp, j = (X + 2.54, Y - 1.0), (X + 2.54, Y + 1.5), 'left'
    elif sname == 'TestPoint':
        rp, vp, j = (X + 1.8, Y - 2.2), (X + 1.8, Y - 0.6), 'left'
    else:
        top = Y - max(ys) - 2.6
        rp, vp, j = (X + min(xs) + 2.54, top - 1.5), (X + min(xs) + 2.54, Y - min(ys) + 4.0), 'left'
    o.append(f'\t\t(property "Reference" {q(ref)} (at {f(rp[0])} {f(rp[1])} 0) {fnt(j)})\n')
    o.append(f'\t\t(property "Value" {q(p["value"])} (at {f(vp[0])} {f(vp[1])} 0) {fnt(j)})\n')
    o.append(f'\t\t(property "Footprint" {q(LIB + ":" + p["fp"])} (at {f(X)} {f(Y)} 0) {fnt(hide=True)})\n')
    o.append(f'\t\t(property "Datasheet" "~" (at {f(X)} {f(Y)} 0) {fnt(hide=True)})\n')
    o.append(f'\t\t(property "Description" {q(p["desc"])} (at {f(X)} {f(Y)} 0) {fnt(hide=True)})\n')
    o.append(f'\t\t(property "LCSC" {q(lcsc)} (at {f(X)} {f(Y)} 0) {fnt(hide=True)})\n')
    o.append(f'\t\t(property "MPN" {q(p.get("mpn", ""))} (at {f(X)} {f(Y)} 0) {fnt(hide=True)})\n')
    for (num, *_r) in s['pins']:
        o.append(f'\t\t(pin {q(num)} (uuid {q(U("spin", ref, num))}))\n')
    o.append(f'\t\t(instances (project {q(PROJECT)} (path "/{ROOT_UUID}" (reference {q(ref)}) (unit 1))))\n\t)\n')
    ITEMS.append(''.join(o))
    nets = dict(p['nets'])
    if nets_override:
        nets.update(nets_override)
    for (num, nm, x, y, a, ln, et) in s['pins']:
        px, py = X + x, Y - y
        pins_out.append((num, px, py, a))
        if num in wired:
            continue
        net = nets.get(num, '')
        if net:
            if labels:
                label(net, px, py, a)
        else:
            noconn(px, py)
    return {n: (x, y) for (n, x, y, a) in pins_out}


def junction(x, y):
    ITEMS.append(f'\t(junction (at {f(x)} {f(y)}) (diameter 0) (color 0 0 0 0) (uuid {q(U("j", x, y))}))\n')


def pwr_flag(x, y, net, n):
    ITEMS.append(f'\t(symbol (lib_id {q(LIB + ":PWR_FLAG")}) (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) '
                 f'(in_bom no) (on_board no) (dnp no) (uuid {q(U("flag", n))})\n'
                 f'\t\t(property "Reference" "#FLG0{n}" (at {f(x)} {f(y - 4)} 0) {fnt(hide=True)})\n'
                 f'\t\t(property "Value" "PWR_FLAG" (at {f(x)} {f(y - 3.6)} 0) {fnt(size=1.0)})\n'
                 f'\t\t(property "Footprint" "" (at {f(x)} {f(y)} 0) {fnt(hide=True)})\n'
                 f'\t\t(property "Datasheet" "" (at {f(x)} {f(y)} 0) {fnt(hide=True)})\n'
                 f'\t\t(property "Description" "" (at {f(x)} {f(y)} 0) {fnt(hide=True)})\n'
                 f'\t\t(pin "1" (uuid {q(U("flagpin", n))}))\n'
                 f'\t\t(instances (project {q(PROJECT)} (path "/{ROOT_UUID}" (reference "#FLG0{n}") (unit 1))))\n\t)\n')
    label(net, x, y, 90)


def build():
    ITEMS.clear()
    text('tomtho-slim mk2  -  65 keys, roBa-style half stagger, centre trackpad (Azoteq TPS43 module)\\n'
         'ALPS SKRA 6.2mm / 18.5 x 18 mm pitch / nRF52840 (Raytac MDBT50Q-1MV2, TELEC) / 1S LiPo + USB-C / ZMK',
         20, 12, 2.0)
    # ---- MCU
    text('MCU  (REG0 LDO mode: DCCH open, VDDH = system rail)', 20, 30)
    place('U1', 60.96, 101.6)
    text('Module decoupling (place at pins)', 20, 168)
    for i, ref in enumerate(['C2', 'C3', 'C4', 'C5', 'C1']):
        place(ref, 25.4 + i * 10.16, 182.88)
    # ---- reset / SWD
    text('Reset (double-tap = UF2)  /  SWD pads', 80, 168)
    place('SW66', 91.44, 182.88)
    for i in range(4):
        place(f'TP{i + 1}', 106.68 + i * 7.62, 182.88)
    # ---- USB
    text('USB-C mid-mount (5.1k CC pull-downs = sink)', 120, 30)
    place('J1', 139.7, 66.04)
    place('U2', 177.8, 50.8)
    place('R1', 170.18, 78.74)
    place('R2', 182.88, 78.74)
    # ---- charger
    text('Charger MCP73831\\nIchg = 1000V / R3 = 100 mA\\nLED1 = charging (VBUS powered)', 205, 30)
    place('U3', 233.68, 55.88)
    place('C6', 213.36, 76.2)
    place('C7', 254.0, 76.2)
    place('R3', 223.52, 76.2)
    place('R4', 213.36, 96.52)
    place('LED1', 223.52, 96.52)
    # ---- power path
    text('Load sharing (AN1149)\\nUSB -> D66, battery -> Q1\\nSW67: VSYS -> VDDH', 275, 30)
    place('D66', 285.75, 55.88)
    place('Q1', 300.99, 66.04)
    place('R5', 285.75, 78.74)
    place('SW67', 297.18, 96.52)
    text('Battery\\n1S LiPo (protected)', 330, 30)
    place('J2', 345.44, 50.8)
    pwr_flag(335.28, 76.2, 'GND', 1)
    pwr_flag(345.44, 76.2, 'VSYS', 2)
    pwr_flag(355.6, 76.2, 'VBAT', 3)
    # ---- LEDs
    text('Indicator LEDs: bicolour, anode = VDD, GPIO sinks (active low)\\n'
         'LED2-4 = BT1-3 (green die)  /  LED5 = power (green OK, red < 20 %)', 375, 22)
    for i in range(3):
        place(f'LED{2 + i}', 393.7 + i * 38.1, 55.88)
        place(f'R{6 + i}', 411.48 + i * 38.1, 71.12)
    place('LED5', 393.7, 101.6)
    place('R9', 416.56, 101.6)
    place('R10', 426.72, 101.6)
    # ---- trackpad connector
    text('Trackpad module (Azoteq TPS43)\\nFPC 6P 0.5 mm, I2C pull-ups here', 450, 88)
    place('J3', 480.06, 109.22)
    place('R11', 508.0, 104.14)
    place('R12', 518.16, 104.14)
    text('Case screws (M2, from below into the top frame)', 450, 140)
    for i in range(len(D.SCREWS)):
        place(f'H{i + 1}', 457.2 + (i % 6) * 7.62, 152.4 + (i // 6) * 7.62)
    # ---- GPIO table
    gp = {v: D.PIN_NAMES[k] for k, v in D.MCU_PINS.items()}
    text('GPIO map (ZMK, diode-direction = col2row)\\n'
         'rows:  ' + ', '.join(f'ROW{r}={gp[f"ROW{r}"]}' for r in range(D.NROWS)) + '\\n'
         'cols:  ' + ', '.join(f'COL{c}={gp[f"COL{c}"]}' for c in range(6)) + '\\n'
         '       ' + ', '.join(f'COL{c}={gp[f"COL{c}"]}' for c in range(6, D.NCOLS)) + '\\n'
         'LED (active low): ' + ', '.join(f'{k}={gp[k]}' for k in ('LED_BT1', 'LED_BT2', 'LED_BT3', 'LED_PWR_G', 'LED_PWR_R'))
         + '\\ntrackpad: ' + ', '.join(f'{k}={gp[k]}' for k in ('TP_SDA', 'TP_SCL', 'TP_RDY', 'TP_RST')),
         150, 128, 1.27)
    # ---- matrix: column wires (vertical), row wires (horizontal), SW + diode per cell, all wired
    X0, Y0, CW, RH = 45.72, 220.98, 43.18, 30.48
    text(f'Key matrix {D.NROWS} x {D.NCOLS}  ({D.NKEYS} keys, ALPS SKRA + 1N4148W, COL -> SW -> D -> ROW)', 20, 200)
    cells = {(r, c): (n, name) for (n, r, c, name) in D.CELLS}
    ytop = Y0 - 10.16
    for c in range(D.NCOLS):
        xs = X0 + c * CW - 7.62
        ys = [Y0 + r * RH for r in range(D.NROWS) if (r, c) in cells]
        pts = [ytop] + ys
        for a, b in zip(pts, pts[1:]):
            wire((xs, a), (xs, b))
        for y in ys[:-1]:
            junction(xs, y)
        label(f'COL{c}', xs, ytop, 270)
    xleft = X0 - 25.4
    for r in range(D.NROWS):
        yr = Y0 + r * RH + 12.7
        xd = [X0 + c * CW + 7.62 for c in range(D.NCOLS) if (r, c) in cells]
        pts = [xleft] + xd
        for a, b in zip(pts, pts[1:]):
            wire((a, yr), (b, yr))
        for x in xd[:-1]:
            junction(x, yr)
        label(f'ROW{r}', xleft, yr, 0)
    for (r, c), (n, name) in sorted(cells.items()):
        X, Y = X0 + c * CW, Y0 + r * RH
        place(f'SW{n}', X, Y, labels=False)
        place(f'D{n}', X + 7.62, Y + 6.35, labels=False)
        wire((X - 7.62, Y), (X - 5.08, Y))
        wire((X + 5.08, Y), (X + 7.62, Y))
        wire((X + 7.62, Y), (X + 7.62, Y + 2.54))
        wire((X + 7.62, Y + 10.16), (X + 7.62, Y + 12.7))
        ITEMS.append(f'\t(label {q(f"K{r}_{c}")} (at {f(X + 7.62)} {f(Y)} 0) {fnt("left bottom", size=1.0)} '
                     f'(uuid {q(U("klbl", r, c))}))\n')
        text(name, X - 6.0, Y - 7.5, 1.6)
    return ''.join(ITEMS)


def write(path):
    body = build()
    o = ['(kicad_sch\n\t(version 20250114)\n\t(generator "eeschema")\n\t(generator_version "9.0")\n',
         f'\t(uuid {q(ROOT_UUID)})\n\t(paper "A2")\n',
         '\t(title_block\n\t\t(title "Ashiyu (tomtho-slim mk2)")\n\t\t(date "2026-10-07")\n\t\t(rev "mk2-0.1")\n'
         '\t\t(comment 1 "65 keys / ALPS SKRA / MDBT50Q-1MV2 / TPS43 trackpad (FPC) / ZMK")\n\t)\n',
         lib_symbols(), body,
         '\t(sheet_instances\n\t\t(path "/" (page "1"))\n\t)\n\t(embedded_fonts no)\n)\n']
    with open(path, 'w') as fh:
        fh.write(''.join(o))


def nc_pad_nets():
    """KiCad names a no-connect pin's net 'unconnected-(REF-PIN-PadN)'; mirror that on the PCB."""
    out = {}
    for ref, p in D.PARTS.items():
        s = SYMS[p['sym']]
        for (num, nm, *_r) in s['pins']:
            if p['nets'].get(num):
                continue
            nm2 = nm.replace('/', '{slash}')
            label = f'{ref}-Pad{num}' if nm in ('~', num) else f'{ref}-{nm2}-Pad{num}'
            out[(ref, num)] = f'unconnected-({label})'
    return out


def write_symlib(path):
    o = ['(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "tomtho_slim_gen")\n\t(generator_version "1.0")\n']
    ls = lib_symbols().split('\n', 1)[1].rsplit('\t)\n', 1)[0]
    ls = ls.replace(f'(symbol "{LIB}:', '(symbol "')
    o.append(ls)
    o.append(')\n')
    with open(path, 'w') as fh:
        fh.write(''.join(o))


if __name__ == '__main__':
    write(f'{REPO}/{PROJECT}.kicad_sch')
    write_symlib(f'{REPO}/lib/{PROJECT}.kicad_sym')
