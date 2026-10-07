# tomtho-slim mk2 trackpad (49 × 43 mm, IQS550, 10 Tx × 10 Rx)

This board is derived from **GR-Trackpad65** by geek-rabb1t (MIT License, see `LICENSE_GR-Trackpad65`; original files in `src_grt65/`).

GR-Trackpad65 is 65 × 49 mm with 15 Tx × 10 Rx. Its electrode pitch is 4.2 mm (Tx) × 4.7 mm (Rx). Keeping 10 Tx columns gives exactly 42 mm, so **the electrode shape, pitch and IC surroundings are reused as they are**. Only the board was cut down.

## Changes from the original
1. **Cut down to Tx5–Tx14.** Tx0–Tx4 and the PCBA rails are removed. With the 0.6 mm frame, the board is **49.1 × 43.1 mm**, 4 layers, 1.6 mm thick (same as the original).
   - The case window is 49 × 42 mm. The extra 1.1 mm sits under the case top, towards the L/R buttons.
2. **Rx series resistors R9–R12 moved.** They were on the part that was cut off. Rx6–Rx9 were re-routed on B.Cu (Freerouting with a custom single-layer DSN). Rx7–Rx9 also got new vias onto their F.Cu Rx lines.
3. **Rotated 90°** so the board fits the layout (49 wide × 43 tall). The FFC connector J1 is on the back, at +9.43 / +18.09 mm from the top-left corner, with its opening facing −x.
4. **KiCad 10 DRC: 0 errors, 0 unconnected.**
   - Remaining warnings: footprint-library differences, and silkscreen near the board edge.

## Not done / needs checking (in priority order)
1. **IQS550 settings.** A freshly mounted IQS550 does not work as a trackpad.
   - The original's hex file is written for 15 Tx, so it **cannot be used as-is**.
   - Settings needed:
     - Total Tx = 10.
     - Tx mapping = IC pins Tx5–Tx14.
     - Rx mapping is unchanged.
     - Resolution, and so on.
   - Two ways to write them:
     - (a) Write and save them with Azoteq's CT210A programmer and the IQS5xx-B000 GUI.
     - (b) Write them over I2C at every boot from the ZMK driver. **(b) is planned.** No extra tool is needed, but whether every register is writable at run time still has to be checked against the datasheet (uncertain).
2. **The QFN pads were not lengthened.**
   - Lengthening them shorts them to the dense original fan-out traces.
   - Hand soldering assumes **solder paste + hotplate or hot air**. The pads are the standard KiCad QFN-48 7×7 footprint.
   - JLC assembles everything except U1. The CPL/BOM leave U1 out.
3. **Overlay.** The original recommends **2 mm matte acrylic**. Other materials need different settings.
4. **Thickness and mounting.** The trackpad sits in a **cut-out in the main board** and rests on the case floor:
   - case floor 0.5 + clearance for the back-side parts (FFC connector about 2 mm)
   - \+ PCB 1.6 + overlay 2.0
   - ≈ the case top.
5. **FFC.**
   - Cable: 6-pin, 0.5 mm pitch, length about 15 mm, **contacts on opposite sides (type B)**.
   - Main board J3 is arranged so each pad faces the same signal at the same height.
   - Check continuity before fitting.

## Files
| File | Contents |
|---|---|
| `tomtho_mk2_trackpad.kicad_pcb` | Finished board |
| `jlc/*_BOM.csv`, `*_CPL.csv` | For JLC PCBA, assembled on the back side, U1 left out |
| `gen/crop.py` → `gen/route_b.py` → `gen/trim.py` → `gen/finish.py` | Build steps (KiCad Python + Freerouting) |
| `src_grt65/` | Original GR-Trackpad65 data (MIT) |
