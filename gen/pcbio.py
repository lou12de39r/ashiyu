"""Writers: KiCad 8-format .kicad_pcb / .kicad_mod (opens in KiCad 8/9/10), Specctra DSN; SES reader."""
import math
import re
import uuid

from fplib import FP
import design as D
from design import rot

NS = uuid.UUID('6c0e8f3a-2b1f-4c55-9a47-3d1c0f8e7a22')
PROJECT = 'tomtho_mk2'
LIB = 'tomtho_mk2'


def PN(n):
    """PCB net name as KiCad derives it from the schematic (local labels get the root-sheet prefix)."""
    return n if n in ('GND', '') else '/' + n


def U(*k):
    return str(uuid.uuid5(NS, '/'.join(str(x) for x in k)))


def f(v):
    s = f'{v:.4f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


ROOT_UUID = U('root-sheet')
NC_NETS = {}
import os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

PCB_LAYERS = '''	(layers
		(0 "F.Cu" signal)
		(31 "B.Cu" signal)
		(32 "B.Adhes" user "B.Adhesive")
		(33 "F.Adhes" user "F.Adhesive")
		(34 "B.Paste" user)
		(35 "F.Paste" user)
		(36 "B.SilkS" user "B.Silkscreen")
		(37 "F.SilkS" user "F.Silkscreen")
		(38 "B.Mask" user)
		(39 "F.Mask" user)
		(40 "Dwgs.User" user "User.Drawings")
		(41 "Cmts.User" user "User.Comments")
		(42 "Eco1.User" user "User.Eco1")
		(43 "Eco2.User" user "User.Eco2")
		(44 "Edge.Cuts" user)
		(45 "Margin" user)
		(46 "B.CrtYd" user "B.Courtyard")
		(47 "F.CrtYd" user "F.Courtyard")
		(48 "B.Fab" user)
		(49 "F.Fab" user)
	)
'''


def _font(size, layer=''):
    th = max(0.08, round(size * 0.15, 3))
    return f'(effects (font (size {f(size)} {f(size)}) (thickness {f(th)})))'


