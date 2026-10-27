# 프로토콜 레퍼런스

## 1. DCS-BIOS (DCS World F-16C_50)

**Source:** DCS-BIOS `F-16C_50.json`
- 로컬: `%USERPROFILE%\Saved Games\DCS\Scripts\DCS-BIOS\doc\json\F-16C_50.json`
- 웹: http://localhost:5010/reference/ (DCS 실행 중)

**Protocol:**
- Binary, sync `0x55` ×4
- 반복 청크: `ADDR_LO ADDR_HI COUNT_LO COUNT_HI DATA[count]`
- 프레임 종료: addr=0x5555, count=0x5555
- Baud: 1,000,000

**LED Address Map** (DcsBiosParser.h):

| Identifier | Addr(hex) | Mask | Bit | Description |
|---|---|---|---|---|
| LIGHT_GEAR_N | 0x447A | 0x4000 | 14 | Nose Gear (green) |
| LIGHT_GEAR_L | 0x447A | 0x8000 | 15 | Left Gear (green) |
| LIGHT_GEAR_R | 0x447C | 0x0001 | 0 | Right Gear (green) |
| LIGHT_GEAR_WARN | 0x447C | 0x0002 | 1 | Gear Warning (red) |
| LIGHT_RWR_SEARCH | 0x447E | 0x0400 | 10 | TWA Search |
| LIGHT_RWR_ACTIVITY | 0x447E | 0x0800 | 11 | TWA Activity |
| LIGHT_RWR_ACT_POWER | 0x447E | 0x1000 | 12 | TWA Act/Power |
| LIGHT_RWR_ALT_LOW | 0x447E | 0x2000 | 13 | TWA Alt Low |
| LIGHT_ECM | 0x4544 | 0x4000 | 14 | ECM Indicator |
| LIGHT_CONSLES | 0x4482 | 0xFFFF | - | Console Lighting (0–65535) |
| LIGHT_INST_PNL | 0x4484 | 0xFFFF | - | Instrument Panel Lighting (0–65535) |

**ECM LED Address Map** (74HC595, 32 outputs):

| Addr(hex) | Bits | LEDs |
|---|---|---|
| 0x4480 | 13–15 | ECM 1 S/A/F |
| 0x448A | 0–15 | ECM 1T, 2–5 S/A/F/T |
| 0x448C | 0–12 | ECM 5T, 6 S/A/F/T, FRM S/A/F/T, SPL S/A/F/T |

**UHF Display** (string outputs):

| Identifier | Addr(hex) | Type | Length | Description |
|---|---|---|---|---|
| UHF_CHAN_DISP | 0x45B0 | string | 2 | UHF Channel Display (" 1"~"20") |
| UHF_FREQ_DISP | 0x45B2 | string | 7 | UHF Manual Frequency Display ("305.000") |

## 2. BMS-BIOS (Falcon BMS 4.38)

**Source:** `C:\Falcon BMS 4.38\Tools\SharedMem\FlightData.h`

**Protocol:**
- Binary, sync `0xAA 0xBB`
- Payload 13바이트:
  - `ledBits` (uint32 LE, 4B) — bits 0–11: LED states, bits 16–23: console backlight PWM, bits 24–31: instr panel backlight PWM
  - `srData` (uint32 LE, 4B) — ECM 시프트 레지스터 32비트
  - `uhfFreq` (uint32 LE, 4B) — UHF 주파수 (kHz)
  - `uhfPreset` (uint8, 1B) — UHF 프리셋 채널 (1–20)
- Checksum: XOR of 13 payload bytes (1B)
- Total: **16 bytes** per frame (sync 2 + payload 13 + checksum 1)
- Baud: 1,000,000

**Shared Memory:**

| 영역 | 오프셋 | 타입 | 필드 | 설명 |
|---|---|---|---|---|
| FalconSharedMemoryArea | 108 | uint | lightBits | LED 상태 비트맵 |
| | 124 | uint | lightBits2 | LED 상태 비트맵 2 |
| | 128 | uint | lightBits3 | LED 상태 비트맵 3 |
| FalconSharedMemoryArea2 | 1104 | uchar | instrLight | 백라이트 (0=OFF, 1=DIM, 2=BRT) |
| | 48 | int | uhf_panel_preset | UHF 채널 프리셋 |
| | 52 | int | uhf_panel_frequency | UHF 주파수 (kHz) |
| | 1168 | uchar | floodConsole | Flood/console 조명 (0~6) — 패널 백라이트와 다른 조명, 미사용 |
| | 1180 | uint[5] | ecmBits | ECM 프로그램 상태 ×5 |

**LightBits Mask Map** (bmsbios_bridge.py):

LightBits (offset 108):

| Name | Mask | Bit | Description |
|---|---|---|---|
| AdvStandby | 0x80000000 | 31 | ADV Standby indicator |

LightBits2 (offset 124):

| Name | Mask | Bit | Description |
|---|---|---|---|
| AuxSrch | 0x00001000 | 12 | TWA Search |
| AuxAct | 0x00002000 | 13 | TWA Activity |
| AuxLow | 0x00004000 | 14 | TWA Alt Low |
| AuxPwr | 0x00008000 | 15 | TWA Power |
| EcmPwr | 0x00010000 | 16 | ECM power indicator |
| EPUOn | 0x00100000 | 20 | EPU RUN light |
| JFSOn | 0x00200000 | 21 | JFS RUN light |
| AdvActive | 0x20000000 | 29 | ADV Active indicator |
| GEARHANDLE | 0x40000000 | 30 | Gear handle lamp |

