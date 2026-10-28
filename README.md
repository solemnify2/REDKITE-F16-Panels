# REDKITE F16 PANELS

![My Cockpit](3d%20stl/MyCockpitv4.png)

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

콕핏 빌더 전문 업체에서 **구매**하거나, 3D 프린터와 아크릴 레이저 커팅으로 **직접 제작**할 수 있습니다.
본 프로젝트는 [PC Flights](https://pcflights.com/flight-simulator-cockpit-panels/f-16c-viper-home-cockpit-panels/)
구매품인 **MISC · Gear · CMDS 세 장**을 빼고, 나머지 패널 전부를
[Greenisland](https://cults3d.com/en/users/Greenisland/3d-models) 모델로 직접 만들었습니다.

Greenisland 패널은 **Top(아크릴) · Diffuser(아크릴) · LED layer(투명 PLA)** 3 레이어에
백라이트 플레이트가 더해지는 구조입니다 — 패널 한 장에 **아크릴 재단 2종 + 3D 프린트 2종**.

구매처 · 3D 모델 출처 · 레이어별 재료와 두께 · 도색과 레이저 각인 방법은
**[docs/REF_PANEL.md](docs/REF_PANEL.md)** 에 있습니다.

### 1-2. 3D 프린트 구조물

`3d stl/` 폴더에 STL 21 개가 있습니다. 인클로저 · 스탠드 · 콘솔 · MFD 홀더는 **PLA 또는 PETG**,
패널 `LED layer` 는 **투명 PLA**, 백라이트 플레이트는 **PLA 또는 레진** 으로 출력합니다.

| 묶음 | 개수 | 내용 |
|------|----:|------|
| 인클로저 & 스탠드 | 2 | 좌우 스탠드. Center Left/Right 인클로저는 구매 모델 가공본이라 STL 을 싣지 않습니다 |
| Left Aux 인클로저 | 3 | Enclosure · Front · Back |
| Left Console | 4 | Upper · Lower · Bottom 2 종 |
| MFD 홀더 | 4 | TM MFD + 7.6" LCD 를 함께 잡는 브래킷 |
| 백라이트 플레이트 | 8 | Left Aux 4 + Left Console 4 — 자작 모델 |

썸네일 · 바운딩 박스 치수 · 내려받기 링크는 **[docs/REF_ENCLOSURE.md](docs/REF_ENCLOSURE.md)** 에 있습니다.

### 1-3. 부품 목록

스위치, IC, LED, 수동 소자, 커넥터, 모듈 전체 목록은
**[docs/REF_PARTS.md](docs/REF_PARTS.md)** 에 있습니다.

### 1-4. 소요 비용

| 유형 | 업체 | 내용 | 제품 (USD) | 배송 (USD) |
|------|------|------|----:|----:|
| 패널 | [PC Flights](https://pcflights.com) | MISC / Gear / CMDS 패널 3종 | $133 | $31 |
| 아크릴 재단 · 도색 | [아크릴마켓](https://smartstore.naver.com/acrylicmarket) 등 | Greenisland DXF 패널 11종, 패널당 약 ₩10,000 | ~$80 | - |
| 3D 프린트 | [JLC3DP](https://jlc3dp.com) / [PCBWay](https://www.pcbway.com) 등 | 구조물 · 플레이트 34종 (아래 수량표) | **견적 참조** | - |
| MFD LCD | [Alibaba](https://www.alibaba.com/product-detail/In-Stock-IPS-7-6-Inch_1601257654342.html) | 7.6" 정사각 800×800 IPS ×2, 장당 $58 (드라이버 보드 포함) | $116 | 무료 |
| MCU | [PJRC](https://www.pjrc.com) | Teensy 4.1 ×2 | ~$70 | - |
| 전자부품 | [AliExpress](https://www.aliexpress.com) | MCP23017, 스위치, LED, 저항 등 | ~$200 | - |
| 커스텀 PCB | JLCPCB / PCBWay 등 | TWA · ECM · UHF 디스플레이 3종, 장당 약 $5 | ~$15 | - |
| 노동력 | - | 약 1년간의 설계, 조립, 프로그래밍 | priceless | - |
| | | **합계** | **~$614** | **~$31** |

**3D 프린트 수량**

| 구분 | 수량 | 재료 | STL 위치 |
|------|----:|------|----------|
| 패널 `LED layer` | 11 | 투명 PLA | Greenisland 모델 동봉 |
| 백라이트 플레이트 | 8 | PLA · 레진 | `3d stl/` |
| Left Aux 인클로저 | 3 | PLA · PETG | `3d stl/` |
| Left Console | 4 | PLA · PETG | `3d stl/` |
| MFD 홀더 | 4 | PLA · PETG | `3d stl/` |
| 스탠드 | 2 | PLA · PETG | `3d stl/` |
| 인클로저 | 2 | PLA · PETG | Cults3D 구매 모델 |
| **합계** | **34** | | |

스위치 캡 · 노브는 별도이며, 수량은 스위치 구성에 따라 달라집니다 (본 프로젝트 기준 64개).

> **3D 프린트 비용은 금액으로 적지 않았습니다.** 업체 발주분과 직접 출력분이 섞여 있고,
> 업체 · 재료 · 시기에 따라 편차가 큽니다. **STL 을 [JLC3DP](https://jlc3dp.com) ·
> [PCBWay](https://www.pcbway.com) 등에 업로드하면 재료별 실시간 견적**이 바로 나오니
> 그쪽을 참고하십시오. 그만큼 실제 지출은 위 합계보다 큽니다.

> 결론: 시간과 노동력을 고려하면 TEK Creations 등 완제품을 사는 게 현명합니다. 직접 만드는 건 취미입니다.

---

## 2. 조립 및 배선

### 2-1. 조립 순서

패널 제작은 [docs/REF_PANEL.md](docs/REF_PANEL.md), 구조물은 [docs/REF_ENCLOSURE.md](docs/REF_ENCLOSURE.md),
배선은 2-2, 백라이트 회로는 2-3 을 보십시오. 여기서는 조립 순서만 정리합니다.

**1. 패널 적층** — Greenisland 패널은 3 층을 겹칩니다. 스위치 · 로터리 · 푸시버튼은 전부
맨 뒤 `LED layer` 에 체결되고, 앞의 두 장은 그 위에 얹힙니다.

```
   Top        아크릴 2 mm — 도색 + 각인        ← 전면
   Diffuser   투명 아크릴 2~3 mm                빛 확산
   LED layer  투명 PLA                         ← 스위치가 여기에 체결됨
   ┊
   ┊ 몇 cm 띄움
   ┊
   백라이트 플레이트   PLA · 레진              ← LED 를 여기에 장착
```

PC Flights 패널(MISC · Gear · CMDS)은 2 층(전면 도색 + 후면 투명)이고,
후면 투명판 뒤 **1~2 cm** 에서 LED 를 쏩니다.

> 적층 상세(체결 순서, 나사 · 스페이서 규격)는 **원본 제공처의 안내를 따르십시오.**
> Greenisland 패널은 [Cults3D 모델](https://cults3d.com/en/users/Greenisland/3d-models)에 동봉된 매뉴얼,
> PC Flights 패널은 [제품 페이지](https://pcflights.com/flight-simulator-cockpit-panels/f-16c-viper-home-cockpit-panels/)를 보십시오.
> 이 문서는 본 프로젝트에서 달라진 부분만 적습니다.

**2. 백라이트 플레이트** — LED 스트링(LED 3개 + 220Ω)을 플레이트에 심고,
패널 **뒤쪽 몇 cm 뒤**에 고정합니다. 간격을 두는 이유는 [docs/REF_BACKLIGHT.md](docs/REF_BACKLIGHT.md) 참조.

**3. 인클로저 조립** — 접착은 전부 **에폭시**입니다.

| 붙이는 것 | 붙이는 곳 |
|-----------|-----------|
| Stand | Center 인클로저 **뒷면** |
| MFD 홀더 | Center 인클로저 **아래쪽** |

`…MFDHolderUpper` 는 접착 부품이 아니라, 인클로저와 MFD 사이에 남는 **빈틈을 메우는** 조각입니다.
에폭시는 위 표의 두 곳에만 씁니다. MFD 와 LCD 는 어디에도 접착하지 않습니다.

**4. MFD** — Thrustmaster MFD 뒤에 7.6인치 정사각 LCD 를 **겹쳐 놓기만** 하고,
MFD 홀더가 둘을 함께 눌러 고정합니다. **서로 붙이지 않습니다** —
수리할 때 홀더에서 두 장을 그대로 빼낼 수 있어야 하기 때문입니다.

LCD 는 HDMI·USB-C 로 PC 에 직접 연결하는 별개 모니터입니다. Teensy 와는 무관합니다.
사양 · 기구 치수 · 홀더 설계 주의점은 **[docs/REF_MFD_LCD.md](docs/REF_MFD_LCD.md)** 에 있습니다.

> 화면을 MFD 창에 맞출 때는 **표시 영역(135.36 × 135.36) 기준으로 정렬**하십시오.
> 모듈 외형(142.56 × 148.24)은 정사각이 아니고 표시 영역이 가운데 있지 않아,
> 외형에 맞추면 화면이 위로 치우칩니다. FPC 리본이 아래로 50 mm 더 나옵니다.

**5. 러더 페달** — 전동 킥보드용 스로틀 페달 2개를 PVC 전선 몰딩 2줄 사이에
**서로 반대 방향으로** 물립니다. 몰딩이 프레임이자 배선 통로입니다.
페달 안에는 홀 센서가 들어 있어 **3.3V · GND · Signal 3선**이고, 신호 2개를 각각
`A16` · `A17` 로 넣습니다. 만드는 법은 **[docs/REF_PEDAL.md](docs/REF_PEDAL.md)**.

> ⚠ 페달에 **5V 를 넣지 마십시오.** 홀 센서 출력이 공급 전압을 따라가므로
> Teensy 아날로그 핀 정격(3.3V)을 넘깁니다.

**6. 배선** — 2-2 의 배선도대로 결선합니다. 패널을 인클로저에 완전히 고정하기 전에
스위치 동작을 먼저 확인하는 편이 낫습니다 (5장 참조).

### 2-2. 보드별 배선도

케이블 구성, Teensy 핀 배열, MCP GPIO 맵, DX 버튼 맵, 시공 체크리스트가 아래 두 문서에 있습니다. **배선 전에 반드시 읽으세요.**

| 보드 | 배선도 |
|---|---|
| Left Aux + MISC | [docs/REF_LEFT_AUX_WIRING.md](docs/REF_LEFT_AUX_WIRING.md) |
| Left Console | [docs/REF_LEFT_CONSOLE_WIRING.md](docs/REF_LEFT_CONSOLE_WIRING.md) |

스위치 배선은 전부 **액티브 로우 + INPUT_PULLUP** (공통 단자 = GND, 눌림 = LOW = ON).
저항 래더(CMDS MODE·PRGM, TWA, ECM) 제작법·값, MCP23017 I2C 배선과 핫플러그 보호 부품도 위 문서에 있습니다.

### 2-3. 백라이트

양쪽 보드 모두 Teensy pin 13 → MOSFET PWM 디밍이고, 12V DC 어댑터 1개를 Y 케이블로 분기해 씁니다.
회로·전원·밝기 제어·LED 배치는 **[docs/REF_BACKLIGHT.md](docs/REF_BACKLIGHT.md)** 에 있습니다.

> **Step-Up(MT3608 등)으로 12V 를 만들지 마십시오.** 저항 래더 판독값이 흔들립니다 — 경위는 위 문서에.

---

## 3. 개발 환경 & 펌웨어 업로드

### 3-1. Arduino IDE 설치

1. [Teensyduino](https://www.pjrc.com/teensy/td_download.html) 설치
2. Arduino IDE에서:
   - **Board**: Teensy 4.1
   - **USB Type**: Serial + Keyboard + Mouse + Joystick

### 3-2. usb_desc.h 수정 (Extreme Joystick)

AUX 51버튼, 콘솔 66버튼이므로 **두 스케치 모두** 128버튼 Extreme 모드가 필요합니다.

파일 위치: `%LOCALAPPDATA%\Arduino15\packages\teensy\hardware\avr\<version>\cores\teensy4\usb_desc.h`

```c
#define JOYSTICK_SIZE         64    //  12 = normal, 64 = extreme joystick
#define PRODUCT_ID            0x0489  // AUX 보드 / 콘솔 보드는 0x048E
```

두 보드가 `JOYSTICK_SIZE 64`를 공유하므로 빌드 사이에 이 값을 고칠 필요는 없습니다. **`PRODUCT_ID`만 디바이스에 맞게** 바꿔 빌드합니다. 값이 틀리면 각 스케치의 `#error`가 빌드를 막아줍니다.

> **축은 6개가 아니라 23개입니다.** Extreme 모드는 명명 축 6개(X/Y/Z/Xrotate/Yrotate/Zrotate)에 더해 `Joystick.slider(1..17)`을 제공합니다. 단, Windows DirectInput은 최대 8축만 인식하므로, `usb_desc.c`에서 Report Count를 8로 줄이고 나머지는 constant padding 처리가 필요합니다. 상세는 [docs/REF_LEFT_CONSOLE_WIRING.md](docs/REF_LEFT_CONSOLE_WIRING.md)의 「usb_desc.c 수정 사항」 참조.

> Teensyduino 업데이트 시 `usb_desc.h`와 `usb_desc.c`가 덮어씌워집니다. 업데이트 전에 백업하거나, 업데이트 후 다시 수정하세요. 상세는 [docs/teensyduino_upgrade.md](docs/teensyduino_upgrade.md) 참조.

### 3-3. 업로드

Arduino IDE에서 해당 `.ino`를 열고 Upload합니다. `usb_desc.h`의 `PRODUCT_ID`가 보드와 일치하는지 먼저 확인하세요.

| 보드 | 파일 | PRODUCT_ID |
|---|---|---|
| Left Aux + MISC | `F16_LEFT_AUX_MISC/F16_LEFT_AUX_MISC.ino` | `0x0489` |
| Left Console | `F16_LEFT_CONSOLE/F16_LEFT_CONSOLE.ino` | `0x048E` |

라이브러리는 `Wire`, `Keyboard` (모두 built-in)만 필요합니다.

---

## 4. BMS · DCS 연동

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

## 5. 테스트 & 캘리브레이션

### 5-1. 조이스틱 확인

Windows `joy.cpl` 은 **32버튼까지만** 표시합니다. 128버튼을 전부 보려면 별도 도구가 필요합니다.

| 도구 | 비고 |
|---|---|
| **AIM Joystick Probe** (Invictus) | 실제로 사용 중. 128버튼·23축을 모두 표시 — `AIM-Joystick-Probe-v1.2.0-Setup.exe` |
| [VKB DevCfg](https://vkbcontrollers.com/?page_id=4609) | 대안 |
| [Joystick Gremlin](https://whitemagic.github.io/JoystickGremlin/) | 대안 |

DX 번호가 배선도의 「DX 버튼 맵」과 맞는지 여기서 확인합니다.

### 5-2. 래더 캘리브레이션 (완료 — 오동작 시에만)

네 래더 모두 **실측값이 이미 반영돼 있어** 그대로 쓰면 됩니다.
버튼이 엉뚱하게 눌리거나 안 눌리면 그때 다시 잡습니다.

1. `F16_LEFT_AUX_MISC.ino` 또는 `F16_LEFT_CONSOLE.ino`에서 `ALLOW_DEBUG = true` 설정
2. 업로드 후 시리얼 모니터(1000000 baud)에서 각 포지션의 ADC 값 확인
3. `values[]` 배열을 실측값으로 업데이트
4. `ALLOW_DEBUG = false`로 복원 후 재업로드

> 값이 **전체적으로 함께 움직였다면** 캘리브레이션이 아니라 배선 문제입니다 —
> 기준 전압·GND 가 흔들린 것이니 ECM 풀다운 접점, 백라이트 전원 경로를 먼저 보십시오.
> (→ 각 배선도의 「저항 래더」 절)

### 5-3. 페달 캘리브레이션

페달은 자동 캘리브레이션을 지원합니다.
- **리셋**: 양 페달 최대 압력 + DN LOCK REL 2초간 홀드
- **브레이크 모드 전환**: Landing Light UP 또는 양 페달 동시 압력

페달 자작 내역과 브레이크/러더 동작의 근거는 **[docs/REF_PEDAL.md](docs/REF_PEDAL.md)** 에 있습니다.

### 5-4. 엔코더 방향 확인

UHF 엔코더의 CW/CCW가 반대면 `encoders[]`의 `pinA`/`pinB`를 교체하세요.

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
│   ├── patch_usb_desc_h.py        #   IDE 업데이트 후 usb_desc.h 자동 패치
│   ├── patch_usb_desc_c.py        #   usb_desc.c HID 슬라이더 디스크립터 패치
│   └── reset_joystick_name.bat
├── docs/                          # 배선도, 프로토콜 참조
│   ├── REF_BACKLIGHT.md           #   백라이트 회로·전원·LED 배치
│   ├── REF_PARTS.md               #   부품 목록
│   ├── REF_PROTOCOL.md            #   DCS/BMS 프로토콜·LED 주소 맵
│   ├── REF_LEFT_AUX_WIRING.md     #   AUX 보드 배선·핀 배열·DX맵·LAN
│   ├── REF_LEFT_CONSOLE_WIRING.md #   콘솔 보드 배선·핀 배열·DX맵·전원
│   ├── REF_MFD_LCD.md             #   MFD 뒤 7.6" 정사각 LCD
│   ├── REF_PEDAL.md               #   러더 페달 자작
│   └── REF_TWA_MOD.md             #   TWA 기판 LED 추가 개조 가이드
├── 3d stl/                        # 3D 프린트용 STL + 썸네일
├── pcb/                           # 커스텀 기판
│   └── uhf_display/               #   UHF 디스플레이 자작 PCB (거버·BOM·설계)
├── CLAUDE.md                      # Claude Code 가이드
└── README.md
```

## 6. 참조 문서

| 문서 | 내용 |
|---|---|
| [docs/REF_PANEL.md](docs/REF_PANEL.md) | 패널 구매처 · 3D 모델 출처, 레이어 구조와 두께, 도색 · 레이저 각인 방법 |
| [docs/REF_ENCLOSURE.md](docs/REF_ENCLOSURE.md) | 3D 프린트 구조물 — 인클로저 · 스탠드 · 콘솔 · MFD 홀더 · 백라이트 플레이트 STL 과 치수 |
| [docs/REF_BACKLIGHT.md](docs/REF_BACKLIGHT.md) | 백라이트 MOSFET 회로, 12V 전원, 밝기 제어, LED 스트링 배치 |
| [docs/REF_PARTS.md](docs/REF_PARTS.md) | 스위치·IC·LED·수동 소자·커넥터·모듈 부품 목록, UHF 디스플레이 보드 BOM |
| [docs/REF_PROTOCOL.md](docs/REF_PROTOCOL.md) | DCS-BIOS / BMS-BIOS 프로토콜, LED 주소 맵, LightBits 매핑 |
| [docs/REF_LEFT_AUX_WIRING.md](docs/REF_LEFT_AUX_WIRING.md) | AUX 보드 케이블 배선, Teensy 핀 배열, MCP GPIO, AUX↔MISC LAN 배선, DX 맵, 시공 체크리스트 |
| [docs/REF_LEFT_CONSOLE_WIRING.md](docs/REF_LEFT_CONSOLE_WIRING.md) | 콘솔 보드 케이블 배선, Teensy 핀 배열, MCP GPIO, DX 맵, 전원 구성, 시공 체크리스트 |
| [docs/REF_PEDAL.md](docs/REF_PEDAL.md) | 러더 페달 자작 — 킥보드 페달 + 전선 몰딩, 홀 센서 배선, 러더·브레이크 처리 |
| [docs/REF_MFD_LCD.md](docs/REF_MFD_LCD.md) | MFD 뒤에 겹쳐 쓰는 7.6인치 정사각 IPS LCD — 사양, 장착, 구매처 |
| [docs/REF_TWA_MOD.md](docs/REF_TWA_MOD.md) | TWA 기판에 Power LED 를 추가한 개조 내용 — 추가 부품, 회로, 적용 방법 |

---

## License

코드·문서·설정은 [MIT License](LICENSE).

`3d stl/` 의 자작 STL 은 **CC BY-NC-SA 4.0** 입니다 (MIT 아님).
구매 모델을 잘라 합친 것(Center Left/Right Enclosure)과 타 프로젝트 패널 STL·거버는
**재배포하지 않습니다** —
원 출처에서 받으십시오. 상세는 [LICENSE](LICENSE) 의 NOTICE.
