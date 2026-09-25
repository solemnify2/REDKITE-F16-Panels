# F16 LEFT CONSOLE — 핀 연결 트리

`F16_LEFT_CONSOLE/` 스케치의 물리 배선도입니다.
핀 번호·버튼 번호는 `.ino`의 config 배열에서 그대로 가져온 값입니다.

USB: PID `0x048E`, `JOYSTICK_SIZE 64`.

| 보드 | 구성 | 핀 | DX 버튼 | 축 |
|---|---|---|---|---|
| Teensy 4.1 | 전 패널 + UHF 엔코더 6 + POT 10 + SW 6 | 40 / 42 | 58 | 10 |

표 형식 상세 배치는 [PIN_ASSIGNMENT.md](PIN_ASSIGNMENT.md) 참조.

---

## 케이블 구성

```
  F-16 LEFT CONSOLE — cable tree     solid box = Teensy/panel,  dashed box = MCP module
  (블록 배치는 연결 관계 기준입니다 — 실제 콘솔 패널 배치가 아닙니다)

        ┌───────────────────────────────────────────────────────────────┐
        │ Teensy    STAGE_T40: 4.0  /  STAGE_T41: 4.1                   │
        └───┬─────────────────────────────────────────────────────────┬─┘
            │ I1 (I2C x8)                                             │ C1~C6
            │                       ┌───────────────────────┐         │
            │                       │ ENGINE START + MPO    ├─C1(x9)──┤
            │                       │ JFS x2  ENG CONT  MPO │         │
            │                       │ AB RST ENGDATA MAXPWR │         │
            │                       │ RUN LED               │         │
            │                       └───────────────────────┘         │
            │                                                         │
        ┌╌╌╌┬╌╌╌╌╌╌╌╌╌╌╌┐           ┌───────────────────────┐         │
        ┆ MCP#0  0x20   ├─ C7(x8) ──┤ UHF                   ├─C13(x3)─┤
        ┆               ├─────┐     │ POT x1 (VOL)  ENC x6  ├─C2(x8)──┤
        └╌╌╌┬╌╌╌╌╌╌╌╌╌╌╌┘     │ C8  │ SW x10                ├─C3(x8)──┤
            │ I2(x8)          │(x9) └───────────────────────┘         │
            │                 │     ┌───────────────────────┐         │
            │                 ├─────┤ AUDIO 1       POT x6  ├─C4(x8)──┤
            │                 │     │ COMM MODE rotary x2   │         │
            │                 │     └───────────────────────┘         │
            │                 │     ┌───────────────────────┐         │
            │                 └─────┤ AUDIO 2  POT x3 SW x2 ├─C5(x5)──┤
            │                       └───────────────────────┘         │
        ┌╌╌╌┬╌╌╌╌╌╌╌╌╌╌╌┐           ┌───────────────────────┐         │
        ┆ MCP#1  0x21   ├─ C9(x13) ─┤ ELEC   SW x3  LED x8  │         │
        ┆               ├─C10(x7)┐  └───────────────────────┘         │
        └╌╌╌┬╌╌╌╌╌╌╌╌╌╌╌┘        │  ┌───────────────────────┐         │
            │ I3(x8)             └──┤ EPU    SW x2  LED x3  │         │
            │                       └───────────────────────┘         │
        ┌╌╌╌┬╌╌╌╌╌╌╌╌╌╌╌┐           ┌───────────────────────┐         │
        ┆ MCP#2  0x22   ├─ C11(x7) ─┤ ECM   SW x6  LED x32  ├─C6(x8)──┘
        ┆               ├─C12(x3)┐  │ LADDER x8             │
        └╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘        │  └───────────────────────┘
                                 │  ┌───────────────────────┐
                                 └──┤ AVTR   SW x2          │
                                    └───────────────────────┘

  I2C chain       I1 Teensy>0x20   I2 0x20>0x21   I3 0x21>0x22   (single bus, daisy-chain)

  Teensy direct   C1 ENGINE+MPO    C2 UHF VOL + ENC x3    C3 UHF ENC x3 (T41 only)
                  C4 AUDIO 1 (x6)  C5 AUDIO 2 (x3)        C6 74HC595 3wire + ECM ladder
                  C13 UHF T-TONE + SQUELCH + STATUS
  MCP > panel     C7 0x20>UHF      C8 AUDIO1·2>0x20  C9 0x21>ELEC  C10 0x21>EPU
                  C11 0x22>ECM     C12 0x22>AVTR
  12V             backlight harness, daisy-chained across all panels (not drawn)

  SW=switch  ENC=rotary encoder  POT=potentiometer  LADDER=resistor ladder
```