def fp_body(fpname, part=None, netcode=None, ind='\t'):
    """Return footprint s-expression. part=None -> library .kicad_mod form."""
    fp = FP[fpname]
    lib = part is None
    a = 0 if lib else part['rot']
    ref = 'REF**' if lib else part['ref']
    val = fpname if lib else part['value']
    key = fpname if lib else part['ref']
    o = []
    o.append(f'(footprint {q(fpname if lib else LIB + ":" + fpname)}')
    if lib:
        o.append('(version 20240108) (generator "pcbnew") (generator_version "8.0")')
    o.append('(layer "F.Cu")')
    if not lib:
        o.append(f'(uuid {q(U("fp", key))})')
        o.append(f'(at {f(part["x"])} {f(part["y"])}{" " + f(a) if a else ""})')
    o.append(f'(descr {q(fp["descr"])})')
    rs = fp.get('ref_size', 0.8)
    rlayer = 'F.Fab' if (not lib and re.fullmatch(r'(SW|D)\d+', ref) and int(re.sub(r'\D', '', ref)) <= D.NKEYS) or (not lib and part.get('ref_fab')) else 'F.SilkS'
    ra = fp['ref_at'] if lib else part.get('ref_at', fp['ref_at'])
    o.append(f'(property "Reference" {q(ref)} (at {f(ra[0])} {f(ra[1])} {f(a)}) (layer {q(rlayer)}) '
             f'(uuid {q(U("ref", key))}) {_font(rs)})')
    o.append(f'(property "Value" {q(val)} (at {f(fp["val_at"][0])} {f(fp["val_at"][1])} {f(a)}) (layer "F.Fab") '
             f'(uuid {q(U("val", key))}) {_font(0.6)})')
    o.append(f'(property "Footprint" {q(LIB + ":" + fpname)} (at 0 0 {f(a)}) (unlocked yes) (layer "F.Fab") (hide yes) '
             f'(uuid {q(U("fpp", key))}) {_font(1.0)})')
    o.append(f'(property "Datasheet" "" (at 0 0 {f(a)}) (unlocked yes) (layer "F.Fab") (hide yes) '
             f'(uuid {q(U("ds", key))}) {_font(1.0)})')
    o.append(f'(property "Description" {q(fp["descr"] if lib else part["desc"])} (at 0 0 {f(a)}) (unlocked yes) '
             f'(layer "F.Fab") (hide yes) (uuid {q(U("de", key))}) {_font(1.0)})')
    if not lib:
        o.append(f'(property "LCSC" {q(part["lcsc"])} (at 0 0 {f(a)}) (unlocked yes) (layer "F.Fab") (hide yes) '
                 f'(uuid {q(U("lcsc", key))}) {_font(1.0)})')
    if not lib:
        o.append(f'(property "MPN" {q(part.get("mpn", ""))} (at 0 0 {f(a)}) (unlocked yes) (layer "F.Fab") (hide yes) '
                 f'(uuid {q(U("mpn", key))}) {_font(1.0)})')
        o.append(f'(path "/{U("sym", part["ref"])}")')
        o.append('(sheetname "Root")')
        o.append(f'(sheetfile "{PROJECT}.kicad_sch")')
    attr = fp['attr']
    if any(p[1] == 'thru' for p in fp['pads']):
        attr = 'through_hole'
    if not lib and not part['bom'] and 'exclude_from_bom' not in attr:
        attr += ' exclude_from_bom'
    o.append(f'(attr {attr})')
    for i, (layer, x1, y1, x2, y2, w) in enumerate(fp['lines']):
        o.append(f'(fp_line (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width {f(w)}) (type solid)) '
                 f'(layer {q(layer)}) (uuid {q(U("l", key, i))}))')
    for i, (layer, cx, cy, r) in enumerate(fp['circles']):
        o.append(f'(fp_circle (center {f(cx)} {f(cy)}) (end {f(cx + r)} {f(cy)}) (stroke (width 0.05) (type solid)) '
                 f'(fill none) (layer {q(layer)}) (uuid {q(U("c", key, i))}))')
    for i, (layer, x, y, txt, sz) in enumerate(fp.get('texts', [])):
        o.append(f'(fp_text user {q(txt)} (at {f(x)} {f(y)} {f(a)}) (layer {q(layer)}) (uuid {q(U("t", key, i))}) {_font(sz)})')
    o.append(f'(fp_text user "${{REFERENCE}}" (at 0 0 {f(a)}) (layer "F.Fab") (uuid {q(U("fabref", key))}) {_font(0.5)})')
    for i, (num, kind, shape, x, y, w, h, drill) in enumerate(fp['pads']):
        ktok = {'smd': 'smd', 'thru': 'thru_hole', 'np': 'np_thru_hole'}[kind]
        if kind == 'smd':
            layers = '"F.Cu" "F.Paste" "F.Mask"'
        else:
            layers = '"*.Cu" "*.Mask"'
        s = f'(pad {q(num)} {ktok} {shape} (at {f(x)} {f(y)}{" " + f(a) if a else ""}) (size {f(w)} {f(h)})'
        if drill is not None:
            if isinstance(drill, tuple):
                s += f' (drill oval {f(drill[0])} {f(drill[1])})'
            else:
                s += f' (drill {f(drill)})'
        s += f' (layers {layers})'
        if shape == 'roundrect':
            s += ' (roundrect_rratio 0.25)'
        if kind == 'thru':
            s += ' (remove_unused_layers no)'
        if not lib and num and kind != 'np':
            net = part['nets'].get(num, '')
            if net:
                s += f' (net {netcode[net]} {q(PN(net))})'
            elif (part['ref'], num) in NC_NETS:
                nn = NC_NETS[(part['ref'], num)]
                s += f' (net {netcode[nn]} {q(nn)})'
            s += ' (pintype "passive")'
        s += f' (uuid {q(U("pad", key, i))}))'
        o.append(s)
    if lib:
        o.append('(embedded_fonts no)')
    return ind + ('\n' + ind + '\t').join(o) + '\n' + ind + ')\n'


def write_footprint_lib(dirpath):
    import os
    os.makedirs(dirpath, exist_ok=True)
    for name in FP:
        with open(f'{dirpath}/{name}.kicad_mod', 'w') as fh:
            fh.write(fp_body(name, ind=''))