LightBits3 (offset 128):

| Name | Mask | Bit | Description |
|---|---|---|---|
| FlcsPmg | 0x00000001 | 0 | FLCS PMG |
| MainGen | 0x00000002 | 1 | MAIN GEN |
| StbyGen | 0x00000004 | 2 | STBY GEN |
| EpuGen | 0x00000008 | 3 | EPU GEN |
| EpuPmg | 0x00000010 | 4 | EPU PMG |
| ToFlcs | 0x00000020 | 5 | BATT TO FLCS |
| FlcsRly | 0x00000040 | 6 | FLCS RLY |
| BatFail | 0x00000080 | 7 | BATT FAIL |
| Hydrazine | 0x00000100 | 8 | EPU HYDRAZN |
| Air | 0x00000200 | 9 | EPU AIR |
| NoseGearDown | 0x00010000 | 16 | Nose gear down and locked |
| LeftGearDown | 0x00020000 | 17 | Left gear down and locked |
| RightGearDown | 0x00040000 | 18 | Right gear down and locked |

## 3. LED Index Mapping — Left Aux + MISC (0x0489)

| Index | Name | Pin | Location | DCS-BIOS | BMS LightBit |
|---|---|---|---|---|---|
| 0 | Nose Gear | 30 | direct | 0x447A bit14 | LB3 NoseGearDown |
| 1 | Left Gear | 31 | direct | 0x447A bit15 | LB3 LeftGearDown |
| 2 | Right Gear | 32 | direct | 0x447C bit0 | LB3 RightGearDown |
| 3 | Gear Warn | 27 | direct | 0x447C bit1 | LB2 GEARHANDLE |
| 4 | TWA Power | 34 | direct | 0x447E bit12 | LB2 AuxPwr |
| 5 | TWA Low | 35 | direct | 0x447E bit13 | LB2 AuxLow |
| 6 | TWA Search | 36 | direct | 0x447E bit10 | LB2 AuxSrch |
| 7 | TWA Act | 37 | direct | 0x447E bit11 | LB2 AuxAct |
| 8 | ECM | MCP0:7 | MCP 0x20 | 0x4544 bit14 | LB2 EcmPwr |
| 9 | ADV Active | MCP0:8 | MCP 0x20 | 0x447E bit2 | LB2 AdvActive |
| 10 | ADV Standby | MCP0:9 | MCP 0x20 | 0x447E bit3 | LB AdvStandby |

## 4. LED Index Mapping — Left Console (0x048E)

| ledBits | Name | Location | BMS LightBit | DCS-BIOS |
|---|---|---|---|---|
| 0 | FLCS PMG | MCP 0x21 PA0 | LB3 FlcsPmg 0x00000001 | 0x447C bit9 |
| 1 | MAIN GEN | MCP 0x21 PA1 | LB3 MainGen 0x00000002 | 0x447C bit10 |
| 2 | STBY GEN | MCP 0x21 PA2 | LB3 StbyGen 0x00000004 | 0x447C bit11 |
| 3 | EPU GEN | MCP 0x21 PA3 | LB3 EpuGen 0x00000008 | 0x447C bit13 |
| 4 | EPU PMG | MCP 0x21 PA4 | LB3 EpuPmg 0x00000010 | 0x447C bit14 |
| 5 | FLCS RLY | MCP 0x21 PA5 | LB3 FlcsRly 0x00000040 | 0x447E bit0 |
| 6 | BATT FAIL | MCP 0x21 PA6 | LB3 BatFail 0x00000080 | 0x447E bit1 |
| 7 | BATT TO FLCS | MCP 0x21 PA7 | LB3 ToFlcs 0x00000020 | 0x447C bit15 |
| 8 | EPU HYDRAZN | MCP 0x22 GPA7 | LB3 Hydrazine 0x00000100 | 0x447C bit6 |
| 9 | EPU AIR | MCP 0x21 PB4 | LB3 Air 0x00000200 | 0x447C bit7 |
| 10 | EPU RUN | MCP 0x22 GPA7 | LB2 EPUOn 0x00100000 | 0x447C bit8 |
| 11 | JFS RUN | Teensy pin 26 | LB2 JFSOn 0x00200000 | 0x447C bit5 |

Backlight 2원화:
- `ledBits` byte 2 (bits 16–23) = console backlight PWM → pin 13 (양쪽 보드)
- `ledBits` byte 3 (bits 24–31) = instr panel backlight PWM → pin 12 (LEFT_AUX_MISC only, MISC 패널)
- Bridge: `instrLight` 0→OFF, 1→DIM(255 or 50), 2→BRT(255). BMS는 소스가 하나라 두 채널 동일 값.
- DCS: `LIGHT_CONSLES`(0x4482) → pin 13, `LIGHT_INST_PNL`(0x4484) → pin 12.
- Offline 수동 조절: AUX = DN LOCK REL + HMCS pot (양쪽 동시), 콘솔 = UHF TEST + STATUS + VOL.

`srData`: uint32, ECM 32 LED (74HC595). FlightData2 `ecmBits[5]`에서 생성.

## 5. 프로토콜 자동 감지

Teensy는 수신된 sync 바이트로 프로토콜을 자동 판별합니다:
- `0x55` ×4 연속 → **DCS-BIOS**
- `0xAA` → `0xBB` → **BMS-BIOS**
- 타임아웃 (AUX 6초 / 콘솔 3초) → UNKNOWN으로 리셋, 재감지