| 케이블 | 구간 | 내용 | 선 수 |
|---|---|---|---|
| **I1** | Teensy → MCP `0x20` | I2C 체인 시작 | 8선 (LAN) |
| **I2** | MCP `0x20` → MCP `0x21` | I2C 체인 | 8선 (LAN) |
| **I3** | MCP `0x21` → MCP `0x22` | I2C 체인 | 8선 (LAN) |
| **C1** | Teensy → ENGINE START | JFS ×2, ENG CONT, MPO, RUN LED, AB RST, ENG DATA, MAX PWR | 9선 |
| **C2** | Teensy → UHF 패널 | **POT 1개** (VOL) + 엔코더 3 (10MHz, 1MHz, 0.1MHz) | 8선 (LAN) |
| **C3** | Teensy → UHF 패널 | 엔코더 3 (PRESET, 100MHz, 0.025MHz) | 8선 (LAN) |
| **C4** | Teensy → AUDIO 1 | **POT 6개** (COMM CH1, COMM CH2, SECURE, MSL, TF, THREAT) | 8선 (LAN) |
| **C5** | Teensy → AUDIO 2 | **POT 3개** (INTERCOM, TACAN, ILS) | 5선 |
| **C6** | Teensy → ECM 패널 | 74HC595 3선 + ECM 저항 래더 1선 (핀 35~38) | 8선 (LAN) |
| **C7** | MCP `0x20` → UHF 패널 | FUNCTION 4, MODE 3 (=7, PB1~7) + GND | 8선 | 없음 |
| **C8** | AUDIO 1·2 → MCP `0x20` | COMM 1/2 모드 로터리 (PA2~7) + HOT MIC·CIPHER (PA0/PA1) | 9선 | 없음 |
| **C13** | Teensy → UHF 패널 | **UHF T-TONE, SQUELCH, STATUS** (핀 34/33/41) ⚠ 신설 | 4선 |
| **C9** | MCP `0x21` → ELEC 패널 | 스위치 3 (PB0~2) + LED 8 (PA0~7) | 13선 | 없음 |
| **C10** | MCP `0x21` → EPU 패널 | 스위치 2 (PB6~7) + LED 3 (PB3~5) | 7선 | 없음 |
| **C11** | MCP `0x22` → ECM 패널 | ECM 스위치 6 → PB2~PB7 | 7선 | 없음 |
| **C12** | MCP `0x22` → AVTR 패널 | AVTR 스위치 2 → PA6/PA7 | 3선 | 없음 |
| 12V | 어댑터 → 백라이트 | 전 패널 데이지체인 | 2선 | 없음 |

선 수에는 3.3V / GND 가 포함되어 있습니다.

### 토폴로지

| 구분 | 케이블 | 성격 |
|---|---|---|
| Teensy 직결 | `C1`~`C6` | MCP 를 거칠 수 없는 신호 (맨 아래 **「MCP 를 거칠 수 없는 신호」** 참조). 패널마다 독립 배선 |
| I2C 체인 | `I1`→`I2`→`I3` | MCP 3장을 한 줄로 연결 |
| MCP ↔ 패널 | `C7`~`C12` | MCP 모듈에서 바로 옆 패널로 가는 짧은 하니스 (저속 신호뿐이라 리본·낱선 무방) |

LAN 이 필요한 것은 I2C(`I1`~`I3`)와 아날로그·고속선(`C2` `C3` `C6`)뿐입니다.

> **MCP 를 한 기판(확장보드)에 모으지 않습니다.** 실제 콘솔 배치상 `0x22`(ECM·AVTR)과
> `0x21`(ELEC·EPU)이 콘솔의 반대편 끝에 있어, 한 기판에 모으면 어느 한쪽
> 팬아웃이 길어집니다. 그래서 담당 패널 옆에 각각 두고 I2C 로 체인합니다.
> 덕분에 **`C6` 가 통과 배선이 아니라 ECM 직결**이 됩니다 (배선 요령은 **「케이블 C6」** 절).

---

### I2C 체인

Teensy 의 SDA·SCL 한 쌍에서 출발해 MCP 3장을 **한 줄로 꿰는 단일 버스**입니다.
브레이크아웃 모듈의 **2열 7핀 헤더**(한 열로 받고 다른 열로 넘김)가 이 용도입니다.

```
  Teensy ──I1---> MCP#0 0x20 ──I2---> MCP#1 0x21 ──I3---> MCP#2 0x22
  SDA/SCL        next to UHF       next to ELEC       next to ECM
                 C7 > UHF          C9  > ELEC        C11 > ECM
                 C8 < AUDIO 1      C10 > EPU         C12 > AVTR
```

> **버스는 하나입니다.** 풀업도 버스 전체에 대해 한 번만 계산합니다
> (모듈 온보드 4.7kΩ ×3 병렬 ≈ **1.57kΩ**).

