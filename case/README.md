# mk2 case: top frame + bottom plate

The case is generated in CadQuery by CI (`.github/workflows/case.yml`). Results, including STEP/STL files, section views and interference checks, go to the **`case-results`** branch.

## Files

| File | Role |
|---|---|
| `export_inputs.py` | Run locally with KiCad's python. Reads the finished PCB and layout and writes `case_inputs.json`. |
| `build_case.py` | CI. Builds the top frame, bottom plate and 0.5u × 0.5u keycap, and exports STEP + STL. `KEY_CLR` adds extra keycap-hole clearance per side. |
| `check_case.py` | CI. Checks keycaps (at rest and pressed 1 mm) against the frame, the bottom plate and part blocks, and draws section PNGs. |
| `measure2.py`, `measure_ref.py` | CI. Measure the reference STEP files (ACC keycaps, ClickBoard Tenkey case, LCSC part models). |
| `render_stl.py` | Local shaded STL preview (numpy + matplotlib). |

## Build heights

z = 0 is the case bottom.

| Level | z (mm) | Notes |
|---|---|---|
| Bottom plate floor | 0 – 1.0 | |
| LiPo pocket | 1.0 – 4.3 | ≤ 3.0 × 40 × 70 cell |
| PCB bottom (seam between the two parts) | 4.3 | |
| PCB top | 5.5 | |
| Plate | 8.5 – 10.5 | 2.0 mm thick. Starts 3.0 mm above the PCB; ACC hooks catch under it, as in the ClickBoard Tenkey case. |
| Keycap top | 11.5 | |

Outline: 280.0 × 110.5 mm.

## Keycaps

- **ACC (Acid Caps ClickProfile, Salicylic-acid3):**
  - 1u × 53.
  - 1.25u × 6 (thumb keys).
  - 0.5u, i.e. 1u × 0.5u, × 4 (L, R, ↑, ↓).
- **Plate holes:** keycap body + 0.14 mm per side, as in the ClickBoard Tenkey case.
  - 1u: 16.5 × 16.0.
  - 1.25u: 21.0 × 16.0.
  - 1u × 0.5u: 16.5 × 7.0.
  - 0.5 mm 45° lead-in at the top.
- **BT and M (0.5u × 0.5u):** no ACC part exists, and hooks cannot fit because the SKRA body (6.2 square, 2.8 mm tall) fills the hole.
  - Uses the printed flange cap `tomtho_mk2_keycap_0.5u_x_0.5u`.
  - The plate is thinned to 0.8 mm around these keys.
  - The cap goes into the frame **from below, before the PCB**.

## Other features

- **TPS43 trackpad:** 1.0 mm skin over a 43.6 × 40.6 pocket. Stick the module to the pocket ceiling with its own adhesive. A 0.4 mm groove round the touch area marks its edge.
- **LEDs:** 1.8 mm windows, with light shrouds that stop 1.0 mm above the PCB.
- **Reset:** 1.6 mm pin hole over the reset switch.
- **Rear wall:**
  - USB-C notch (open at the top: a 6 mm plug overmold leaves no wall above it).
  - Power-switch slot.
- **Screws:** 11 × M2 from below, through the PCB, into Ø 4.6 bosses with a 1.6 mm pilot.
  - Plate posts (1.4 square) in the webs between keys keep the plate height.
- **Bottom plate:** 7 × 7 support islands under every switch (none over the LiPo), solid blocks under USB-C, the power switch and reset, and counterbores for the screw heads.

## Reference data

Measured only, not copied: the ACC keycaps (`Salicylic-acid3/ACC_Keycaps`) and the ClickBoard Tenkey case (`Salicylic-acid3/Case_Data`) are both CC BY-NC 4.0. CI clones them at build time; this repo stores only numbers derived from them.
