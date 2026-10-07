"""Re-extract the netlist from the written .kicad_sch (independently of the generator's internal
state) and compare it with design.PARTS.  Connectivity rules follow KiCad: points that coincide
(pin ends, label anchors, wire ends, power-symbol pins) are connected; wires connect along their length
to endpoints lying on them; labels/power symbols with the same name are the same net."""
import sys
from collections import defaultdict
from pcbio import _tok, _parse
import design as D


def load(path):
    tree = _parse(_tok(open(path).read()))
    libs = {}
    insts, labels, wires, ncs = [], [], [], []
    for node in tree[1:]:
        if not isinstance(node, list):
            continue
        if node[0] == 'lib_symbols':
            for s in node[1:]:
                name = s[1]
                pins = []
                for sub in s[2:]:
                    if isinstance(sub, list) and sub[0] == 'symbol':
                        for pp in sub[2:]:
                            if isinstance(pp, list) and pp[0] == 'pin':
                                at = next(x for x in pp if isinstance(x, list) and x[0] == 'at')
                                num = next(x for x in pp if isinstance(x, list) and x[0] == 'number')[1]
                                pins.append((num, float(at[1]), float(at[2])))
                power = any(isinstance(x, list) and x[0] == 'power' for x in s)
                val = next(x for x in s if isinstance(x, list) and x[0] == 'property' and x[1] == 'Value')[2]
                libs[name] = (pins, power, val)
        elif node[0] == 'symbol':
            lid = next(x for x in node if isinstance(x, list) and x[0] == 'lib_id')[1]
            at = next(x for x in node if isinstance(x, list) and x[0] == 'at')
            props = {x[1]: x[2] for x in node if isinstance(x, list) and x[0] == 'property'}
            insts.append((lid, float(at[1]), float(at[2]), int(float(at[3])), props))
        elif node[0] == 'label':
            at = node[2]
            labels.append((node[1], float(at[1]), float(at[2])))
        elif node[0] == 'wire':
            pts = node[1]
            a = (float(pts[1][1]), float(pts[1][2]))
            b = (float(pts[2][1]), float(pts[2][2]))
            wires.append((a, b))
        elif node[0] == 'no_connect':
            ncs.append((float(node[1][1]), float(node[1][2])))
    return libs, insts, labels, wires, ncs


def key(x, y):
    return (round(x, 3), round(y, 3))


def extract(path):
    libs, insts, labels, wires, ncs = load(path)
    parent = {}

    def f(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def u(a, b):
        parent[f(a)] = f(b)
    pinpts = []   # (ref, num, point)
    pt_owner = defaultdict(list)
    for (lid, X, Y, r, props) in insts:
        pins, power, val = libs[lid]
        ref = props['Reference']
        for (num, px, py) in pins:
            # rotation (only power symbols are rotated; their single pin is at origin)
            P = key(X + px, Y - py)
            if power:
                u(('net', val), ('pt', P))
            else:
                pinpts.append((ref, num, P))
                pt_owner[P].append((ref, num))
            f(('pt', P))
    for (name, x, y) in labels:
        u(('net', name), ('pt', key(x, y)))
    allpts = set(k[1] for k in parent if k[0] == 'pt')
    for (a, b) in wires:
        A, B = key(*a), key(*b)
        u(('pt', A), ('pt', B))
        for P in allpts:
            if min(A[0], B[0]) - 1e-6 <= P[0] <= max(A[0], B[0]) + 1e-6 and \
               min(A[1], B[1]) - 1e-6 <= P[1] <= max(A[1], B[1]) + 1e-6:
                # collinear check for axis-aligned wires
                if (A[0] == B[0] == P[0]) or (A[1] == B[1] == P[1]):
                    u(('pt', A), ('pt', P))
    problems = []
    for P, owners in pt_owner.items():
        if len(owners) > 1:
            problems.append(f'pins overlap at {P}: {owners}')
    nc = set(key(*p) for p in ncs)
    groups = defaultdict(set)
    for (ref, num, P) in pinpts:
        groups[f(('pt', P))].add((ref, num))
    names = {}
    for k in list(parent):
        if k[0] == 'net':
            names.setdefault(f(k), set()).add(k[1])
    result = {}
    for root, members in groups.items():
        nm = names.get(root)
        if nm and len(nm) > 1:
            problems.append(f'label conflict {nm}')
        result[root] = (sorted(nm)[0] if nm else None, members)
    # pins left unconnected without no_connect
    for (ref, num, P) in pinpts:
        root = f(('pt', P))
        if len(groups[root]) == 1 and root not in names and P not in nc:
            problems.append(f'dangling pin {ref}.{num}')
    return result, problems


def compare(path):
    result, problems = extract(path)
    # expected: set of frozensets of (ref,pin) per net, using unique pin numbers
    exp = defaultdict(set)
    for ref, p in D.PARTS.items():
        for num, net in p['nets'].items():
            if net:
                exp[net].add((ref, num))
    got = {}
    for root, (nm, members) in result.items():
        members = {m for m in members if not m[0].startswith('#')}
        if len(members) == 1 and nm is None:
            continue
        got[nm or f'<unnamed:{sorted(members)[0]}>'] = got.get(nm, set()) | members
    # unnamed nets in matrix: match by member set
    exp_sets = {frozenset(v): k for k, v in exp.items()}
    mism = []
    matched = set()
    for nm, mem in got.items():
        fs = frozenset(mem)
        if fs in exp_sets:
            matched.add(exp_sets[fs])
        else:
            mism.append((nm, sorted(mem)[:6], len(mem)))
    missing = [k for k in exp if k not in matched]
    return problems, mism, missing


if __name__ == '__main__':
    p, m, miss = compare(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/tomtho_slim/tomtho_slim.kicad_sch')
    print('problems:', len(p))
    for x in p[:30]:
        print(' ', x)
    print('mismatched nets:', len(m))
    for x in m[:30]:
        print(' ', x)
    print('expected nets not found:', miss[:30])
