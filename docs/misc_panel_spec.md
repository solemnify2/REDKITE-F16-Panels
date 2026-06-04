# MISC Panel Specification (F-16C Block 50)

## Overview
우측 콘솔 3개 패널 (HUD Remote, SNSR PWR, LIGHTING)을 Teensy 4.0 Slave로 구동.
메인 패널 Teensy 4.1 (Master)과 LAN (Cat5e) I2C로 연결.

## Panel Summary

| Panel | Switches | Digital Pins | Analog Pins |
|-------|----------|-------------|-------------|
| HUD Remote | 8 × 3-pos toggle | 16 | 0 |
| SNSR PWR | 4 toggle | 4 | 0 |
| LIGHTING | 5 knobs (pot) | 0 | 5 |
| **Total** | | **20** | **5** |

## HUD Remote Control Panel
8 × 3-position toggle switches (각 2핀, 총 16 디지털 입력)

| # | Switch | Positions |
|---|--------|-----------|
| 1 | SCALES | VV/VAH / VAH / OFF |
| 2 | FP MARKER | ATT/FPM / FPM / OFF |
| 3 | DED DATA | DED / PFLD / OFF |
| 4 | DEPRESS RET | STBY / PRI / OFF |
| 5 | SPEED | CAS / TAS / GND SPD |
| 6 | ALT | RADAR / BARO / AUTO |
| 7 | BRT | DAY / AUTO BRT / NIGHT |
| 8 | TEST | STEP / ON / OFF |

## SNSR PWR Panel
4 toggle switches (4 디지털 입력)

## LIGHTING Panel
5 potentiometers (5 아날로그 입력)

## Controller: Teensy 4.0

| Resource | Available | Used | Remaining |
|----------|-----------|------|-----------|
| Digital GPIO | 24+ | 20 | 4+ |
| Analog (ADC) | 14 | 5 | 9 |

- I2C Slave (address TBD, e.g. 0x10)
- Teensy 4.1 (Master)과 LAN Cat5e로 연결
- 3.3V 전원: Teensy 4.1에서 LAN Pair 4로 직접 공급

## LAN Connection (from Main Panel)

| Pin | Signal | Pair |
|-----|--------|------|
| 1 | SDA | Pair 1 (Orange) |
| 2 | GND | Pair 1 |
| 3 | SCL | Pair 2 (Green) |
| 6 | GND | Pair 2 |
| 4 | 12V | Pair 3 (Blue) |
| 5 | 12V | Pair 3 |
| 7 | 3.3V | Pair 4 (Brown) |
| 8 | GND | Pair 4 |

- 12V: 백라이트 LED 전용
- 3.3V: Teensy 4.0 전원 (Teensy 4.1에서 직접 공급, AMS1117 불필요)
- I2C: 100Ω × 2 직렬 보호 (hotplug)

## Hotplug Protection
- 100Ω × 2 (SDA, SCL 직렬)
- 10µF + 100nF (3.3V VDD bypass, 병렬)
- See `hotplug_spec.md` for details
