# 백라이트

양쪽 보드 모두 **MOSFET PWM 디밍**을 씁니다. 인게임 조명 노브에 연동되며,
채널은 두 가지입니다:

- **Pin 13 — console backlight**: AUX 로컬 패널(Gear/CMDS/TWA/HMCS) + LEFT CONSOLE 패널
- **Pin 12 — MISC backlight**: instrument panel 채널 (LEFT_AUX_MISC 전용, LAN 으로 전송)

---

## 회로

```
IRLML6244 SOT-23, N-ch low-side switching
                        ┌────────┐
   Teensy ── 1kΩ ─┬─────┤ G 1    │
               10kΩ     │    D 3 ├──── LED-RTN
           GND ───┴─────┤ S 2    │
                        └────────┘
  12V ── LED strips (3 LED + 220Ω 직렬) ── LED-RTN ── D(3)
  12V adapter GND ═══ Teensy GND (단일점!)
```

```
LEFT_AUX_MISC 는 MOSFET 이 2개입니다:
  pin 13 → MOSFET₁ → AUX 로컬 (Gear·CMDS·TWA·HMCS)   console channel
  pin 12 → MOSFET₂ → MISC (LAN 으로 전송)               instr panel channel
Online 일 때 각 채널이 독립 제어됩니다. Offline 수동 조절은 양쪽 동시.
```

## 전원

**12V DC 어댑터 1개**를 **DC Y 케이블로 분기**해 양쪽 보드에 공급합니다.
백라이트 전원은 USB와 분리합니다. AUX는 스텝업 사용 중 래더 값이 흔들려 외부 어댑터로 변경했습니다.

> 이 구성에서는 USB 전원을 승압하는 MT3608 대신 12V 어댑터를 사용합니다. 스텝업 사용 시 관찰한 래더 변동은 전원·GND 리플과 관련된 것으로 판단했습니다. 외부 어댑터를 사용하면 백라이트의 공급 전류를 USB에서 분리할 수 있습니다. 단, 제어 기준을 위한 공통 GND는 연결해야 합니다.

**양쪽 모두 어댑터 GND ↔ Teensy GND를 단일점(star)으로 반드시 연결하세요.** MOSFET Gate 기준이 없으면 백라이트가 동작하지 않습니다.

> 어댑터를 공유하므로 두 보드의 12V GND가 이어집니다. 두 Teensy는 PC의 USB GND로도 이미
> 연결되어 접지 루프가 형성될 수 있습니다. 래더 값이 흔들리면 백라이트 리턴 전류가 ADC 기준 GND를 통과하는지 확인하십시오.

## 밝기 제어

| 상태 | 동작 |
|---|---|
| BMS online | 브리지가 `instrLight` → `ledBits` byte 2 (console, bits 16-23) + byte 3 (instr panel, bits 24-31) 전송. BMS는 소스가 `instrLight` 하나뿐이라 두 채널 동일 값 |
| DCS online | Teensy가 `LIGHT_CONSLES`(0x4482) → pin 13 (remap 11200~58510 → 0~255), `LIGHT_INST_PNL`(0x4484) → pin 12 (>>8 → 0~255) 독립 제어 |
| Offline 수동 (AUX) | DN LOCK REL 누른 채 HMCS Symbology pot(A15)로 **양쪽 핀 동시** 밝기 조절 (방향 반전) |
| Offline 수동 (콘솔) | UHF TEST + STATUS 동시에 누른 채 UHF VOL pot(A9)로 밝기 조절 |
| Idle 30분 | 자동 꺼짐. 아무 입력으로 복귀 |
| USB Suspend | LED + 백라이트 소등, MCU 절전 |

### Cougar MFD 백라이트

패널 백라이트와 별개로, 브리지가 **Thrustmaster Cougar MFD** 의 백라이트도 같이 맞춥니다.
Teensy 를 거치지 않고 PC 에서 HID feature report 로 직접 보냅니다.

