# F16 LEFT AUX + MISC — 핀 연결 트리

`F16_LEFT_AUX_MISC/` 스케치의 물리 배선도입니다.
핀 번호·버튼 번호는 `.ino`의 config 배열에서 그대로 가져온 값입니다.

- **Board**: Teensy 4.1 (헤더 핀 0–41)
- **USB**: PID `0x0487`, `JOYSTICK_SIZE 64` (128버튼) — 콘솔 장치(`0x048E`)와 헤더 공유
- **I2C**: `Wire` — SDA = pin 18, SCL = pin 19 @ 100kHz, MCP23017 1장 (`0x20`, MISC 패널)
- **DX 버튼 49, 축 6**, 메인 루프 20Hz

케이블 이름(C1~C6, M1, I1)은 이 문서에서 부여한 명명입니다.
관련 문서: [misc_panel_spec.md](misc_panel_spec.md) · [backlight_spec.md](backlight_spec.md) ·
[hotplug_spec.md](hotplug_spec.md) · [stepup_en_control.md](stepup_en_control.md)

---

## 케이블 구성

```
  F-16 LEFT AUX + MISC — cable tree     solid box = Teensy/panel,  dashed box = MCP module
  (블록 배치는 연결 관계 기준입니다 — 실제 콘솔 패널 배치가 아닙니다)

        ┌───────────────────────────────────────────────────────────────┐
        │ Teensy 4.1    LEFT AUX + MISC    PID 0x0487                   │
        └───┬─────────────────────────────────────────────────────────┬─┘
            │ I1 (I2C, LAN)                                           │ C1~C7
        ┌╌╌╌┬╌╌╌╌╌╌╌╌╌╌╌┐           ┌───────────────────────┐         │
        ┆ MCP#0  0x20   ├─ M1(x14) ─┤ MISC                  │         │
        └╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘           │ SW x11  LED x3        │         │
                                    └───────────────────────┘         │
                                    ┌───────────────────────┐         │
                                    │ GEAR                  ├─C1(x17)─┤
                                    │ SW x13  LED x4        │         │
                                    └───────────────────────┘         │
                                    ┌───────────────────────┐         │
                                    │ CMDS                  ├─C2(x10)─┤
                                    │ SW x8  LADDER x2      │         │
                                    │ LED x6 (GO/NOGO/RDY)  ├─C7(x6)──┤
                                    └───────────────────────┘         │
                                    ┌───────────────────────┐         │
                                    │ TWA                   ├─C3(x5)──┤
                                    │ LADDER x1  LED x4     │         │
                                    └───────────────────────┘         │
                                    ┌───────────────────────┐         │
                                    │ ALT GEAR   SW x2      ├─C4(x2)──┤
                                    └───────────────────────┘         │
                                    ┌───────────────────────┐         │
                                    │ HMCS       POT x3     ├─C5(x3)──┤
                                    └───────────────────────┘         │
                                    ┌───────────────────────┐         │
                                    │ PEDALS     POT x2     ├─C6(x2)──┘
                                    └───────────────────────┘

  I2C             I1 Teensy(18/19) > 0x20 — 스타 토폴로지, LAN (hotplug_spec.md 준용)
  Teensy direct   C1 GEAR   C2 CMDS   C3 TWA   C4 ALT GEAR   C5 HMCS   C6 PEDALS
                  C7 CMDS 램프 — 헤더가 아니라 하단 SD 패드(42~47)에서 SD 확장 케이블로 인출
  MCP > panel     M1 0x20 > MISC (모듈-패널 하니스)
  12V             backlight: pin 0 PWM > MOSFET > 스텝업 5V→12V (backlight_spec.md, not drawn)

  xN = 신호선 수 (3.3V/GND 제외)   SW = switch GPIO 수   LADDER = resistor ladder   POT = potentiometer
```

