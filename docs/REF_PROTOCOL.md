# LED·디스플레이 프로토콜

이 문서는 브리지와 펌웨어 사이의 출력 데이터 형식을 정리합니다.
스위치·축 입력은 USB 조이스틱으로 전달하며, 입력 키맵은 [REF_KEYMAP.md](REF_KEYMAP.md)를 참고하십시오.

## 1. DCS-BIOS (DCS World F-16C_50)

**참조:** DCS-BIOS `F-16C_50.json`
- 로컬: `%USERPROFILE%\Saved Games\DCS\Scripts\DCS-BIOS\doc\json\F-16C_50.json`
- 웹: http://localhost:5010/reference/ (DCS 실행 중)

**전송 형식:**
- Binary, sync `0x55` ×4
- 반복 청크: `ADDR_LO ADDR_HI COUNT_LO COUNT_HI DATA[count]`
- 동기 바이트 `0x55` ×4를 감지하면 파서가 다음 주소·길이 읽기를 시작합니다.
- Baud: 1,000,000

**LED 주소** (DcsBiosParser.h):

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
| LIGHT_CMDS_NO_GO | 0x4480 | 0x0200 | 9 | CMDS NO GO (green) |
| LIGHT_CMDS_GO | 0x4480 | 0x0400 | 10 | CMDS GO (green) |
| LIGHT_CMDS_DISP | 0x4480 | 0x0800 | 11 | CMDS DISP (green) |
| LIGHT_CMDS_RDY | 0x4480 | 0x1000 | 12 | CMDS RDY (green) |
| LIGHT_CONSLES | 0x4482 | 0xFFFF | - | Console Lighting (0–65535, remap 11200–58510 → 0–255) |
| LIGHT_INST_PNL | 0x4484 | 0xFFFF | - | Instrument Panel Lighting (0–65535) |

**ECM LED 주소** (74HC595, 32 outputs):

| Addr(hex) | Bits | LEDs |
|---|---|---|
| 0x4480 | 13–15 | ECM 1 S/A/F |
| 0x448A | 0–15 | ECM 1T, 2–5 S/A/F/T |
| 0x448C | 0–12 | ECM 5T, 6 S/A/F/T, FRM S/A/F/T, SPL S/A/F/T |

**UHF 표시 데이터** (문자열):

| Identifier | Addr(hex) | Type | Length | Description |
|---|---|---|---|---|
| UHF_CHAN_DISP | 0x45B0 | string | 2 | UHF Channel Display (" 1"~"20") |
| UHF_FREQ_DISP | 0x45B2 | string | 7 | UHF Manual Frequency Display ("305.000") |

## 2. BMS-BIOS (Falcon BMS 4.38)

**참조:** `C:\Falcon BMS 4.38\Tools\SharedMem\FlightData.h`

**전송 형식:**
- Binary, sync `0xAA 0xBB`
- Payload 13바이트:
  - `ledBits` (uint32 LE, 4B) — 하위 16비트: 장치별 LED 상태, bits 16–23: console backlight PWM, bits 24–31: instr panel backlight PWM
  - `srData` (uint32 LE, 4B) — ECM 시프트 레지스터 32비트
  - `uhfFreq` (uint32 LE, 4B) — UHF 주파수 (kHz)
  - `uhfPreset` (uint8, 1B) — UHF 프리셋 채널 (1–20)
- Checksum: XOR of 13 payload bytes (1B)
- Total: **16 bytes** per frame (sync 2 + payload 13 + checksum 1)
- Baud: 1,000,000

**공유 메모리:**

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

**LightBits 마스크** (bridge.py):

LightBits (offset 108):

| Name | Mask | Bit | Description |
|---|---|---|---|
| AdvStandby | 0x80000000 | 31 | ADV Standby indicator |

LightBits2 (offset 124):

| Name | Mask | Bit | Description |
|---|---|---|---|
| Go | 0x00000040 | 6 | CMDS GO |
| NoGo | 0x00000080 | 7 | CMDS NO GO |
| Degr | 0x00000100 | 8 | AUTO DEGR (미사용) |
| Rdy | 0x00000200 | 9 | CMDS DISPENSE RDY |
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

## 3. LED 비트·핀 대응 — Left Aux + MISC (0x0487)

