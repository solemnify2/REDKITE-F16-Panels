# LEFT_AUX ↔ MISC 패널 LAN 배선도

Teensy (AUX 통) ↔ MCP23017 (MISC 패널) 간 Cat5e LAN 케이블 연결.
I2C 풀업, 핫플러그 보호, PWM 백라이트 디밍 포함.

## LAN 핀 배정

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

## 회로도

### AUX 통 (Teensy 측)

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

### MISC 패널 (MCP23017 측)

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

## 보호 부품

| 위치 | 부품 | 값 | 용도 |
|------|------|----|------|
| AUX | 풀업 저항 | 4.7kΩ x2 | I2C 풀업 (SDA, SCL -> 3.3V) |
| AUX | Gate 직렬 저항 | 1kΩ | MOSFET 스위칭 링잉 방지 |
| AUX | Gate 풀다운 저항 | 10kΩ | 핫플러그 시 MOSFET OFF 유지 |
| AUX | MOSFET | IRLML6344 (SOT-23) | N-ch logic-level, Vgs(th) ~1V |
| MISC | 직렬 저항 | 100Ω x2 | SDA/SCL 돌입전류 제한 (래치업 방지) |
| MISC | 전해캡 | 10uF (10V+) | MCP VDD 핫플러그 스파이크 흡수 |
| MISC | 세라믹캡 | 100nF | MCP VDD 고주파 노이즈 필터 (핀 근접 배치) |

## 불필요한 부품

| 부품 | 사유 |
|------|------|
| TVS 다이오드 | 3.3V/12V USB 전원 수준, 과전압 파괴 위험 없음 |
| 페라이트 비드 | 저전류 (~1mA), 노이즈 문제 없음 |
| 100uF+ 대용량 캡 | 과잉, 돌입전류만 증가 |
| 외부 풀업 (MISC측) | AUX측 4.7kΩ로 충분 (1m 이내) |

## 설계 근거

- **I2C 풀업 4.7kΩ**: 1m 이내 Cat5e에서 Teensy 내부 풀업(~22kΩ)으로도 동작하나, 외부 4.7kΩ이 더 안정적
- **100Ω 직렬**: 핫플러그 시 핀 접촉 순서 불규칙 → 과도 전류 제한. I2C 100~400kHz에 영향 미미
- **10kΩ 풀다운**: LAN 미연결/핫플러그 시 Gate 플로팅 → MOSFET 의도치 않게 ON 방지
- **Pair 3 (12V + LED return)**: 꼬임쌍 내 전류 왕복 → 자기장 상쇄, 다른 쌍과 간섭 최소
- **MISC 백라이트 전류**: 3 strips x 13.6mA = 41mA @12V → Cat5e 1선(0.5A 한계)의 8%
