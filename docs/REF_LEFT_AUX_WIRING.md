# F16 LEFT AUX + MISC — 배선도

`F16_LEFT_AUX_MISC/` 스케치의 물리 배선도입니다.
핀 번호·버튼 번호는 `.ino`의 config 배열에서 그대로 가져온 값입니다.

- **Board**: Teensy 4.1 (헤더 핀 0–41)
- **USB**: PID `0x0489`, `JOYSTICK_SIZE 64` (128버튼) — 콘솔 장치(`0x048E`)와 헤더 공유
- **I2C**: `Wire` — SDA = pin 18, SCL = pin 19 @ 100kHz, MCP23017 1장 (`0x20`, MISC 패널)
- **DX 버튼 51, 축 4**, 메인 루프 20Hz

케이블 이름(C1~C7, M1, I1)은 이 문서에서 부여한 명명입니다.

---

## 케이블 구성

```
  F-16 LEFT AUX + MISC — cable tree     solid box = Teensy/panel,  dashed box = MCP module
  (블록 배치는 연결 관계 기준입니다 — 실제 콘솔 패널 배치가 아닙니다)

        ┌───────────────────────────────────────────────────────────────┐
        │ Teensy 4.1    LEFT AUX + MISC    PID 0x0489                   │
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
                                    │ LED x8 (GO/NOGO/DISP/RDY) ├─C7(x5)──┤
                                    └───────────────────────┘         │
                                    ┌───────────────────────┐         │
                                    │ TWA                   ├─C3(x5)──┤
                                    │ LADDER x1  LED x4     │         │
                                    └───────────────────────┘         │
                                    ┌───────────────────────┐         │
                                    │ ALT GEAR   SW x1      ├─C4(x1)──┤
                                    └───────────────────────┘         │
                                    ┌───────────────────────┐         │
                                    │ HMCS       POT x1     ├─C5(x1)──┤
                                    └───────────────────────┘         │
                                    ┌───────────────────────┐         │
                                    │ PEDALS     POT x2     ├─C6(x2)──┘
                                    └───────────────────────┘

  I2C             I1 Teensy(18/19) > 0x20 — 스타 토폴로지, LAN (아래 "I1 — LAN 배선" 참조)
  Teensy direct   C1 GEAR   C2 CMDS   C3 TWA   C4 ALT GEAR   C5 HMCS   C6 PEDALS
                  C7 CMDS 램프 — 하단 SD 패드에서 15핀 FPC 확장 케이블로 인출 (42 미사용)
  MCP > panel     M1 0x20 > MISC (모듈-패널 하니스)
  12V             backlight: pin 13 PWM 1kHz > MOSFET > 별도 12V 어댑터

  xN = 신호선 수 (3.3V/GND 제외)   SW = switch GPIO 수   LADDER = resistor ladder   POT = potentiometer
```

| 케이블 | 구간 | 내용 | 신호 수 |
|---|---|---|---|
| **I1** | Teensy → MCP `0x20` | I2C (SDA 18, SCL 19) | 2 (LAN, +3.3V/GND) |
| **M1** | MCP `0x20` → MISC 패널 | 스위치 GPIO 11 + LED 3 | 14 |
| **C1** | Teensy → GEAR 패널 | 스위치 GPIO 13 + LED 4 (Nose/Left/Right/Warn) | 17 |
| **C2** | Teensy → CMDS 패널 | 스위치 8 + 래더 2 (MODE, PRGM) | 10 |
| **C3** | Teensy → TWA 패널 | 래더 1 + LED 4 | 5 |
| **C4** | Teensy → ALT GEAR | Handle (Reset 미연결) | 1 |
| **C5** | Teensy → HMCS | Symbology 1개 (Brightness / Contrast 미연결) | 1 |
| **C6** | Teensy → 페달 | 포트 2 (Left / Right) | 2 |
| **C7** | Teensy 하단 SD 패드 → CMDS 램프 | LED 8 (DISPENSE RDY 5 / NO GO 2 / GO 1) on 5 pins | 5 (+GND, LAN 6심, pin 42 미사용) |
| 12V | 별도 12V 어댑터 → 백라이트 | 게이트는 핀 13 PWM 1kHz (MOSFET) | 2 |

