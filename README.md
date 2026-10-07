# tomtho-slim mk2 — layout v20 and board plan

This folder holds the frozen layout and the board plan for the second keyboard: roBa-style column stagger, centre trackpad, thin case.

| File | Contents |
|---|---|
| `layout_v20.py` | Script that draws the layout (`roba_ortho_v20.png`) |
| `layout_v20.json` | Fixed coordinates of every key, the trackpad and the LEDs (mm; origin is the rear-left corner of the outline, +y towards the user) |
| `freeze.py` | Regenerates the JSON above from `layout_v20.py` |
| `layout_v20_print_A4.pdf` / `print11.py` | 1:1 print sheet (A4 landscape). Print at **actual size / 100%** and check the 100 mm bar with a ruler |

## Settled specification

### Layout
- **Keys:** 65 total.
  - Left block: 6 columns × number row + 3 rows, plus Fn / Ctrl→**Alt** (firmware) / Win.
  - Right block: 6 columns × number row + 3 rows, plus arrows (← ↑↓ →; ↑ and ↓ are stacked 0.5u keys).
  - Thumbs: 1.25u × 3 per side. Fan is half of roBa's: tilt 0 / 4.5 / 10°, drop 0 / 0.8 / 3.5 mm.
  - Centre: mouse L / R (1u × 0.5u) and M (0.5u × 0.5u).
  - Rear strip, top-left: BT key (0.5u × 0.5u; tap = next profile, 1 s hold = clear and re-pair).
- **Pitch:** 18.5 × 18.0 mm.
- **Column stagger:** half of roBa's offsets. Relative to the pinky column: ring 3.3, middle 5.5, index 4.4, inner 3.2 mm towards the rear. The trackpad top lines up with the tops of T / Y; the MCU module, USB-C and charger sit in the free area above it (nothing is stacked under the trackpad).
- **Outline:** 277.0 × 107.5 mm.
- **Trackpad:** 49 × 42.0 mm.
- **LEDs:**
  - BT1–3, green: light for 3 s on a press; blink while waiting to pair.
  - Power, yellow-green/red bicolour XL-2012SURSYGC (firmware): green for 3 s on power-up and on a profile switch; below 20 % a short red blink every 5 s.
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
  - The MCU module, USB-C and charger sit in the free area between 5 and 6, above the trackpad, with the antenna at the rear edge.
- **Trackpad board:**
  - 4 layers, IQS550, based on GR-Trackpad65 (MIT), reworked to 49 × 42.0 mm.
  - Gestures:
    - Two-finger scroll uses the IQS550's built-in gesture engine.
    - Three-finger swipe = **app switch**, done in the firmware driver from the touch coordinates:
      - Three fingers land: hold Alt.
      - Each 8–10 mm of sideways travel: Tab (rightwards) or Shift+Tab (leftwards).
      - Fingers lift: release Alt.
  - **IQS550 is hand-soldered (decided).**
    - JLC assembles everything else, with U1 marked DNP.
    - Buy the IQS550 from an authorised distributor (Mouser / DigiKey) and get a few spares.
    - Board-side help for hand soldering:
      - IC on the bottom side; electrodes on the top layer.
      - QFN pads lengthened outwards by 0.3–0.4 mm.
      - A plated hole of about 1.0 mm in the exposed pad, so it can be soldered from the other side.
      - A JLC stencil for the trackpad board.
    - Tools needed: hot air or a hotplate, solder paste, flux, magnifier.
  - Connects to the main board with a 6-pin 0.5 mm FPC: VDD, GND, SDA, SCL, RDY, RST.

## Schematic (mk2-0.1)

- **Files:** `tomtho_mk2.kicad_sch` (KiCad 9). `gen/build_sch.py` regenerates it from `gen/design.py`, which in turn reads `layout_v20.json`. CI ERC: **0 errors, 0 warnings**. The netlist re-extracted from the schematic matches `design.py`.
- **Matrix:** drawn as a wired grid, COL → SW → D → ROW.
- **Charge LED:** red KT-0603R, driven straight from the charger STAT pin.
- **DRAFT footprints, to verify against the drawings before the PCB is final:**
  - USB-C C2906290.
  - Bicolour LED XL-2012SURSYGC. Pad map 1 = red K, 2 = green K, 3/4 = anode is **assumed**.
  - FPC C5213729.

