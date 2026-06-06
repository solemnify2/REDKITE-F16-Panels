# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Teensy 4.0-based USB joystick controller for F-16 ELEC + ECM panels. Supports Falcon BMS (BMS-BIOS) and DCS World (DCS-BIOS) with automatic protocol detection for LED synchronization. Part of the Redkite Project.

## Build & Upload

- **IDE**: Arduino IDE with [Teensyduino](https://www.pjrc.com/teensy/td_download.html)
- **Board**: Teensy 4.0
- **USB Type**: Serial + Keyboard + Mouse + Joystick
- **PID**: `0x048E` (set in `usb_desc.h`)
- **JOYSTICK_SIZE**: 12 (default) is sufficient (17 buttons). `JOYSTICK_SIZE > 12` triggers a build warning.
- **Upload**: Open `REDKITE_F16_ELEC_ECM_AVTR.ino` in Arduino IDE and Upload

## Architecture

Single `.ino` file structure (`REDKITE_F16_ELEC_ECM_AVTR.ino`):

### Data-Driven Hardware Configuration

All hardware is declared in config arrays under the **HARDWARE CONFIGURATION** section. To add/remove hardware, only edit these arrays:

- `switches[]` — digital switches (direct Teensy pins, 6 switches: ECM 4 + ELEC 2)
- `analogBtnArrays[]` — resistor ladder button groups (ECM 8-button on A9)
- `leds[]` — ELEC panel LEDs (direct GPIO, 8 LEDs, indexed by `LedIdx` enum)
- `ecmSrLedNames[]` / `srMap[]` — ECM panel LEDs (74HC595 shift registers, 32 outputs)

Joystick button numbers are auto-assigned at runtime (button 1 onwards).

### 74HC595 Shift Register Driver

4 daisy-chained 74HC595 chips drive 32 ECM panel LEDs. Each ECM group (1-6, FRM, SPL) has 4 LEDs (S, A, F, T). `srMap[]` remaps logical LED index to physical SR output (PCB wiring doesn't follow standard shift order). Control functions: `srWrite(idx, state)`, `srFlush()`, `srClear()`.

### Protocol Auto-Detection

Teensy receives serial bytes and auto-detects the protocol:
- **BMS-BIOS**: sync `0xAA 0xBB`, 7-byte frames with XOR checksum. Parsed by `BiosHandler/BmsBiosParser.h`.
- **DCS-BIOS**: sync `0x55 x4`, address/count/data chunks. Parsed by `BiosHandler/DcsBiosParser.h`.
- 3-second heartbeat timeout triggers protocol reset and re-detection.
- All LEDs off on bridge offline.

### USB Suspend Detection

SOF-based suspend detection using `USB1_FRINDEX`. When PC enters sleep, USB SOF packets stop — if no frame change for 50ms, Teensy considers USB suspended. On suspend: all LEDs off (GPIO + SR), CPU enters `wfi` sleep. On resume: welcome ceremony runs on next input change.

### Welcome Ceremony

ECM LED column-by-column sweep (S→A→F→T, 500ms per column, previous column off) + ELEC LED sequence + blink. Runs on: startup, USB resume (on input change), bridge online (offline→online transition).

### Key Files

| File | Purpose |
|------|---------|
| `REDKITE_F16_ELEC_ECM_AVTR.ino` | Main sketch: config arrays, 74HC595 driver, switch/analog processing, protocol detection, main loop |
| `BiosHandler/DcsBiosParser.h` | DCS-BIOS frame parser + F-16C ELEC/ECM address map |
| `BiosHandler/BmsBiosParser.h` | BMS-BIOS frame parser (packed LED bitfield) |
| `name.c` | USB device name override ("REDKITE F16 ELEC ECM AVTR") |

## Key Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `BAUDRATE` | 1000000 | Serial baud rate (USB CDC, rate is nominal) |
| `ALLOW_DEBUG` | false | Set true for serial debug output |
| `LOOP_DELAY_MS` | 50 | Main loop interval (20Hz) |
| `SERIAL_TIMEOUT` | 3 | Seconds before protocol reset on no data |
| `USB_SUSPEND_THRESHOLD_MS` | 50 | SOF silence threshold for suspend detection |

## Conventions

- Mixed Korean (comments) and English (code/identifiers)
- Switch wiring: active-low with INPUT_PULLUP (pressed = LOW = logical ON)
- New switch: add to `switches[]`. New analog ladder: add to `analogBtnArrays[]`
- New ELEC LED: add to `leds[]` + `LedIdx` enum. New ECM LED: add to `ecmSrLedNames[]` + `srMap[]`
- Resistor ladder calibration: set `ALLOW_DEBUG = true`, read serial monitor, adjust `values[]`