| 케이블 | 구간 | 내용 | 신호 수 |
|---|---|---|---|
| **I1** | Teensy → MCP `0x20` | I2C (SDA 18, SCL 19) | 2 (LAN, +3.3V/GND) |
| **M1** | MCP `0x20` → MISC 패널 | 스위치 GPIO 11 + LED 3 | 14 |
| **C1** | Teensy → GEAR 패널 | 스위치 GPIO 13 + LED 4 (Nose/Left/Right/Warn) | 17 |
| **C2** | Teensy → CMDS 패널 | 스위치 8 + 래더 2 (MODE, PRGM) | 10 |
| **C3** | Teensy → TWA 패널 | 래더 1 + LED 4 | 5 |
| **C4** | Teensy → ALT GEAR | Handle, Reset | 2 |
| **C5** | Teensy → HMCS | 포트 3 (Brightness / Contrast / Symbology) | 3 |
| **C6** | Teensy → 페달 | 포트 2 (Left / Right) | 2 |
| **C7** | Teensy 하단 SD 패드 → CMDS 램프 | LED 6 (GO 1 / NO GO 2 / RDY 3) | 6 (+GND, LAN 7심) |
| 12V | 스텝업 → 백라이트 | 게이트는 핀 0 PWM | 2 |

콘솔 장치와 달리 MCP가 1장뿐이라 **I2C는 체인이 아닌 스타(단일 링크)**입니다.
MCP 단선 시 **GEAR WARN LED가 점등**되어 패널에서 바로 알 수 있고 (콘솔에는 없는 표시등),
500ms 간격으로 재접속을 시도합니다.

---

## Teensy 4.1 물리 핀 배열

핀 순서는 PJRC 핀아웃 카드([`teensy/card11a_rev4_web.pdf`](teensy/card11a_rev4_web.pdf)) 기준.
**양쪽 열 모두 24포지션**, 오른쪽 열의 핀 13과 41 사이에 GND가 하나 들어갑니다.

```
  CABLE   SIGNAL                PIN      PIN   SIGNAL                CABLE
                                  ┌──── USB ────┐
  ---   GND                  ─────┤ ○         ○ ├─────  Vin                  ---
  C4    ALTGEAR RST           0 ──┤ ○         ○ ├──     GND                  ---
  C1    DN LOCK REL           1 ──┤ ○         ○ ├──     3V3                  ---
  C1    HORN SILENCER         2 ──┤ ○         ○ ├── 23  CMDS FL       (A9)  C2
  C1    LANDING LIGHT 1       3 ──┤ ○         ○ ├── 22  CMDS CH       (A8)  C2
  C1    LANDING LIGHT 2       4 ──┤ ○         ○ ├── 21  CMDS O2       (A7)  C2
  C1    STORE CAT             5 ──┤ ○         ○ ├── 20  CMDS O1       (A6)  C2
  C1    ANTI SKID 1           6 ──┤ ○         ○ ├── 19  I2C SCL       (A5)  I1
  C1    ANTI SKID 2           7 ──┤ ○         ○ ├── 18  I2C SDA       (A4)  I1
  C1    BRAKES CHANNEL        8 ──┤ ○         ○ ├── 17  CMDS RWR      (A3)  C2
  C1    GND JETT ENABLE       9 ──┤ ○         ○ ├── 16  CMDS JMR      (A2)  C2
  C1    EMER JETTISON        10 ──┤ ○         ○ ├── 15  CMDS MWS      (A1)  C2
  C1    HOOK                 11 ──┤ ○         ○ ├── 14  CMDS JETT     (A0)  C2
  C1    GEAR WARN LED        12 ──┤ ○         ○ ├── 13  BACKLIGHT [!]LED    12V
  ---   3.3V                 ─────┤ ○         ○ ├─────  GND                  ---
  C3    TWA LADDER    (A10)  24 ──┤ ○         ○ ├── 41  PEDAL RIGHT  (A17)  C6
  C2    CMDS MODE LDR (A11)  25 ──┤ ○         ○ ├── 40  PEDAL LEFT   (A16)  C6
  C2    CMDS PRGM LDR (A12)  26 ──┤ ○         ○ ├── 39  HMCS SYMBOL  (A15)  C5
  C5    HMCS BRIGHT   (A13)  27 ──┤ ○         ○ ├── 38  HMCS CONTRAST(A14)  C5
  C1    LANDING GEAR UP      28 ──┤ ○         ○ ├── 37  TWA ACT LED         C3
  C1    LANDING GEAR DN      29 ──┤ ○         ○ ├── 36  TWA SEARCH LED      C3
  C1    NOSE GEAR LED        30 ──┤ ○         ○ ├── 35  TWA LOW LED         C3
  C1    LEFT GEAR LED        31 ──┤ ○         ○ ├── 34  TWA POWER LED       C3
  C1    RIGHT GEAR LED       32 ──┤ ○         ○ ├── 33  ALTGEAR HANDLE      C4
                                  └─────────────┘

  [!] pin 13 is shared with the Teensy on-board LED. Used as an OUTPUT here,
      so the on-board LED simply mirrors the backlight state (same as LEFT_CONSOLE).

  pin 27 conflict resolved: Gear Warn LED moved to pin 12.
      pin 27 (A13) is now HMCS Brightness only.
```

