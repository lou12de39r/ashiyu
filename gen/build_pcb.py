"""Write the unrouted (or routed, if routed.pkl exists) mk2 PCB + footprint lib + project, then run KiCad DRC locally."""
import os, pickle, subprocess, sys, json, collections
import design as D
import pcbio as P
import sch as S
import project as PR

REPO = P.REPO
PCB = f'{REPO}/{P.PROJECT}.kicad_pcb'
KPY = '/opt/kicad/AppDir/bin/python3'
KCLI = '/opt/kicad/AppDir/bin/kicad-cli'


def write(tracks=(), vias=()):
    P.write_pcb(PCB, list(tracks), list(vias), nc_nets=S.nc_pad_nets())
    P.write_footprint_lib(f'{REPO}/lib/{P.PROJECT}.pretty')
    PR.write_pro()


def fill_and_drc(tag='drc'):
    out = f'{REPO}/out'
    os.makedirs(out, exist_ok=True)
    filled = f'{out}/{P.PROJECT}_filled.kicad_pcb'
    code = (f'import pcbnew\nb = pcbnew.LoadBoard({PCB!r})\npcbnew.ZONE_FILLER(b).Fill(b.Zones())\n'
            f'pcbnew.SaveBoard({filled!r}, b)\n')
    subprocess.run([KPY, '-c', code], capture_output=True, text=True)
    for ext in ('kicad_pro', 'kicad_sch', 'kicad_dru'):
        src = f'{REPO}/{P.PROJECT}.{ext}'
        dst = f'{out}/{P.PROJECT}_filled.{ext}'
        open(dst, 'w').write(open(src).read())
    js = f'{out}/{tag}.json'
    subprocess.run([KCLI, 'pcb', 'drc', '--schematic-parity', '--severity-all', '--format', 'json', '-o', js, filled],
                   capture_output=True, text=True)
    d = json.load(open(js))
    items = [('violations', v) for v in d.get('violations', [])] + \
            [('unconnected', v) for v in d.get('unconnected_items', [])] + \
            [('parity', v) for v in d.get('schematic_parity', [])]
    c = collections.Counter((k, v.get('severity'), v.get('type')) for k, v in items)
    for (k, s, t), n in sorted(c.items()):
        print(f'  {k:12s} {s:8s} {t:30s} {n}')
    return d, filled


if __name__ == '__main__':
    t, v = (pickle.load(open('routed.pkl', 'rb')) if os.path.exists('routed.pkl') and 'raw' not in sys.argv else ([], []))
    write(t, v)
    fill_and_drc()
