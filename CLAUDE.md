# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Redkite Project: a collection of Teensy-based USB joystick controllers for an F-16 cockpit simulator. Each subfolder is an independent Arduino sketch targeting a specific panel group. Supports Falcon BMS and DCS World with automatic protocol detection for LED synchronization.

## Sketch Folders (Independent Projects)

| Folder | MCU | Description |
|--------|-----|-------------|
| `REDKITE_F16_LEFT_AUX_MISC/` | Teensy 4.1 | Left Aux panels (Gear, CMDS, TWA, Alt Gear) + MISC panel via MCP23017 I2C. Pedal axes, backlight, Python bridges. **Primary/most complex sketch.** |
| `REDKITE_F16_LEFT_CONSOLE/` | Teensy 4.0 | ECM panel (74HC595 shift registers for 32 LEDs, 8-button resistor ladder) + ELEC panel. Standalone, no I2C expansion. |

Each sketch has its own `CLAUDE.md` with detailed architecture — read that first when working in a specific sketch.

## Build & Upload

- **IDE**: Arduino IDE with [Teensyduino](https://www.pjrc.com/teensy/td_download.html)
- **USB Type**: Serial + Keyboard + Mouse + Joystick
- **Extreme Joystick (LEFT_AUX_MISC only)**: Set `JOYSTICK_SIZE 64` in `usb_desc.h` before building
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
