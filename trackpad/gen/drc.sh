#!/bin/bash
# fill zones + DRC (no parity) ; usage: drc.sh board.kicad_pcb
B=$1; KPY=/opt/kicad/AppDir/bin/python3; K=/opt/kicad/AppDir/bin/kicad-cli
$KPY -c "import pcbnew; b=pcbnew.LoadBoard('$B'); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard('$B', b)" >/dev/null 2>&1
$K pcb drc --severity-all --format json -o ${B%.kicad_pcb}_drc.json $B >/dev/null 2>&1
python3 - "${B%.kicad_pcb}_drc.json" <<'PY'
import json, sys, collections
d = json.load(open(sys.argv[1]))
c = collections.Counter((v['severity'], v['type']) for v in d['violations'])
print('unconnected', len(d['unconnected_items']))
for k, n in sorted(c.items()): print(' ', k, n)
PY
