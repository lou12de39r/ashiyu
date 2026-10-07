"""Join remaining islands of a net with the minirouter."""
import itertools
import design as D
import check as C
import minirouter as M


def islands(t, v, net):
    objs = [o for o in C.build(t, v) if o.net == net]
    par = list(range(len(objs)))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i, j in itertools.combinations(range(len(objs)), 2):
        if set(objs[i].layers) & set(objs[j].layers) and C.dist(objs[i], objs[j]) <= 1e-4:
            par[f(i)] = f(j)
    first = {}
    for i, o in enumerate(objs):
        if o.owner in D.PARTS:
            k = (o.owner, o.desc)
            if k in first:
                par[f(i)] = f(first[k])
            else:
                first[k] = i
    g = {}
    for i, o in enumerate(objs):
        g.setdefault(f(i), []).append(o)
    return list(g.values())


def pts(group):
    out = []
    for o in group:
        L = 'F.Cu' if 'F.Cu' in o.layers else 'B.Cu'
        if o.kind == 'rect':
            out.append(((o.rect[0] + o.rect[2]) / 2, (o.rect[1] + o.rect[3]) / 2, L))
        else:
            for L2 in o.layers:
                if L2 in ('F.Cu', 'B.Cu'):
                    out.append((o.a[0], o.a[1], L2))
                    out.append((o.b[0], o.b[1], L2))
    return out


def join(t, v, net, w=0.25, clr=0.16):
    t, v = list(t), list(v)
    for _ in range(10):
        gs = islands(t, v, net)
        if len(gs) <= 1:
            return t, v, True
        gs.sort(key=len)
        small, rest = gs[0], [o for g in gs[1:] for o in g]
        # start from a pad of the small island if any, else first point
        sp = [p for p in pts(small)]
        src = None
        for o in small:
            if o.kind == 'rect' and 'F.Cu' in o.layers:
                src = ((o.rect[0] + o.rect[2]) / 2, (o.rect[1] + o.rect[3]) / 2)
                break
        if src is None:
            fpts = [p for p in sp if p[2] == 'F.Cu']
            if not fpts:
                return t, v, False
            src = fpts[0][:2]
        r = M.route(t, v, net, src, pts(rest), w=w, clr=clr)
        if not r:
            return t, v, False
        t += r[0]
        v += r[1]
    return t, v, len(islands(t, v, net)) <= 1