### 하단 SD 패드 — CMDS 램프 (C7)

헤더 42핀이 모두 차 있어 **CMDS 램프 6개는 하단 microSD 패드에서 뽑습니다.**
SD 확장 케이블을 끼우면 납땜 없이 6신호 + 3.3V + GND 가 한 번에 나옵니다
(LEFT_CONSOLE 의 UHF 디스플레이와 같은 방식). SD 카드는 쓰지 않으므로 충돌이 없습니다.

| microSD 핀 | 신호 | Teensy 핀 | 용도 |
|---|---|---|---|
| 1 | DAT2 | **47** | CMDS RDY 3 |
| 2 | CD/DAT3 (CS2) | **44** | CMDS NO GO 2 |
| 3 | CMD (MOSI2) | **43** | CMDS NO GO 1 |
| 4 | VDD | 3.3V | (미사용 — LED 는 핀에서 직접 구동) |
| 5 | CLK (SCK2) | **45** | CMDS RDY 1 |
| 6 | VSS | GND | LED 공통 캐소드 |
| 7 | DAT0 (MISO2) | **42** | CMDS GO |
| 8 | DAT1 | **46** | CMDS RDY 2 |

> 확장 케이블 제품마다 패드 번호 표기가 다를 수 있으니, 연결 후 `ALLOW_DEBUG`
> 또는 LED 를 하나씩 켜 보며 매핑을 확인하세요. 순서가 다르면 `leds[]` 의 핀 번호만 바꾸면 됩니다.

---

## MCP23017 모듈 물리 핀 배열

### MCP #0  `0x20` — MISC 패널 실장

```
   LONG EDGE HEADER : single row, 20 pins
   -----------------------------------------
    1  PA7  ECM LED
    2  PA6  -- spare --
    3  PA5  RF pos2
    4  PA4  RF pos1
    5  PA3  LASER ARM
    6  PA2  ALT REL
    7  PA1  MASTER ARM pos2
    8  PA0  MASTER ARM pos1
    9  GND  GND
   10  VCC  3.3V
   11  PB0  ADV STANDBY LED
   12  PB1  ADV ACTIVE LED
   13  PB2  ADV MODE
   14  PB3  ROLL AP pos1
   15  PB4  ROLL AP pos2
   16  PB5  PITCH AP pos1
   17  PB6  PITCH AP pos2
   18  PB7  -- spare --
   19  GND  GND
   20  VCC  3.3V

   ADDRESS JUMPER (3 rows x 2 cols)      [ VCC | GND ]
        A0  ------------------------> GND
        A1  ------------------------> GND
        A2  ------------------------> GND
```

