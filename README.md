# REDKITE F16 PANELS

![My Cockpit](3d%20stl/MyCockpitv4.png)

VR 전용 F-16 미니멀 데스크핏
**Falcon BMS**(BMS-BIOS)와 **DCS World**(DCS-BIOS) 자동 감지로 패널의 LED 연동

---

## 개요

VR에서 손이 닿는 위치에 실물 스위치를 배치하는 F-16 데스크핏입니다.
Meta Quest 3의 핸드 패스스루를 사용하며, 가상 콕핏과 위치를 맞추기 위해 패널을 실기 1:1 크기로 제작했습니다.

MISC·Left Aux·Left Console·MFD를 중심으로 구성합니다. 계기류는 게임 화면을 사용하고,
실물 패널에는 스위치·노브·표시등을 배치했습니다. 사용 후 이동하거나 수납할 수 있는 구조입니다.

### 주요 기능

- **Viper TQS 결합**: Left Console 인클로저를 Thrustmaster Viper TQS 옆면에 연결합니다.
- **MFD와 LCD 고정**: Thrustmaster MFD 뒤에 7.6인치 정사각 LCD를 겹쳐 홀더로 고정합니다. 패스스루에서 실물 MFD가 가리는 게임 화면을 LCD에 표시합니다.
- **자작 러더 페달**: 홀 센서가 내장된 킥보드용 스로틀 페달 2개를 PVC 전선 몰딩에 고정합니다.
- **게임 상태 표시**: BMS-BIOS/DCS-BIOS로 경고등·백라이트·[UHF 디스플레이](pcb/uhf_display/)를 연동합니다.
- **입력 자동화**: COMM 볼륨 끝점의 전원 제어와 토글 커버 개폐용 DX를 출력합니다. DX 출력은 시뮬레이터와 무관하며, 필요한 기능만 각 게임에 매핑합니다.

### 디바이스 구성

Teensy 4.1 기반 USB 디바이스 **2대**가 핵심이고, 각각 독립된 스케치를 사용합니다.
여기에 PC 에 직접 붙는 **MFD · LCD** 가 더해집니다.

| 디바이스 | 폴더 | PID | 규모 | 담당 |
|---|---|---|---|---|
| **Left Aux + MISC** | `F16_LEFT_AUX_MISC/` | `0x0487` | DX 51 · 축 4 | Gear, CMDS, TWA, Alt Gear, MISC, HMCS, Pedal |
| **Left Console** | `F16_LEFT_CONSOLE/` | `0x048E` | DX 64 · 축 10 | ECM, ELEC, EPU, AVTR, UHF, ENGINE START, MPO, AUDIO 1/2 |
| **MFD + LCD** | — | — | — | Thrustmaster MFD ×2 (USB) · 7.6인치 정사각 LCD ×2 (HDMI). PC에 직접 연결합니다. MFD 백라이트는 브리지가 게임 조명과 동기화합니다 |
| **ICP** | — | — | — | SimGears ICP (USB). PC에 직접 연결하며, 백라이트는 자체 조절합니다 |

패널별 입력 종류 · LED 구성 · DX 번호 주석은 **[docs/REF_DEVICES.md](docs/REF_DEVICES.md)** 에 있습니다.

---

## 1. 준비물

### 1-1. 패널

