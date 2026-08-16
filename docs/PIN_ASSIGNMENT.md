# REDKITE F16 LEFT CONSOLE — Teensy 4.1 Pin Assignment

패널: ECM / ELEC / EPU / AVTR / UHF / ENGINE START / MPO / AUDIO 1-2

- **Board**: Teensy 4.1 (헤더 핀 0–41, 아날로그 A0–A17)
- **USB**: PID `0x048E`, `JOYSTICK_SIZE 64` (128버튼)
- **I2C**: `Wire2` — SCL2 = pin 24, SDA2 = pin 25 @ 100kHz
- **사용 31 / 42핀, 여유 11핀** (12, 28–37)

> **이 문서는 STAGE_T41(Teensy 4.1 전체 구성) 기준입니다.**
> Teensy 4.0 임시 구성(엔코더를 제외한 전 패널, 19핀, DX 41, 축 7)은
> [LEFT_CONSOLE_PIN_TREE.md](LEFT_CONSOLE_PIN_TREE.md#stage_t40--teensy-40) 참조.
> 두 단계에서 **버튼 1~41과 축 7개가 완전히 동일**합니다 — 확장 시 재바인딩이 필요 없습니다.

> UHF 스위치 10개와 AUDIO 1 COMM 1/2 모드 로터리 2개는 패널 위 **MCP23017 `0x20`** 가 받습니다.
> 덕분에 Teensy 직결 핀 16개가 절약되고, UHF 케이블도 17선으로 줄어듭니다.

> 배선 트리(케이블·패널 단위 연결도)는 [LEFT_CONSOLE_PIN_TREE.md](LEFT_CONSOLE_PIN_TREE.md) 참조.

> 이전 Teensy 4.0 배치는 `F16_LEFT_CONSOLE/backup/` 참조.

---

## Teensy 4.1 핀 전체

| 핀 | ADC | 패널 | 신호 |
|-----|-----|------|------|
| 0 / 1 | | UHF | 엔코더 10MHz (A / B) |
| 2 / 3 | | UHF | 엔코더 1MHz (A / B) |
| 4 / 5 | | UHF | 엔코더 0.1MHz (A / B) |
| 6 / 7 | | UHF | 엔코더 PRESET (A / B) |
| 8 / 9 | | UHF | 엔코더 100MHz (A / B) |
| 10 / 11 | | UHF | 엔코더 0.025MHz (A / B) |
| 12 | | – | **여유** |
| 13 | | – | 백라이트 MOSFET 게이트 (ON/OFF, 디밍 없음) — 온보드 LED 공유, 출력이라 무해 |
| 14 | A0 | ECM | 74HC595 ST_CP (LATCH) |
| 15 | A1 | ECM | 74HC595 SH_CP (CLOCK) |
| 16 | A2 | ECM | 74HC595 DS (DATA) |
| 17 | A3 | ECM | 8버튼 저항 래더 |
| 18 | A4 | ENGINE | ENG CONT (PRI / SEC) |
| 19 | A5 | ENGINE | **JFS RUN LED** (출력) |
| 20 | A6 | ENGINE | JFS pin2 (START 2) |
| 21 | A7 | ENGINE | JFS pin1 (START 1) |
| 22 | A8 | MPO | MANUAL PITCH OVERRIDE |
| 23 | A9 | UHF | VOL 포트 |
| 24 | A10 | – | I2C SCL2 |
| 25 | A11 | – | I2C SDA2 |
| 26 | A12 | AUDIO 2 | ILS VOL |
| 27 | A13 | AUDIO 2 | INTERCOM |
| **28–37** | | – | **여유 10** (비ADC) |
| 38 | A14 | AUDIO 1 | THREAT VOL |
| 39 | A15 | AUDIO 1 | MSL VOL |
| 40 | A16 | AUDIO 1 | COMM CH2 |
| 41 | A17 | AUDIO 1 | COMM CH1 |

### 확장기를 통과할 수 없는 신호

| 신호 | 이유 |
|------|------|
| 74HC595 3선 (14, 15, 16) | 32비트 시프트 = MCP 경유 시 약 38ms 소요 (루프 예산 초과) |
| ECM 저항 래더 (17) | MCP23017에 ADC 없음 |
| 엔코더 12선 | 인터럽트 필요 — I2C 폴링으로 펄스 유실 |
| 포트 7개 | MCP23017에 ADC 없음 |

---

## MCP23017 — 3칩, 40 / 48 GPIO

MCP 핀 번호: **GPA0–7 = 0–7, GPB0–7 = 8–15**

### `0x20` — UHF + AUDIO 1 COMM (UHF 패널 실장)

| GPIO | 신호 | 타입 |
|------|------|------|
| GPA0–GPA3 | UHF FUNCTION (OFF / MAIN / BOTH / ADF) | 4단 로터리 |
| GPA4–GPA6 | UHF MODE (MNL / PRESET / GRD) | 3단 로터리 |
| GPA7 | UHF SQUELCH | ON/OFF |
| GPB0 | UHF T-TONE | 모멘터리 |
| GPB1 | UHF STATUS | 모멘터리 |
| GPB2–GPB4 | AUDIO1 COMM 1 MODE (OFF / SQL / GD XMT) | 3단 로터리 |
| GPB5–GPB7 | AUDIO1 COMM 2 MODE (OFF / SQL / GD XMT) | 3단 로터리 |

> `SW_ROTARY` 는 `pin1` 부터 연속 GPIO 를 읽습니다 — 패널 배선 순서 필수.

### `0x21` — ELEC + EPU (ELEC 패널 실장)

| GPIO | 신호 | 타입 |
|------|------|------|
| GPA0 / GPA1 | ELEC MAIN PWR (BATT / OFF / MAIN) | ON/OFF/ON |
| GPA2 | ELEC CAUTION RST | 모멘터리 |
| GPA3 / GPA4 | EPU (OFF / NORM / ON) | ON/OFF/ON |
| GPA5 | **EPU HYDRAZN LED** | 출력 |
| GPA6 | **EPU AIR LED** | 출력 |
| GPA7 | **EPU RUN LED** | 출력 |
| GPB0 | LED FLCS PMG | 출력 |
| GPB1 | LED MAIN GEN | 출력 |
| GPB2 | LED STBY GEN | 출력 |
| GPB3 | LED EPU GEN | 출력 |
| GPB4 | LED EPU PMG | 출력 |
| GPB5 | LED FLCS RLY | 출력 |
| GPB6 | LED BATT FAIL | 출력 |
| GPB7 | LED BATT TO FLCS | 출력 |

> LED 8개를 GPB 포트에 몰아둔 덕에 `OLATB` **1회 쓰기로 8개 동시 갱신**됩니다.
> **개당 10mA 이하**로 유지하세요 — 이 칩에 LED 가 11개(GPB 8 + GPA5~7 3) 붙고,
> 캐소드 공통 GND = 소싱 구성이라 한계가 `VDD` 유입 **125mA** 입니다 (11 × 10 = 110mA).

### `0x22` — ECM + AVTR (ECM 패널 실장)

| GPIO | 신호 | 타입 |
|------|------|------|
| GPA0 / GPA1 | ECM OPR/STBY (OPR / OFF / STBY) | ON/OFF/ON |
| GPA2 / GPA3 | ECM XMIT (1 / 2 / 3) | ON/OFF/ON |
| GPA4 | ECM BIT | 모멘터리 |
| GPA5 | ECM RESET | 모멘터리 |
| GPA6 / GPA7 | AVTR (OFF / AUTO / ON) | ON/OFF/ON |
| GPB0–GPB7 | 여유 8 | |

---

## 조이스틱 축 (7 / 23)

Extreme 조이스틱(`JOYSTICK_SIZE 64`)은 명명 축 6개 + `slider(1..17)` = **23채널**입니다.

| 축 | 신호 | 핀 |
|----|------|-----|
| X | AUDIO COMM CH1 | 41 (A17) |
| Y | AUDIO COMM CH2 | 40 (A16) |
| Z | AUDIO MSL VOL | 39 (A15) |
| Xrotate | AUDIO THREAT VOL | 38 (A14) |
| Yrotate | AUDIO INTERCOM | 27 (A13) |
| Zrotate | AUDIO ILS VOL | 26 (A12) |
| `slider(1)` | UHF VOL | 23 (A9) |

여유 슬라이더 16채널.

---

## DX 버튼 맵 (53 / 128)

| 버튼 | 패널 | 신호 |
|------|------|------|
| 1–2 | ECM | OPR / STBY |
| 3–4 | ECM | XMIT 1 / XMIT 3 |
| 5 | ECM | BIT |
| 6 | ECM | RESET |
| 7–8 | ELEC | BATT / MAIN |
| 9 | ELEC | CAUTION RST |
| 10–11 | AVTR | AUTO / ON |
| 12–13 | ENGINE | JFS START 1 / START 2 |
| 14 | ENGINE | ENG CONT |
| 15 | MPO | MANUAL PITCH OVERRIDE |
| 16–17 | EPU | NORM / ON |
| 18–21 | UHF | FUNCTION OFF / MAIN / BOTH / ADF |
| 22–24 | UHF | MODE MNL / PRESET / GRD |
| 25 | UHF | SQUELCH |
| 26 | UHF | T-TONE |
| 27 | UHF | STATUS |
| 28–30 | AUDIO 1 | COMM 1 MODE — OFF / SQL / GD XMT |
| 31–33 | AUDIO 1 | COMM 2 MODE — OFF / SQL / GD XMT |
| 34–41 | ECM | 저항 래더 — ECM 1~6, FRM, SPL |
| 42–53 | UHF | 엔코더 6개 × (CW / CCW) |

---

## ECM 저항 래더 (PCB 고정)

10kΩ 직렬 체인 + 20kΩ 풀다운. `ADC_k = 1023 × 20000 / (k × 10000 + 20000)`

| 버튼 | 기대값 | 인접 경계 | 노이즈 여유 |
|------|--------|-----------|-------------|
| ECM 1 | 1024 | 852 | ±172 |
| ECM 2 | 680 | 594 | ±86 |
| ECM 3 | 509 | 457 | ±52 |
| ECM 4 | 406 | 372 | ±34 |
| ECM 5 | 338 | 314 | ±24 |
| ECM 6 | 290 | 271 | ±18 |
| ECM FRM | 253 | 239 | **±14** |
| ECM SPL | 225 | 239 | **±14** |

**판별은 최근접값(nearest-value) 방식**입니다. 창 겹침으로 인한 동시 매칭·오인식이 구조적으로 발생하지 않습니다. 8회 오버샘플링으로 ADC 노이즈가 약 ±2카운트라 최악 조합(FRM/SPL)에서도 7배 마진을 확보합니다.

`maxDist = 60` 을 넘으면 무입력으로 처리합니다 (대기 시 ADC ≈ 0).

> 12비트(`analogReadResolution(12)`)로 올리려면 `ecmBtnValues[]`와 `maxDist`를 모두 **×4** 해야 합니다. 현재는 기존 캘리브레이션을 보존하기 위해 10비트를 유지합니다.

---

## 74HC595 — ECM LED 32개 (변경 없음)

ECM 1~6 / FRM / SPL × (S, A, F, T). `srMap[]`이 논리 인덱스를 물리 출력으로 리맵합니다.

**32 / 32 전부 사용 중.** 칩을 추가하면 BMS-BIOS 프레임의 `srData` 32비트를 초과하므로 `BB_FRAME_PAYLOAD`, 양쪽 `BmsBiosParser.h`, `bmsbios_bridge.py`를 모두 수정해야 합니다.

---

## 배선 — 패널별

### 간선 (Teensy에서 나가는 케이블 8가닥)

| 케이블 | 대상 | 신호 | 내역 | 합계 |
|---|------|------|------|------|
| **1** | ENGINE + MPO | 5 | JFS ×2, ENG CONT, MPO, **RUN LED** | **6선** (+GND) |
| **I1** | UHF 패널 · I2C | 2 | SDA, SCL | **8선** (LAN, +3.3V ×2, GND ×4) |
| **C2** | UHF 패널 · VOL + 엔코더 | 7 | **POT 1개**(VOL) + 10MHz, 1MHz, 0.1MHz × A/B | **8선** (LAN, +GND) |
| **C3** | UHF 패널 · 엔코더 | 6 | PRESET, 100MHz, 0.025MHz × A/B | **8선** (LAN, +GND ×2) |
| **C4** | AUDIO 1 | 4 | **POT 4개** — COMM CH1, COMM CH2, MSL VOL, THREAT VOL (38–41, 오른쪽 연속) | **6선** (+3.3V, GND) |
| **C5** | AUDIO 2 | 2 | **POT 2개** — INTERCOM, ILS VOL (26–27, 왼쪽 연속) | **4선** (+3.3V, GND) |
| **C6** | ECM 패널 | 4 | DS, SH_CP, ST_CP, ECM래더 | **8선** (LAN, +3.3V, GND ×3) |


> `C3` 는 **STAGE_T41 전용**입니다. `C2` 는 T40 에서도 VOL 때문에 필요하지만
> 엔코더 6선은 미결선으로 둡니다.

### 패널 간 점퍼 (Teensy 미경유)

| 구간 | 신호 | 내역 | 합계 |
|------|------|------|------|
| AUDIO 1 → UHF 패널 (케이블 C8) | 6 | COMM 1 MODE ×3, COMM 2 MODE ×3 → MCP `0x20` GPB2~7 | **7선** (+GND) |

> AUDIO 1 의 COMM 모드 로터리는 Teensy 로 가지 않고 **옆 UHF 패널의 MCP** 로 직접 들어갑니다.
> 두 패널이 좌측 콘솔에서 인접하고, STAGE_T40 의 Teensy 여유 핀이 5개뿐이라 직결이 불가능하기 때문입니다.

### MCP 모듈 → 담당 패널 하니스 (`C7`~`C12`)

모듈을 담당 패널 옆에 각각 실장하는 **배치 근거와 케이블별 선수**는
[LEFT_CONSOLE_PIN_TREE.md](LEFT_CONSOLE_PIN_TREE.md) 의 「케이블 구성」·「토폴로지」 절이 정본입니다.

`C6`(ECM 래더 1선 + SR 3선)만은 MCP 를 거치지 않는 **Teensy 직결**이며, LAN 페어 배치에서
**래더/GND 와 SH_CP/GND 를 서로 다른 페어**에 두어 리턴 경로를 분리해야 합니다
(판별 여유 ±14카운트). 상세는 같은 문서의 「케이블 C6」 절.

### 케이블 권장

| 구간 | 구성 |
|------|------|
| → ECM 패널 | LAN ×2 — **I3**(체인): SDA/GND, SCL/GND, 3.3V/GND ×2 · **C6**: DS/GND, **래더/GND**, SH_CP/GND, ST_CP/3.3V |
| → ELEC 패널 | LAN ×1 — **I2**(체인): SDA/GND, SCL/GND, 3.3V/GND ×2 |
| → UHF | LAN ×3 — **I1**: SDA/GND, SCL/GND, 3.3V/GND ×2 · **C2**: 엔코더 A/B 3쌍 + **VOL/GND** · **C3**: 엔코더 A/B 3쌍 + GND 페어 |
| → ENGINE+MPO | **1** — 6선 일반 (RUN LED 포함) |
| → AUDIO | **C4** 6선 / **C5** 4선. 와이퍼는 각각 GND와 트위스트 페어 |

아날로그선(ECM 래더, UHF VOL, AUDIO 와이퍼 6)은 **전부 GND와 트위스트 페어**로 처리합니다.

I2C 핫플러그 보호: SDA/SCL 직렬 100Ω, 각 보드 3.3V에 10µF + 100nF (`hotplug_spec.md` 준용).

---

## 전원

```
USB 5V (900mA)
    └─ Teensy 4.1 ─┬─ 3.3V ─┬─ MCP23017 x3 (0x20 / 0x21 / 0x22)
                   │        ├─ 74HC595 x4
                   │        └─ indicator LEDs x43 (ECM 32 + ELEC/EPU 11)
                   GND ─────────────┐
                                    │  ! common ground required (single point)
12V adapter ─┬─ 12V+ ─> backlight strips (all panels, daisy-chain)
            └─ GND ──┴─ LED-RTN ─> MOSFET(IRLML6344) ─> GND
                                      Gate <- 1kΩ <- pin 13
                                             10kΩ pull-down -> GND
```

| 항목 | 값 |
|------|-----|
| 백라이트 전원 | **별도 12V 어댑터 (1A 권장)** — MT3608 스텝업 불필요 |
| USB 예산 | 900mA − Teensy 100 − 로직 10 − LED 최대 440 ≈ **여유 350mA** |
| 12V 하니스 | `12V+` / `LED-RTN` 2선, 신호 케이블과 물리적 분리 |

**⚠️ 어댑터 GND와 Teensy GND를 반드시 연결하세요.** MOSFET 게이트가 Teensy GND 기준으로 동작하므로, 접지가 분리되면 백라이트 제어가 성립하지 않습니다. 그라운드 루프를 피하려면 **단일점(star) 접지**로 한 곳에서만 연결합니다.

**⚠️ USB 2.0 포트(500mA)에서는 `welcomeCeremony()` 피크(약 548mA)가 초과할 수 있습니다.** USB 3.0 포트를 쓰거나 세리머니의 전체 동시 점등을 순차 점등으로 바꾸세요.

**⚠️ USB 예산보다 Teensy 3.3V 레귤레이터가 먼저 걸립니다.** 위 계통도대로 74HC595 4장과 MCP23017 3장, 그리고 표시등 43개가 **전부 3.3V 레일 하나**에서 나옵니다. 전점등 시 약 430mA 로 PJRC 권장 **250mA** 를 넘으므로, USB 3.0 을 써도 해결되지 않습니다. 세리머니 순차 점등이 필수이고, 상시 여유가 필요하면 **74HCT595 를 5V(Vin) 급전**으로 바꾸십시오 (HCT 는 VIH 2.0V 라 3.3V 로직으로 구동 가능, LED 직렬저항 재계산 필요).

MCP23017 의 LED 는 캐소드 공통 GND = **소싱** 구성이라 한계가 `VDD` 유입 **125mA** 입니다. `0x21` 한 장에 11개가 붙으므로 **개당 10mA 이하**로 잡으십시오 (11 × 10 = 110mA).