> **주소 점퍼 = 공장 출하 그대로** (A0/A1/A2 전부 GND) → `0x20`.
> 여유 GPIO 는 **PA6, PB7** 두 개입니다.
> 스위치는 전부 입력(내부 풀업), LED 3개(PA7, PB0, PB1)는 출력입니다.

---

## CMDS 램프 (GO / NO GO / RDY)

LED **6개를 Teensy 핀에 1:1 직결**합니다. 드라이버 IC 가 없습니다.
BMS 신호는 3개뿐이라, 브릿지가 NO GO 비트를 LED 2개에, RDY 비트를 LED 3개에 **같은 값으로** 내려보냅니다.
그래서 그룹은 항상 함께 켜지면서도, 펌웨어 쪽에서는 LED 하나하나가 독립 제어 가능한 상태로 남습니다.

| 램프 | LED | Teensy 핀 | `leds[]` 인덱스 | BMS `lightBits2` (offset 124) |
|---|---|---|---|---|
| GO | 1 | 42 | 11 | `Go` `0x40` |
| NO GO | 2 | 43, 44 | 12, 13 | `NoGo` `0x80` |
| RDY | 3 | 45, 46, 47 | 14, 15, 16 | `Rdy` `0x200` |

### 결선

```
   Teensy 42 ──[ R ]──►├── GO
   Teensy 43 ──[ R ]──►├── NO GO 1
   Teensy 44 ──[ R ]──►├── NO GO 2        LED 는 핀이 소스(HIGH = 점등),
   Teensy 45 ──[ R ]──►├── RDY 1          캐소드는 전부 GND 공통
   Teensy 46 ──[ R ]──►├── RDY 2
   Teensy 47 ──[ R ]──►├── RDY 3
                        │
   SD GND ──────────────┴───────── GND
```

LED 마다 **개별 직렬저항**을 답니다. 3.3V 구동이므로

  R = (3.3V − Vf) / I ≈ (3.3 − 2.0) / 8mA ≈ 160Ω → **180Ω** (적색 기준)

밝으면 330~470Ω 으로 올리면 됩니다. 핀당 8mA, 6개 합쳐 약 48mA 로
Teensy 4.1 GPIO 한계(핀당 연속 10mA 권장) 안에 들어옵니다.

> **LED 색 주의** — Vf 가 3.0V 를 넘는 고휘도 녹색·청색은 3.3V 로 제대로 켜지지 않습니다.
> 기존 GEAR·TWA LED 와 같은 종류(3.3V 직결로 동작하는 것)를 쓰세요.
> 굳이 고Vf LED 를 써야 하면 5V + ULN2003A 싱크 드라이버 경로가 필요합니다.

### 케이블

신호 6 + GND = **7심**이라 LAN 케이블 한 가닥에 들어갑니다.

> DCS-BIOS 는 아직 이 램프를 구동하지 않습니다 (BMS 전용). DCS 주소 맵을 확인한 뒤 `DcsBiosParser.h` 에 추가하면 됩니다.

---

## DX 버튼 맵 (49 / 128)

버튼 번호는 `switches[]` → `analogBtnArrays[]` 순서로 런타임에 자동 배정됩니다.

| 버튼 | 패널 | 신호 |
|---|---|---|
| 1–2 | MISC | RF |
| 3 | MISC | Laser ARM |
| 4 | MISC | ALT REL |
| 5–6 | MISC | Master ARM |
| 7 | MISC | ADV MODE |
| 8–9 | MISC | Roll AP |
| 10–11 | MISC | Pitch AP |
| 12 | GEAR | EMER Jettison |
| 13 | GEAR | Store CAT |
| 14 | GEAR | Horn Silencer |
| 15–16 | GEAR | Landing Light |
| 17 | GEAR | Hook |
| 18–19 | GEAR | Landing Gear UP / DN |
| 20 | GEAR | DN LOCK REL (콤보 모디파이어 겸용) |
| 21 | GEAR | GND JETT ENABLE |
| 22–23 | GEAR | ANTI SKID |
| 24 | GEAR | BRAKES Channel |
| 25–31 | CMDS | RWR, JMR, MWS, O1, O2, CH, FL |
| 32 | CMDS | JETT |
| 33 | ALT GEAR | Handle |
| 34 | ALT GEAR | Reset |
| 35–38 | TWA | 래더 — ACT/PWR, SEARCH, ALT, SYS PWR |
| 39–44 | CMDS | MODE 래더 — 1~6 |
| 45–49 | CMDS | PRGM 래더 — BIT, 1~4 |

