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
| 인디케이터 LED | 22 (GEAR 4 · TWA 7 · MISC 3 · CMDS 8) | 44 (ECM 32 · ELEC 8 · EPU 3 · JFS 1) | 66 |
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
| 택타일 스위치 6×6mm | 20 | 실사용 12 — TWA 4버튼(SMD) + **ECM 8버튼은 관통형(THT)**, 핀 간격 6.5×4.5mm |
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
| 74HC595 시프트 레지스터 (SO16) | 4 | ECM 패널 32 LED 구동 — ECM 커스텀 PCB 에 실장 |
| IRLML6244 N-ch MOSFET | 3 | 백라이트 PWM 스위칭. **현재 2개** (콘솔 1 + AUX 1), MISC 전용 1개 추가 예정 |
| AO3400A N-ch MOSFET | 1 | TWA 기판 `Q1` — TWA Power LED 4개 묶음 구동 |
| 로터리 엔코더 EC11 (디텐트) | 6 | UHF — PRESET은 20디텐트 권장 |
| MAX7219 LED 드라이버 | 1 | UHF 디스플레이 커스텀 PCB 에 실장 (주파수 6 + 채널 2자리) |

## LED

### 인디케이터 — 66개

| 패널 | 신호 | 수 | 색 / 크기 |
|---|---|---:|---|
| ECM (콘솔) | 8그룹 × S/A/F/T | 32 | 녹·청·적·황 **각 8**, 3mm |
| CMDS | GO 1 · NO GO 2 · DISPENSE RDY 5 | 8 | 녹색 5mm |
| ELEC | 경고등 8 | 8 | 주황 3mm |
| TWA | Power 4 · Search 1 | 5 | 녹색 3mm |
| TWA | Low 1 · Act 1 | 2 | 주황 3mm |
| GEAR | Nose · Left · Right | 3 | 주황 5mm |
| GEAR | Gear Warn | 1 | 적색 5mm |
| EPU | RUN | 1 | 녹색 5mm |
| EPU | HYDRAZN · AIR | 2 | 주황 3mm |
| MISC | ECM 표시등 | 1 | 녹색 5mm |
| MISC | ADV Active | 1 | 녹색 **길쭉한 사각** |
| MISC | ADV Standby | 1 | 주황 **길쭉한 사각** |
| ENGINE | JFS RUN | 1 | 녹색 5mm |

### 색·크기별 발주 수량

| 품목 | 실사용 | 비고 |
|---|---:|---|
| 3mm 녹색 | 13 | ECM 8 + TWA 5 |
| 3mm 청색 | 8 | ECM |
| 3mm 적색 | 8 | ECM |
| 3mm 황색 | 8 | ECM |
| 3mm 주황 | 12 | ELEC 8 + TWA 2 + EPU 2 |
| 5mm 녹색 | 11 | CMDS 8 + EPU 1 + MISC 1 + ENGINE 1 |
| 5mm 주황 | 3 | GEAR |
| 5mm 적색 | 1 | GEAR Warn |
| 길쭉한 사각 녹색 | 1 | MISC ADV Active |
| 길쭉한 사각 주황 | 1 | MISC ADV Standby |
| **합** | **66** | |

> ECM 32개는 기판 지정품 **Würth WL-TMRC `151031SS04000`** 입니다 (3mm, 20mA).

### 백라이트

| 부품 | 수량 | 비고 |
|------|------|------|
| 3mm LED Green (백라이트용) | 100 | 고휘도(Vf ≈ 3.0V). `LED 3개 + 220Ω 직렬 = 1스트링` |

스트링당 `(12 − 3×3.0) / 220 ≈ 13.6mA` 입니다.

| 구간 | 스트링 | LED | 전류 @12V |
|---|---:|---:|---:|
| 콘솔 | 16 | **48** | 약 218mA |
| MISC 패널 | 3 | 9 | 41mA |
| ECM 기판 (조립 가이드) | — | 8 | — |
| 확인된 합 | | **65** | 약 259mA |

12V 어댑터 1A 를 Y 케이블로 나눠 쓰므로 여유가 충분합니다.