> **체인의 대가** — 한 링크가 끊기면 그 **하류 전체**가 버스에서 사라집니다.
> `I1` 이 빠지면 MCP 3장 모두, `I2` 가 빠지면 `0x21`·`0x22` 두 장이 죽습니다.
> 스케치는 **매 루프 I2C 응답을 검사**해(`mcpReadPorts()`) 실패한 칩을 분리 처리하고
> 500ms 마다 재접속을 시도합니다. 이때 그 칩의 스위치는 **전부 릴리즈 상태**로 읽히고
> (`mcpPortCache = 0xFFFF`), `0x21` 의 LED 11개는 꺼진 채 남습니다.
>
> ⚠ **패널에 보이는 경고는 없습니다.** LEFT_AUX 와 달리 콘솔에는 단선 표시등이 없어
> 시리얼 로그(`[MCP@0x2X] ... NOT DETECTED`)로만 알 수 있습니다. 재접속 시 `OLAT` 이
> 0으로 초기화되므로 다음 BMS 프레임(하트비트 약 1초)까지 LED 가 꺼져 있습니다.
> 커넥터 체결을 시공 시 확인하십시오.

> **얻는 것** — 분기 스터브가 없어 반사가 사라지고 총 배선 길이도 짧아집니다.
> Star 구성(3m ×2 = 6m) → 체인(2m + 2m + 0.3m ≈ 4.3m) 으로 줄어
> 버스 용량 약 350pF → **약 265pF**, 라이즈타임 465ns → **약 352ns**.
> 그래도 400kHz 규격(300ns)은 못 맞추므로 `MCP_I2C_CLOCK` 은 **100kHz 유지**입니다.

신호별 Teensy 핀 번호는 아래 **물리 핀 배열**,
MCP 쪽 배치는 그 다음 **MCP23017 모듈 물리 핀 배열**,
DX 버튼 번호는 [PIN_ASSIGNMENT.md](PIN_ASSIGNMENT.md) 를 보십시오.

---

## Teensy 4.1 — 물리 핀 배열

핀 순서는 PJRC 핀아웃 카드([`teensy/card11a_rev4_web.pdf`](teensy/card11a_rev4_web.pdf))
에서 좌표를 추출해 검증했습니다. **양쪽 열 모두 24포지션**이며,
왼쪽 열의 **핀 13과 41 사이에 GND가 하나** 들어갑니다.

> ⚠ **이 그림은 바닥면(납땜면)에서 본 배치입니다** — 기판을 뒤집어 놓고 배선할 때
> 보이는 그대로라 좌우가 PJRC 핀아웃 카드(부품면 기준)와 **반대**입니다.
> 부품면에서 확인할 때는 좌우를 뒤집어 읽으십시오.

```
  ▼ BOTTOM VIEW (기판을 뒤집어 본 모습)

  CABLE   SIGNAL                PIN      PIN   SIGNAL                CABLE
                                  ┌──── USB ────┐
  ---   Vin                  ─────┤ ○         ○ ├─────  GND                  ---
  ---   GND                     ──┤ ○         ○ ├──  0  ENC PRESET  A      C3
  ---   3V3                     ──┤ ○         ○ ├──  1  ENC PRESET  B      C3
  C2    UHF VOL       (A9)   23 ──┤ ○         ○ ├──  2  ENC 100M    A      C3
  C4    AUDIO1 COMM1  (A8)   22 ──┤ ○         ○ ├──  3  ENC 100M    B      C3
  C4    AUDIO1 COMM2  (A7)   21 ──┤ ○         ○ ├──  4  ENC 10M     A      C2
  C4    AUDIO1 SECURE (A6)   20 ──┤ ○         ○ ├──  5  ENC 10M     B      C2
  C4    AUDIO1 MSL    (A5)   19 ──┤ ○         ○ ├──  6  ENC 1M      A      C2
  C4    AUDIO1 TF     (A4)   18 ──┤ ○         ○ ├──  7  ENC 1M      B      C2
  C4    AUDIO1 THREAT (A3)   17 ──┤ ○         ○ ├──  8  ENC 0.1M    A      C2
  C5    AUDIO2 INTCOM (A2)   16 ──┤ ○         ○ ├──  9  ENC 0.1M    B      C2
  C5    AUDIO2 TACAN  (A1)   15 ──┤ ○         ○ ├── 10  ENC 0.025M  A      C3
  C5    AUDIO2 ILS    (A0)   14 ──┤ ○         ○ ├── 11  ENC 0.025M  B      C3
  12V   BACKLIGHT [!]LED     13 ──┤ ○         ○ ├── 12  -- spare --        ---
  ---   GND                  ─────┤ ○         ○ ├─────  3.3V                 ---
  C13   UHF STATUS   (A17)  41 ──┤ ○         ○ ├── 24  I2C SCL2    (A10)  I1
  C1    MPO           (A16)  40 ──┤ ○         ○ ├── 25  I2C SDA2    (A11)  I1
  ---   -- spare --  (A15)  39 ──┤ ○         ○ ├── 26  JFS RUN LED (A12)  C1
  C6    ECM LADDER    (A14)  38 ──┤ ○         ○ ├── 27  JFS pin1    (A13)  C1
  C6    74HC595 ST_CP        37 ──┤ ○         ○ ├── 28  JFS pin2           C1
  C6    74HC595 SH_CP        36 ──┤ ○         ○ ├── 29  ENG CONT           C1
  C6    74HC595 DS           35 ──┤ ○         ○ ├── 30  AB RESET           C1
  C13   UHF T-TONE           34 ──┤ ○         ○ ├── 31  ENG DATA           C1
  C13   UHF SQUELCH          33 ──┤ ○         ○ ├── 32  MAX POWER          C1
                                  └─────────────┘

  [!] pin 13 is shared with the Teensy on-board LED. Used as an OUTPUT here,
      so the on-board LED simply mirrors the backlight state (same as T40).
```