콘솔 장치와 달리 MCP가 1장뿐이라 **I2C는 체인이 아닌 스타(단일 링크)**입니다.
MCP 단선 시 **GEAR WARN LED가 점등**되어 패널에서 바로 알 수 있고 (콘솔에는 없는 표시등),
500ms 간격으로 재접속을 시도합니다.

---

## I1 — LAN 배선 (Teensy ↔ MISC 패널)

Teensy(AUX 통) ↔ MCP23017(MISC 패널) 간 Cat5e 한 가닥에 I2C·백라이트 12V·3.3V 를 함께 싣습니다.

### LAN 핀 배정

| Pin | Pair | Signal | 비고 |
|-----|------|--------|------|
| 1 | Pair 1 (Orange) | SDA | |
| 2 | Pair 1 | GND | SDA 리턴 |
| 3 | Pair 2 (Green) | SCL | |
| 6 | Pair 2 | GND | SCL 리턴 |
| 4 | Pair 3 (Blue) | 12V dimmed | MOSFET 출력 (PWM) |
| 5 | Pair 3 | LED return | GND |
| 7 | Pair 4 (Brown) | 3.3V | MCP23017 전용 |
| 8 | Pair 4 | GND | 3.3V 리턴 |

### 회로도

#### AUX 통 (Teensy 측)

```
                 4.7kΩ
Teensy 3.3V ──┬──┤├──── Teensy SDA (18) ──────────── LAN pin 1
              │
              └──┤├──── Teensy SCL (19) ──────────── LAN pin 3
                 4.7kΩ

GND ──────────────────────────────────────────────── LAN pin 2
GND ──────────────────────────────────────────────── LAN pin 6

Teensy pin 13 ──[1kΩ]──┬── MOSFET Gate
                      [10kΩ]
                        │
                       GND
12V ─────────── MOSFET Drain
                MOSFET Source ────────────────────── LAN pin 4 (dimmed 12V)
                                              ┌──── LAN pin 5 (LED return)
                                              │
                                             GND

3.3V ─────────────────────────────────────────────── LAN pin 7
GND ──────────────────────────────────────────────── LAN pin 8
```

#### MISC 패널 (MCP23017 측)

```
LAN pin 1 ──[100Ω]── SDA ── MCP23017 SDA
LAN pin 3 ──[100Ω]── SCL ── MCP23017 SCL
LAN pin 2 ── GND
LAN pin 6 ── GND

LAN pin 4 ── LED+ (12V dimmed)
LAN pin 5 ── LED- (LED return)

LAN pin 7 ── 3.3V ──┬──┬── MCP23017 VDD
                     │  │
                   10uF 100nF
                     │  │
LAN pin 8 ── GND ───┴──┴── MCP23017 GND
```

### 보호 부품

| 위치 | 부품 | 값 | 용도 |
|------|------|----|------|
| AUX | 풀업 저항 | 4.7kΩ x2 | I2C 풀업 (SDA, SCL -> 3.3V) |
| AUX | Gate 직렬 저항 | 1kΩ | MOSFET 스위칭 링잉 방지 |
| AUX | Gate 풀다운 저항 | 10kΩ | 핫플러그 시 MOSFET OFF 유지 |
| AUX | MOSFET | IRLML6244 (SOT-23) | N-ch logic-level, Vgs(th) ~1V |
| MISC | 직렬 저항 | 100Ω x2 | SDA/SCL 돌입전류 제한 (래치업 방지) |
| MISC | 전해캡 | 10uF (10V+) | MCP VDD 핫플러그 스파이크 흡수 |
| MISC | 세라믹캡 | 100nF | MCP VDD 고주파 노이즈 필터 (핀 근접 배치) |

### 불필요한 부품

| 부품 | 사유 |
|------|------|
| TVS 다이오드 | 3.3V/12V USB 전원 수준, 과전압 파괴 위험 없음 |
| 페라이트 비드 | 저전류 (~1mA), 노이즈 문제 없음 |
| 100uF+ 대용량 캡 | 과잉, 돌입전류만 증가 |
| 외부 풀업 (MISC측) | AUX측 4.7kΩ로 충분 (1m 이내) |

