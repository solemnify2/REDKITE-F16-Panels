# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Teensy 4.1-based USB joystick controller for an F-16 cockpit sim panel (Falcon BMS + DCS World). Handles switches, LEDs, analog inputs (resistor ladders, pots, pedals), MCP23017 I2C expansion, and backlight control. Python bridges relay sim data to Teensy over serial for LED synchronization.

## Build & Upload

- **IDE**: Arduino IDE with [Teensyduino](https://www.pjrc.com/teensy/td_download.html)
- **Board**: Teensy 4.1
- **USB Type**: Serial + Keyboard + Mouse + Joystick
- **Libraries**: `Wire`, `Keyboard` (both built-in)
- **Extreme Joystick**: Before building, set `JOYSTICK_SIZE 64` in `%LOCALAPPDATA%\Arduino15\packages\teensy\hardware\avr\<version>\cores\teensy4\usb_desc.h` for 128-button support
- **Upload**: Open `F16_LEFT_AUX_MISC.ino` in Arduino IDE and Upload

### Python Bridges

```
pip install pyserial
python ../tools/bmsbios_bridge.py             # Falcon BMS (COM port auto-detect)
python ../tools/dcsbios_bridge.py             # DCS World (COM port auto-detect, also needs DCS-BIOS installed)
```

## Architecture

### Data-Driven Hardware Configuration

All hardware is declared in config arrays in `F16_LEFT_AUX_MISC.ino` under the **HARDWARE CONFIGURATION** section (~line 99-244). To add/remove hardware, only edit these arrays:

- `switches[]` — digital switches (direct Teensy pins or MCP23017)
- `analogBtnArrays[]` — resistor ladder button groups (one analog pin per group)
- `pots[]` — potentiometers mapped to joystick axes
- `leds[]` — LEDs (direct or MCP23017), indexed by `LedIdx` enum
- `mcpDevices[]` — MCP23017 I2C expanders (addr 0x20-0x27)

Joystick button numbers are auto-assigned at runtime. `mcpIdx = -1` means direct Teensy pin; `>= 0` indexes into `mcpDevices[]`.

### Protocol Auto-Detection

Teensy receives serial bytes and auto-detects the protocol:
- **BMS-BIOS**: sync `0xAA 0xBB`, **16-byte frames** (ledBits 4 + srData 4 + uhfFreq 4 + uhfPreset 1 + XOR). Parsed by `BiosHandler/BmsBiosParser.h`.
  - The bridge sends one unified frame to every device. This board uses only `ledBits`; `srData` (console ECM shift register) and `uhf*` (console UHF 7-segment display) are parsed and discarded.
  - ⚠ `BB_FRAME_PAYLOAD` must stay identical to `F16_LEFT_CONSOLE/BiosHandler/BmsBiosParser.h`. Changing the frame means re-flashing **both** boards — and flash the boards *before* updating the bridge, or the old firmware will reject every frame on the checksum.
- **DCS-BIOS**: sync `0x55 x4`, address/count/data chunks. Parsed by `BiosHandler/DcsBiosParser.h`.
- 6-second heartbeat timeout triggers protocol reset and re-detection.

The parsers call `writeLed()` and `setBacklightBrightness()` to control hardware. When offline, `updateLedsOffline()` simulates gear LEDs based on switch state.

### Key Files

| File | Purpose |
|------|---------|
| `F16_LEFT_AUX_MISC.ino` | Main sketch: config arrays, MCP23017 driver, switch/analog/pedal processing, protocol detection, main loop |
| `BiosHandler/DcsBiosParser.h` | DCS-BIOS frame parser + F-16C address map (addresses from `F-16C_50.json`) |
| `BiosHandler/BmsBiosParser.h` | BMS-BIOS frame parser (reads packed LED bitfield) |
| `tools/bmsbios_bridge.py` | Python: reads BMS shared memory (`FalconSharedMemoryArea`), sends binary frames to Teensy |
| `tools/dcsbios_bridge.py` | Python: receives DCS-BIOS UDP multicast, forwards changed frames to Teensy serial |
| `name.c` | USB device name override |

### MCP23017 I2C Expansion

MCP23017 chips add 16 GPIO pins each over I2C. Used for MISC panel (addr 0x20). Pins are configured as input (pull-up) for switches or output for LEDs automatically based on `leds[]` array entries. Star topology with LAN cables; hotplug supported with 500ms reconnect polling.

### USB Suspend Detection

SOF(Start-of-Frame)-based suspend detection using `USB1_FRINDEX`. When PC enters sleep, USB SOF packets stop — if no frame change for 50ms, Teensy considers USB suspended. On suspend: all LEDs off, backlight off, CPU enters `wfi` (Wait For Interrupt) sleep. On resume: welcome ceremony runs automatically.

### Backlight Control (PWM Dimming)

Step-Up converter (5V→12V) controlled via MOSFET on `BACKLIGHT_PIN` (pin 13, PWM 1kHz).

**Brightness control by source:**

| Source | How | Detail |
|--------|-----|--------|
| BMS | Bridge sends PWM in `ledBits` byte 2 | bits 16~23 = brightness 0~255 |
| DCS | Teensy direct | `LIGHT_INST_PNL` (0x4484) 0–65535 → `>>8` → PWM 0–255 |
| Offline manual | DN LOCK REL (held) + HMCS Symbology pot | A15, reversed (CW=dark, CCW=bright) |
| Idle auto-off | 30 min no input while offline | `backlightIdleOff` flag, any input restores |
| USB suspend | SOF silence >50ms | All LEDs + backlight off, `wfi` sleep |

Bridge reconnect always restores backlight and triggers welcome ceremony.

### Welcome Ceremony

LED sweep animation runs on: startup, USB resume from suspend, bridge online (offline→online transition), idle wake, and MCP23017 reconnect.

## Key Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `BAUDRATE` | 1000000 | Serial baud rate (USB CDC, rate is nominal) |
| `ALLOW_DEBUG` | false | Set true for serial debug output (analog calibration, switch states) |
| `LOOP_DELAY_MS` | 50 | Main loop interval (20Hz) |
| `SERIAL_TIMEOUT` | 6 | Seconds before protocol reset on no data |
| `BACKLIGHT_PIN` | **13** | MOSFET gate (PWM 1kHz). Step-Up 5V→12V 제어 |
| `IDLE_TIMEOUT_MS` | 30 min | Offline idle before backlight auto-off |
| `SW_IDX_DN_LOCK_REL` | 13 | Manual backlight modifier key (switches[] index) |
| `USB_SUSPEND_THRESHOLD_MS` | 50 | SOF silence threshold for suspend detection |

## Conventions

- The project language is mixed Korean (comments/README) and English (code/identifiers)
- Switch pin wiring uses active-low with INPUT_PULLUP (pressed = LOW = logical ON)
- MCP pin numbering: GPA0-7 = 0-7, GPB0-7 = 8-15
- Resistor ladder calibration: set `ALLOW_DEBUG = true`, read serial monitor, adjust `values[]` arrays
- `stateRef` in `SwitchDef` links a switch's state to a variable used by other logic (e.g., pedal brake mode, offline gear LED sim, manual backlight control)
- `SW_ON_OFF_ON` state values: -1 (pin1 active), 0 (center/off), 1 (pin2 active)
- Pedal calibration reset: hold both pedals + DN LOCK REL for 2 seconds
- DN LOCK REL (switches[13]) is used as a modifier key for special combos (pedal cal reset, manual backlight)

## Pin Assignment

See `docs/LEFT_AUX_PIN_TREE.md` for the cable tree, full Teensy pin map, MCP GPIO map, DX button map, joystick axes, the CMDS lamp wiring, and the build checklist. Pin 27 conflict (Gear Warn LED vs HMCS Brightness A13) has been resolved — Gear Warn LED moved to pin 12.

All 42 header pins are used. The six CMDS lamps hang off the **bottom microSD pads (42–47)**, broken out with an SD extension cable — no soldering, no header pins consumed.

### CMDS EWS Lamps

Six LEDs driven 1:1 from pins 42–47 (`HIGH` = lit, individual series resistor, cathodes to the SD connector GND). BMS supplies only three signals, so `AUX_LED_MAP` in the bridge maps one bit to several `leds[]` indices — NO GO to two, RDY to three — and a group always lights together.

| Lamp | LEDs | Pins | `lightBits2` (offset 124) |
|---|---|---|---|
| GO | 1 | 42 | `Go` `0x40` |
| NO GO | 2 | 43, 44 | `NoGo` `0x80` |
| RDY | 3 | 45, 46, 47 | `Rdy` `0x200` |

Keep LED Vf under ~3.0 V — these run straight off 3.3 V logic, same as the GEAR/TWA LEDs. DCS-BIOS does not drive these yet.
