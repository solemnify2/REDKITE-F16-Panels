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
- **Libraries**: `Wire`, `Keyboard` (both built-in to Teensyduino)
- **Extreme Joystick (LEFT_AUX_MISC only)**: Set `JOYSTICK_SIZE 64` in `%LOCALAPPDATA%\Arduino15\packages\teensy\hardware\avr\<version>\cores\teensy4\usb_desc.h` before building. The sketch enforces this with `#if JOYSTICK_SIZE < 64 #error`.
- **Upload**: Open the `.ino` file in Arduino IDE and Upload

### Python Bridges

Located in `Bios/`. COM port auto-detect by VID/PID (VID `0x16C0`):
```
pip install pyserial
python Bios/bmsbios_bridge.py               # Falcon BMS (auto-detect)
python Bios/dcsbios_bridge.py               # DCS World (auto-detect)
```

## Architecture Patterns (Shared Across Sketches)

### Sim Data Flow

**Falcon BMS** — bridge가 공유 메모리를 polling:
```
Falcon BMS → FalconSharedMemoryArea (Shared Memory)
                    ↑ polling (20Hz)
          bmsbios_bridge.py (변경분만 전송 + 주기적 heartbeat)
                    ↓
              Teensy Serial
```

**DCS World** — 게임이 UDP로 push:
```
DCS World (Lua export) → UDP multicast 239.255.50.10:5010
                              ↓
                    dcsbios_bridge.py (그대로 포워딩)
                              ↓
                        Teensy Serial
```
- DCS-BIOS는 초기 접속 시 전체 상태 덤프, 이후 변경분만 delta update
- 전체 주소 공간을 여러 프레임에 나눠 순회하며, 한 바퀴 완료 시 sync frame(`0x5555 0x5555`) 전송
- bridge는 필터링 없이 전체 UDP 패킷을 모든 Teensy에 포워딩 (각 Teensy가 관심 주소만 파싱)

### Data-Driven Hardware Config
All hardware is declared in config arrays in the `HARDWARE CONFIGURATION` section of each `.ino`. To add/remove hardware, only edit these arrays — joystick button numbers are auto-assigned at runtime:
- `switches[]` — digital switches (active-low, INPUT_PULLUP)
- `analogBtnArrays[]` — resistor ladder button groups
- `leds[]` — LED outputs
- `mcpDevices[]` — MCP23017 I2C expanders (LEFT_AUX_MISC only)
- `pots[]` — potentiometers/axes (LEFT_AUX_MISC only)

### Protocol Auto-Detection (Serial)
Both sketches detect the sim protocol from incoming serial bytes:
- **BMS-BIOS**: sync `0xAA 0xBB`, 7-byte frames (parsed by `BiosHandler/BmsBiosParser.h`)
- **DCS-BIOS**: sync `0x55 x4`, address/count/data chunks (parsed by `BiosHandler/DcsBiosParser.h`)
- Heartbeat timeout (3-6 sec) resets to unknown, enabling sim switching without reboot

### LED Output Architecture
- **LEFT_AUX_MISC**: Direct GPIO pins + MCP23017 I2C pins, indexed by `LedIdx` enum
- **LEFT_CONSOLE**: Direct GPIO (ELEC) + 74HC595 daisy-chain shift registers (ECM 32 LEDs)

## Conventions

- Mixed Korean (comments, README, docs) and English (code identifiers, CLAUDE.md)
- Switch wiring: active-low with INPUT_PULLUP (pressed = LOW = logical ON)
- `mcpIdx = -1` means direct Teensy pin; `>= 0` indexes into `mcpDevices[]`
- MCP23017 pin numbering: GPA0-7 = 0-7, GPB0-7 = 8-15
- Resistor ladder calibration: set `ALLOW_DEBUG = true`, read serial monitor, adjust `values[]` arrays
- `SW_ON_OFF_ON` state values: -1 (pin1 active), 0 (center/off), 1 (pin2 active)
- `name.c` in each sketch folder overrides the USB device name

## Reference Docs

- `docs/` — wiring diagrams, panel specs, protocol reference, pin assignments (all panels)
- `docs/PIN_ASSIGNMENT.md` — LEFT_CONSOLE pin mapping and joystick button layout
- `F4TS/` — legacy F4ToSerial app (replaced by BMS-BIOS in current version)
- `Custom Stick/` — reference files for Teensyduino USB descriptor customization
