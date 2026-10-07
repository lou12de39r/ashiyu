# tomtho-slim mk2 — layout v19 and board plan

This folder holds the frozen layout and the board plan for the second keyboard: roBa-style column stagger, centre trackpad, thin case.

| File | Contents |
|---|---|
| `layout_v19.py` | Script that draws the layout (`roba_ortho_v19.png`) |
| `layout_v19.json` | Fixed coordinates of every key, the trackpad and the LEDs (mm; origin is the rear-left corner of the outline, +y towards the user) |
| `freeze.py` | Regenerates the JSON above from `layout_v19.py` |
| `layout_v19_print_A4.pdf` / `print11.py` | 1:1 print sheet (A4 landscape). Print at **actual size / 100%** and check the 100 mm bar with a ruler |

## Settled specification

### Layout
- **Keys:** 65 total.
  - Left block: 6 columns × number row + 3 rows, plus Fn / Ctrl→**Alt** (firmware) / Win.
  - Right block: 6 columns × number row + 3 rows, plus arrows (← ↑↓ →; ↑ and ↓ are stacked 0.5u keys).
  - Thumbs: 1.25u × 3 per side. Fan is half of roBa's: tilt 0 / 4.5 / 10°, drop 0 / 0.8 / 3.5 mm.
  - Centre: mouse L / R (1u × 0.5u) and M (0.5u × 0.5u).
  - Rear strip, top-left: BT key (0.5u × 0.5u; tap = next profile, 1 s hold = clear and re-pair).
- **Pitch:** 18.5 × 18.0 mm.
- **Column stagger:** half of roBa's offsets. Relative to the pinky column: ring 3.3, middle 5.5, index 4.4, inner 3.2 mm towards the rear. The tops of 3 / 8 line up with the trackpad top.
- **Outline:** 277.0 × 107.5 mm.
- **Trackpad:** 49 × 62.4 mm.
- **LEDs:**
  - BT1–3, green: light for 3 s on a press; blink while waiting to pair.
  - Power, green/red bicolour (firmware): green for 3 s on power-up and on a profile switch; below 20 % a short red blink every 5 s.
  - Charge, orange: driven directly by the charger STAT pin; lights only while USB is connected.

### Matrix and GPIO (draft)

| Row | Left side (C0–C5) | Right side (C6–C11) |
|---|---|---|
| R0 | ` 1 2 3 4 5 | 6 7 8 9 0 - |
| R1 | Tab Q W E R T | Y U I O P [ |
| R2 | Ctl A S D F G | H J K L ' ] |
| R3 | ⇧ Z X C V B | N M , . / Ent |
| R4 | Fn Alt Win 変換 Space 無変換 | BS Enter Del ← ↑ → |
| R5 | BT L M R ↓ (5 keys) | — |

**Pin budget:**

| Function | Pins |
|---|---|
| Matrix (6 rows + 12 columns) | 18 |
| BT LEDs | 3 |
| Power LED | 2 |
| Charger STAT sense (lets firmware see charging) | 1 |
| Trackpad (SDA, SCL, RDY, RST) | 4 |
| **Total** | **28** |

The MDBT50Q has room to spare. Reset, NFC and crystal pins are avoided.

### Board split (decided: separate trackpad board)
- **Main board:**
  - 2 layers, 1.2 mm thick (same as v0.1).
  - Holds keys, MCU module, charging, LEDs and USB-C (mid-mount, opening in the rear edge).
  - The MCU module sits under the trackpad with its antenna at the rear edge.
- **Trackpad board:**
  - 4 layers, IQS550, based on GR-Trackpad65 (MIT), reworked to 49 × 62.4 mm.
  - Connects to the main board with a 6-pin 0.5 mm FPC: VDD, GND, SDA, SCL, RDY, RST.

## Verify before ordering (in priority order)
1. **Trackpad size:** GR-Trackpad65 is 65 mm tall, so it is 2.6 mm too long as-is. Check whether dropping one electrode row fits it, and whether that needs re-tuning (uncertain).
2. **Stock at JLC/LCSC (unchecked):** IQS550, the mid-mount USB-C, the 0603 green / orange / bicolour LEDs, and the 0.5 mm FPC connector.
3. **Clearance:** check the space between the parts on the main board and the trackpad board above them (estimated about 2.5 mm).
4. **Keycaps:** fit of the Acid Caps on the tilted thumb keys, checked by laying out the 3D data.
5. **0.5u × 0.5u caps (BT, M):** these are not sold, so they must be made. Print a test piece first.
