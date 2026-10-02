# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Teensy 4.1-based USB joystick controller for the F-16 left console. Covers ECM, ELEC, EPU, AVTR, UHF backup radio, ENGINE START (JFS), MPO, and AUDIO 1/2. Supports Falcon BMS (BMS-BIOS) and DCS World (DCS-BIOS) with automatic protocol detection for LED synchronization. Part of the Redkite Project.

## Build & Upload

- **IDE**: Arduino IDE with [Teensyduino](https://www.pjrc.com/teensy/td_download.html)
- **Board**: Teensy 4.1
- **USB Type**: Serial + Keyboard + Mouse + Joystick
- **PID**: `0x048E` (set in `usb_desc.h`). Compile-time `#error` if mismatch.
- **JOYSTICK_SIZE**: **64** — 59 buttons exceeds the 32-button limit of size 12. Both sketches use 64, so `usb_desc.h` no longer needs editing between builds.
- **usb_desc.c patch**: Report Count 23→8 + 15 constant padding (fixes DirectInput slider recognition). See `docs/teensyduino_upgrade.md`.
- **Auto-patch after IDE update**: `python tools/patch_usb_desc_h.py` and `python tools/patch_usb_desc_c.py`
- **Upload**: Open `F16_LEFT_CONSOLE.ino` in Arduino IDE and Upload

## Architecture

### Data-Driven Hardware Configuration

All hardware is declared in config arrays under the **HARDWARE CONFIGURATION** section. To add/remove hardware, only edit these arrays:

- `mcpDevices[]` — MCP23017 I2C expanders (addr 0x20–0x27)
- `switches[]` — digital switches, direct or MCP (`mcpIdx = -1` means direct Teensy pin)
- `encoders[]` — rotary encoders (direct pins only)
- `pots[]` — potentiometers mapped to joystick axes (direct ADC pins only)
- `analogBtnArrays[]` — resistor ladder groups (ECM 8-button — T40 A0 / T41 A3)
- `leds[]` — ELEC panel LEDs, indexed by `LedIdx` enum
- `ecmSrLedNames[]` / `srMap[]` — ECM panel LEDs via 74HC595

Joystick button numbers are auto-assigned at runtime in this order: `switches[]` (39) → `analogBtnArrays[]` (8) → `encoders[]` (12, 2 each: CW then CCW) = **59 buttons**.

⚠ Inserting a switch anywhere but the end of `switches[]` renumbers every button after it, which invalidates existing BMS bindings. Append to the end of the array when adding hardware.

### What Cannot Go on the MCP23017

This constraint drives the whole pin layout:

| Signal | Reason |
|--------|--------|
| 74HC595 control (3 pins) | 32-bit shift via I2C would take ~38ms — exceeds the loop budget |
| Resistor ladder | MCP23017 has no ADC |
| Rotary encoders | Need interrupt-rate sampling; I2C polling drops pulses |
| Potentiometers | MCP23017 has no ADC |

Everything else (29 switches, 11 ELEC/EPU LEDs) rides the 2-wire I2C bus.

### Switch Types

- `SW_ON_OFF` — 1 pin, 1 button
- `SW_ON_OFF_ON` — 2 pins, 2 buttons (center = both off)
- `SW_ROTARY` — `numPos` consecutive pins from `pin1`, `numPos` buttons (one active at a time). Used for UHF FUNCTION (4), UHF MODE (3), and AUDIO 1 COMM 1/COMM 2 MODE (3 each).

### Rotary Encoders

Six encoders on the UHF panel. A 1kHz `IntervalTimer` ISR (`encoderPollISR`) runs the quadrature state machine; the main loop drains detent deltas straight into a signed pulse queue and emits DX button pulses one at a time. The sketch does not track an absolute value — digit wrap and range limits (e.g., the 100MHz digit is only 2–3) are BMS's job, and BMS simply ignores pulses past a limit.

- `ENC_PULSE_TICKS` (4) — pulse held ~40ms at 100Hz, then a 1-tick gap before the next
- `ENC_PENDING_MAX` (30) — queue cap so fast spinning doesn't lag indefinitely

Encoders never appear in `prevBtnState` change detection; they set `lastInputTime` directly.

### Resistor Ladder — Nearest-Value Matching

The ECM PCB is fixed (10kΩ chain + 20kΩ pulldown), and its top values sit only 28 counts apart. `processAnalogButtons()` therefore picks the **closest** value rather than testing tolerance windows, which makes overlapping windows structurally impossible. Combined with 8× oversampling (~±2 counts of noise), the worst pair (FRM/SPL) keeps a ±14 count margin.

`maxDist` rejects readings that match nothing (idle ADC ≈ 0).

> Values are calibrated for **10-bit** ADC. Switching to `analogReadResolution(12)` requires scaling `ecmBtnValues[]` and `maxDist` by 4.

### MCP23017 Output Batching

`mcpWritePin()` only updates a cached port byte and sets a dirty flag; `mcpFlushOutputs()` writes each changed port once per loop. All 8 ELEC LEDs live on the GPB port of `0x21`, so a full LED update costs **one** I2C write instead of eight.

LEDs are sourced (cathode common to GND), so the binding limit is **VDD inflow 125mA**, not the VSS 150mA figure. `0x21` carries 11 LEDs (ELEC 8 + EPU 3) — keep each at or below **10mA** (11 × 10 = 110mA).

### Protocol Auto-Detection

- **BMS-BIOS**: sync `0xAA 0xBB`, **16-byte frames** (ledBits 4 + srData 4 + uhfFreq 4 + uhfPreset 1 + XOR). `BiosHandler/BmsBiosParser.h`
  - **Both devices receive this same frame**; LEFT_AUX_MISC uses only `ledBits` and ignores the rest. `BB_FRAME_PAYLOAD` must stay identical in both `BmsBiosParser.h` files — if you change the frame, re-flash **both** boards.
  - Source: BMS `FlightData2.uhf_panel_frequency` (offset **+52**, kHz) and `uhf_panel_preset` (offset **+48**). The bridge zeroes a frequency outside 100000–999999 so the panel shows dashes.
- **DCS-BIOS**: sync `0x55 ×4`, address/count/data chunks. `BiosHandler/DcsBiosParser.h`
- 3-second heartbeat timeout triggers protocol reset and re-detection
- All LEDs off when the bridge goes offline

`ledBits` byte 2 (bits 16–23) carries the backlight PWM brightness. DCS uses `LIGHT_INST_PNL` (0x4484) directly on Teensy.

### Backlight (PWM Dimming)

Pin 13 drives a MOSFET gate via 1kΩ resistor (10kΩ pulldown to GND). On-board LED mirrors backlight state. Powered by a **separate 12V adapter**, not USB — the adapter GND must be tied to Teensy GND at a single point or the MOSFET has no valid gate reference.

**Brightness control by source:**

| Source | How | Detail |
|--------|-----|--------|
| BMS | Bridge sends PWM in `ledBits` byte 2 | Adaptive: DIM(instrLight=1)→PWM 255 by default; if BRT(=2) ever received, DIM drops to 50, BRT=255. instrLight=0→OFF |
| DCS | Teensy direct | `LIGHT_INST_PNL` (0x4484) 0–65535 → `>>8` → PWM 0–255 |
| Offline manual | UHF STATUS (held) + TF pot | `checkManualBacklight()` — 10-bit ADC → 8-bit PWM |
| Idle auto-off | 30 min no input while offline | `backlightIdleOff` flag, any input restores |
| USB suspend | SOF silence >50ms | All LEDs + backlight off, `wfi` sleep |

### USB Suspend Detection

SOF-based via `USB1_FRINDEX`. No frame change for 50ms → suspended. All LEDs and backlight off, CPU enters `wfi`. On resume the welcome ceremony runs at the next input change.

### UHF 7-Segment Display (MAX7219)

8 × 0.36" common-cathode digits on the UHF panel — 6 for frequency (decimal point on DIG2) and 2 for the preset channel. Board: `f-16-cockpit-uhf-radio-panel/display/pcb`, driven through a 74AHCT125 level shifter from 5 V.

**It uses no edge pins.** The Teensy 4.1 SD-card interface on the underside carries SPI2, broken out with an SD extension cable:

| Teensy | SPI2 | J1 |
|---|---|---|
| 43 | MOSI2 | DIN |
| 45 | SCK2 | CLK |
| 44 | CS2 | CS (toggled in software) |

Toggle the whole feature with `HAS_UHF_DISPLAY` in the sketch. `displayFrequency()` falls back to dashes outside 100000–999999 kHz, and the panel shows dashes whenever the bridge is offline (`resetProtocol()`), blanking only on USB suspend. Writes are cached per digit, so a steady display costs no SPI traffic.

⚠ These pins are shared with the microSD socket — an SD card cannot be used on this board.

### Key Files

| File | Purpose |
|------|---------|
| `F16_LEFT_CONSOLE.ino` | Config arrays, MCP23017/74HC595/encoder drivers, processing, protocol detection, main loop |
| `BiosHandler/DcsBiosParser.h` | DCS-BIOS frame parser + F-16C ELEC/ECM/backlight address map |
| `BiosHandler/BmsBiosParser.h` | BMS-BIOS frame parser (packed LED bitfield + SR bitfield + backlight + UHF display) |
| `Display/Max7219Display.h` | UHF 7-segment display driver (MAX7219 over SPI2) |
| `name.c` | USB device name override |
| `backup/` | Pre-expansion Teensy 4.0 version |
| `../tools/patch_usb_desc_h.py` | Auto-patch `usb_desc.h` after IDE update (JOYSTICK_SIZE + PID) |
| `../tools/patch_usb_desc_c.py` | Auto-patch `usb_desc.c` HID slider descriptor |
| `../docs/teensyduino_upgrade.md` | Manual upgrade guide for both files |

## Key Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `BAUDRATE` | 1000000 | Serial baud (USB CDC, nominal) |
| `ALLOW_DEBUG` | false | Serial debug output |
| `LOOP_DELAY_MS` | **10** | 100Hz main loop — raised from 50ms for encoder pulse throughput |
| `SERIAL_TIMEOUT` | 3 | Seconds before protocol reset |
| `BACKLIGHT_PIN` | **13** | MOSFET gate (PWM). 온보드 LED가 상태 표시등. Circuit: Drain←LED-RTN, Source→GND, Gate←1kΩ←pin13, Gate→10kΩ→GND |
| `IDLE_TIMEOUT_MS` | 30 min | Offline idle before backlight auto-off |
| `PIN_UHF_STATUS` | **41** | Manual backlight trigger (active-low, held) |
| `PIN_POT_TF` | **A4 (18)** | Manual backlight brightness source (offline only) |
| `MCP_WIRE` | `Wire2` | SCL2 = 24, SDA2 = 25 |
| `MCP_I2C_CLOCK` | 100000 | Standard Mode — 데이지 체인 `I1`→`I2`→`I3` 단일 버스. 풀업 4.7kΩ ×3 병렬 ≈ 1.57kΩ, 체인 총 용량 ≈ 265pF → tr ≈ 352ns (400kHz 규격 300ns 초과, 100kHz 여유) |
| `ENC_PULSE_TICKS` | 4 | DX pulse width (~40ms) |
| `USB_SUSPEND_THRESHOLD_MS` | 50 | SOF silence threshold |

## Conventions

- Mixed Korean (comments/docs) and English (code/identifiers)
- Switch wiring: active-low with `INPUT_PULLUP` (pressed = LOW = logical ON)
- MCP pin numbering: GPA0–7 = 0–7, GPB0–7 = 8–15
- New switch: add to `switches[]`. New encoder: `encoders[]`. New pot: `pots[]` + a free `JoyAxis`
- New ELEC LED: `leds[]` + `LedIdx` enum. New ECM LED: `ecmSrLedNames[]` + `srMap[]`
- Extreme joystick (`JOYSTICK_SIZE 64`) exposes 6 named axes + `slider(1..17)` — but only 8 axes (6 named + 2 sliders) are visible to DirectInput/joy.cpl due to the `usb_desc.c` HID patch. 10 pots total: 7 BMS-bindable (axes 1–7), 3 DirectInput-invisible (slider 3–4)

## Constraints to Watch

- **74HC595 is at 32/32.** Adding a chip overflows the BMS-BIOS `srData` 32-bit field and requires changing `BB_FRAME_PAYLOAD`, both `BmsBiosParser.h` files, and `bmsbios_bridge.py`.
- **Peak current**: `welcomeCeremony()` lights all 32 SR LEDs plus every entry in `leds[]` (8 ELEC + 3 EPU + JFS RUN) at once. Two separate ceilings apply, and the tighter one is not USB:
  - **Teensy 3.3V regulator (~250mA, PJRC guidance)** — the 74HC595s and all MCP23017s are fed from this single rail, so full illumination (~430mA) exceeds it. A USB 3.0 port does not help. Stagger the blink phase, or move the '595s to **74HCT595 on 5V/Vin** (HCT's VIH is 2.0V, so 3.3V logic still drives it; recalculate the LED series resistors).
  - **USB 2.0 port (500mA)** — the ~548mA total peak also exceeds this.
  - **74HC595 package (~70mA/chip)** — normal operation lights 2 of 8 outputs per chip (~20mA), but the ceremony and the `ALL_LIT` ECM state light all 8.
- **Teensy pin 13** is shared with the on-board LED. As an *output* that is its native role — both stages use it for the backlight MOSFET, so the LED mirrors backlight state. Avoid using it as an *input*: the LED path can pull it below VIH and make it read permanently pressed.

## Pin Assignment

See `docs/LEFT_CONSOLE_PIN_TREE.md` for the cable/panel wiring tree, and `docs/PIN_ASSIGNMENT.md` for the full pin table, MCP GPIO map, encoder ranges, DX button map, per-panel wiring, and power topology.