def board_outline(r=1.0):
    x1, y1, x2, y2 = D.BOARD
    o = []
    segs = [((x1 + r, y1), (x2 - r, y1)), ((x2, y1 + r), (x2, y2 - r)),
            ((x2 - r, y2), (x1 + r, y2)), ((x1, y2 - r), (x1, y1 + r))]
    for i, (a, b) in enumerate(segs):
        o.append(f'\t(gr_line (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) (stroke (width 0.1) (type default)) '
                 f'(layer "Edge.Cuts") (uuid {q(U("edge", i))}))\n')
    k = r * (1 - math.sqrt(0.5))
    arcs = [((x1, y1 + r), (x1 + k, y1 + k), (x1 + r, y1)), ((x2 - r, y1), (x2 - k, y1 + k), (x2, y1 + r)),
            ((x2, y2 - r), (x2 - k, y2 - k), (x2 - r, y2)), ((x1 + r, y2), (x1 + k, y2 - k), (x1, y2 - r))]
    for i, (s, m, e) in enumerate(arcs):
        o.append(f'\t(gr_arc (start {f(s[0])} {f(s[1])}) (mid {f(m[0])} {f(m[1])}) (end {f(e[0])} {f(e[1])}) '
                 f'(stroke (width 0.1) (type default)) (layer "Edge.Cuts") (uuid {q(U("arc", i))}))\n')
    return ''.join(o)


def _poly(x1, y1, x2, y2):
    return f'(polygon (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y1)}) (xy {f(x2)} {f(y2)}) (xy {f(x1)} {f(y2)})))'