| ledBits | Name | Location | BMS LightBit | DCS-BIOS |
|---|---|---|---|---|
| 0 | ECM | MCP 0x20 GPA7 | `LB2_ECM_PWR` (LightBits2) | 0x4544 bit14 |
| 1 | ADV Active | MCP 0x20 GPB1 | `LB2_ADV_ACTIVE` (LightBits2) | 0x447E bit2 |
| 2 | ADV Standby | MCP 0x20 GPB0 | `LB_ADV_STANDBY` (LightBits) | 0x447E bit3 |
| 3 | Nose Gear | Teensy pin 30 | `LB3_NOSE_GEAR_DN` (LightBits3) | 0x447A bit14 |
| 4 | Left Gear | Teensy pin 31 | `LB3_LEFT_GEAR_DN` (LightBits3) | 0x447A bit15 |
| 5 | Right Gear | Teensy pin 32 | `LB3_RIGHT_GEAR_DN` (LightBits3) | 0x447C bit0 |
| 6 | Gear Warn | Teensy pin 27 | `LB_GEARHANDLE` (LightBits2) | 0x447C bit1 |
| 7 | TWA Search | Teensy pin 36 | `LB2_AUX_SRCH` (LightBits2) | 0x447E bit10 |
| 8 | TWA Act | Teensy pin 37 | `LB2_AUX_ACT` (LightBits2) | 0x447E bit11 |
| 9 | TWA Low | Teensy pin 28 | `LB2_AUX_LOW` (LightBits2) | 0x447E bit13 |
| 10 | TWA Power | Teensy pin 29 | `LB2_AUX_PWR` (LightBits2) | 0x447E bit12 |
| 11 | CMDS DISP 12 | Teensy pin 45 | `LB2_EWS_RDY` (LightBits2) | 0x4480 bit11 |
| 12 | CMDS DISP 3 | Teensy pin 46 | `LB2_EWS_RDY` (LightBits2) | 0x4480 bit11 |
| 13 | CMDS RDY | Teensy pin 47 | `LB2_EWS_RDY` (LightBits2) | 0x4480 bit12 |
| 14 | CMDS NO GO | Teensy pin 43 | `LB2_EWS_NOGO` (LightBits2) | 0x4480 bit9 |
| 15 | CMDS GO | Teensy pin 44 | `LB2_EWS_GO` (LightBits2) | 0x4480 bit10 |

> `ledBits` 비트 번호는 해당 장치의 `leds[]`/`LedIdx` 순서와 같습니다.
> 배열 순서를 바꾸면 `tools/bridge.py`의 장치별 LED 맵도 함께 수정해야 합니다.


## 4. LED 비트·핀 대응 — Left Console (0x048E)

| ledBits | Name | Location | BMS LightBit | DCS-BIOS |
|---|---|---|---|---|
| 0 | JFS RUN | Teensy pin 26 | `LB2_JFS_ON` (LightBits2) | 0x447C bit5 |
| 1 | EPU HYDRAZN | MCP 0x21 GPB3 | `LB3_HYDRAZINE` (LightBits3) | 0x447C bit6 |
| 2 | EPU AIR | MCP 0x21 GPB4 | `LB3_AIR` (LightBits3) | 0x447C bit7 |
| 3 | EPU RUN | MCP 0x22 GPA7 | `LB2_EPU_ON` (LightBits2) | 0x447C bit8 |
| 4 | FLCS PMG | MCP 0x21 GPA0 | `LB3_FLCS_PMG` (LightBits3) | 0x447C bit9 |
| 5 | MAIN GEN | MCP 0x21 GPA1 | `LB3_MAIN_GEN` (LightBits3) | 0x447C bit10 |
| 6 | STBY GEN | MCP 0x21 GPA2 | `LB3_STBY_GEN` (LightBits3) | 0x447C bit11 |
| 7 | EPU GEN | MCP 0x21 GPA3 | `LB3_EPU_GEN` (LightBits3) | 0x447C bit13 |
| 8 | EPU PMG | MCP 0x21 GPA4 | `LB3_EPU_PMG` (LightBits3) | 0x447C bit14 |
| 9 | BATT TO FLCS | MCP 0x21 GPA5 | `LB3_TO_FLCS` (LightBits3) | 0x447C bit15 |
| 10 | FLCS RLY | MCP 0x21 GPA6 | `LB3_FLCS_RLY` (LightBits3) | 0x447E bit0 |
| 11 | BATT FAIL | MCP 0x21 GPA7 | `LB3_BAT_FAIL` (LightBits3) | 0x447E bit1 |

> `ledBits` 비트 번호는 해당 장치의 `leds[]`/`LedIdx` 순서와 같습니다.
> 배열 순서를 바꾸면 `tools/bridge.py`의 장치별 LED 맵도 함께 수정해야 합니다.


### 백라이트 채널
- `ledBits` byte 2 (bits 16–23) = console backlight PWM → pin 13 (양쪽 보드)
- `ledBits` byte 3 (bits 24–31) = instr panel backlight PWM → pin 12 (LEFT_AUX_MISC only, MISC 패널)
- 브리지: `instrLight` 0→OFF, 1→DIM(255 or 50), 2→BRT(255). BMS는 소스가 하나라 두 채널 동일 값.
- DCS: `LIGHT_CONSLES`(0x4482) → pin 13 (remap 11200~58510 → 0~255), `LIGHT_INST_PNL`(0x4484) → pin 12.
- Offline 수동 조절: AUX = DN LOCK REL + HMCS pot (양쪽 동시), 콘솔 = UHF TEST + STATUS + VOL.

`srData`는 ECM 32개 LED용 비트맵입니다. 브리지가 FlightData2의 `ecmBits[5]`를 변환하고, 펌웨어는 `srMap[]`으로 실제 74HC595 출력에 대응시킵니다.

## 5. 프로토콜 자동 감지

Teensy는 수신된 sync 바이트로 프로토콜을 자동 판별합니다.

- `0x55` ×4 연속 → **DCS-BIOS**
- `0xAA` → `0xBB` → **BMS-BIOS**
- 타임아웃 (AUX 6초 / 콘솔 3초) → UNKNOWN으로 리셋, 재감지

프로토콜 타임아웃은 현재 수신 처리 기준입니다. 정상 프레임 여부를 별도로 검증하는 감시와는 구분하십시오.
