# REDKITE F16 PANELS — 부품 목록

두 보드(`F16_LEFT_AUX_MISC`, `F16_LEFT_CONSOLE`)를 모두 만들 때 기준입니다.
수량은 여유분을 포함한 발주 단위라 실제 사용량보다 많습니다.

빌드 전체 비용(패널·3D 프린트·MCU 포함)은 [README](../README.md#1-5-소요-비용) 의 「소요 비용」 절에 있습니다.

---

## 코드 기준 실사용량

각 스케치의 config 배열에서 뽑은 **실제 사용 수량**입니다. 아래 발주 수량과 달리 여유분이 없습니다.

| 항목 | LEFT_AUX | LEFT_CONSOLE | 합 |
|---|---:|---:|---:|
| 스위치 신호 (`switches[]` 항목) | 26 | 33 | 59 |
| 저항 래더 | 3 (TWA, CMDS MODE·PRGM) | 1 (ECM) | 4 |
| 포텐셔미터 | 1 (HMCS) + 페달 2 | 10 (AUDIO 1×6, AUDIO 2×3, UHF VOL) | 13 |
| 로터리 엔코더 EC11 | — | 6 (UHF) | 6 |
| MCP23017 | 1 (`0x20`) | 3 (`0x20`·`0x21`·`0x22`) | 4 |
| 74HC595 | — | 4 (ECM 32 LED) | 4 |
| MAX7219 7세그 보드 | — | 1 (UHF, 8자리) | 1 |
| 인디케이터 LED | 19 (GEAR 4 · TWA 4 · MISC 3 · CMDS 8) | 44 (ECM 32 · ELEC 8 · EPU 3 · JFS 1) | 63 |
| 백라이트 MOSFET | 1 | 1 | 2 |
| microSD 확장 케이블 (15핀 FPC) | 1 (CMDS 램프) | 1 (UHF 디스플레이) | 2 |

> CMDS 램프는 LED 8개를 Teensy 핀 5개로 구동합니다 (`leds[]` 항목은 5개).

### 스위치 부품 내역

`switches[]` 59개 항목과 저항 래더 4개가 실제 부품 **63개**에 대응합니다.
로터리와 3포지션 토글은 한 부품이 여러 항목을 차지합니다.

| 부품 | 수 | 내역 |
|---|---:|---|
| 토글 On-Off-On | 14 | `SW_ON_OFF_ON` 13 + AUDIO 2 (HOT MIC‑OFF‑CIPHER) 1 |
| 토글 On-On | 20 | AUX 13 (Laser ARM, Store CAT, Hook, GND JETT ENABLE, BRAKES Channel, CMDS 8) + 콘솔 7 (ENG CONT·DATA, MAX POWER, AB RESET, MPO, UHF SQUELCH·T-TONE) |
| 푸시 | 9 | AUX 4 (ALT REL, EMER Jettison, Horn Silencer, DN LOCK REL) + 콘솔 5 (ECM BIT·RESET, ELEC CAUTION RST, UHF STATUS·TEST) |
| 택타일 | 12 | 래더 — TWA 4버튼, ECM 8버튼 |
| 로터리 | 6 | UHF FUNC 4P, UHF MODE 3P, COMM1 3P, COMM2 3P, CMDS MODE 7P, CMDS PRGM 7P |
| 코리 스위치 | 1 | MISC ADV MODE |
| 마이크로 스위치 | 1 | ALT GEAR Handle |

---

## 스위치류

| 부품 | 수량 | 비고 |
|------|------|------|
| 토글 스위치 On-Off-On (12mm, 3P) | 20 | 실사용 14 |
| 토글 스위치 On-On (12mm, 3P) | 20 | 실사용 20 |
| 푸시 스위치 7mm (PBS-110) | 12 | 푸시 실사용 9 (6mm 와 합산) |
| 모멘터리 푸시 스위치 6mm (3핀) | 5 | 위와 합산 |
| 택타일 스위치 SMD (6x6x4.3mm) | 20 | 실사용 12 — TWA 4버튼, ECM 8버튼 래더 |
| 리밋 스위치 (12x6mm) | 10 | 실사용 1 — ALT GEAR Handle |
| 로터리 스위치 SR26 1P12T | 4 | 로터리 실사용 6 — CMDS MODE·PRGM 7P, UHF FUNC 4P, UHF MODE 3P, COMM1·2 3P |
| 로터리 스위치 RS16 1P6T / 1P5T | 2 / 2 | 위와 합산 |
| 포텐셔미터 10kΩ | 15 | 실사용 11 (콘솔 10 + HMCS 1). 페달 2개는 페달 유닛 내장 |
| 코리 스위치 | 1 | 실사용 1 (MISC ADV MODE). [HispaPanel](https://hispapanels.com/tienda/en/buttons-encoders/71-korry-type-tactile-switch-momentary.html) |
| 키보드 스위치 (Brown) | 2 | |

## IC / 반도체

| 부품 | 수량 | 비고 |
|------|------|------|
| MCP23017 I2C I/O Expander | 4 | AUX: MISC `0x20` / 콘솔: UHF+AUDIO `0x20`, ELEC+EPU `0x21`, ECM+AVTR `0x22` |
| 74HC595 시프트 레지스터 | 4 | ECM 패널 32 LED 구동 (데이지체인) |
| IRLML6244 N-ch MOSFET | 2+ | 백라이트 PWM 스위칭 |
| 로터리 엔코더 EC11 (디텐트) | 6 | UHF — PRESET은 20디텐트 권장 |
| MAX7219 7세그 디스플레이 보드 (8자리) | 1 | UHF 주파수 6 + 채널 2. **자작 PCB** — 아래 「UHF 7세그 디스플레이 보드」 절 참조 |

## LED

| 부품 | 수량 | 비고 |
|------|------|------|
| 3mm LED Green (백라이트용) | 100 | 고휘도 |
| LED 키트 3mm/5mm Mixed | 300 | Red, Green, Yellow — 인디케이터 실사용 63개 (ECM 32 포함) |

## 수동 소자

| 부품 | 수량 | 비고 |
|------|------|------|
| 1/4W 저항 (1K, 4.7K, 10K, 100Ω, 150Ω, 220Ω) | 각 100 | 래더, 풀다운, 풀업, LED 직렬 |
| SMD 1206 저항 (220Ω, 2.2K, 10K) | 각 100 | |

> **LED 직렬저항** — ECM·GEAR·TWA·MISC 는 220Ω, CMDS 램프 8개는 **320Ω(220+100 직렬)** 입니다.
> CMDS 는 한 핀에 LED 2개를 병렬로 다는 자리가 셋이라 핀 전류를 낮춰야 합니다.
| 전해 커패시터 25V (10µF / 100µF) | 각 40 | 바이패스 |
| 세라믹 커패시터 (100nF / 1nF) | 각 100 | 바이패스 |

## 커넥터 / 배선

| 부품 | 수량 | 비고 |
|------|------|------|
| 실리콘 와이어 22AWG 5색 | 50m | |
| Dupont 커넥터 & 점퍼선 | 다수 | 쉘, 핀, F-F 점퍼. **`I1` 을 뺀 모든 패널 간 배선**에 사용 |
| Spade 압착 터미널 2.8mm | 200쌍 | 토글 스위치 연결 |
| Pin Header 1x30P | 10 | |
| 수축 튜브 | 750 | |

## UHF 7세그 디스플레이 보드

콘솔 UHF 패널의 주파수·채널 표시부입니다. 기성 모듈이 아니라 **직접 발주하는 PCB** 입니다.

설계 일체는 이 저장소 **밖**의 `Redkite Project/f-16-cockpit-uhf-radio-panel/display/pcb/`
에 있습니다 — 거버(`uhf_display_gerber_revB.zip`), BOM, KiCad 프로젝트, 그리고 설계 문서
`README.md`. 그쪽 README 의 주요 절:

| 절 | 내용 |
|---|---|
| 7.3 | Rset 계산 — 밝기 조정 |
| 7.4 | Teensy VIN 5V 급전, USB 전류 예산 |
| 10 | 조립 순서 |
| 14.3 | PCB 발주 사양 |

**PCB 발주 사양** — 2층, 86×50mm, 두께 1.6mm, 최소 선폭/간격 0.20mm, 최소 드릴 0.30mm,
HASL 또는 ENIG. JLCPCB·PCBWay·Elecrow 모두 기본 사양이라 추가 요금이 없습니다.

| 부품 | Ref | 수량 | 사양 | 비고 |
|------|-----|-----:|------|------|
| PCB | — | 1 | rev B | `uhf_display_gerber_revB.zip` |
| 0.36" 7세그 (공통 캐소드) | D1–D8 | 8 | 7.5×14×8.5mm, 10핀 | 핀아웃 `A=10 B=9 C=8 D=5 E=4 F=2 G=3 DP=7 COM=1,6`. **색 편차 때문에 같은 로트로** |
| LED 드라이버 | U1 | 1 | MAX7219CWG+ (SOIC-24W) | MAX7221CWG+ 가 더 좋음 — slew 제한으로 노이즈 적음 |
| 레벨 시프터 | U2 | 1 | 74AHCT125D (SOIC-14) | 3.3V → 5V. SN74AHCT125D / 74HCT125D 도 가능 |
| 저항 | R1, R2 | 2 | 10k 1% 0805 | 직렬 20k = Rset, 세그먼트당 26mA 피크 |
| 세라믹 캡 | C1, C3 | 2 | 100nF THT (104), P5.0 | U1 pin19·U2 pin14 디커플링 |
| 벌크 캡 | C2 | 1 | 47µF X5R 1210 | **또는** C4–C7 로 대체 |
| 벌크 캡 (대안) | C4–C7 | 4 | 10µF 25V 전해, D5×11 P2.0 | **눕혀서 실장** — 세우면 높이가 안 맞음 |
| 핀 헤더 | J1 | 1 | 1×5 2.54mm **라이트앵글** | **뒷면 실장** — 앞면 여유가 5.5mm 뿐 |
| 스페이서 볼트 | — | 4 | OD 5.5 / ID 3.25 / h 5.5mm | 3D 프린트. 디스플레이 깊이 8.5mm 를 잡아줌 |
| M3 나사 | — | 4 | M3 × 20mm | 디스플레이 PCB ↔ LED 레이어 |
| 스모키 아크릴 | — | 2 | 52×11mm (주파수), 13×11mm (채널) | 표시창 |

**밝기 조정** — R1+R2 합이 Rset 입니다. 20k 가 기본, 27k 면 어둡게, 15k 면 최대 밝기입니다.

**전원** — Teensy 4.1 에는 `5V` 핀이 없고 **`VIN` 이 5V 접점**입니다 (USB 급전 시 VUSB↔VIN
연결, 실측 4.6~5.0V). MAX7219 최소 V+ 가 4.0V 라 동작하지만, V_IH 마진이 없으므로
**레벨 시프터(U2)는 반드시 필요**합니다. Rset 20k 에 전 자리 최대 밝기면 디스플레이만
208mA, Teensy 포함 최악 약 320mA 입니다 — 기본 `INTENSITY 0x08` 에서는 절반 수준.

**J1 배선 — 하단 SD 패드 인출이 최종입니다.** 엣지 핀은 쓰지 않습니다.

| J1 | 신호 | Teensy | FPC |
|---|---|---|---|
| J1.1 | +5V | **VIN** (FPC 아님) | — |
| J1.2 | GND | GND | 15 |
| J1.3 | DIN | 43 (MOSI2) | 12 |
| J1.4 | CLK | 45 (SCK2) | 6 |
| J1.5 | CS | 46 | 4 |

15핀 FPC 확장 케이블 4선 + VIN 1선 = 5선입니다.
상세는 [REF_LEFT_CONSOLE_WIRING.md](REF_LEFT_CONSOLE_WIRING.md) 의 「하단 SD 카드 인터페이스」 절.

> ⚠ 원본 BOM 의 `5-wire harness — VIN / GND / 11 / 13 / 10` 은 SPI0 직결 전제라
> 이 프로젝트에는 해당하지 않습니다.

---

## 모듈 / 기타

| 부품 | 수량 | 비고 |
|------|------|------|
| 12V DC 어댑터 (1A) | 2 | 백라이트 전용 (AUX 1 + 콘솔 1). Step-Up은 래더 ADC 노이즈 유발 |
| RJ45 패널 마운트 커넥터 / 키스톤 잭 | 1 | **AUX 통에 장착** — MISC 패널 연결(`I1`, I2C)용. 다른 LAN 구간은 패널 커넥터를 쓰지 않습니다 |
| Cat5e LAN 케이블 | 1 | **AUX ↔ MISC 패널(`I1`) 전용.** 그 외 구간은 전부 듀폰 케이블 |
| microSD 확장 케이블 (15핀 FPC) | 2 | 하단 SD 패드 인출 — AUX CMDS 램프, 콘솔 UHF 디스플레이 |