def write_pcb(path, tracks, vias, zones=True, nc_nets=None):
    nets = D.all_nets()
    netcode = {n: i + 1 for i, n in enumerate(nets)}
    global NC_NETS
    NC_NETS = dict(nc_nets or {})
    for i, n in enumerate(sorted(set(NC_NETS.values()))):
        netcode[n] = len(nets) + 1 + i
    o = ['(kicad_pcb\n\t(version 20240108)\n\t(generator "pcbnew")\n\t(generator_version "8.0")\n',
         '\t(general\n\t\t(thickness 1.2)\n\t\t(legacy_teardrops no)\n\t)\n\t(paper "A3")\n',
         '\t(title_block\n\t\t(title "tomtho-slim mk2")\n\t\t(date "2026-10-07")\n\t\t(rev "mk2-0.1")\n'
         '\t\t(comment 1 "65 keys / ALPS SKRA / 18.5x18mm / MDBT50Q-1MV2 (nRF52840) / TPS43 trackpad via FPC / ZMK")\n\t)\n',
         PCB_LAYERS,
         '\t(setup\n\t\t(pad_to_mask_clearance 0)\n\t\t(allow_soldermask_bridges_in_footprints no)\n'
         '\t\t(aux_axis_origin 18.5 113.5)\n\t\t(grid_origin 20 40)\n\t)\n',
         '\t(net 0 "")\n']
    o += [f'\t(net {netcode[n]} {q(PN(n))})\n' for n in nets]
    o += [f'\t(net {netcode[n]} {q(n)})\n' for n in sorted(set(NC_NETS.values()))]
    for ref in sorted(D.PARTS, key=lambda r: (re.sub(r'\d', '', r), int(re.sub(r'\D', '', r) or 0))):
        o.append(fp_body(D.PARTS[ref]['fp'], D.PARTS[ref], netcode))
    o.append(board_outline(D.CORNER_R))
    for i, (layer, x1, y1, x2, y2) in enumerate(D.SILK_RECTS):
        for j, (p, q2) in enumerate([((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)), ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))]):
            o.append(f'\t(gr_line (start {f(p[0])} {f(p[1])}) (end {f(q2[0])} {f(q2[1])}) (stroke (width 0.12) (type default)) '
                     f'(layer {q(layer)}) (uuid {q(U("srect", i, j))}))\n')
    for i, (layer, x, y, t, sz) in enumerate(D.SILK_TEXTS):
        mirror = ' (justify mirror)' if layer.startswith('B.') else ''
        o.append(f'\t(gr_text {q(t)} (at {f(x)} {f(y)}) (layer {q(layer)}) (uuid {q(U("txt", i))}) '
                 f'{_font(sz)[:-1]}{mirror}))\n')
    lg = getattr(D, 'LOGO', None)
    if lg:
        src = open(os.path.join(REPO, lg['file'])).read()
        mir = -1 if lg['layer'].startswith('B.') else 1
        for i, blk in enumerate(re.findall(r'\(fp_poly\s*\(pts(.*?)\)\s*\(stroke', src, re.S)):
            pts = [(lg['x'] + mir * lg['scale'] * float(a), lg['y'] + lg['scale'] * float(b))
                   for a, b in re.findall(r'\(xy (-?[\d.]+) (-?[\d.]+)\)', blk)]
            o.append('\t(gr_poly (pts ' + ' '.join(f'(xy {f(x)} {f(y)})' for x, y in pts) + ') '
                     f'(stroke (width 0) (type solid)) (fill yes) (layer {q(lg["layer"])}) (uuid {q(U("logo", i))}))\n')
    for i, (x1, y1, x2, y2) in enumerate(D.SLOTS):
        r = min(x2 - x1, y2 - y1) / 2
        o.append(f'\t(gr_rect (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width 0.1) (type default)) '
                 f'(fill no) (layer "Edge.Cuts") (uuid {q(U("slot", i))}))\n')
    for i, (layer, x1, y1, x2, y2, w, net) in enumerate(tracks):
        o.append(f'\t(segment (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (width {f(w)}) (layer {q(layer)}) '
                 f'(net {netcode[net]}) (uuid {q(U("seg", i, x1, y1, x2, y2))}))\n')
    for i, (x, y, net) in enumerate(vias):
        o.append(f'\t(via (at {f(x)} {f(y)}) (size {f(D.VIA[0])}) (drill {f(D.VIA[1])}) (layers "F.Cu" "B.Cu") '
                 f'(net {netcode[net]}) (uuid {q(U("via", i, x, y))}))\n')
    if zones:
        x1, y1, x2, y2 = D.BOARD
        for layer in ('F.Cu', 'B.Cu'):
            o.append(f'\t(zone (net {netcode["GND"]}) (net_name "GND") (layer {q(layer)}) (uuid {q(U("zone", layer))}) '
                     f'(name "GND_{layer[0]}") (hatch edge 0.5) (priority 0) (connect_pads (clearance 0.25)) '
                     f'(min_thickness 0.2) (filled_areas_thickness no) '
                     f'(fill (thermal_gap 0.3) (thermal_bridge_width 0.4) (island_removal_mode 0)) {_poly(x1 + 0.3, y1 + 0.3, x2 - 0.3, y2 - 0.3)})\n')
        ax1, ay1, ax2, ay2 = D.ANT_KEEPOUT
        o.append(f'\t(zone (net 0) (net_name "") (layers "F.Cu" "B.Cu") (uuid {q(U("ant"))}) (name "ANTENNA_KEEPOUT") '
                 f'(hatch edge 0.5) (connect_pads (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no) '
                 f'(keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed) (copperpour not_allowed) '
                 f'(footprints allowed)) (fill (thermal_gap 0.5) (thermal_bridge_width 0.5)) '
                 f'{_poly(ax1, ay1 - 1.0, ax2, ay2)})\n')
    o.append(')\n')
    with open(path, 'w') as fh:
        fh.write(''.join(o))


# ------------------------------------------------------------------ Specctra DSN
def um(v):
    return f'{v * 1000:.1f}'.rstrip('0').rstrip('.')


