"""Write the mk2 schematic + symbol library, render a preview and re-check the netlist."""
import sch as S
import schrender as SR
import schcheck as SC
from pcbio import REPO, PROJECT
S.write(f'{REPO}/{PROJECT}.kicad_sch')
S.write_symlib(f'{REPO}/lib/{PROJECT}.kicad_sym')
SR.main(f'{REPO}/{PROJECT}.kicad_sch', f'{REPO}/docs/schematic_full.png')
p, m, miss = SC.compare(f'{REPO}/{PROJECT}.kicad_sch')
print('schematic re-check: problems', len(p), 'mismatched nets', len(m), 'missing', len(miss))
for x in (p + m)[:20]:
    print(' ', x)
print(miss[:20])
