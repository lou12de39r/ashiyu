"""Post-route cleanup driven by KiCad DRC feedback:
duplicate vias, too-close via pairs, dangling track stubs, vias that only touch one layer's copper."""
import math
import design as D
import check as C


def dedupe_vias(vias):
    seen, out = set(), []
    for v in vias:
        k = (round(v[0], 3), round(v[1], 3), v[2])
        if k not in seen:
            seen.add(k)
            out.append(v)
    return out


def close_vias(vias, min_hole=0.25):
    """Merge vias of the same net whose drill edges are closer than min_hole: keep the first."""
    out = []
    drill = D.VIA[1]
    for v in vias:
        if any(o[2] == v[2] and math.hypot(o[0] - v[0], o[1] - v[1]) - drill < min_hole for o in out):
            continue
        out.append(v)
    return out


def _pt_obj(pt, layer):
    o = C.Obj()
    o.kind, o.a, o.b, o.rad, o.layers = 'cap', pt, pt, 0.0, (layer,)
    return o


def drop_dangling(tracks, vias, keep_nets=()):
    """Remove track segments that have an end touching nothing of the same net (iterate)."""
    tracks = list(tracks)
    while True:
        objs = C.build(tracks, vias)
        bynet = {}
        for o in objs:
            bynet.setdefault(o.net, []).append(o)
        removed = False
        new = []
        for i, t in enumerate(tracks):
            layer, x1, y1, x2, y2, w, net = t
            ok = True
            for pt in ((x1, y1), (x2, y2)):
                p = _pt_obj(pt, layer)
                hit = False
                for o in bynet.get(net, []):
                    if o.owner == f'trk{i}' or layer not in o.layers:
                        continue
                    if C.dist(p, o) <= 1e-3:
                        hit = True
                        break
                if not hit:
                    ok = False
                    break
            if ok or net in keep_nets:
                new.append(t)
            else:
                removed = True
        tracks = new
        if not removed:
            return tracks


def run(tracks, vias):
    n0 = (len(tracks), len(vias))
    vias = dedupe_vias(vias)
    vias = close_vias(vias)
    tracks = drop_dangling(tracks, vias)
    # vias left with no track on either side are fine only for GND (pour); others -> drop
    objs = C.build(tracks, vias)
    keep = []
    for (x, y, n) in vias:
        if n == 'GND':
            keep.append((x, y, n))
            continue
        layers_hit = set()
        for L in ('F.Cu', 'B.Cu'):
            p = _pt_obj((x, y), L)
            if any(o.net == n and L in o.layers and not o.owner.startswith('via') and C.dist(p, o) <= 0.31
                   for o in objs):
                layers_hit.add(L)
        if len(layers_hit) == 2:
            keep.append((x, y, n))
    vias = keep
    tracks = drop_dangling(tracks, vias)
    print(f'cleanup: tracks {n0[0]} -> {len(tracks)}, vias {n0[1]} -> {len(vias)}')
    return tracks, vias