def write_dsn(path, tracks, vias, only=None, clr=150, wsig=200, extra=None, obstacle_nets=()):
    nets = [n for n in D.all_nets() if only is None or n in only]
    o = [f'(pcb {PROJECT}.dsn\n  (parser (string_quote ") (space_in_quoted_tokens on) (host_cad "KiCad") (host_version "8"))\n',
         '  (resolution um 10)\n  (unit um)\n  (structure\n',
         '    (layer F.Cu (type signal) (property (index 0)))\n    (layer B.Cu (type signal) (property (index 1)))\n']
    x1, y1, x2, y2 = D.BOARD
    o.append(f'    (boundary (path pcb 0 {um(x1)} {um(-y1)} {um(x2)} {um(-y1)} {um(x2)} {um(-y2)} {um(x1)} {um(-y2)} {um(x1)} {um(-y1)}))\n')
    ax1, ay1, ax2, ay2 = D.ANT_KEEPOUT
    o.append(f'    (keepout "ant" (rect signal {um(ax1)} {um(-ay2)} {um(ax2)} {um(-y1)}))\n')
    mx1, my1, mx2, my2 = D.MODULE_FCU_KEEPOUT
    o.append(f'    (keepout "modF" (rect F.Cu {um(mx1)} {um(-my2)} {um(mx2)} {um(-my1)}))\n')
    # obstacle nets (GND stubs / stitching vias): plain keepouts so the router never tries to connect them
    for (layer, xa, ya, xb, yb, w, net) in tracks:
        if net in obstacle_nets:
            o.append(f'    (keepout "" (path {layer} {um(w + 0.3)} {um(xa)} {um(-ya)} {um(xb)} {um(-yb)}))\n')
    for (x, y, net) in vias:
        if net in obstacle_nets:
            o.append(f'    (keepout "" (circle signal {um(D.VIA[0] + 0.3)} {um(x)} {um(-y)}))\n')
    for (sx1, sy1, sx2, sy2) in getattr(D, 'SLOTS', []):
        o.append(f'    (keepout "slot" (rect signal {um(sx1 - 0.4)} {um(-sy2 - 0.4)} {um(sx2 + 0.4)} {um(-sy1 + 0.4)}))\n')
    o.append('    (via "Via600" )\n')
    o.append(f'    (rule (width {wsig}) (clearance {clr}) (clearance {clr} (type default_smd)) (clearance 100 (type smd_smd)))\n  )\n')
    # placement + library: one image per part, pins pre-rotated, placed at rot 0
    o.append('  (placement\n')
    for ref, p in sorted(D.PARTS.items()):
        o.append(f'    (component "IMG_{ref}" (place "{ref}" {um(p["x"])} {um(-p["y"])} front 0))\n')
    o.append('  )\n  (library\n')
    padstacks = {}
    for ref, p in sorted(D.PARTS.items()):
        o.append(f'    (image "IMG_{ref}"\n')
        seen = {}
        for (num, kind, shape, X, Y, W, H, drill, net) in D.pad_world(p):
            lx, ly = X - p['x'], -(Y - p['y'])
            if kind == 'np':
                o.append(f'      (keepout "" (circle signal {um(W + 0.3)} {um(lx)} {um(ly)}))\n')
                continue
            if kind == 'thru':
                if H >= W:
                    ps = f'Oval_{um(W)}x{um(H)}'
                    padstacks[ps] = ''.join(f'(shape (path {L} {um(W)} 0 {um(-(H - W) / 2)} 0 {um((H - W) / 2)}))' for L in ('F.Cu', 'B.Cu'))
                else:
                    ps = f'Oval_{um(W)}x{um(H)}'
                    padstacks[ps] = ''.join(f'(shape (path {L} {um(H)} {um(-(W - H) / 2)} 0 {um((W - H) / 2)} 0))' for L in ('F.Cu', 'B.Cu'))
            elif shape == 'circle':
                ps = f'Round_{um(W)}'
                padstacks[ps] = f'(shape (circle F.Cu {um(W)}))'
            elif p['rot'] % 90:
                ang = p['rot']
                ps = f'Poly_{um(W)}x{um(H)}_r{ang:g}'.replace('-', 'm').replace('.', 'p')
                pts = []
                for cx_, cy_ in ((-W / 2, -H / 2), (W / 2, -H / 2), (W / 2, H / 2), (-W / 2, H / 2), (-W / 2, -H / 2)):
                    rx_, ry_ = rot(cx_, cy_, ang)
                    pts += [um(rx_), um(-ry_)]
                padstacks[ps] = f'(shape (polygon F.Cu 0 {" ".join(pts)}))'
            else:
                ps = f'Rect_{um(W)}x{um(H)}'
                padstacks[ps] = f'(shape (rect F.Cu {um(-W / 2)} {um(-H / 2)} {um(W / 2)} {um(H / 2)}))'
            pid = num or 'X'
            k = seen.get(pid, 0)
            seen[pid] = k + 1
            pin = pid if k == 0 else f'{pid}@{k}'
            o.append(f'      (pin {ps} "{pin}" {um(lx)} {um(ly)})\n')
        o.append('    )\n')
    for ps, shape in sorted(padstacks.items()):
        o.append(f'    (padstack {ps} {shape} (attach off))\n')
    vd = D.VIA[0]
    o.append(f'    (padstack "Via600" (shape (circle F.Cu {um(vd)})) (shape (circle B.Cu {um(vd)})) (attach off))\n  )\n')
    # network
    pins = {n: [] for n in nets}
    for ref, p in sorted(D.PARTS.items()):
        seen = {}
        for (num, kind, shape, X, Y, W, H, drill, net) in D.pad_world(p):
            if kind == 'np':
                continue
            pid = num or 'X'
            k = seen.get(pid, 0)
            seen[pid] = k + 1
            if net and net in pins:
                pins[net].append(f'{ref}-{pid if k == 0 else f"{pid}@{k}"}')
    for n, plist in (extra or {}).items():
        pins[n] = [f'{r}-{q}' for r, q in plist]
    o.append('  (network\n')
    for n in list(nets) + list(extra or {}):
        o.append(f'    (net "{n}" (pins {" ".join(pins[n])}))\n')
    pw = [n for n in nets if n in D.POWER_NETS]
    sig = [n for n in nets if n not in D.POWER_NETS] + list(extra or {})
    o.append('    (class default ' + ' '.join(f'"{n}"' for n in sig) +
             ' (circuit (use_via "Via600")) (rule (width {wsig}) (clearance {clr})))\n'.format(wsig=wsig, clr=clr))
    o.append('    (class power ' + ' '.join(f'"{n}"' for n in pw) +
             ' (circuit (use_via "Via600")) (rule (width 300) (clearance {clr})))\n  )\n'.format(clr=clr))
    o.append('  (wiring\n')
    for (layer, xa, ya, xb, yb, w, net) in tracks:
        if net not in pins:
            continue
        o.append(f'    (wire (path {layer} {um(w)} {um(xa)} {um(-ya)} {um(xb)} {um(-yb)}) (net "{net}") (type protect))\n')
    for (x, y, net) in vias:
        if net not in pins:
            continue
        o.append(f'    (via "Via600" {um(x)} {um(-y)} (net "{net}") (type protect))\n')
    o.append('  )\n)\n')
    with open(path, 'w') as fh:
        fh.write(''.join(o))