| 항목 | 값 |
|------|-----|
| 장치 | VID `0x044F`, PID `0xB351` · `0xB352` (F16 MFD 1 · 2) |
| 전송 | `send_feature_report([0x00, 0x01, brightness])`, 밝기 0~255 |
| 소스 | BMS: 공유 메모리 `instrLight` / DCS: DCS-BIOS 조명 데이터 |
| 소등 | 심 오프라인, 브리지 종료, 콘솔 창 닫기 |

`pip install hidapi` 가 안 돼 있으면 이 부분만 건너뛰고 나머지는 그대로 동작합니다.

> SimGears ICP의 백라이트 연동은 구현하지 않았습니다. 현재는 장치 자체 밝기 조절을 사용합니다.

## LED 배치

### 패널 구조

패널 출처에 따라 구조가 다르고, LED 를 두는 위치도 달라집니다.

| 패널 | 구조 | LED 위치 |
|------|------|----------|
| PC Flights — MISC · Gear · CMDS | 2중: 전면(검정 도색 + 흰색 각인) / 후면(투명) | 후면 투명판 뒤 **1~2 cm** |
| Greenisland — 그 외 전 패널 | 3중: Top(흰색 또는 투명 아크릴 2 mm) / Diffuser(투명 아크릴 2~3 mm) / LED layer(투명 PLA) | 패널 뒤 **몇 cm** 뒤 백라이트 플레이트 |

LED와 패널 사이에 간격을 두어 빛이 퍼지도록 합니다.

### 백라이트 플레이트 — 원설계와 다른 점

Greenisland 설계는 백라이트 LED 를 `LED layer` 에 함께 장착하도록 되어 있습니다.
`LED layer` 는 스위치가 체결되는 층이라 Top 바로 뒤에 붙습니다.

본 프로젝트는 LED 수를 줄이기 위해 패널 뒤에 별도 백라이트 플레이트를 설치합니다.

- `LED layer` 는 Top 과 거의 붙어 있어, LED 빛이 퍼지기 전에 패널에 닿습니다.
  고르게 밝히려면 LED 를 촘촘히 깔아야 하고, 그만큼 개수와 전류가 늘어납니다.
- 몇 cm 를 띄우면 빛이 퍼진 뒤 패널에 닿으므로, **훨씬 적은 수로 같은 균일도**가 나옵니다.

덕분에 전체 31스트링 93 LED, 약 422mA 로 끝나 12V 1A 어댑터 하나에 들어갑니다.

플레이트 STL 은 Left Aux 4장이 `3d stl/LeftAuxMiscCenter/LED Plate - *.stl`
(Gear · CMDS · TWA · HMCS), Left Console 4장이 `3d stl/LeftConsole/LED Plate1~4.stl` 입니다. 자작 모델이며 PLA 또는 레진 출력으로 충분합니다.

### LED layer 재질 — 투명 PLA 의 한계

`LED layer` 는 DXF 가 없어 **투명 PLA 로 3D 프린트**했습니다. 쓸 수는 있지만,
투명 PLA 출력물은 빛을 산란시킵니다. 백라이트 플레이트에서 나온 빛이 이 층을
지나면서 눈에 띄게 어두워집니다.

광량 손실을 줄이려면 투명 아크릴을 검토할 수 있습니다.
단, LED layer 용 재단 DXF 는 제공되지 않으므로 **제공되는 STL 이나 DXF 로부터 도면을 직접 떠야** 합니다.

### 스트링

- LED 3개 + 220Ω 저항 1개 = 직렬 스트링. 고휘도 녹색(Vf ≈ 3.0V) 기준 스트링당 약 13.6mA
- 콘솔 16스트링(48 LED, 218mA) · AUX 12스트링(36 LED, 163mA) · MISC 3스트링(9 LED, 41mA)
- 합 31스트링 93 LED, 약 422mA — 12V 1A 어댑터 하나로 충분

![Backlight LED 배치](backlight_photo.jpg)
