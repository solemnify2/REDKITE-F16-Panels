# Backlight System Specification

## Power Budget
- USB 3.0: 900mA @ 5V
- Teensy 4.1 consumption: ~100mA @ 5V
- MCP23017: ~1mA (negligible)
- LED backlight budget: ~800mA @ 5V
- MT3608 step-up: 5V → 12V (85% efficiency)
- Max 12V output: 283mA → **18 strips (54 LEDs) safe limit**

## LED Strip
- Green 3V 20mA high-brightness LED
- 3-series per strip + 220Ω resistor
- Strip current: (12V - 9V) / 220Ω = **13.6mA** (68% of 20mA rating)
- Strip count is freely adjustable (parallel connection, no circuit change needed)

| Resistor | Current | Brightness |
|----------|---------|------------|
| 150Ω | 20.0mA | 100% (max, shorter life) |
| **220Ω** | **13.6mA** | **68% (recommended)** |
| 330Ω | 9.1mA | 45% |
| 470Ω | 6.4mA | 32% |
| 1kΩ | 3.0mA | 15% |

## Current Configuration
- Main panel: 10 strips (30 LEDs) = 136mA @12V
- MISC panel: 3 strips (9 LEDs) = 41mA @12V
- Total: 13 strips, 39 LEDs, 177mA @12V, ~538mA @5V

## MT3608 Step-Up Converter
- Input: 5V (Teensy VIN)
- Output: 12V
- Switching frequency: 1.2MHz
- Place 2~3cm away from Teensy MCU and I2C lines (EMI)
- Do not route I2C lines parallel to/over inductor
- Input/output caps included on module

---

## Circuit Options (4 variants)

### Option A: PWM Dimming (MOSFET ×2)
**File:** `backlight_circuit.png` / `draw_circuit.py`

- MOSFET: IRLML6344 (SOT-23, N-ch, Vgs(th) ~1V) × 2
- 1 per panel, low-side switching
- Gate: 1kΩ series resistor
- Pull-down: 10kΩ Gate→GND (hotplug protection)
- PWM dimming: Teensy Pin 0 → `analogWrite(0, 0~255)`
- MISC panel 3.3V: AMS1117-3.3 (12V → 3.3V) + 10µF × 2

| Pin | Signal | Pair |
|-----|--------|------|
| 1 | SDA | Pair 1 (Orange) |
| 2 | GND | Pair 1 |
| 3 | SCL | Pair 2 (Green) |
| 6 | GND | Pair 2 |
| 4 | 12V | Pair 3 (Blue) |
| 5 | 12V | Pair 3 |
| 7 | PWM | Pair 4 (Brown) |
| 8 | GND | Pair 4 |

**Pros:** 0~100% 무단계 디밍, PWM+GND 꼬임쌍으로 간섭 없음
**Cons:** 부품 가장 많음 (AMS1117 + caps + MOSFET ×2 + 저항 ×4)

### Option B: Always ON (No MOSFET)
**File:** `backlight_circuit_no_pwm.png` / `draw_circuit_no_pwm.py`

- MOSFET 없음, LED cathode → GND 직결
- 밝기는 저항값으로만 결정 (고정)
- MISC panel 3.3V: AMS1117-3.3 (12V → 3.3V) + 10µF × 2

| Pin | Signal | Pair |
|-----|--------|------|
| 1 | SDA | Pair 1 (Orange) |
| 2 | GND | Pair 1 |
| 3 | SCL | Pair 2 (Green) |
| 6 | GND | Pair 2 |
| 4 | 12V | Pair 3 (Blue) |
| 5 | 12V | Pair 3 |
| 7 | GND | Pair 4 (Brown) |
| 8 | GND | Pair 4 |

**Pros:** 단순, MOSFET/게이트 저항 6개 절감
**Cons:** 디밍 불가

### Option C: MCP23017 Only (No Backlight)
**File:** `backlight_circuit_mcp_only.png` / `draw_circuit_mcp_only.py`

- 백라이트 없음, MT3608 불필요, AMS1117 불필요
- Teensy 3.3V (250mA max) → LAN → MCP23017 직접 구동
- 100nF 바이패스 캡만 필요

| Pin | Signal | Pair |
|-----|--------|------|
| 1 | SDA | Pair 1 (Orange) |
| 2 | GND | Pair 1 |
| 3 | SCL | Pair 2 (Green) |
| 6 | GND | Pair 2 |
| 4 | 3.3V | Pair 3 (Blue) |
| 5 | 3.3V | Pair 3 |
| 7 | GND | Pair 4 (Brown) |
| 8 | GND | Pair 4 |

**Pros:** 최소 부품, 최소 전력
**Cons:** 백라이트 없음

### Option D: 12V Backlight + 3.3V Direct (No AMS1117)
**File:** `backlight_circuit_12v_3v3.png` / `draw_circuit_12v_3v3.py`

- MT3608 12V → 양쪽 패널 백라이트 (always on)
- Teensy 3.3V → LAN → MCP23017 직접 구동 (AMS1117 불필요)
- MOSFET 없음 (PWM 신호선 자리에 3.3V 배정)

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

**Pros:** AMS1117 + 전해캡 2개 절감, 백라이트 있음
**Cons:** PWM 디밍 불가 (LAN 핀 부족), 3.3V+GND 꼬임쌍 (전용 GND 있음)

---

## Option Comparison

| | A: PWM | B: Always ON | C: MCP Only | D: 12V+3.3V |
|---|--------|-------------|-------------|-------------|
| Backlight | O (dimmable) | O (fixed) | X | O (fixed) |
| MT3608 | O | O | X | O |
| AMS1117 | O | O | X | **X** |
| MOSFET | 2 | 0 | 0 | 0 |
| PWM dimming | O | X | - | X |
| Parts count | Most | Medium | Least | Medium-Low |
| 5V draw | ~538mA | ~538mA | ~100mA | ~538mA |

## MISC Panel Components by Option

### Option A (PWM)
| Part | Value | Purpose |
|------|-------|---------|
| MCP23017 | 0x20 | I2C GPIO expander |
| AMS1117-3.3 | SOT-223 | 12V → 3.3V LDO |
| Electrolytic cap | 10µF ×2 (25V) | AMS1117 in/out |
| Resistor | 100Ω ×2 | I2C hotplug protection |
| Resistor | 220Ω ×3 | LED current limiting |
| MOSFET | IRLML6344 | Backlight switching |
| Resistor | 1kΩ | MOSFET gate series |
| Resistor | 10kΩ | MOSFET gate pull-down |

### Option D (12V+3.3V, recommended)
| Part | Value | Purpose |
|------|-------|---------|
| MCP23017 | 0x20 | I2C GPIO expander |
| Ceramic cap | 100nF | MCP23017 bypass |
| Resistor | 100Ω ×2 | I2C hotplug protection |
| Resistor | 220Ω ×3 | LED current limiting |

## Main Panel Components (backlight options)
| Part | Value | Purpose |
|------|-------|---------|
| MT3608 module | 5V→12V | Step-up converter |
| Resistor | 220Ω ×10 | LED current limiting |
| MOSFET (Option A only) | IRLML6344 | PWM switching |
| Resistor (Option A only) | 1kΩ | Gate series |
| Resistor (Option A only) | 10kΩ | Gate pull-down |
