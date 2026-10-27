# REDKITE F16 PANELS

![My Cockpit](docs/3d%20stl/My%20Cockpit3.png)

VR 전용 F-16 미니멀 데스크핏
**Falcon BMS**(BMS-BIOS)와 **DCS World**(DCS-BIOS) 자동 감지로 패널의 LED 연동

---

## 개요

VR 전용 미니멀 데스크핏을 지향합니다. VR 헤드셋을 쓰고 손을 뻗은 곳에 스위치가 있었으면 하는 생각을 1년 이상 참다가 결국 만들었습니다 ㅠㅠ 실기 1:1 스케일로 제작했습니다. 사용하지 않을 때 쉽게 치울 수 있는 이동식/수납식 구조를 대외적으로 표방(치울지는 모르겠음), 인게임 디스플레이로 충분한 계기류(DED, RWR, 엔진 게이지, HSI 등)는 제작하지 않고 스위치와 LED 위주로 구성했습니다.

### 주요 기능

- **PWM 백라이트 디밍** — MOSFET PWM으로 인게임 조명 노브에 연동되는 무단계 밝기 조절
- **USB Suspend 감지** — PC 절전 시 LED 소등 및 MCU 저전력 모드 진입
- **프로토콜 자동 감지** — BMS-BIOS / DCS-BIOS 자동 판별, LED·백라이트 연동
- **MCP23017 I2C 확장** — 새로운 패널을 I2C로 추가 가능. 핫플러그 지원
- **74HC595 시프트 레지스터** — ECM 32 LED를 3핀으로 구동
- **로터리 엔코더** — UHF 주파수 5자리 + PRESET을 6개 엔코더로 구현 (1kHz ISR)
- **DCS 커버 자동화** — ENG CONT, EPU 스위치 조작 시 커버를 자동으로 열고 닫음

### 디바이스 구성

독립된 USB 디바이스 2대. 각각 별도의 Teensy 4.1과 스케치를 사용합니다.

| 디바이스 | 폴더 | PID | 담당 |
|---|---|---|---|
| **Left Aux + MISC** | `F16_LEFT_AUX_MISC/` | `0x0489` | Gear, CMDS, TWA, Alt Gear, MISC, HMCS, Pedal |
| **Left Console** | `F16_LEFT_CONSOLE/` | `0x048E` | ECM, ELEC, EPU, AVTR, UHF, ENGINE START, MPO, AUDIO 1/2 |

#### Left Aux + MISC (`0x0489`) — DX 51, 축 4

| Panel | Type | Description |
|-------|------|-------------|
| Gear | Switch, LED | Landing Gear, Hook, Anti-skid, Landing Light, Gear Warning 등 |
| Alt Gear | Switch | ALT Gear Handle |
| MISC | Switch, LED (MCP23017) | Master ARM, Laser ARM, RF, Autopilot Pitch/Roll, ECM LED 등 |
| CMDS | Switch, Analog Ladder, LED | RWR, JMR, MWS, JETT, MODE (7-pos), PRGM (7-pos), GO/NO GO/RDY EWS 램프 |
| TWA | Analog Ladder, LED | Threat Warning Aux — Search, Act/Pwr, Low, Power |
| HMCS | Analog | Symbology 포텐셔미터 |
| Pedal | Analog | Rudder + Left/Right Brake (auto calibration) |

#### Left Console (`0x048E`) — DX 66, 축 10

