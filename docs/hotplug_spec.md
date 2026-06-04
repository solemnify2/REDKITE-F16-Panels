# LAN Hotplug & PWM Specification

## Overview
Teensy 4.1 ↔ MISC Panel (MCP23017) 간 LAN (Cat5e RJ45) 연결 시 핫플러그 보호 및 PWM 디밍 설계.
3.3V와 12V는 완전 분리 (3.3V = MCP 전용, 12V = 백라이트 전용).

## Hardware

### I2C Protection
| Part | Value | Location | Purpose |
|------|-------|----------|---------|
| Resistor | 100Ω | SDA 직렬 (MISC 입력단) | 돌입전류 제한, 래치업 방지 |
| Resistor | 100Ω | SCL 직렬 (MISC 입력단) | 돌입전류 제한, 래치업 방지 |

- LAN 연결 시 핀 접촉 순서가 불규칙 → 100Ω이 과도 전류 제한
- I2C 100~400kHz 통신에 영향 거의 없음

### Power Protection (MCP23017 VDD)
| Part | Value | Location | Purpose |
|------|-------|----------|---------|
| Electrolytic cap | 10µF (10V+) | MCP23017 VDD-GND | 핫플러그 전압 스파이크 흡수 |
| Ceramic cap | 100nF | MCP23017 VDD-GND (핀 근접) | 고주파 노이즈 필터 |

#### Connection
```
3.3V ──┬──┬── MCP23017 VDD
       │  │
     10µF 100nF
       │  │
GND  ──┴──┴── MCP23017 GND
```
- 두 캡 모두 3.3V-GND 사이 병렬
- 100nF을 MCP23017 핀에 더 가까이 배치
- 10µF 전해캡은 극성 주의 (+를 3.3V 쪽)

### Capacitor Sizing
| 용량 | 판단 |
|------|------|
| 10µF | 충분 (MCP23017 ~1mA) |
| 47µF | AMS1117 사용 시 12V PWM 리플 흡수용 (현재 불필요) |
| 100µF | 과잉 — 충전 돌입전류 증가, 이점 없음 |

현재 3.3V/12V 완전 분리 → 12V PWM 리플이 MCP에 영향 없음 → **10µF이면 충분**

## Software

### MCP23017 재초기화
```cpp
// 주기적으로 MCP23017 연결 확인 (예: 500ms 간격)
Wire.beginTransmission(0x20);
if (Wire.endTransmission() == 0) {
    // MCP23017 detected → reinitialize
    mcp.begin();
}
```
- LAN 분리 후 재연결 시 MCP23017 레지스터가 리셋됨
- I2C 응답 확인 후 재초기화 필요

## Not Required
| Part | Reason |
|------|--------|
| TVS diode (P6KE15A) | 3.3V/12V USB 전원 수준, 과전압 파괴 위험 없음 |
| Ferrite bead | 저전류(~1mA), 노이즈 문제 없음 |
| 100µF+ 대용량 캡 | 과잉, 돌입전류만 증가 |
| Gate pull-down 10kΩ | MOSFET 없는 경우 불필요 (Option D) |

---

## PWM Dimming

### Overview
- Teensy Pin 0 → `analogWrite(0, 0~255)` → MOSFET Gate → LED 밝기 조절
- MOSFET: IRLML6344 (SOT-23, N-ch, Vgs(th) ~1V, logic-level)
- Low-side switching: LED cathode(−) → MOSFET Drain, MOSFET Source → GND

### Teensy 4.1 PWM
- Pin 0: PWM 출력 가능 (FlexPWM)
- 기본 주파수: ~4.482kHz
- 해상도: 8-bit (0~255)
- `analogWrite(0, 0)` = OFF, `analogWrite(0, 255)` = 최대 밝기

### MOSFET Circuit (per panel)
```
Teensy Pin0 ──→ 1kΩ ──→ Gate (G)
                         │
                        10kΩ (pull-down)
                         │
                        GND

12V → 220Ω → LED×3 → Drain (D)
                      Source (S) → GND
```

| Part | Value | Purpose |
|------|-------|---------|
| MOSFET | IRLML6344 (SOT-23) | N-ch logic-level, Vgs(th) ~1V |
| Resistor | 1kΩ | Gate 직렬 — 스위칭 링잉 방지 |
| Resistor | 10kΩ | Gate pull-down — 핫플러그 시 LED 오동작 방지 |

### Gate Pull-down 10kΩ 역할
- LAN 미연결 또는 핫플러그 순간 Gate가 플로팅 → MOSFET 의도치 않게 ON
- 10kΩ이 Gate를 GND로 끌어내려 OFF 상태 유지
- **핫플러그 보호의 일부** — PWM 사용 시 필수

### PWM via LAN Cable
- PWM 신호를 LAN Pair 4 (Brown)로 MISC 패널에 전송 가능
- PWM+GND 꼬임쌍 → I2C/12V와 간섭 없음 (Cat5e 크로스토크 억제)
- PWM ~4.5kHz, I2C 100~400kHz — 주파수 대역 다름, 간섭 미미
- MOSFET 게이트 구동 전류 거의 0 → 방사 노이즈 최소

### PWM 사용 시 LAN Pin Assignment
| Pin | Signal | Pair | Note |
|-----|--------|------|------|
| 1 | SDA | Pair 1 (Orange) | 100Ω 직렬 보호 |
| 2 | GND | Pair 1 | SDA 리턴 |
| 3 | SCL | Pair 2 (Green) | 100Ω 직렬 보호 |
| 6 | GND | Pair 2 | SCL 리턴 |
| 4 | 12V | Pair 3 (Blue) | 백라이트 전용 |
| 5 | 12V | Pair 3 | 백라이트 전용 |
| 7 | PWM | Pair 4 (Brown) | MOSFET Gate 구동 |
| 8 | GND | Pair 4 | PWM 리턴 |

- PWM 사용 시 3.3V를 LAN으로 보낼 수 없음 (핀 부족)
- → MISC 3.3V는 AMS1117 (12V→3.3V)로 생성 필요

### PWM 미사용 시 LAN Pin Assignment
| Pin | Signal | Pair | Note |
|-----|--------|------|------|
| 1 | SDA | Pair 1 (Orange) | 100Ω 직렬 보호 |
| 2 | GND | Pair 1 | SDA 리턴 |
| 3 | SCL | Pair 2 (Green) | 100Ω 직렬 보호 |
| 6 | GND | Pair 2 | SCL 리턴 |
| 4 | 12V | Pair 3 (Blue) | 백라이트 전용 |
| 5 | 12V | Pair 3 | 백라이트 전용 |
| 7 | 3.3V | Pair 4 (Brown) | MCP23017 전용 |
| 8 | GND | Pair 4 | 3.3V 리턴 |

- AMS1117 불필요 — Teensy 3.3V 직접 전송
- MOSFET / 1kΩ / 10kΩ 불필요

### MCP23017은 PWM 불가
- MCP23017 GPIO는 디지털 ON/OFF만 가능
- I2C 통신 속도 한계로 소프트웨어 PWM도 불가 (~1kHz 미만)
- PWM 디밍은 반드시 Teensy 하드웨어 PWM 핀 사용