### 설계 근거

- **I2C 풀업 4.7kΩ**: 1m 이내 Cat5e에서 Teensy 내부 풀업(~22kΩ)으로도 동작하나, 외부 4.7kΩ이 더 안정적
- **100Ω 직렬**: 핫플러그 시 핀 접촉 순서 불규칙 → 과도 전류 제한. I2C 100~400kHz에 영향 미미
- **10kΩ 풀다운**: LAN 미연결/핫플러그 시 Gate 플로팅 → MOSFET 의도치 않게 ON 방지
- **Pair 3 (12V + LED return)**: 꼬임쌍 내 전류 왕복 → 자기장 상쇄, 다른 쌍과 간섭 최소
- **MISC 백라이트 전류**: 3 strips x 13.6mA = 41mA @12V → Cat5e 1선(0.5A 한계)의 8%

---

## Teensy 4.1 물리 핀 배열

핀 순서는 PJRC 핀아웃 카드([`teensy/card11a_rev4_web.pdf`](teensy/card11a_rev4_web.pdf)) 기준.
**양쪽 열 모두 24포지션**, 왼쪽 열의 핀 13과 41 사이에 GND가 하나 들어갑니다.

> ⚠ **이 그림은 바닥면(납땜면)에서 본 배치입니다** — 기판을 뒤집어 놓고 배선할 때
> 보이는 그대로라 좌우가 PJRC 핀아웃 카드(부품면 기준)와 **반대**입니다.
> 부품면에서 확인할 때는 좌우를 뒤집어 읽으십시오. LEFT_CONSOLE 도면과 같은 기준입니다.

```
  ▼ BOTTOM VIEW (기판을 뒤집어 본 모습)

  CABLE SIGNAL                   PIN                    PIN SIGNAL                   CABLE
                                      ┌──── USB ────┐
  ---   Vin                      ─────┤ ○         ○ ├─────  GND                      ---
  ---   GND                      ─────┤ ○         ○ ├──  0  -- spare --              --
  ---   3V3                      ─────┤ ○         ○ ├──  1  DN LOCK REL              C1
  C2    CMDS FL            (A9)  23 ──┤ ○         ○ ├──  2  HORN SILENCER            C1
  C2    CMDS CH            (A8)  22 ──┤ ○         ○ ├──  3  LANDING LIGHT 1          C1
  C2    CMDS O2            (A7)  21 ──┤ ○         ○ ├──  4  LANDING LIGHT 2          C1
  C2    CMDS O1            (A6)  20 ──┤ ○         ○ ├──  5  STORE CAT                C1
  I1    I2C SCL            (A5)  19 ──┤ ○         ○ ├──  6  ANTI SKID 1              C1
  I1    I2C SDA            (A4)  18 ──┤ ○         ○ ├──  7  ANTI SKID 2              C1
  C2    CMDS RWR           (A3)  17 ──┤ ○         ○ ├──  8  BRAKES CHANNEL           C1
  C2    CMDS JMR           (A2)  16 ──┤ ○         ○ ├──  9  GND JETT ENABLE          C1
  C2    CMDS MWS           (A1)  15 ──┤ ○         ○ ├── 10  EMER JETTISON            C1
  C2    CMDS JETT          (A0)  14 ──┤ ○         ○ ├── 11  HOOK                     C1
  12V   BACKLIGHT [!]LED         13 ──┤ ○         ○ ├── 12  GEAR WARN LED            C1
  ---   GND                      ─────┤ ○         ○ ├─────  3.3V                     ---
  C6    PEDAL RIGHT       (A17)  41 ──┤ ○         ○ ├── 24  TWA LADDER        (A10)  C3
  C6    PEDAL LEFT        (A16)  40 ──┤ ○         ○ ├── 25  CMDS MODE LDR     (A11)  C2
  C5    HMCS SYMBOL       (A15)  39 ──┤ ○         ○ ├── 26  CMDS PRGM LDR     (A12)  C2
  --    -- spare --       (A14)  38 ──┤ ○         ○ ├── 27  -- spare --       (A13)  --
  C3    TWA ACT LED              37 ──┤ ○         ○ ├── 28  LANDING GEAR UP          C1
  C3    TWA SEARCH LED           36 ──┤ ○         ○ ├── 29  LANDING GEAR DN          C1
  C3    TWA LOW LED              35 ──┤ ○         ○ ├── 30  NOSE GEAR LED            C1
  C3    TWA POWER LED            34 ──┤ ○         ○ ├── 31  LEFT GEAR LED            C1
  C4    ALTGEAR HANDLE           33 ──┤ ○         ○ ├── 32  RIGHT GEAR LED           C1
                                      └─────────────┘

  [!] pin 13 is shared with the Teensy on-board LED. Used as an OUTPUT here,
      so the on-board LED simply mirrors the backlight state (same as LEFT_CONSOLE).

  pin 27 conflict resolved: Gear Warn LED moved to pin 12.

  -- spare -- = 여유 핀 (미사용). pin 0, pin 27 (A13), pin 38 (A14)
```