| Panel | Type | Description |
|-------|------|-------------|
| ECM | Switch (MCP23017), Analog Ladder, LED (74HC595) | OPR/STBY, XMIT, BIT, RESET + 8버튼 래더 + S/A/F/T 32 LED |
| ELEC | Switch, LED (MCP23017) | MAIN PWR, CAUTION RST + 경고등 8개 |
| EPU | Switch (MCP23017) | OFF / NORM / ON |
| AVTR | Switch (MCP23017) | OFF / AUTO / ON |
| UHF | Switch, Encoder ×6, Analog, 7-seg | FUNCTION(4), MODE(3), SQUELCH, T-TONE, STATUS, TEST + 주파수 엔코더 + VOL + MAX7219 디스플레이 |
| ENGINE START | Switch | JFS, ENG CONT, MAX PWR, AB RESET, ENG DATA |
| MPO | Switch | Manual Pitch Override |
| AUDIO 1/2 | Analog, Switch (MCP23017) | 볼륨 6개 + COMM 1/2 모드 로터리 2개 |

DX 59~61은 ENG CONT·EPU 커버 자동화용으로 **DCS에서만** 사용됩니다. 62~65는 COMM1/COMM2 볼륨 pot의 전원 스위치(ADC 임계값 감지), 66은 UHF TEST 입니다.

---

## 1. 준비물

### 1-1. 패널

콕핏 빌더 전문 업체에서 구매하거나 3D 프린터로 직접 출력할 수 있습니다.