> **LED 직렬저항** — ECM·GEAR·TWA·MISC 는 220Ω, CMDS 램프 8개는 **320Ω(220+100 직렬)** 입니다.
> CMDS 는 한 핀에 LED 2개를 병렬로 다는 자리가 셋이라 핀 전류를 낮춰야 합니다.

## 수동 소자

| 부품 | 수량 | 비고 |
|------|------|------|
| 1/4W 저항 (1K, 4.7K, 10K, 100Ω, 150Ω, 220Ω) | 각 100 | 래더, 풀다운, 풀업, LED 직렬. ECM 20kΩ 풀다운은 기판이 아닌 **배선에 직결** |
| SMD 1206 저항 (220Ω, 2.2K, 10K) | 각 100 | ECM 기판에 39개 — LED 직렬 220Ω ×32(`R8`–`R39`), 래더 체인 10kΩ ×7(`R1`–`R7`) |
| 전해 커패시터 25V (10µF / 100µF) | 각 40 | 바이패스 |
| 세라믹 커패시터 (100nF / 1nF) | 각 100 | 바이패스 |

> **LED 직렬저항** — ECM·GEAR·TWA·MISC 는 220Ω, CMDS 램프 8개는 **320Ω(220+100 직렬)** 입니다.
> CMDS 는 한 핀에 LED 2개를 병렬로 다는 자리가 셋이라 핀 전류를 낮춰야 합니다.

## 커넥터 / 배선

| 부품 | 수량 | 비고 |
|------|------|------|
| 실리콘 와이어 22AWG 5색 | 50m | |
| Dupont 커넥터 & 점퍼선 | 다수 | 쉘, 핀, F-F 점퍼. **`I1` 을 뺀 모든 패널 간 배선**에 사용 |
| Spade 압착 터미널 2.8mm | 200쌍 | 토글 스위치 연결 |
| Pin Header 1x30P | 10 | |
| 수축 튜브 | 750 | |

## 모듈 / 기타

| 부품 | 수량 | 비고 |
|------|------|------|
| 12V DC 어댑터 (1A) | 1 | 백라이트 전용. **DC Y 케이블로 AUX·콘솔 두 보드에 분기.** Step-Up 은 래더 ADC 노이즈 유발 |
| DC 전원 Y 분배 케이블 | 1 | 12V 어댑터 → AUX / 콘솔 |
| RJ45 패널 마운트 커넥터 / 키스톤 잭 | 1 | **AUX 통에 장착** — MISC 패널 연결(`I1`, I2C)용. 다른 LAN 구간은 패널 커넥터를 쓰지 않습니다 |
| Cat5e LAN 케이블 | 1 | **AUX ↔ MISC 패널(`I1`) 전용.** 그 외 구간은 전부 듀폰 케이블 |
| microSD 확장 케이블 (15핀 FPC) | 2 | 하단 SD 패드 인출 — AUX CMDS 램프, 콘솔 UHF 디스플레이 |

## 커스텀 PCB

직접 발주하는 기판 3장입니다. 실장 부품은 각 보드 폴더의 BOM 을 따릅니다 (이 문서 범위 밖).
설계 파일은 모두 이 저장소 **밖**, `Redkite Project/` 아래에 있습니다.

| 기판 | 수량 | 사양 | 설계 위치 / 거버 |
|------|-----:|------|------|
| TWA 패널 | 1 | 2층, 42.1 × 53.7 mm, 1.6 mm | `TWA Panel/f-16-cockpit-left-aux-console-threat-warning-aux-panel/KiCad_TWA_v36/` — `TWA_v36_gerber.zip` |
| ECM 패널 | 1 | 2층, 83 × 59 mm, 1.57 mm | `ECM Panel/f-16-cockpit-left-console-ecm-panel/` — `Leiterplatte ECM Panel 2025-03-08.zip` |
| UHF 7세그 디스플레이 | 1 | 2층, 86 × 50 mm, 1.6 mm | `f-16-cockpit-uhf-radio-panel/display/pcb/` — `uhf_display_gerber_revB.zip` |

세 기판 모두 조립 가이드와 STL(탑 커버·LED 레이어·디퓨저), 레이저 커팅 DXF 가 같은 폴더에 있습니다.
UHF 쪽은 KiCad 프로젝트와 설계 문서 `README.md` 도 포함합니다.