헤더 42핀 외에 **하단 SD 패드** 5개(43·44·45·46·47)를 CMDS 램프가 씁니다. 42 는 미사용.
FPC 배선표는 아래 **CMDS 램프** 절에 있습니다.

---
  --    -- spare --           0 ──┤ ○         ○ ├──     GND                  ---
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
  --    -- spare --   (A13)  27 ──┤ ○         ○ ├── 38  -- spare --  (A14)  --
  C1    LANDING GEAR UP      28 ──┤ ○         ○ ├── 37  TWA ACT LED         C3
  C1    LANDING GEAR DN      29 ──┤ ○         ○ ├── 36  TWA SEARCH LED      C3
  C1    NOSE GEAR LED        30 ──┤ ○         ○ ├── 35  TWA LOW LED         C3
  C1    LEFT GEAR LED        31 ──┤ ○         ○ ├── 34  TWA POWER LED       C3
  C1    RIGHT GEAR LED       32 ──┤ ○         ○ ├── 33  ALTGEAR HANDLE      C4
                                  └─────────────┘

  [!] pin 13 is shared with the Teensy on-board LED. Used as an OUTPUT here,
      so the on-board LED simply mirrors the backlight state (same as LEFT_CONSOLE).

  pin 27 conflict resolved: Gear Warn LED moved to pin 12.

  -- spare -- = 여유 핀 (미사용). pin 0, pin 27 (A13), pin 38 (A14)
```

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

## CMDS 램프 — 하단 SD 패드 (C7)

헤더 42핀이 모두 차 있어 **LED 8개를 하단 microSD 패드 5핀**에서 뽑습니다.
15핀 FPC 확장 케이블로 인출하며, 한 핀에 LED 2개를 병렬로 다는 자리가 셋입니다.
드라이버 IC 는 없습니다.

`DISPENSE RDY` 는 LED 가 5개라 한 핀으로는 전류가 모자랍니다. 핀 셋에 2+1+2 로 나눠 달고
브릿지가 같은 `Rdy` 비트를 세 항목에 보내므로 함께 점등합니다.

> **`DISPENSE` 와 `RDY` 는 한 램프입니다** — 범례가 두 단어로 나뉘어 보여도 BMS 가 주는
> 신호는 `Rdy` 하나뿐입니다. CMDS 상단 지시등은 GO / NO GO / DISPENSE RDY **셋**이고
> (`TO-BMS1F-16CM-1.pdf` p.34), `FlightData.h` 의 EWS 비트도
> `Rdy = 0x200 // Status message: DISPENSE RDY` 가 유일합니다.
> `Degr` 0x100 은 **AUTO DEGR** 로 별개 램프이며 지금은 쓰지 않습니다.

