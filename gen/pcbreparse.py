"""Independent re-read of the written .kicad_pcb -> rebuild copper -> run checks."""
import math, sys
from pcbio import _tok, _parse
import check as C
import design as D


def rotp(x, y, a):
    a = a % 360
    if a == 90: return y, -x
    if a == 180: return -x, -y
    if a == 270: return -y, x
    return x, y


def main(path):
    tree = _parse(_tok(open(path).read()))
    nets = {}
    fps, segs, vias = [], [], []
    for n in tree[1:]:
        if not isinstance(n, list): continue
        if n[0] == 'net': nets[n[1]] = n[2].lstrip('/')
        elif n[0] == 'footprint': fps.append(n)
        elif n[0] == 'segment':
            d = {x[0]: x for x in n[1:] if isinstance(x, list)}
            segs.append((d['layer'][1], float(d['start'][1]), float(d['start'][2]), float(d['end'][1]),
                         float(d['end'][2]), float(d['width'][1]), nets[d['net'][1]]))
        elif n[0] == 'via':
            d = {x[0]: x for x in n[1:] if isinstance(x, list)}
            vias.append((float(d['at'][1]), float(d['at'][2]), nets[d['net'][1]]))
    # compare pads with design
    bad = 0
    npads = 0
    for fp in fps:
        d = [x for x in fp if isinstance(x, list)]
        at = next(x for x in d if x[0] == 'at')
        X, Y = float(at[1]), float(at[2])
        A = float(at[3]) if len(at) > 3 else 0
        ref = next(x for x in d if x[0] == 'property' and x[1] == 'Reference')[2]
        want = [(h[0], round(h[3], 3), round(h[4], 3), h[8]) for h in D.pad_world(D.PARTS[ref]) if h[1] != 'np']
        got = []
        for p in d:
            if p[0] != 'pad' or p[2] == 'np_thru_hole': continue
            pa = next(x for x in p if isinstance(x, list) and x[0] == 'at')
            lx, ly = float(pa[1]), float(pa[2])
            dx, dy = rotp(lx, ly, A)
            netl = [x for x in p if isinstance(x, list) and x[0] == 'net']
            got.append((p[1], round(X + dx, 3), round(Y + dy, 3), netl[0][2].lstrip('/') if netl else ''))
            npads += 1
        if sorted(got) != sorted(want):
            bad += 1
            print('PAD MISMATCH', ref, sorted(set(got) ^ set(want))[:4])
    print(f'footprints {len(fps)}, pads {npads}, segments {len(segs)}, vias {len(vias)}, pad mismatches {bad}')
    e, u = C.run(segs, vias, verbose=False)
    e = [x for x in e if not x.startswith('ISLAND without pad on GND')]
    print('DRC-lite errors', len(e), e[:5], 'unrouted (non-GND)', {k: x for k, x in u.items() if k != 'GND'})
    txt = open(path).read()
    print('paren balance', txt.count('(') - txt.count(')'))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/tomtho_slim/tomtho_slim.kicad_pcb')