**엔코더 쌍은 모두 같은 엣지에 있습니다.** Teensy 4.1 의 두 엣지는 `0–12`+`24–32` 와
`13–23`+`33–41` 입니다 (위 바닥면 그림에서는 각각 **오른쪽 열**, **왼쪽 열**).
엔코더 6개가 `0–11` 을 **패널 손잡이 순서**(PRESET → 100M → 10M → 1M → 0.1M → 0.025M)
대로 채웁니다. 케이블 기준으로는 **C2 가 `4–9` 연속**, **C3 는 `0–3` + `10–11`** 로 나뉩니다.
엔코더 케이블에서 반대 엣지로 넘어가는 것은 **VOL(`23`) 한 선뿐**입니다.

**`C1` 만 두 엣지로 나뉩니다.** ENGINE 스위치 7개는 `26–32`, **MPO 만 `40`** 입니다.
`24/25` 가 I2C 라 `26–32` 7핀이 그 엣지 하단 블록의 전부여서 8번째 신호를 넣을 자리가
없기 때문입니다. 한 엣지로 몰고 싶으면 MPO 를 여유 핀 `12` 로 옮기면 됩니다
(엔코더 블록 옆이라 `26–32` 와는 떨어집니다).

**여유 핀** — 12, 39(A15) = 2개.

---

## 공통 — MCP23017 모듈 물리 핀 배열


### MCP #0  `0x20` — UHF + AUDIO 1 COMM  (UHF 패널 실장)

```
   LONG EDGE HEADER : single row, 20 pins    CABLE
   -----------------------------------------------
    1  VCC  3.3V                 ---
    2  GND  GND                  C7 C8
    3  PB0  -- spare --           ---
    4  PB1  UHF MODE MNL         C7
    5  PB2  UHF MODE PRESET      C7
    6  PB3  UHF MODE GRD         C7
    7  PB4  UHF FUNCTION OFF     C7
    8  PB5  UHF FUNCTION MAIN    C7
    9  PB6  UHF FUNCTION BOTH    C7
   10  PB7  UHF FUNCTION ADF     C7
   11  VCC  3.3V                 ---
   12  GND  GND                  C7 C8
   13  PA0  AUDIO2 HOT MIC       C8
   14  PA1  AUDIO2 CIPHER        C8
   15  PA2  AUDIO1 COMM1 GD XMT  C8
   16  PA3  AUDIO1 COMM1 SQL     C8
   17  PA4  AUDIO1 COMM1 OFF     C8
   18  PA5  AUDIO1 COMM2 GD XMT  C8
   19  PA6  AUDIO1 COMM2 SQL     C8
   20  PA7  AUDIO1 COMM2 OFF     C8

   ADDRESS JUMPER (3 rows x 2 cols)      [ VCC | GND ]
        A0  ------------------------> GND
        A1  ------------------------> GND
        A2  ------------------------> GND
```

> **주소 점퍼 = 공장 출하 그대로** (A0/A1/A2 전부 GND) → `0x20`.
> **19/20 사용 — PB0 여유 1핀.** STATUS 가 Teensy pin 41 직결(`C13`)로 이설되어 PB0 이 빈 상태입니다.
> `PA0`~`PA7` 은 **AUDIO 패널** 신호입니다 — `PA0/PA1` 은 AUDIO 2 의 HOT MIC·CIPHER,
> `PA2`~`PA7` 은 AUDIO 1 의 COMM 1/2 모드 로터리. 모두 **케이블 C8**(패널 간 점퍼)로 들어옵니다.
> UHF(C7)가 헤더 앞쪽 `PB` 블록에 모여 있어, 모듈이 실장된 UHF 패널 쪽 배선이 짧습니다.
> **T-TONE·SQUELCH·STATUS 는 Teensy 직결**(`C13`)이라 이 모듈을 거치지 않습니다.
> GND 는 두 핀 다 같은 네트이므로, **C7 은 PB 블록 위쪽의 2번**, **C8 은 12번**에
> 물리면 배선이 가장 짧습니다.
> ⚠ **로터리 배선 순서 절대 준수** — FUNCTION `PB4→5→6→7`(OFF→MAIN→BOTH→ADF),
> MODE `PB1→2→3`(MNL→PRESET→GRD).
> COMM1 `PA4→3→2`(OFF→SQL→GD), COMM2 `PA7→6→5`(OFF→SQL→GD) — 개별 `SW_ON_OFF` 로 DX 역순 처리.

