"""Write .kicad_pro (design rules + net classes), lib tables, JLCPCB BOM/CPL."""
import csv
import json
import re
from collections import OrderedDict

import design as D
from pcbio import PROJECT, LIB

from pcbio import REPO as ROOT


def write_pro():
    pro = {
        "board": {
            "design_settings": {
                "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2, "copper_text_size_h": 1.5,
                             "copper_text_size_v": 1.5, "copper_text_thickness": 0.3, "silk_line_width": 0.12,
                             "silk_text_size_h": 1.0, "silk_text_size_v": 1.0, "silk_text_thickness": 0.15},
                "rules": {
                    "min_clearance": 0.15, "min_track_width": 0.15, "min_connection": 0.15,
                    "min_via_diameter": 0.5, "min_via_annular_width": 0.1, "min_through_hole_diameter": 0.3,
                    "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25, "min_copper_edge_clearance": 0.3,
                    "min_silk_clearance": 0.0, "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1,
                    "solder_mask_to_copper_clearance": 0.0, "use_height_for_length_calcs": True
                },
                "track_widths": [0.0, 0.2, 0.25, 0.3, 0.4],
                "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}],
                "rule_severities": {"courtyards_overlap": "error", "silk_overlap": "ignore",
                                    "silk_over_copper": "warning", "lib_footprint_issues": "ignore",
                                    "lib_footprint_mismatch": "ignore", "footprint_type_mismatch": "ignore"}
            }
        },
        "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 1},
        "net_settings": {
            "classes": [
                {"name": "Default", "clearance": 0.15, "track_width": 0.2, "via_diameter": 0.6, "via_drill": 0.3,
                 "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
                 "microvia_diameter": 0.3, "microvia_drill": 0.1, "wire_width": 6, "bus_width": 12,
                 "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
                 "priority": 2147483647},
                {"name": "Power", "clearance": 0.15, "track_width": 0.3, "via_diameter": 0.6, "via_drill": 0.3,
                 "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
                 "microvia_diameter": 0.3, "microvia_drill": 0.1, "wire_width": 6, "bus_width": 12,
                 "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
                 "priority": 0}],
            "meta": {"version": 4},
            "netclass_patterns": [{"netclass": "Power", "pattern": n} for n in sorted(D.POWER_NETS)]
        },
        "pcbnew": {"page_layout_descr_file": ""},
        "schematic": {"drawing": {"default_line_thickness": 6.0, "default_text_size": 50.0}, "legacy_lib_dir": "",
                      "legacy_lib_list": []},
        "sheets": [["" + __import__('pcbio').ROOT_UUID, "Root"]],
        "text_variables": {}
    }
    with open(f'{ROOT}/{PROJECT}.kicad_pro', 'w') as fh:
        json.dump(pro, fh, indent=2)
    with open(f'{ROOT}/fp-lib-table', 'w') as fh:
        fh.write(f'(fp_lib_table\n\t(version 7)\n\t(lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/lib/{LIB}.pretty")'
                 f'(options "")(descr "tomtho-slim footprints"))\n)\n')
    with open(f'{ROOT}/sym-lib-table', 'w') as fh:
        fh.write(f'(sym_lib_table\n\t(version 7)\n\t(lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/lib/{LIB}.kicad_sym")'
                 f'(options "")(descr "tomtho-slim symbols"))\n)\n')


def natkey(r):
    m = re.match(r'([A-Z]+)(\d+)', r)
    return (m.group(1), int(m.group(2))) if m else (r, 0)


def write_jlc():
    groups = OrderedDict()
    for ref in sorted(D.PARTS, key=natkey):
        p = D.PARTS[ref]
        if not p['bom']:
            continue
        k = (p['value'], p['fp'], p['lcsc'])
        groups.setdefault(k, []).append(ref)
    with open(f'{ROOT}/jlc/{PROJECT}_BOM.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #', 'Qty', 'MPN', 'Note'])
        for (val, fp, lcsc), refs in groups.items():
            p = D.PARTS[refs[0]]
            w.writerow([val, ','.join(refs), fp, lcsc, len(refs), p['mpn'], p['desc']])
    ox, oy = D.BOARD[0], D.BOARD[3]
    with open(f'{ROOT}/jlc/{PROJECT}_CPL.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for ref in sorted(D.PARTS, key=natkey):
            p = D.PARTS[ref]
            if not p['bom']:
                continue
            w.writerow([ref, f'{p["x"] - ox:.4f}mm', f'{oy - p["y"]:.4f}mm', 'Top', f'{p["rot"] % 360:.0f}'])
    return groups


if __name__ == '__main__':
    write_pro()
    g = write_jlc()
    for k, v in g.items():
        print(len(v), k)