콕핏 빌더 전문 업체에서 **구매**하거나, 3D 프린터와 아크릴 레이저 커팅으로 **직접 제작**할 수 있습니다.
본 프로젝트는 [PC Flights](https://pcflights.com/flight-simulator-cockpit-panels/f-16c-viper-home-cockpit-panels/)
구매품인 **MISC · Gear · CMDS 세 장**을 빼고, 나머지 패널 전부를
[Greenisland](https://cults3d.com/en/users/Greenisland/3d-models) 모델로 직접 만들었습니다.

Greenisland 패널은 **Top(아크릴) · Diffuser(아크릴) · LED layer(투명 PLA)** 3 레이어에
백라이트 플레이트가 더해지는 구조입니다 — 패널 한 장에 **아크릴 재단 2종 + 3D 프린트 2종**.

| 구매 — MISC | 구매 — Gear | 구매 — CMDS |
|:----:|:----:|:----:|
| [![MISC](https://pcflights.com/image/cache/catalog/panels/f-16c_viper_misc_panel-600x400.jpg)](https://pcflights.com/f-16c-viper-miscellaneous-misc-panel-flight-sim-part/) | [![Gear](https://pcflights.com/image/cache/catalog/panels/f-16c_viper_landing_gear_panel-600x400.jpg)](https://pcflights.com/f-16c-viper-landing-gear-panel-flight-simulator-module/) | [![CMDS](https://pcflights.com/image/cache/catalog/panels/f-16c_viper_cmds_control_panel-600x400.jpg)](https://pcflights.com/f-16c-viper-cmds-control-panel-module/) |

구매처 · 3D 모델 출처 · 레이어별 재료와 두께 · 도색과 레이저 각인 방법은
**[docs/REF_PANEL.md](docs/REF_PANEL.md)** 에 있습니다.

### 1-2. 3D 프린트 구조물

`3d stl/` 폴더에 STL 21 개가 있습니다. 인클로저 · 스탠드 · 콘솔 · MFD 홀더는 **PLA 또는 PETG**,
패널 `LED layer` 는 **투명 PLA**, 백라이트 플레이트는 **PLA 또는 레진** 으로 출력합니다.

| 인클로저 & 스탠드 | Left Aux 인클로저 | Left Console | MFD 홀더 | 백라이트 플레이트 |
|:----:|:----:|:----:|:----:|:----:|
| <a href="docs/REF_ENCLOSURE.md"><img src="3d%20stl/Center%20Left%20Enclosure.png" width="150"></a> | <a href="docs/REF_ENCLOSURE.md"><img src="3d%20stl/LeftAuxEnclosure.png" width="150"></a> | <a href="docs/REF_ENCLOSURE.md"><img src="3d%20stl/LeftConsoleUpper.png" width="150"></a> | <a href="docs/REF_ENCLOSURE.md"><img src="3d%20stl/LeftMFDHolder.png" width="150"></a> | <a href="docs/REF_ENCLOSURE.md"><img src="3d%20stl/LED%20Plate%20-%20Gear.png" width="150"></a> |
| **2** — 좌우 스탠드<br>Center 인클로저는 구매 모델<br>가공본이라 STL 미포함 | **3** — Enclosure<br>Front · Back | **4** — Upper · Lower<br>Bottom 2 종 | **4** — TM MFD + 7.6" LCD<br>를 함께 잡는 브래킷 | **8** — Left Aux 4<br>Left Console 4, 자작 모델 |

썸네일·치수·STL 링크는 [REF_ENCLOSURE.md](docs/REF_ENCLOSURE.md)에 있습니다.

### 1-3. 부품 목록

스위치, IC, LED, 수동 소자, 커넥터, 모듈 전체 목록은
**[docs/REF_PARTS.md](docs/REF_PARTS.md)** 에 있습니다.

### 1-4. 소요 비용

| 유형 | 업체 | 내용 | 제품 (USD) | 배송 (USD) |
|------|------|------|----:|----:|
| 패널 | [PC Flights](https://pcflights.com) | MISC / Gear / CMDS 패널 3종 | $133 | $31 |
| 아크릴 재단 · 도색 | [아크릴마켓](https://smartstore.naver.com/acrylicmarket) 등 | Greenisland DXF 패널 11종, 패널당 약 ₩10,000 | ~$80 | - |
| 3D 프린트 | [JLC3DP](https://jlc3dp.com) / [PCBWay](https://www.pcbway.com) 등 | 구조물 · 플레이트 [34종](docs/REF_ENCLOSURE.md#출력-수량) | **견적 참조** | - |
| MFD LCD | [Alibaba](https://www.alibaba.com/product-detail/In-Stock-IPS-7-6-Inch_1601257654342.html) | 7.6" 정사각 800×800 IPS ×2, 장당 $58 (드라이버 보드 포함) | $116 | 무료 |
| MCU | [PJRC](https://www.pjrc.com) | Teensy 4.1 ×2 | ~$70 | - |
| 전자부품 | [AliExpress](https://www.aliexpress.com) | MCP23017, 스위치, LED, 저항 등 | ~$200 | - |
| 커스텀 PCB | JLCPCB / PCBWay 등 | TWA · ECM · UHF 디스플레이 3종, 장당 약 $5 | ~$15 | - |
| 노동력 | - | 약 1년간의 설계, 조립, 프로그래밍 | priceless | - |
| | | **합계** | **~$614** | **~$31** |

> 위 금액은 프로젝트 구매 기록을 바탕으로 한 부분 합계입니다. 3D 출력비와 ICP·TQS·MFD·페달 등 표에 없는 품목은 포함하지 않습니다.
> 출력비는 재료와 업체에 따라 달라지므로 [출력물 목록](docs/REF_ENCLOSURE.md#출력-수량)으로 별도 견적을 확인하십시오.

---

## 2. 조립 및 배선

### 2-1. 조립 순서

1. **패널 제작·적층**: Greenisland 패널은 Top(아크릴 2 mm), Diffuser(투명 아크릴 2~3 mm), LED layer(투명 PLA) 순서로 겹칩니다. 스위치는 LED layer에 체결합니다. PC Flights 패널은 전면·후면 2층입니다. 상세는 [REF_PANEL.md](docs/REF_PANEL.md)와 원본 모델의 조립 안내를 따릅니다.
2. **백라이트 설치**: LED 3개와 220Ω 저항으로 스트링을 만들고 별도 플레이트에 고정합니다. 패널과의 간격은 [REF_BACKLIGHT.md](docs/REF_BACKLIGHT.md)를 참고합니다.
3. **인클로저 조립**: 스탠드는 Center 인클로저 뒷면에, MFD 홀더는 아래쪽에 에폭시로 고정합니다. `MFDHolderUpper`는 빈틈을 메우는 부품입니다. Left Console을 TQS와 결합하려면 Mission Pack 또는 더미 덮개를 먼저 분리합니다.
4. **MFD·LCD 장착**: 두 장치를 겹쳐 홀더로 고정하며 서로 접착하지 않습니다. LCD는 외형이 아닌 표시 영역(135.36 × 135.36 mm)을 기준으로 정렬합니다. 아래쪽 FPC 리본의 여유 공간도 확보합니다. 상세는 [REF_MFD_LCD.md](docs/REF_MFD_LCD.md)를 참고합니다.
5. **페달 제작**: 홀 센서 페달 2개를 몰딩 사이에 반대 방향으로 고정하고, 신호를 A16·A17에 연결합니다. 전원은 **3.3V**를 사용합니다. 상세는 [REF_PEDAL.md](docs/REF_PEDAL.md)를 참고합니다.
6. **배선·확인**: 아래 배선도대로 결선한 뒤, 패널을 완전히 고정하기 전에 입력과 표시등을 확인합니다.

### 2-2. 보드별 배선도

케이블 구성, Teensy 핀 배열, MCP GPIO 맵, DX 버튼 맵, 시공 체크리스트가 아래 두 문서에 있습니다. 배선 전에 확인하십시오.

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

AUX 51버튼, 콘솔 64버튼이므로 **두 스케치 모두** 128버튼 Extreme 모드가 필요합니다.

파일 위치: `%LOCALAPPDATA%\Arduino15\packages\teensy\hardware\avr\<version>\cores\teensy4\usb_desc.h`

```c
#define JOYSTICK_SIZE         64    //  12 = normal, 64 = extreme joystick
#define PRODUCT_ID            0x0487  // AUX 보드 / 콘솔 보드는 0x048E
```

두 보드가 `JOYSTICK_SIZE 64`를 공유하므로 빌드 사이에 이 값을 고칠 필요는 없습니다. **`PRODUCT_ID`만 디바이스에 맞게** 바꿔 빌드합니다. 값이 틀리면 각 스케치의 `#error`가 빌드를 막아줍니다.

Extreme 모드의 API는 명명 축 6개와 `slider(1..17)`을 제공합니다.
이 프로젝트는 DirectInput용으로 HID 디스크립터를 8개 축과 나머지 패딩으로 수정합니다.
펌웨어에서 출력하는 축과 게임에서 인식하는 축은 구분해야 합니다.

코어 수정 절차와 업데이트 후 확인 항목은 [teensyduino_upgrade.md](docs/teensyduino_upgrade.md)를 참고하십시오.

### 3-3. 업로드

Arduino IDE에서 해당 `.ino`를 열고 Upload합니다. `usb_desc.h`의 `PRODUCT_ID`가 보드와 일치하는지 먼저 확인하십시오.

| 보드 | 파일 | PRODUCT_ID |
|---|---|---|
| Left Aux + MISC | `F16_LEFT_AUX_MISC/F16_LEFT_AUX_MISC.ino` | `0x0487` |
| Left Console | `F16_LEFT_CONSOLE/F16_LEFT_CONSOLE.ino` | `0x048E` |

라이브러리는 Teensyduino에 포함된 `Wire`, `Keyboard`를 사용합니다.

---

## 4. BMS · DCS 연동

스위치 입력은 USB Joystick으로 직접 전달되지만, **LED 상태는 시뮬레이터에서 받아와야 합니다.** Python 브리지가 시뮬레이터 데이터를 읽어 시리얼로 Teensy에 전송합니다.

```bash
pip install pyserial hidapi
```

- `pyserial` — Teensy 시리얼 통신 (필수)
- `hidapi` — Cougar MFD 백라이트 동기화 (선택, 없으면 MFD 건너뜀)

### 실행

```bash
pythonw tools/bridge.py                          # 트레이 상주 (권장)
python  tools/bridge.py --foreground             # 콘솔 창으로
python  tools/bridge.py COM4:AUX COM5:CONSOLE    # 포트 수동 지정
python  tools/bridge.py --debug --foreground     # LightBits 실시간 출력
```

브리지는 **하나**입니다. 대기 상태에서 BMS 공유 메모리나 DCS-BIOS UDP 중 먼저
잡히는 쪽으로 들어가고, 심이 끝나면 다시 대기로 돌아옵니다. 심보다 먼저 띄워도
됩니다.

`pythonw` 로 띄우면 알림 영역에만 남습니다. 아이콘을 **우클릭**하면 현재 모드
(대기 / Falcon BMS / DCS World)와 `콘솔 보기·숨기기`, `종료` 가 나오고,
**더블클릭**으로도 콘솔을 여닫습니다. 콘솔은 숨어 있을 뿐이라 지난 출력도 그대로
남아 있습니다. 바로가기로 만들 때 아이콘은 `tools/bridge.ico` 를 쓰십시오.

### Falcon BMS (BMS-BIOS)

- `0xAA 0xBB` sync로 자동 감지
- BMS 공유 메모리에서 LED 상태를 읽어 Teensy로 전송
- 프레임: `sync(2) + ledBits(4) + srData(4) + uhfFreq(4) + uhfPreset(1) + XOR(1)` = 16바이트
- Cougar MFD 연결 시 `instrLight`에 따라 백라이트 자동 동기화
- 종료는 IntelliVibe 의 `IsExitGame` 으로 감지합니다

### DCS World (DCS-BIOS)

- `0x55 ×4` sync로 자동 감지
- [DCS-BIOS](https://github.com/DCS-Skunkworks/dcs-bios) 설치 필요

### 키맵 자동 생성

브리지를 종료하고 6초 이상 기다린 뒤 실행합니다. 보드마다 파일을 하나씩 생성합니다.

```powershell
python tools/gen_bms_setup_xml.py
python tools/gen_dcs_profile.py
```

BMS는 장치별 Setup XML에 복사하고, DCS는 해당 장치 열에서 Load Profile로 불러옵니다.
적용 절차와 미매핑 항목은 [REF_KEYMAP.md](docs/REF_KEYMAP.md)를 참고하십시오.

### 프로토콜 자동 감지

Teensy는 수신된 sync 바이트로 BMS/DCS 프로토콜을 자동 판별합니다. 타임아웃(AUX 6초 / 콘솔 3초) 후 프로토콜을 리셋하고 재감지합니다.

**오프라인(브리지 미연결) 동작:**

- AUX 보드: Landing Gear 스위치 상태에 따라 Gear LED 3개를 시뮬레이션 (2초 딜레이 + Gear Warn 5초)
- 콘솔 보드: 모든 LED 소등

---

## 5. 테스트 & 캘리브레이션

### 5-1. 조이스틱 확인

Windows `joy.cpl` 은 **32버튼까지만** 표시합니다. 128버튼을 전부 보려면 별도 도구가 필요합니다.

| 도구 | 비고 |
|---|---|
| **AIM Joystick Probe** (Invictus) | 프로젝트에서 사용한 입력 확인 도구 — `AIM-Joystick-Probe-v1.2.0-Setup.exe` |
| [VKB DevCfg](https://vkbcontrollers.com/?page_id=4609) | 대안 |
| [Joystick Gremlin](https://whitemagic.github.io/JoystickGremlin/) | 대안 |

DX 번호가 배선도의 「DX 버튼 맵」과 맞는지 여기서 확인합니다.

### 5-2. 래더 캘리브레이션 (완료 — 오동작 시에만)

저장된 실측값은 이 프로젝트의 배선 기준입니다. 부품이나 배선이 달라지거나 오인식이 발생하면 다시 측정합니다.

1. `F16_LEFT_AUX_MISC.ino` 또는 `F16_LEFT_CONSOLE.ino`에서 `ALLOW_DEBUG = true` 설정
2. 업로드 후 시리얼 모니터(1000000 baud)에서 각 포지션의 ADC 값 확인
3. `values[]` 배열을 실측값으로 업데이트
4. `ALLOW_DEBUG = false`로 복원 후 재업로드

> 여러 위치의 값이 함께 변하면 기준 전압·GND 또는 접점 문제를 먼저 확인하십시오.
> ECM 풀다운 접점과 백라이트 전류 경로를 점검한 뒤 캘리브레이션합니다.
> (→ 각 배선도의 「저항 래더」 절)

### 5-3. 페달 캘리브레이션

페달은 자동 캘리브레이션을 지원합니다.

- **리셋**: 양 페달 최대 압력 + DN LOCK REL 2초간 홀드
- **브레이크 모드 전환**: Landing Light UP 또는 양 페달 동시 압력

페달 자작 내역과 브레이크/러더 동작의 근거는 **[docs/REF_PEDAL.md](docs/REF_PEDAL.md)** 에 있습니다.

### 5-4. 엔코더 방향 확인

UHF 엔코더를 돌려 DX의 CCW/CW와 게임의 감소/증가 방향을 확인합니다.
현재 핀 배정은 유지하고, 방향을 변경해야 하면 배선과 매핑 표를 먼저 대조하십시오.

---

## 프로젝트 구조

| 경로 | 내용 |
|---|---|
| `F16_LEFT_AUX_MISC/` | AUX·MISC 펌웨어, BIOS 파서, USB 장치명 |
| `F16_LEFT_CONSOLE/` | 콘솔 펌웨어, BIOS 파서, USB 장치명 |
| `tools/` | 통합 브리지(`bridge.py`)와 트레이 아이콘, 키맵 생성기, USB 디스크립터 도구 |
| `tools/keymap/` | 보드 질의, 컨트롤 매핑 표, 축 설정, DCS 명령 카탈로그 |
| `tests/` | 키맵 생성기 회귀 테스트 |
| `docs/` | 제작·배선·설정 문서와 참고 자료, 패널 도면(`GearLedLayout.dxf`) |
| `3d stl/` | 자작 STL과 썸네일 |
| `pcb/uhf_display/` | UHF 디스플레이 거버·BOM·설계 문서 |

## 6. 참조 문서

| 문서 | 내용 |
|---|---|
| [docs/REF_KEYMAP.md](docs/REF_KEYMAP.md) | 장치별 BMS/DCS 키맵 생성·적용·수정 |
| [docs/teensyduino_upgrade.md](docs/teensyduino_upgrade.md) | Teensyduino 업데이트 후 USB 코어 수정 |
| [docs/REF_DEVICES.md](docs/REF_DEVICES.md) | 디바이스 2대의 PID · 담당 패널, 패널별 입력 · LED 구성 |
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