### MCP #1  `0x21` — ELEC + EPU  (ELEC 패널 실장)

```
   LONG EDGE HEADER : single row, 20 pins    CABLE
   -----------------------------------------------
    1  VCC  3.3V                 ---
    2  GND  GND                  C9 C10
    3  PB0  ELEC MAIN            C9
    4  PB1  ELEC BATT            C9
    5  PB2  ELEC CAUTION RST     C9
    6  PB3  LED EPU HYDRAZN      C10
    7  PB4  LED EPU AIR          C10
    8  PB5  LED EPU RUN          C10
    9  PB6  EPU OFF              C10
   10  PB7  EPU ON               C10
   11  VCC  3.3V                 ---
   12  GND  GND                  C9 C10
   13  PA0  LED FLCS PMG         C9
   14  PA1  LED MAIN GEN         C9
   15  PA2  LED STBY GEN         C9
   16  PA3  LED EPU GEN          C9
   17  PA4  LED EPU PMG          C9
   18  PA5  LED BATT TO FLCS     C9
   19  PA6  LED FLCS RLY         C9
   20  PA7  LED BATT FAIL        C9

   ADDRESS JUMPER (3 rows x 2 cols)      [ VCC | GND ]
        A0  ------------------------> VCC  <<< MOVE HERE
        A1  ------------------------> GND
        A2  ------------------------> GND
```

> **주소 점퍼: A0 만 VCC 쪽으로 옮기십시오** (A1/A2 는 GND 유지) → `0x21`.
> **20/20 전부 사용 — 여유 없음.** LED 11개가 붙는 칩이라 전류가 가장 큽니다.
> PA0~PA7 ELEC LED 8개가 한 포트에 모여 있어 `OLATA` **1회 쓰기로 8개 동시 갱신**됩니다
> (PB3~PB5 EPU LED 3개 때문에 `OLATB` 가 한 번 더 — 칩당 최대 2회).
> ⚠ **LED 개당 10mA 이하로 잡으십시오.** LED 캐소드 공통을 GND 로 두는 **소싱** 구성이라
> 한계는 `VSS` 150mA 가 아니라 **`VDD` 유입 125mA**(절대최대)입니다. 11 × 12mA = 132mA 는
> 이미 초과이고, 11 × 10 = 110mA 라야 여유가 생깁니다. 더 밝게 쓰려면 애노드를 3.3V 로
> 올려 **싱킹**(`VSS` 150mA 기준)으로 바꾸고 `writeElecLed()` 극성을 반전해야 합니다.
> LED 캐소드 공통은 **19번 핀 GND**(PB7 바로 옆)를 쓰면 배선이 짧습니다.

### MCP #2  `0x22` — ECM + AVTR  (ECM 패널 실장)

```
   LONG EDGE HEADER : single row, 20 pins    CABLE
   -----------------------------------------------
    1  PA7  AVTR ON              C12
    2  PA6  AVTR AUTO            C12
    3  PA5  -- spare --          ---
    4  PA4  -- spare --          ---
    5  PA3  -- spare --          ---
    6  PA2  -- spare --          ---
    7  PA1  -- spare --          ---
    8  PA0  -- spare --          ---
    9  GND  GND                  C12
   10  VCC  3.3V                 ---
   11  PB0  -- spare --          ---
   12  PB1  -- spare --          ---
   13  PB2  ECM OFF              C11
   14  PB3  ECM OPR              C11
   15  PB4  ECM XMIT 3           C11
   16  PB5  ECM XMIT 1           C11
   17  PB6  ECM BIT              C11
   18  PB7  ECM RESET            C11
   19  GND  GND                  C11
   20  VCC  3.3V                 ---

   ADDRESS JUMPER (3 rows x 2 cols)      [ VCC | GND ]
        A0  ------------------------> GND
        A1  ------------------------> VCC  <<< MOVE HERE
        A2  ------------------------> GND
```

