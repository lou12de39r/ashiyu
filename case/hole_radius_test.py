"""How round can the keycap-hole corners be?  Intersect each ACC cap (at rest, and pressed 1 mm) with a plate patch
whose hole has corner radius r.  Plate in cap-local z: -1.5 .. +0.5 (plate bottom = top of the hooks).  Runs in CI."""
import os, sys
import cadquery as cq
ACC = sys.argv[1]
CAPS = {'1u': ('ACC_1u.step', (8.25, -8.0), (16.5, 16.0)),
        '1.25u': ('ACC_1.25u.step', (10.5, -8.0), (21.0, 16.0)),
        '1u_x_0.5u': ('ACC_0.5u.step', (8.25, -3.5), (16.5, 7.0))}
for key, (fn, (cx, cy), (w, h)) in CAPS.items():
    cap = cq.importers.importStep(os.path.join(ACC, fn)).val().translate(cq.Vector(-cx, -cy, 0))
    for r in (0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0):
        plate = cq.Workplane('XY').workplane(offset=-1.5).rect(w + 8, h + 8).extrude(2.0)
        hole = cq.Workplane('XY').workplane(offset=-1.6).sketch().rect(w, h).vertices().fillet(r).finalize().extrude(2.2)
        plate = plate.cut(hole).val()
        res = []
        for dz in (0.0, -1.0):
            for dx, dy in ((0, 0), (0.1, 0.1), (-0.1, -0.1)):      # also with 0.1 mm of sideways play
                v = cap.translate(cq.Vector(dx, dy, dz)).intersect(plate).Volume()
                res.append(round(v, 3))
        print(f'{key:10s} r={r:.1f}: interference mm3 (rest, +play, -play, pressed...) {res}', flush=True)