---

## 조이스틱 축 (6 / 23)

| 축 | 신호 | 핀 |
|---|---|---|
| X | HMCS Brightness | 27 (A13) |
| Y | HMCS Contrast | 38 (A14) |
| Z | HMCS Symbology | 39 (A15) |
| Xrotate | Left Brake | 40 (A16) |
| Yrotate | Right Brake | 41 (A17) |
| Zrotate | Rudder | 좌우 페달 조합으로 계산 |

페달은 브레이크/러더 겸용 — Landing Light UP 또는 양 페달 동시 압력으로 브레이크 모드 전환.
캘리브레이션 리셋: 양 페달 최대 + EMER Jettison 2초.

---

## 리소스 사용

| 항목 | 값 |
|---|---|
| **Teensy 헤더 핀** | **42 / 42** (여유 없음) |
| **하단 SD 패드** | **6 / 6** (42~47 = CMDS 램프) |
| ├ 아날로그 입력 | 8 / 18 (래더 3 + HMCS 3 + 페달 2) — A0~A9 는 CMDS 스위치·I2C 가 디지털로 점유 |
| └ 여유 핀 | 없음 |
| **MCP23017 GPIO** | 14 / 16 (여유 PA6, PB7) |
| LED | 17 (GEAR 4 + TWA 4 + MISC 3 + CMDS 6) |
| **DX 버튼** | **49 / 128** |
| 조이스틱 축 | 6 / 23 |
| I2C | `Wire`(18/19) 100kHz, `0x20` 1장 |
| 메인 루프 | 20Hz (50ms) |

---

## 시공 체크리스트

| # | 항목 |
|---|---|
| 1 | ~~핀 27 충돌~~ **해결됨** — Gear Warn LED 를 핀 12 로 이설. 핀 27(A13)은 HMCS Brightness 전용 |
| 2 | ~~핀 13 확인~~ **해결됨** — 백라이트 출력으로 변경. 온보드 LED가 백라이트 상태를 표시 (LEFT_CONSOLE과 동일). ALT GEAR Reset은 핀 0으로 이설 |
| 3 | **래더 캘리브레이션** — TWA·CMDS MODE·PRGM 은 백라이트 ON/OFF 두 세트(`values[]` / `valuesBlOn[]`)를 각각 보정. `ALLOW_DEBUG = true` 로 실측 |
| 4 | **I2C 핫플러그 보호** — SDA/SCL 직렬 100Ω, 보드 3.3V에 10µF + 100nF ([hotplug_spec.md](hotplug_spec.md)). 단선 시 GEAR WARN 점등, 500ms 재접속 |
| 5 | **MCP 주소 점퍼** — 출하 상태 그대로 (`0x20`) |
| 6 | **백라이트** — 핀 0 PWM → MOSFET → 5V→12V 스텝업 ([backlight_spec.md](backlight_spec.md), [stepup_en_control.md](stepup_en_control.md)). 오프라인 수동 제어: DN LOCK REL 누른 채 Landing Light 조작 |
| 7 | **스위치 배선** — 전부 액티브 로우 + 내부 풀업 (공통 단자 GND) |
| 8 | **CMDS 램프** — 하단 SD 확장 케이블 → LED 6개 직결(각 180Ω, 캐소드 GND 공통). 확장 케이블 핀 매핑을 실측 확인하고, Vf 3.0V 이상 LED 는 쓰지 말 것 |