> **주소 점퍼: A1 만 VCC 쪽으로 옮기십시오** (A0/A2 는 GND 유지) → `0x22`.
> **PA0~PA5 6핀 + PB0~PB1 2핀 여유** — 프로젝트 전체에서 남은 MCP 확장 여지입니다.
> ECM 스위치는 **PB2~PB7**(19번 핀 GND 바로 옆), AVTR 는 **PA6~PA7**(9번 핀 GND 바로 옆)에
> 배치되어 각각 가까운 GND 핀을 공통 연결하면 됩니다.

### 주소 점퍼 설정

3행 × 2열 솔더 점퍼입니다. 각 행(`A0` `A1` `A2`)을 `VCC` 열 또는 `GND` 열에 연결합니다.
**공장 출하 상태는 3행 모두 `GND` = `0x20`** 입니다.

| 칩 | 주소 | A2 | A1 | A0 | 출하 상태에서 할 일 |
|---|---|---|---|---|---|
| #0 | `0x20` | GND | GND | GND | **그대로 사용** |
| #1 | `0x21` | GND | GND | **VCC** | `A0` 만 VCC 쪽으로 이설 |
| #2 | `0x22` | GND | **VCC** | GND | `A1` 만 VCC 쪽으로 이설 |

> 0Ω 저항을 떼서 옮기거나, 떼어낸 뒤 **납으로 브리지**해도 됩니다.
> **양쪽 동시 연결은 절대 금지** — VCC와 GND가 단락됩니다.
> 이설 후 `i2cdetect` 상당 스캔(스케치 시리얼 로그)으로 `0x20 0x21 0x22` 세 개가
> 모두 보이는지 확인하십시오.


---

## 12V 백라이트 하니스 (별도 어댑터)

신호 케이블과 **물리적으로 분리**해서 포설합니다.

```
  12V ADAPTER (1A)
      │
      ├─ 12V+ ──┬─ ECM ─ ELEC ─ EPU ─ AVTR ─ UHF ─ AUDIO ─ ENGINE ──┐
      │         │       (each strip: LED x3 series + 220Ω = 13.6mA)  │
      │         │                                                      │
      │         │   LED-RTN (cathode common) <─────────────────────────┘
      │         │       │
      │         │     Drain
      │         │       │
      │         │    MOSFET (IRLML6344, N-ch)
      │         │       │
      │         │    Source
      │         │       │
      │         │      GND ─── 12V adapter GND
      │         │
      │         │              Gate
      │         │               ├────┤1kΩ├──── Teensy pin 13
      │         │               │
      │         │              10kΩ
      │         │               │
      │         │              GND
      │
      └─ GND ═══ ! single-point (star) tie to Teensy GND — REQUIRED
```

**어댑터 GND와 Teensy GND를 연결하지 않으면 MOSFET 게이트 기준이 없어 백라이트 제어가
아예 동작하지 않습니다.** 그라운드 루프를 피하려면 한 지점에서만 접속합니다.

### 밝기 제어

| 상태 | 제어 방식 |
|------|-----------|
| **BMS online** | bridge가 `instrLight` → PWM 변환 (adaptive: BRT 미수신 시 DIM=255, 수신 후 DIM=50/BRT=255) |
| **DCS online** | Teensy가 `LIGHT_INST_PNL` (0~65535) → PWM 0~255 직접 변환 |
| **Offline 수동** | UHF STATUS 버튼을 누른 채 AUDIO1 TF pot → PWM 0~255 |
| **Idle 30분** | 자동 꺼짐. 입력 시 복귀 |

---

## 케이블 배선 상세

### 케이블 I1 · I2 · I3 — I2C 체인 (RJ45 T568B)

세 링크 모두 배선이 동일합니다.

| 핀 | 신호 | 페어 | 색상 |
|---|---|---|---|
| 1 | SDA | P2 | 흰/주황 |
| 2 | GND | P2 | 주황 |
| 3 | SCL | P3 | 흰/녹색 |
| 6 | GND | P3 | 녹색 |
| 4 | 3.3V | P1 | 파랑 |
| 5 | GND | P1 | 흰/파랑 |
| 7 | 3.3V (병렬) | P4 | 흰/갈색 |
| 8 | GND | P4 | 갈색 |

신호가 SDA·SCL 2개뿐이라 페어가 둘 남습니다. 남는 2페어를 **전원 병렬**에 써서
급전 임피던스를 낮췄습니다.

> ⚠ **체인이라 전원도 직렬로 흐릅니다.** MCP `0x21` 의 LED 11개(ELEC 8 + EPU 3)
> 전류가 `I1` → `I2` 를 통과합니다 (`I3` 는 `0x22` 의 수 mA 뿐). 개당 12mA 기준 약 132mA 이고,
> Cat5e 24AWG 2가닥 병렬(약 0.042Ω/m)로 4m 이면 강하가 **약 25mV** 라 문제없습니다.
> 다만 LED 전류를 올리거나 체인을 늘리면 이 값이 함께 커집니다.

