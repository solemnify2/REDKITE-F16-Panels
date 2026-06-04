# Step-Up Converter EN Pin Control via MOSFET

## Overview
USB 5V → Step-Up 컨버터 → 12V 백라이트 ON/OFF 제어.
Teensy GPIO 핀 하나로 MOSFET을 통해 EN 핀을 제어한다.

## EN Pin 특성
- **GND 연결 → 컨버터 ON** (12V 출력)
- **Float(미연결) → 컨버터 OFF** (출력 없음)

## GPIO 직결이 안 되는 이유 → MOSFET 필수

Step-Up 매뉴얼에 따르면:
- **EN = LOW (GND) → 컨버터 ON**
- **EN = HIGH → 컨버터 OFF**

GPIO 직결 시 두 가지 문제가 발생한다:

### 1. 3.3V HIGH로는 꺼지지 않는다
Teensy GPIO HIGH = 3.3V인데, Step-Up EN 핀은 5V VIN 기준으로 동작한다.
3.3V는 5V 도메인에서 확실한 HIGH로 인식되지 않아 **컨버터가 꺼지지 않는다.**
(GPIO LOW → EN LOW → ON은 정상 동작하지만, OFF가 안 됨)

### 2. Teensy GPIO는 5V tolerant 하지 않다
Step-Up EN 핀 내부에 5V 풀업 저항이 있을 수 있다.
GPIO를 직결하면 EN 핀을 통해 **5V가 Teensy GPIO에 역류**하여
3.3V 전용인 Teensy 4.1 GPIO가 **손상될 위험**이 있다.

### 해결: N-ch MOSFET
MOSFET을 EN과 GND 사이에 넣으면:
- GPIO는 Gate만 구동 (전류 거의 0, 3.3V로 충분)
- Drain-Source가 EN-GND 스위치 역할 → 확실한 GND 연결
- GPIO와 5V EN 핀이 전기적으로 격리 → Teensy 보호

## 회로

```
Teensy GPIO ──→ 1kΩ ──→ Gate (G)
                              │
                         IRLML6244
                          N-ch MOSFET
                              │
                    Drain (D)     Source (S)
                      │              │
                    EN pin          GND
```

## 동작

| GPIO | MOSFET | EN Pin | Step-Up | 12V |
|------|--------|--------|---------|-----|
| HIGH | ON | GND | ON | 출력 |
| LOW | OFF | Float | OFF | 없음 |

## 부품

| Part | Value | Purpose |
|------|-------|---------|
| MOSFET | IRLML6244 (N-ch, SOT-23) | EN-GND 스위치, Vgs(th) ~1V → 3.3V GPIO 직접 구동 |
| Resistor | 1kΩ | Gate 직렬 — 스위칭 링잉 방지 |
| Resistor | 220Ω × N | LED 전류 제한 (스트립당 1개) |

- 10K pull-down 불필요: MOSFET은 Step-Up과 상시 연결 (핫플러그 없음)

## LED 백라이트

- 12V → LED × 3 → 220Ω → GND (1개 스트립)
- 최대 15개 스트립 병렬 연결 가능

## USB 3.0 필수

- USB 3.0: 5V / 900mA
- USB 2.0: 5V / 500mA → 스트립 다수 사용 시 전류 부족
- Step-Up 효율 ~85% 고려 시 USB 3.0이 안정적

## 회로도
`stepup_en_circuit.png` 참조 (draw_stepup_en.py로 생성)