| FPC | microSD 핀 | SDIO | SPI2 | Teensy 핀 | 용도 | BMS `lightBits2` (offset 124) |
|---|---|---|---|---|---|---|
| 15 | 6 | VSS | — | **GND** | **LED 공통 캐소드** |  |
| 14 | 8 | DAT1 | MISO2 | 42 | 미사용 |  |
| 13 | 6 | VSS | — | GND |  |  |
| 12 | 7 | DAT0 | MOSI2 | **43** | **NO GO 1·2** (병렬) | `NoGo` `0x80` |
| 11 | 6 | VSS | — | GND |  |  |
| 10 | 5 | CLK | CS2 | **44** | **GO** | `Go` `0x40` |
| 9 | 6 | VSS | — | GND |  |  |
| 8 | 4 | VDD | — | 3.3V | 미사용 — LED 는 핀에서 직접 구동 |  |
| 7 | 6 | VSS | — | GND |  |  |
| 6 | 3 | CMD | SCK2 | **45** | **DISP 1·2** (병렬) | `Rdy` `0x200` |
| 5 | 6 | VSS | — | GND |  |  |
| 4 | 2 | DAT3 | — | **46** | **DISP 3** | `Rdy` `0x200` |
| 3 | 6 | VSS | — | GND |  |  |
| 2 | 1 | DAT2 | — | **47** | **RDY 1·2** (병렬) | `Rdy` `0x200` |
| 1 | 6 | VSS | — | GND |  |  |

핀↔µSD 대응은 `docs/teensy/card11b_rev4_web.pdf` 기준입니다. SD 소켓은 SDIO 배선이라
`CMD` 가 `SCK2` 핀에, `DAT0` 가 `MOSI2` 핀에 올라갑니다.

> 확장 케이블 제품마다 패드 번호 표기가 다를 수 있으니, 연결 후 `ALLOW_DEBUG`
> 또는 LED 를 하나씩 켜 보며 매핑을 확인하세요. 순서가 다르면 `leds[]` 의 핀 번호만 바꾸면 됩니다.

### 결선

LED 는 Teensy 핀이 소스(HIGH = 점등)이고, 캐소드는 전부 FPC GND 에 공통입니다.
저항은 **320Ω = 220Ω + 100Ω 직렬**. 병렬 자리도 **LED 마다 따로** 답니다.

**병렬 때문에 320Ω 입니다.** 보드의 다른 LED(ECM·GEAR·TWA)는 220Ω 인데, 병렬 자리는
한 핀이 두 가닥 전류를 함께 흘려서 220Ω 이면 핀당 약 9.8mA 로 Teensy 권장치(연속 10mA)에
여유가 없어집니다. 320Ω 이면 7.1mA 로 떨어지고, 단독 자리와 밝기도 맞습니다.

```
   핀 ──┬──[320Ω]──►├──┐
        └──[320Ω]──►├──┤     ✗ 저항 하나를 공유하면 Vf 편차로
                       │        전류가 한쪽으로 쏠립니다
   GND ────────────────┘
```

### 실측

LED 1개만 연결한 상태에서 **320Ω 양단 = 1.2V** → 단독 전류 **3.75mA**.
여기서 역산하면 이 전류에서의 Vf 는 2.0~2.06V 로, 다이오드 모드 측정값 1.99V(약 1mA)와
전류 상승분까지 들어맞습니다.

| 자리 | LED | 가지당 | 핀 합계 |
|---|---|---|---|
| 병렬 2개 (핀 47 · 45 · 43) | 2 | 약 3.5mA | 약 **7.1mA** |
| 단독 (핀 46 · 44) | 1 | **3.75mA** (실측) | **3.75mA** |

8개 전부 켜도 합계 약 **25mA** 입니다.

> **LED 색 주의** — Vf 가 3.0V 를 넘는 고휘도 녹색·청색은 3.3V 로 제대로 켜지지 않습니다.
> 고휘도 자체는 괜찮습니다 — 같은 전류에서 더 밝으니 오히려 유리합니다. 일반 녹색(GaP,
> Vf 2.1V) 중에서 `Iv` 100mcd@20mA 이상, 지향각 60° 이상, 산광형을 고르세요.
> 고Vf LED 가 꼭 필요하면 5V + ULN2003A 싱크 드라이버 경로가 필요합니다.

### 케이블

신호 5 + GND = **6심**이라 LAN 케이블 한 가닥에 들어갑니다.

> DCS-BIOS 는 아직 이 램프를 구동하지 않습니다 (BMS 전용). DCS 주소 맵을 확인한 뒤 `DcsBiosParser.h` 에 추가하면 됩니다.