### 케이블 C2 / C3 — UHF VOL + 엔코더 (RJ45 T568B)

**케이블 C2 — VOL + 엔코더 10M·1M·0.1M**

| 핀 | 신호 | Teensy 핀 | 페어 | 색상 |
|---|---|---|---|---|
| 1 | ENC 10MHz **A** | 4 | P2 | 흰/주황 |
| 2 | ENC 10MHz **B** | 5 | P2 | 주황 |
| 3 | ENC 1MHz **A** | 6 | P3 | 흰/녹색 |
| 6 | ENC 1MHz **B** | 7 | P3 | 녹색 |
| 4 | ENC 0.1MHz **A** | 8 | P1 | 파랑 |
| 5 | ENC 0.1MHz **B** | 9 | P1 | 흰/파랑 |
| 7 | **UHF VOL** | **23 (A9)** | P4 | 흰/갈색 |
| 8 | **GND** | — | P4 | 갈색 |

**케이블 C3 — 엔코더 PRESET·100M·0.025M**

| 핀 | 신호 | Teensy 핀 | 페어 | 색상 |
|---|---|---|---|---|
| 1 | ENC PRESET **A** | 0 | P2 | 흰/주황 |
| 2 | ENC PRESET **B** | 1 | P2 | 주황 |
| 3 | ENC 100MHz **A** | 2 | P3 | 흰/녹색 |
| 6 | ENC 100MHz **B** | 3 | P3 | 녹색 |
| 4 | ENC 0.025MHz **A** | 10 | P1 | 파랑 |
| 5 | ENC 0.025MHz **B** | 11 | P1 | 흰/파랑 |
| 7 | GND | — | P4 | 흰/갈색 |
| 8 | GND | — | P4 | 갈색 |

**UHF 로만 Teensy 케이블이 세 가닥(`I1` `C2` `C3`) 가는 이유** — 100kHz I2C 를 나머지와
격리하기 위해서입니다. 스위치 10개는 패널 옆 MCP `0x20` 가 받으므로 `I1` 은 SDA/SCL
2선으로 끝나고, 아날로그인 VOL 만 `C2` 로 빼냅니다.

**VOL 을 I2C 케이블에서 뺀 이유** — VOL 은 아날로그인데 `I1` 의 SDA/SCL 은 100kHz 로
스위칭합니다. 같은 케이블에 두면 인접 페어 크로스토크를 그대로 받습니다.
반면 엔코더는 **사람이 손으로 돌리는 기계식 접점**이라 빠른 엣지가 없어, VOL 과 한
케이블에 있어도 서로 간섭하지 않습니다. `C2` 의 P4 에서 **VOL/GND 트위스트 페어**를
이루므로 아날로그 리턴 경로도 전용으로 확보됩니다.

**엔코더는 A/B 를 같은 페어에 묶습니다.** 신호마다 전용 GND 리턴을 주려면 페어가 8개
필요해 LAN 3가닥이 되는데, 위와 같은 이유로 그럴 필요가 없습니다.
엔코더 공통 단자는 GND 로, **전원은 필요 없습니다** (내부 풀업 `INPUT_PULLUP` 사용).


---

### 케이블 C6 — ECM 직결 (RJ45 T568B)

| 핀 | 신호 | 페어 | 색상 |
|---|---|---|---|
| 1 | DS | P2 | 흰/주황 |
| 2 | GND | P2 | 주황 |
| 3 | **ECM 래더** | P3 | 흰/녹색 |
| 6 | GND | P3 | 녹색 |
| 4 | **SH_CP** | P1 | 파랑 |
| 5 | GND | P1 | 흰/파랑 |
| 7 | ST_CP | P4 | 흰/갈색 |
| 8 | **3.3V** | P4 | 갈색 |

**래더(P3)와 SH_CP(P1)를 서로 다른 페어에 배치**하는 것이 핵심입니다. 각자 전용 GND
리턴을 가지므로 고주파 리턴 전류가 상대 페어의 접지 기준을 통과하지 않습니다.

> RJ45 핀 3과 6은 같은 페어(녹색)입니다. 번호 순서대로 묶으면 트위스트 페어가 깨집니다.

---

## 리소스 사용

| 항목 | 값 |
|---|---|
| **Teensy 헤더 핀** | **40 / 42** (여유 2) |
| ├ 아날로그 입력 | 11 / 18 (여유 ADC: A15 = 1개) |
| └ 여유 핀 | 12, 39 |
| **MCP23017 GPIO** | 39 / 48 |
| 74HC595 출력 | 32 / 32 ⚠ |
| **DX 버튼** | **58 / 128** |
| 조이스틱 축 | 10 / 23 |
| I2C 주소 | `0x20` `0x21` `0x22` |