## PCB (mk2-0.1)

- **Board:** `tomtho_mk2.kicad_pcb`, 2 layers, 276 × 107 mm.
- **Build pipeline:**
  1. `gen/route.py` writes a Specctra DSN and runs Freerouting. GND is routed as a normal net (a tree), then poured on both layers.
  2. `gen/post.py` adds about 600 GND stitching vias.
  3. `gen/build_pcb.py` writes the board, fills the zones and runs KiCad DRC.
- **Check:** DRC with schematic parity gives **0 violations, 0 unconnected, 0 parity** in both local KiCad 10 and CI KiCad 9.
- **Fab files:** JLC BOM/CPL are in `jlc/`. CI exports the Gerbers and drill files to `ci-results:mk2/gerber`.
- **USB-C:** top-mount HRO TYPE-C-31-M-12 (C165948). It sits in the free area, so the mid-mount part is not needed.
- **Before ordering, check:**
  - In JLC's assembly preview: the rotation of the tilted thumb keys, the USB-C and the LEDs.
  - The battery-lead slot near J2.
  - The routing is automatic and rough in places; it could be tidied by hand.

## Parts check (2026-10-07, LCSC / JLCPCB pages)

| Part | Result |
|---|---|
| IQS550BLQNR (C5271144) | **Out of stock at LCSC.** The trackpad board cannot be assembled at JLC as planned |
| USB-C TYPE-C 16PIN 2MD(073) (C2765186) | In stock, but right-angle SMD, not mid-mount. Not used |
| **USB-C SHOU HAN TYPE-C 16P CB1.6 073 (C2906290)** | **Use this.** Mid-mount (sinks 1.6 mm), 16-pin, 6.5 mm long, plentiful stock (LCSC). JLC rates assembly difficulty "High". It is made for a 1.6 mm board, so on our 1.2 mm board it sticks out about 0.4 mm below → add a pocket in the case bottom |
| FPC 0.5 mm 6-pin HC-FPC-05-10-6RLTAG (C5213729) | In stock (5k), bottom contact, flip lock |
| Green LED 19-217/GHC (C72043) | Vf 3.3 V: **too high for a 3.0 V VDD**. Needs a yellow-green (≈2.0 V) part instead |
| Red LED KT-0603R (C2286) | Vf 1.8–2.4 V, usable |
| Bicolour LED XINGLIGHT XL-2012SURSYGC (C965847) | **Use this.** 2.0 × 1.2 mm, common anode, red + yellow-green (Vf ≈ 2.4 V at 20 mA; lower at 1–2 mA, so it works from 3.0 V). In stock (20k) |
| IQS550-BL-QNR elsewhere | Octopart lists it only at non-authorised resellers (about 1.1k and 32k pcs, $1.7–3.0). Stock at Mouser / DigiKey could not be read (unconfirmed) |

## Verify before ordering (in priority order)
1. **Trackpad size:** GR-Trackpad65 is 65 mm tall, so the 42 mm pad needs about a third fewer electrode rows. Check how far the electrode pattern has to be redrawn and whether it needs re-tuning (uncertain).
2. **Stock at JLC/LCSC (unchecked):** IQS550, the mid-mount USB-C, the 0603 green / orange / bicolour LEDs, and the 0.5 mm FPC connector.
3. **Height:** check that the parts in the free area (module about 2.2 mm, USB-C) fit under the case top. Nothing is stacked under the trackpad any more.
4. **Keycaps:** fit of the Acid Caps on the tilted thumb keys, checked by laying out the 3D data.
5. **0.5u × 0.5u caps (BT, M):** these are not sold, so they must be made. Print a test piece first.
