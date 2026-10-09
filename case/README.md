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
| Keycap top | 11.5 | thumb caps 11.8 (domed, raised 0.3) |

Outline: 280.0 × 110.5 mm.

## Keycaps

- **ACC (Acid Caps ClickProfile, Salicylic-acid3):**
  - 1u × 51, plus 1u Home × 2 (F, J).
  - 0.5u, i.e. 1u × 0.5u, × 4 (L, R, ↑, ↓).
  - Thumb keys (1u × 4, 1.25u × 2) use printed domed caps instead (see below).
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
- **Reset:** a printed plunger in a 4.8 mm hole over the reset switch (no pin needed). Its stem is 3.0 mm across, covering the whole switch top, so slight offset or tilt still presses it; the stem ends 0.1 mm above the switch. It goes in from below like the 0.5u caps; two plungers are on the 0.5u keycap sprue.
- **Rear wall:**
  - USB-C notch (open at the top: a 6 mm plug overmold leaves no wall above it).
  - Power-switch slot.
- **Screws:** 11 × M2 from below, through the PCB, into Ø 5.2 bosses with a 1.7 mm pilot (sized for resin).
  - Plate posts (1.4 square) in the webs between keys keep the plate height.
- **Bottom plate:** 7 × 7 support islands under every switch (none over the LiPo), solid blocks under USB-C, the power switch and reset, and counterbores for the screw heads.

## Reference data

Measured only, not copied: the ACC keycaps (`Salicylic-acid3/ACC_Keycaps`) and the ClickBoard Tenkey case (`Salicylic-acid3/Case_Data`) are both CC BY-NC 4.0. CI clones them at build time; this repo stores only numbers derived from them.

## Keycap files (`keycaps.py`, CI → `case-results:keycaps/`)
- **One file per size** (STEP + STL): 1u, 1u home (F / J), 1.25u, 1u × 0.5u, and 0.5u × 0.5u (our flange cap).
- **Thumb caps** `keycap_1u_thumb` / `keycap_1.25u_thumb`: the ACC cap with the dish (about 0.45 mm deep) filled and a gentle ellipsoid dome on top.
  - The top is raised 0.3 mm, so the dome's edges sit near the other caps' rim height. The peak is 0.3 mm above the other keys (11.8 mm total at the thumb row); the middle of each top edge is 0.4 mm below the peak and the corners about 0.75 mm below.
  - Walls, hooks, nub and edge rounding are unchanged ACC. No ACC part exists for these, so they are always printed.
  - The first four are Salicylic-acid3's ACC models, re-centred and converted, under **CC BY-NC 4.0** (see `LICENSE.txt` there).
  - **Non-commercial use only.**
- **Print sprues**: the caps mk2 needs, joined by 1 mm bars at the middle of each side, clear of the corner hooks.

| Sprue | Contents |
|---|---|
| `print_sprue_1u_x29_a`, `print_sprue_1u_x28_b` | 51 needed + 10 % spares (57, split in two so each STL stays under 30 MB) |
| `print_sprue_thumb_1.25u_x3_1u_x6` | thumb caps: 1.25u 2 + 1 spare, 1u 4 + 2 spares (**always printed**) |
| `print_sprue_1u_x_0.5u_x5` | 4 + 1 spare |
| `print_sprue_1u_home_x3` | 2 + 1 spare |
| 0.5u × 0.5u | 6 on the case sprue, with the 2 reset plungers |

- **Printing caution:** the ClickBoard author found that about 1 in 10 caps from a JLC 3D-print trial failed on small burrs. The released ACC caps are injection-moulded PBT. Printed hooks in brittle resin may also snap.
