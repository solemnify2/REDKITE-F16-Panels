# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Redkite Project: a collection of Teensy-based USB joystick controllers for an F-16 cockpit simulator. Each subfolder is an independent Arduino sketch targeting a specific panel group. Supports Falcon BMS and DCS World with automatic protocol detection for LED synchronization.

## Sketch Folders (Independent Projects)

| Folder | MCU | Description |
|--------|-----|-------------|
| `F16_LEFT_AUX_MISC/` | Teensy 4.1 | Left Aux panels (Gear, CMDS, TWA, Alt Gear) + MISC panel via MCP23017 I2C. Pedal axes, backlight, Python bridges. |
| `F16_LEFT_CONSOLE/` | Teensy 4.0 / 4.1 | Left console: ECM (74HC595 ×4 for 32 LEDs, 8-button resistor ladder) + ELEC + EPU + AVTR + UHF (6 rotary encoders) + ENGINE START + MPO + AUDIO 1/2 (7 pots). MCP23017 ×3 over I2C (`0x20` `0x21` `0x22`). **Primary/most complex sketch.** Two build stages via `BOARD_REV`: `STAGE_T40` (Teensy 4.0 interim — every panel except the 6 UHF encoders, 41 buttons) and `STAGE_T41` (full, 53 buttons). Buttons 1–41 and all 7 axes are identical across both stages, so upgrading needs no BMS rebinding. |

Each sketch has its own `CLAUDE.md` with detailed architecture — read that first when working in a specific sketch.

## Build & Upload

- **IDE**: Arduino IDE with [Teensyduino](https://www.pjrc.com/teensy/td_download.html)
- **USB Type**: Serial + Keyboard + Mouse + Joystick
- **Extreme Joystick**: Set `JOYSTICK_SIZE 64` in `usb_desc.h`. **Both sketches now require 64**, so the header no longer needs editing between builds. PID differs per device (`0x0487` / `0x048E`) and is enforced by `#error` in each sketch.
- **Joystick axes**: `JOYSTICK_SIZE 64` exposes 6 named axes (X/Y/Z/Xrotate/Yrotate/Zrotate) **plus `slider(1..17)`** — 23 analog channels, not 6.
- **Upload**: Open the `.ino` file in Arduino IDE and Upload

### Python Bridges

Located in `tools/`. COM port auto-detect by VID/PID (VID `0x16C0`):
```
pip install pyserial
python tools/bmsbios_bridge.py               # Falcon BMS (auto-detect)
python tools/dcsbios_bridge.py               # DCS World (auto-detect)
```

## Conventions

- Mixed Korean (comments, README, docs) and English (code identifiers, CLAUDE.md)
- Switch wiring: active-low with INPUT_PULLUP (pressed = LOW = logical ON)
- `name.c` in each sketch folder overrides the USB device name
- Hardware is data-driven: edit config arrays (`switches[]`, `leds[]`, etc.) to add/remove hardware