# ------------------------------------------------------------------ SES reader
def _tok(s):
    return re.findall(r'"[^"]*"|\(|\)|[^\s()]+', s)


def _parse(tokens):
    stack = [[]]
    for t in tokens:
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop()
            stack[-1].append(x)
        else:
            stack[-1].append(t.strip('"'))
    return stack[0][0]


def read_ses(path):
    tree = _parse(_tok(open(path).read()))
    res = 10.0
    tracks, vias = [], []

    def walk(node):
        nonlocal res
        if not isinstance(node, list) or not node:
            return
        if node[0] == 'resolution':
            res = float(node[2])
        if node[0] == 'net':
            name = node[1]
            for item in node[2:]:
                if isinstance(item, list) and item and item[0] == 'wire':
                    for sub in item[1:]:
                        if isinstance(sub, list) and sub[0] == 'path':
                            layer, w = sub[1], float(sub[2])
                            pts = [float(v) for v in sub[3:] if not isinstance(v, list)]
                            xy = [(pts[i], pts[i + 1]) for i in range(0, len(pts) - 1, 2)]
                            for a, b in zip(xy, xy[1:]):
                                tracks.append((layer, a[0], a[1], b[0], b[1], w, name))
                elif isinstance(item, list) and item and item[0] == 'via':
                    vias.append((float(item[2]), float(item[3]), name))
            return
        for ch in node[1:]:
            walk(ch)
    walk(tree)
    k = 1000.0 * res
    tracks = [(l, a / k, -b / k, c / k, -d / k, w / k, n) for (l, a, b, c, d, w, n) in tracks]
    vias = [(x / k, -y / k, n) for (x, y, n) in vias]
    return tracks, vias