---

## DX 버튼 맵 (51 / 128)

버튼 번호는 `switches[]` → `analogBtnArrays[]` 순서로 런타임에 자동 배정됩니다.

| 버튼 | 패널 | 신호 |
|---|---|---|
| 1–2 | MISC | RF |
| 3 | MISC | Laser ARM |
| 4 | MISC | ALT REL (NC — DX 반전) |
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
| 34–37 | TWA | 래더 — ACT/PWR, SEARCH, ALT, SYS PWR |
| 38–44 | CMDS | MODE 래더 — 1~7 |
| 45–51 | CMDS | PRGM 래더 — BIT, 1~6 |

---

## 조이스틱 축 (4 / 23)

| 축 | 신호 | 핀 |
|---|---|---|
| Z | HMCS Symbology | 39 (A15) |
| Xrotate | Left Brake | 40 (A16) |
| Yrotate | Right Brake | 41 (A17) |
| Zrotate | Rudder | 좌우 페달 조합으로 계산 |

페달은 브레이크/러더 겸용 — Landing Light UP 또는 양 페달 동시 압력으로 브레이크 모드 전환.
캘리브레이션 리셋: 양 페달 최대 + DN LOCK REL 2초.

---

## 리소스 사용

| 항목 | 값 |
|---|---|
| **Teensy 헤더 핀** | **39 / 42** (여유 3개: pin 0, A13, A14) |
| **하단 SD 패드** | **5 / 6** (CMDS 램프 5핀, 42 = 미사용) |
| ├ 아날로그 입력 | 6 / 18 (래더 3 + HMCS 1 + 페달 2) — A0~A9 는 CMDS 스위치·I2C 가 디지털로 점유 |
| └ 여유 핀 | 3개 (pin 0, A13, A14) |
| **MCP23017 GPIO** | 14 / 16 (여유 PA6, PB7) |
| LED | 16 (GEAR 4 + TWA 4 + MISC 3 + CMDS 5핀/8LED) |
| **DX 버튼** | **51 / 128** (switches 33 + ladder 18) |
| 조이스틱 축 | 4 / 23 |
| I2C | `Wire`(18/19) 100kHz, `0x20` 1장 |
| 메인 루프 | 20Hz (50ms) |

---

## 시공 체크리스트

| # | 항목 |
|---|---|
| 1 | ~~핀 27 충돌~~ **해결됨** — Gear Warn LED 를 핀 12 로 이설. 핀 27(A13)은 여유 |
| 2 | ~~핀 13 확인~~ **해결됨** — 백라이트 출력으로 변경. 온보드 LED가 백라이트 상태를 표시 (LEFT_CONSOLE과 동일). 핀 0은 여유 |
| 3 | **래더 캘리브레이션** — TWA·CMDS MODE·PRGM. PWM 디밍 방식 변경 후 BL OFF/ON 값 동일(±4)하여 1세트로 통합. `ALLOW_DEBUG = true` 로 실측 |
| 4 | **I2C 핫플러그 보호** — SDA/SCL 직렬 100Ω, 보드 3.3V에 10µF + 100nF (위 "I1 — LAN 배선" 절). 단선 시 GEAR WARN 점등, 500ms 재접속 |
| 5 | **MCP 주소 점퍼** — 출하 상태 그대로 (`0x20`) |
| 6 | **백라이트** — 핀 13 PWM 1kHz → MOSFET → 별도 12V 어댑터 (Step-Up은 래더 ADC 노이즈 유발). 오프라인 수동 밝기: DN LOCK REL 누른 채 HMCS Symbology pot (A15, 방향 반전). 배선은 위 "I1 — LAN 배선" 절 참조 |
| 7 | **스위치 배선** — 전부 액티브 로우 + 내부 풀업 (공통 단자 GND) |
| 8 | **CMDS 램프** — 하단 15핀 FPC 확장 케이블 → 5핀으로 LED 8개 (개별 320Ω = 220+100 직렬, 캐소드는 FPC 15 공통). pin 42 = 미사용. 병렬 자리 핀당 약 7.1mA. Vf 3.0V 이상 LED 는 쓰지 말 것 |
