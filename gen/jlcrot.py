"""JLC placement check: compare each BOM footprint with the LCSC/EasyEDA footprint JLC places at 0 deg.

For every footprint, find the rotation (0/90/180/270) and the origin offset that map the LCSC pads onto ours,
matching pads by number.  JLC rotation = our rotation + offset; JLC centre = our origin + R(rot) * shift.
The LCSC footprints come from the lcsc-parts branch (.github/workflows/lcsc.yml).

usage: python3 jlcrot.py <dir with LCSC .kicad_mod files>  -> prints a table and writes jlc_offsets.json
"""
import json, math, os, re, sys
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
OURS = os.path.join(HERE, '..', 'lib', 'tomtho_mk2.pretty')
LCSC_FP = {
    'C19666': 'C0603', 'C19702': 'C0603', 'C14663': 'C0603',
    'C23186': 'R0603', 'C25804': 'R0603', 'C21190': 'R0603', 'C25803': 'R0603', 'C23162': 'R0603',
    'C81598': 'SOD-123F_L2.7-W1.6-LS3.8-RD', 'C8598': 'SOD-123_L2.7-W1.6-LS3.7-RD-1',
    'C165948': 'USB-C_SMD-TYPE-C-31-M-12_1', 'C160402': 'CONN-SMD_2P-P1.00_SM02B-SRSS-TB-LF-SN',
    'C5213729': 'FPC-SMD_6P-P0.50_HCTL_HC-FPC-05-10-6RLTAG', 'C2286': 'LED-SMD_L1.6-W0.8-R-RD',
    'C965847': 'LED-SMD_4P-L2.0-W1.3-RD-TL', 'C15127': 'SOT-23_L2.9-W1.3-P1.90-LS2.4-BR',
    'C202383': 'SW-SMD_4P-L6.2-W6.2-P4.00-LS6.8', 'C1121891': 'KEY-SMD_4P-L2.8-W2.0-P1.20-LS3.0-TL',
    'C221841': 'SW-SMD_PCM12SMTR', 'C5118826': 'COMM-SMD_MDBT50Q-1MV2-1',
    'C7519': 'SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL', 'C424093': 'SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BL',
}


def pads(path):
    out = {}
    for m in re.finditer(r'\(pad\s+"?([^"\s)]*)"?\s+\w+\s+\w+\s+\(at\s+([-\d.]+)\s+([-\d.]+)', open(path).read()):
        name, x, y = m.group(1), float(m.group(2)), float(m.group(3))
        if name:
            out.setdefault(name, []).append((x, y))
    return out


def rot(p, a):   # KiCad convention (y down, positive = counter-clockwise on screen)
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return (p[0] * c + p[1] * s, -p[0] * s + p[1] * c)


def fit(ours, theirs):
    names = [n for n in ours if n in theirs]
    best = None
    for a in (0, 90, 180, 270):
        pairs = []
        for n in names:   # translation from pad numbers that occur once on both sides
            if len(ours[n]) == 1 and len(theirs[n]) == 1:
                pairs.append((ours[n][0], rot(theirs[n][0], a)))
        if not pairs:   # every number repeats (switches): match centroids of all named pads
            P = [p for n in names for p in ours[n]]; Q = [rot(q, a) for n in names for q in theirs[n]]
            if not P or not Q:
                continue
            pairs = [((sum(p[0] for p in P) / len(P), sum(p[1] for p in P) / len(P)),
                      (sum(q[0] for q in Q) / len(Q), sum(q[1] for q in Q) / len(Q)))]
        # each pad number may have several pads (EP, shield): match each of ours with the nearest rotated pad
        tx = sum(p[0] - q[0] for p, q in pairs) / len(pairs)
        ty = sum(p[1] - q[1] for p, q in pairs) / len(pairs)
        err = 0.0
        for n in names:
            for p in ours[n]:
                err = max(err, min(math.hypot(p[0] - tx - rq[0], p[1] - ty - rq[1])
                                   for rq in (rot(q, a) for q in theirs[n])))
        if best is None or err < best[0]:
            best = (err, a, tx, ty)
    return best, names


if __name__ == '__main__':
    src = sys.argv[1]
    res = {}
    seen = {}
    for ref, p in D.PARTS.items():
        if p['bom'] and p['lcsc'] in LCSC_FP:
            seen.setdefault((p['fp'], p['lcsc']), []).append(ref)
    print(f'{"our footprint":32s} {"LCSC":9s} {"pads":>4s} {"rot+":>5s} {"shift x,y":>14s} {"max err":>8s}')
    for (fp, lc), refs in sorted(seen.items()):
        ours = pads(os.path.join(OURS, fp + '.kicad_mod'))
        theirs = pads(os.path.join(src, LCSC_FP[lc] + '.kicad_mod'))
        best, names = fit(ours, theirs)
        if best is None:
            print(f'{fp:32s} {lc:9s} no common pad numbers: ours {sorted(ours)} / LCSC {sorted(theirs)}')
            continue
        err, a, tx, ty = best
        # their origin sits at -t in our frame: JLC centre = our origin + R(rot) * (tx, ty)
        res[fp + '|' + lc] = {'rot': a, 'shift': [round(tx, 3), round(ty, 3)], 'err': round(err, 3),
                              'pads_matched': len(names), 'refs': len(refs)}
        flag = '' if err < 0.15 else '  <-- check'
        print(f'{fp:32s} {lc:9s} {len(names):4d} {a:5d} {tx:7.2f},{ty:6.2f} {err:8.3f}{flag}')
    # Checked by hand against the LCSC symbols (pad numbers mean different things, so the pad fit is not used):
    #  - KT-0603R: LCSC pad 2 = K at -x, our pad 1 = K at -x  -> same orientation
    #  - SKRA / TS-1928-B: LCSC pads 1-2 and 3-4 are the joined pairs (rows), same as our 1/1 and 2/2 rows
    for k in ('LED_0603|C2286', 'SW_ALPS_SKRA_6.2mm|C202383', 'SW_TS-1928-B|C1121891'):
        res[k].update(rot=0, shift=[0.0, 0.0], note='checked by hand (pin functions), see jlcrot.py')
    json.dump(res, open(os.path.join(HERE, 'jlc_offsets.json'), 'w'), indent=1)