---

## 시공 체크리스트

| # | 항목 |
|---|---|
| 1 | **UHF 로터리 연속 배선** — MCP#0 에서 FUNCTION = PB4→5→6→7 (OFF→ADF), MODE = PB1→2→3 (MNL→GRD). STATUS 는 Teensy pin 41 직결 |
| 2 | **AUDIO COMM 로터리 배선** — MCP#0 에서 COMM1 = PA4→3→2 (OFF→SQL→GD), COMM2 = PA7→6→5 (OFF→SQL→GD) (케이블 C8) |
| 3 | **C6 페어 배치** — LAN 에서 **래더/GND 와 SH_CP/GND 를 서로 다른 페어**에 (→ 「케이블 C6」 절) |
| 4 | **래더 필터 캡** — 1~10nF 세라믹을 Teensy A14(핀 38) 바로 옆에 |
| 5 | **아날로그선 트위스트** — ECM 래더, UHF VOL, AUDIO 와이퍼 6개를 각각 GND와 페어링 |
| 6 | **12V 어댑터 공통 GND** — Teensy GND와 단일점 연결 (누락 시 백라이트 제어 불가) |
| 7 | **I2C 풀업 추가 금지** — 모듈 온보드 **4.7kΩ ×3 병렬 ≈ 1.57kΩ**. 체인 전체가 한 버스라 풀업은 한 번만 셉니다. 전원 off 상태에서 `SDA↔VCC` 저항을 재서 확인 |
| 8 | **MCP `RST` 핀** — 이 모듈은 온보드 풀업이 있어 **미결선 가능**. 실측(`RST↔VCC` ≈ 4.7kΩ)으로 확인하고, 없으면 VCC 직결 |
| 9 | **MCP 모듈 위치** — `0x20` UHF 패널 옆 · `0x21` ELEC 패널 옆 · `0x22` ECM 패널 옆 |
| 10 | **MCP 주소 점퍼** — 출하 상태(전부 GND) = `0x20`. `0x21` 은 **A0만**, `0x22` 는 **A1만** VCC 쪽으로 이설. 양쪽 동시 연결 금지 |
| 11 | **I2C 핫플러그 보호** — SDA/SCL 직렬 100Ω, 각 보드 3.3V에 10µF + 100nF. 체인 **총 길이 5m 이내**(`I1`+`I2`+`I3` 합산이 라이즈타임을 결정) |
| 12 | **MCP#1 LED 전류** — LED **11개**(PA0~7 8개 + PB3~5 3개). 소싱 구성이라 `VDD` 유입 **125mA** 가 한계 → **개당 10mA 이하** (11 × 10 = 110mA) |
| 13 | **핀 13** — 백라이트 **출력**. 온보드 LED 공유는 출력이라 무해하고 LED가 상태 표시등이 됨. **입력으로는 쓰지 말 것** (LED 경로 때문에 상시 눌림 위험) |
| 14 | **엔코더 방향** — CW/CCW가 반대면 `encoders[]` 의 `pinA`/`pinB` 교체 |
| 15 | **⚠ Teensy 3.3V 레일** — ECM 32 LED(74HC595)와 MCP LED 11개가 **전부 Teensy 3.3V 레귤레이터**에서 나옵니다. 전점등 시 약 430mA 로 PJRC 권장 **250mA** 를 넘습니다. 세리머니 순차 점등은 필수이고, 상시 여유가 필요하면 **74HCT595 를 5V(Vin) 급전**으로 바꾸십시오 (HCT 는 VIH 2.0V 라 3.3V 로직으로 구동 가능, 직렬저항 재계산 필요) |
| 16 | **74HC595 패키지 전류** — VCC/GND 절대최대 약 **70mA/칩**. 정상 운용은 칩당 2점등(약 20mA)이라 무관하지만 **세리머니·`ALL_LIT` 상태에서 8점등**이면 초과합니다 |
| 17 | **USB 포트** — `welcomeCeremony()` 피크가 약 548mA. USB 2.0(500mA)에서는 순차 점등으로 변경 |

---

## MCP 를 거칠 수 없는 신호

| 신호 | 이유 |
|---|---|
| 74HC595 제어 3선 | 32비트 시프트 = MCP 경유 시 약 38ms (루프 예산 초과) |
| ECM 저항 래더 | MCP23017에 ADC 없음 |
| 로터리 엔코더 12선 | 인터럽트 필요 — I2C 폴링으로 펄스 유실 |
| POT 10개 | MCP23017에 ADC 없음 |

이 신호들만 Teensy 직결입니다. 나머지 **스위치 28 GPIO 와 LED 11개는 전부 I2C 2선**에
실립니다 (`0x20` 15 + `0x21` 16 + `0x22` 8 = 39 GPIO).