**구매처:**
- [PC Flights](https://pcflights.com/flight-simulator-cockpit-panels/f-16c-viper-home-cockpit-panels/) — F-16C 패널 전문 **(본 프로젝트에서 사용)**
- [HispaPanel](https://hispapanels.com/tienda/en/20-f-16-fighting-falcon) — 레이저 커팅/각인 패널 키트
- [TEK Creations](https://tekcreations.space/shop/) — LED 백라이트 패널, DCS-BIOS 레디

| MISC | Gear | CMDS |
|:----:|:----:|:----:|
| [![MISC](https://pcflights.com/image/cache/catalog/panels/f-16c_viper_misc_panel-600x400.jpg)](https://pcflights.com/f-16c-viper-miscellaneous-misc-panel-flight-sim-part/) | [![Gear](https://pcflights.com/image/cache/catalog/panels/f-16c_viper_landing_gear_panel-600x400.jpg)](https://pcflights.com/f-16c-viper-landing-gear-panel-flight-simulator-module/) | [![CMDS](https://pcflights.com/image/cache/catalog/panels/f-16c_viper_cmds_control_panel-600x400.jpg)](https://pcflights.com/f-16c-viper-cmds-control-panel-module/) |

**3D 프린트 모델:**
- [Greenisland](https://cults3d.com/en/users/Greenisland/3d-models) — F-16 콕핏 거의 전체 파트
- [Legarsdusofa](https://cults3d.com/en/design-collections/Legarsdusofa/f-16-cockpit-simulator) — F-16 콕핏 거의 전체 파트
- [The_Viper_Project](https://cults3d.com/en/users/The_Viper_Project/3d-models) — 버튼 노브, 스위치 캡 등 무료

### 1-2. 인클로저 & 스탠드

`docs/3d stl/` 폴더에 STL 파일이 있습니다. PETG 권장 (JLC3DP는 PETG 미지원, PCBWay 별도 주문).
Stand는 Enclosure 뒷면에 에폭시 접착제로 부착합니다. new 버전 권장.

| Left Stand | Left Stand (new) | Right Stand | Right Stand (new) |
|:----:|:----:|:----:|:----:|
| <a href="docs/3d%20stl/Left%20Stand.stl"><img src="docs/3d%20stl/Left%20Stand.png" width="150"></a> | <a href="docs/3d%20stl/Left%20Stand%20-%20new.stl"><img src="docs/3d%20stl/Left%20Stand%20-%20new.png" width="150"></a> | <a href="docs/3d%20stl/Right%20Stand.stl"><img src="docs/3d%20stl/Right%20Stand.png" width="150"></a> | <a href="docs/3d%20stl/Right%20Stand-%20new.stl"><img src="docs/3d%20stl/Right%20Stand-%20new.png" width="150"></a> |

| Left Enclosure | Right Enclosure (new) | Enclosure OnePiece |
|:----:|:----:|:----:|
| <img src="docs/3d%20stl/Left%20Enclosure.png" width="150"> | <img src="docs/3d%20stl/Right%20Enclosure%20-%20new.png" width="150"> | <a href="docs/3d%20stl/Enclosure%20-%20%20OnePiece2.stl"><img src="docs/3d%20stl/Enclosure%20-%20%20OnePiece2.png" width="150"></a> |

> Left/Right Enclosure STL은 Cults3D 구매 모델 기반이라 저작권 보호를 위해 재배포하지 않습니다.

### 1-3. MCU

[Teensy 4.1](https://www.pjrc.com/store/teensy41.html) × 2대. 선택 이유:
- USB 조이스틱 128버튼 네이티브 지원 (Arduino Mega 등은 USB HID 미지원)
- 600MHz ARM Cortex-M7 — 다중 작업에 충분한 성능
- 42 GPIO + 하단 SD 패드 — 충분한 핀 수

**구조** — Teensy 2대가 각각 독립된 USB 조이스틱으로 잡히고, 모자라는 핀은 MCP23017 I2C 확장으로 채웁니다.

```
  PC ─USB─ Teensy 4.1  LEFT AUX + MISC  (PID 0x0489)
             │ 헤더 39/42 + SD 패드 5
             │
             └─ I2C ─ [MCP23017 0x20] ─ MISC 패널


  PC ─USB─ Teensy 4.1  LEFT CONSOLE     (PID 0x048E)
             │ 헤더 41/42 + SD 패드 3
             │
             ├─ I2C ─ [MCP23017 0x20] ─ [MCP23017 0x21] ─ [MCP23017 0x22]
             │          UHF + AUDIO        ELEC + EPU        ECM + AVTR
             │         └──────────── 데이지체인 3장 ────────────┘
             │
             └─ 3선 ─ [74HC595] ×4 ─ ECM 32 LED
```

| | LEFT AUX + MISC | LEFT CONSOLE |
|---|---|---|
| Teensy 헤더 핀 | 39 / 42 | 41 / 42 |
| 하단 SD 패드 | 5 (CMDS 램프) | 3 (UHF 디스플레이) |
| MCP23017 | **1장** (`0x20`) | **3장** (`0x20`·`0x21`·`0x22`) |
| 그 외 확장 | — | 74HC595 ×4 (ECM 32 LED) |

**양쪽 다 헤더 핀이 거의 찼습니다.** 스위치·LED 를 더 붙이려면 MCP23017 을 추가하는 쪽이지,
Teensy 핀을 더 찾는 방향은 막혀 있습니다. MCP 는 칩당 16 GPIO 이고 주소를 `0x20`~`0x27`
범위에서 고를 수 있어 보드당 8장까지 늘릴 수 있습니다.

> 엔코더만은 MCP 에 올릴 수 없습니다 — I2C 폴링으로는 쿼드러처 펄스를 놓칩니다.
> UHF 엔코더 6개가 콘솔 Teensy 의 `0`–`11` 을 직접 쓰는 이유입니다.

### 1-4. 부품 목록

스위치, IC, LED, 수동 소자, 커넥터, 모듈 전체 목록은
**[docs/REF_PARTS.md](docs/REF_PARTS.md)** 에 있습니다.

### 1-5. 소요 비용

| 유형 | 업체 | 내용 | 제품 (USD) | 배송 (USD) |
|------|------|------|----:|----:|
| 패널 | [PC Flights](https://pcflights.com) | MISC / Gear / CMDS 패널 3종 | $133 | $31 |
| 3D 프린트 (SLA/MJF) | [JLC3DP](https://jlc3dp.com) | 스위치 캡, 노브, LED 레이어 등 | $64 | $20 |
| 3D 프린트 (PETG) | [PCBWay](https://www.pcbway.com) | Enclosure, Stand 등 구조물 | $119 | ~$50 |
| MCU | [PJRC](https://www.pjrc.com) | Teensy 4.1 ×2 | ~$70 | - |
| 전자부품 | [AliExpress](https://www.aliexpress.com) | MCP23017, 스위치, LED, 저항 등 | ~$200 | - |
| 노동력 | - | 약 1달간의 설계, 조립, 프로그래밍 | priceless | - |
| | | **합계** | **~$586** | **~$101** |

> 결론: 시간과 노동력을 고려하면 TEK Creations 등 완제품을 사는 게 현명합니다. 직접 만드는 건 취미입니다.

---

## 2. 개발 환경 설정

### 2-1. Arduino IDE 설치

1. [Teensyduino](https://www.pjrc.com/teensy/td_download.html) 설치
2. Arduino IDE에서:
   - **Board**: Teensy 4.1
   - **USB Type**: Serial + Keyboard + Mouse + Joystick

### 2-2. usb_desc.h 수정 (Extreme Joystick)

AUX 51버튼, 콘솔 66버튼이므로 **두 스케치 모두** 128버튼 Extreme 모드가 필요합니다.

파일 위치: `%LOCALAPPDATA%\Arduino15\packages\teensy\hardware\avr\<version>\cores\teensy4\usb_desc.h`

```c
#define JOYSTICK_SIZE         64    //  12 = normal, 64 = extreme joystick
#define PRODUCT_ID            0x0489  // AUX 보드 / 콘솔 보드는 0x048E
```

두 보드가 `JOYSTICK_SIZE 64`를 공유하므로 빌드 사이에 이 값을 고칠 필요는 없습니다. **`PRODUCT_ID`만 디바이스에 맞게** 바꿔 빌드합니다. 값이 틀리면 각 스케치의 `#error`가 빌드를 막아줍니다.

> **축은 6개가 아니라 23개입니다.** Extreme 모드는 명명 축 6개(X/Y/Z/Xrotate/Yrotate/Zrotate)에 더해 `Joystick.slider(1..17)`을 제공합니다. 단, Windows DirectInput은 최대 8축만 인식하므로, `usb_desc.c`에서 Report Count를 8로 줄이고 나머지는 constant padding 처리가 필요합니다. 상세는 [docs/REF_LEFT_CONSOLE_WIRING.md](docs/REF_LEFT_CONSOLE_WIRING.md)의 「usb_desc.c 수정 사항」 참조.

> Teensyduino 업데이트 시 `usb_desc.h`와 `usb_desc.c`가 덮어씌워집니다. 업데이트 전에 백업하거나, 업데이트 후 다시 수정하세요. 상세는 [docs/teensyduino_upgrade.md](docs/teensyduino_upgrade.md) 참조.

---

## 3. 배선

### 3-1. 보드별 배선도

케이블 구성, Teensy 핀 배열, MCP GPIO 맵, DX 버튼 맵, 시공 체크리스트가 아래 두 문서에 있습니다. **배선 전에 반드시 읽으세요.**

| 보드 | 배선도 |
|---|---|
| Left Aux + MISC | [docs/REF_LEFT_AUX_WIRING.md](docs/REF_LEFT_AUX_WIRING.md) |
| Left Console | [docs/REF_LEFT_CONSOLE_WIRING.md](docs/REF_LEFT_CONSOLE_WIRING.md) |

스위치 배선은 전부 **액티브 로우 + INPUT_PULLUP** (공통 단자 = GND, 눌림 = LOW = ON).
저항 래더(CMDS MODE·PRGM, TWA, ECM) 제작법·값, MCP23017 I2C 배선과 핫플러그 보호 부품도 위 문서에 있습니다.
MCP 를 몇 장 어떻게 붙였는지는 [1-3. MCU](#1-3-mcu) 참조.

### 3-2. 백라이트

양쪽 보드 모두 Teensy pin 13 → MOSFET PWM 디밍이고, 12V DC 어댑터 1개를 Y 케이블로 분기해 씁니다.
회로·전원·밝기 제어·LED 배치는 **[docs/REF_BACKLIGHT.md](docs/REF_BACKLIGHT.md)** 에 있습니다.

> **Step-Up(MT3608 등)으로 12V 를 만들지 마십시오.** 저항 래더 판독값이 흔들립니다 — 경위는 위 문서에.

---

## 4. 펌웨어 업로드

Arduino IDE에서 해당 `.ino`를 열고 Upload합니다. `usb_desc.h`의 `PRODUCT_ID`가 보드와 일치하는지 먼저 확인하세요.

| 보드 | 파일 | PRODUCT_ID |
|---|---|---|
| Left Aux + MISC | `F16_LEFT_AUX_MISC/F16_LEFT_AUX_MISC.ino` | `0x0489` |
| Left Console | `F16_LEFT_CONSOLE/F16_LEFT_CONSOLE.ino` | `0x048E` |

라이브러리는 `Wire`, `Keyboard` (모두 built-in)만 필요합니다.

---

## 5. 소프트웨어 설정 (Python 브릿지)

스위치 입력은 USB Joystick으로 직접 전달되지만, **LED 상태는 시뮬레이터에서 받아와야 합니다.** Python 브릿지가 시뮬레이터 데이터를 읽어 시리얼로 Teensy에 전송합니다.

```bash
pip install pyserial hidapi
```

- `pyserial` — Teensy 시리얼 통신 (필수)
- `hidapi` — Cougar MFD 백라이트 동기화 (선택, 없으면 MFD 건너뜀)

### Falcon BMS (BMS-BIOS)

```bash
python tools/bmsbios_bridge.py                          # 두 디바이스 자동 감지
python tools/bmsbios_bridge.py COM4:AUX COM5:CONSOLE    # 수동 지정
python tools/bmsbios_bridge.py --debug                  # LightBits 실시간 출력
```

- `0xAA 0xBB` sync로 자동 감지
- BMS 공유 메모리에서 LED 상태를 읽어 Teensy로 전송
- 프레임: `sync(2) + ledBits(4) + srData(4) + uhfFreq(4) + uhfPreset(1) + XOR(1)` = 16바이트
- Cougar MFD 연결 시 `instrLight`에 따라 백라이트 자동 동기화
- BMS 실행 전에 bridge를 먼저 실행해도 안전

### DCS World (DCS-BIOS)

```bash
python tools/dcsbios_bridge.py    # COM port auto-detect
```

- `0x55 ×4` sync로 자동 감지
- [DCS-BIOS](https://github.com/DCS-Skunkworks/dcs-bios) 설치 필요

### 프로토콜 자동 감지

Teensy는 수신된 sync 바이트로 BMS/DCS 프로토콜을 자동 판별합니다. 타임아웃(AUX 6초 / 콘솔 3초) 후 프로토콜을 리셋하고 재감지합니다.

**오프라인(브릿지 미연결) 동작:**
- AUX 보드: Landing Gear 스위치 상태에 따라 Gear LED 3개를 시뮬레이션 (2초 딜레이 + Gear Warn 5초)
- 콘솔 보드: 모든 LED 소등

---

## 6. 테스트 & 캘리브레이션

### 6-1. 조이스틱 확인

Windows `joy.cpl`은 32버튼까지만 표시합니다. 128버튼을 확인하려면 [VKB DevCfg](https://vkbcontrollers.com/?page_id=4609) 또는 [Joystick Gremlin](https://whitemagic.github.io/JoystickGremlin/)을 사용하세요.

### 6-2. 래더 캘리브레이션

1. `F16_LEFT_AUX_MISC.ino` 또는 `F16_LEFT_CONSOLE.ino`에서 `ALLOW_DEBUG = true` 설정
2. 업로드 후 시리얼 모니터(1000000 baud)에서 각 포지션의 ADC 값 확인
3. `values[]` 배열을 실측값으로 업데이트
4. `ALLOW_DEBUG = false`로 복원 후 재업로드

### 6-3. 페달 캘리브레이션

페달은 자동 캘리브레이션을 지원합니다.
- **리셋**: 양 페달 최대 압력 + DN LOCK REL 2초간 홀드
- **브레이크 모드 전환**: Landing Light UP 또는 양 페달 동시 압력

### 6-4. 엔코더 방향 확인

UHF 엔코더의 CW/CCW가 반대면 `encoders[]`의 `pinA`/`pinB`를 교체하세요.

---

## 커스터마이징

스위치/LED 등 하드웨어 변경 시 각 `.ino`의 **HARDWARE CONFIGURATION** 섹션의 config 배열만 수정합니다. 조이스틱 버튼 번호는 런타임에 자동 재할당됩니다.

| 배열 | 용도 | 보드 |
|---|---|---|
| `switches[]` | 디지털 스위치 (직결 / MCP) | 공통 |
| `analogBtnArrays[]` | 저항 래더 그룹 | 공통 |
| `mcpDevices[]` | MCP23017 I2C 주소 | 공통 |
| `leds[]` | LED (직결 / MCP) | 공통 |
| `pots[]` | 포텐셔미터 → 조이스틱 축 | 공통 |
| `encoders[]` | 로터리 엔코더 | 콘솔 |
| `srMap[]` | 74HC595 논리→물리 출력 리맵 | 콘솔 |

```cpp
// 스위치 추가 예시 (mcpIdx: -1=Teensy직결, 0+=MCP 인덱스)
{"My Switch",   PNL_GEAR,  SW_ON_OFF,  -1,  5,  0,  NULL},
{"MCP Switch",  PNL_MISC,  SW_ON_OFF,   0,  5,  0,  NULL},  // mcpIdx=0, GPA5
```

새 MCP 디바이스를 추가하려면 `mcpDevices[]`에 I2C 주소를 등록하면 됩니다. 패널을 비활성화하려면 해당 항목을 주석 처리하면 됩니다.

---

## Left Console 보드 상세

콘솔 보드(`F16_LEFT_CONSOLE/`)는 AUX 보드 대비 몇 가지 고유 사항이 있습니다.

**로터리 엔코더 (UHF 6개)**
1kHz `IntervalTimer` ISR에서 쿼드러처를 디코딩하고, 메인 루프가 CW/CCW DX 버튼 펄스로 배출합니다. 엔코더는 **MCP23017에 올릴 수 없습니다** — I2C 폴링으로는 펄스를 놓칩니다.

**UHF 7세그 디스플레이 (MAX7219)**
기성 모듈이 아니라 2층 86×50mm **자작 PCB** 입니다 — 거버·BOM·설계 문서는 저장소 밖의 `f-16-cockpit-uhf-radio-panel/display/pcb/` 에 있고, 부품은 [docs/REF_PARTS.md](docs/REF_PARTS.md) 의 「UHF 7세그 디스플레이 보드」 절에 정리돼 있습니다.
UHF 주파수 6자리 + 채널 2자리를 표시합니다. DCS에서는 DCS-BIOS가 디스플레이 상태를 직접 제공하므로 UHF OFF 시 자동으로 꺼집니다. BMS 공유 메모리에는 UHF FUNCTION 스위치 상태가 없어서, 펌웨어가 물리 스위치(FUNCTION=OFF) 위치를 직접 읽어 디스플레이를 끕니다. 브릿지 미연결 시에도 번인 방지를 위해 디스플레이가 꺼집니다.

**74HC595 32/32 소진**
칩을 추가하면 BMS-BIOS 프레임의 `srData` 32비트를 넘으므로 `BB_FRAME_PAYLOAD`, 양쪽 `BmsBiosParser.h`, `bmsbios_bridge.py`를 모두 수정해야 합니다.

**I2C 데이지체인**
AUX의 Star와 달리 MCP 3장을 한 줄로 체인합니다. 한 링크가 끊기면 하류 전체가 사라지는 대신, 분기 스터브가 없어 반사가 줄고 총 배선이 짧아집니다.

**12V 어댑터 (AUX와 Y 케이블로 공유)**
인디케이터 LED 40개(ECM 32 + ELEC 8)로 USB 전력 예산을 초과합니다. **어댑터 GND와 Teensy GND를 단일점으로 반드시 연결하세요.**

상세는 [docs/REF_LEFT_CONSOLE_WIRING.md](docs/REF_LEFT_CONSOLE_WIRING.md) 참조.

---

## 프로젝트 구조

```
REDKITE-F16-Panels/
├── F16_LEFT_AUX_MISC/             # Teensy 4.1 (PID 0x0489)
│   │                              #   Gear, CMDS, TWA, Alt Gear, MISC, HMCS, Pedal
│   ├── F16_LEFT_AUX_MISC.ino
│   ├── BiosHandler/               # DcsBiosParser.h / BmsBiosParser.h
│   ├── CLAUDE.md
│   └── name.c
├── F16_LEFT_CONSOLE/              # Teensy 4.1 (PID 0x048E)
│   │                              #   ECM, ELEC, EPU, AVTR, UHF,
│   │                              #   ENGINE START, MPO, AUDIO 1/2
│   ├── F16_LEFT_CONSOLE.ino
│   ├── BiosHandler/
│   ├── Display/                   # Max7219Display.h (UHF 7-seg)
│   ├── CLAUDE.md
│   └── name.c
├── tools/                         # Python 브릿지 (BMS/DCS → Teensy)
│   ├── bmsbios_bridge.py          #   VID/PID로 두 디바이스 동시 인식
│   ├── dcsbios_bridge.py
│   ├── reset_joystick_name.bat
│   └── backup_to_synology.ps1
├── docs/                          # 배선도, 프로토콜 참조
│   ├── REF_BACKLIGHT.md           #   백라이트 회로·전원·LED 배치
│   ├── REF_PARTS.md               #   부품 목록
│   ├── REF_PROTOCOL.md            #   DCS/BMS 프로토콜·LED 주소 맵
│   ├── REF_LEFT_AUX_WIRING.md     #   AUX 보드 배선·핀 배열·DX맵·LAN
│   ├── REF_LEFT_CONSOLE_WIRING.md #   콘솔 보드 배선·핀 배열·DX맵·전원
│   └── 3d stl/                    #   3D 프린트용 STL 파일
├── CLAUDE.md                      # Claude Code 가이드
└── README.md
```

## 7. 참조 문서

| 문서 | 내용 |
|---|---|
| [docs/REF_BACKLIGHT.md](docs/REF_BACKLIGHT.md) | 백라이트 MOSFET 회로, 12V 전원, 밝기 제어, LED 스트링 배치 |
| [docs/REF_PARTS.md](docs/REF_PARTS.md) | 스위치·IC·LED·수동 소자·커넥터·모듈 부품 목록, UHF 디스플레이 보드 BOM |
| [docs/REF_PROTOCOL.md](docs/REF_PROTOCOL.md) | DCS-BIOS / BMS-BIOS 프로토콜, LED 주소 맵, LightBits 매핑 |
| [docs/REF_LEFT_AUX_WIRING.md](docs/REF_LEFT_AUX_WIRING.md) | AUX 보드 케이블 배선, Teensy 핀 배열, MCP GPIO, AUX↔MISC LAN 배선, DX 맵, 시공 체크리스트 |
| [docs/REF_LEFT_CONSOLE_WIRING.md](docs/REF_LEFT_CONSOLE_WIRING.md) | 콘솔 보드 케이블 배선, Teensy 핀 배열, MCP GPIO, DX 맵, 전원 구성, 시공 체크리스트 |

---

## License

This project is licensed under the [MIT License](LICENSE).
