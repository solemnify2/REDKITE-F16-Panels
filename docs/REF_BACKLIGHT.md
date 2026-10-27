# 백라이트

양쪽 보드 모두 **MOSFET PWM 디밍**을 씁니다. Teensy pin 13 으로 MOSFET 을 PWM 제어하며,
인게임 조명 노브에 연동됩니다.

---

양쪽 보드 모두 **MOSFET PWM 디밍**을 지원합니다. Teensy pin 13으로 MOSFET을 PWM 제어하며, 인게임 조명 노브에 연동됩니다.

## 회로

```
12V ─── LED strips (3 LED + 220Ω 직렬) ─── LED-RTN
                                               │
                                             Drain
                                               │
                                            MOSFET (IRLML6244, N-ch)
                                               │
                                             Source
                                               │
                                              GND ── 12V adapter GND ═══ Teensy GND (단일점!)
                                             Gate
                                              ├──┤1kΩ├── Teensy pin 13
                                              │
                                             10kΩ
                                              │
                                             GND
```

## 전원

**12V DC 어댑터 1개**를 **DC Y 케이블로 분기**해 양쪽 보드에 공급합니다.
콘솔은 백라이트 전류가 USB 예산을 넘고, AUX는 **Step-Up 을 쓰다가 래더 문제로 교체**했습니다.

> **Step-Up(MT3608 등)을 다시 쓰지 마십시오.** AUX 는 처음에 5V→12V 스텝업으로 백라이트를
> 구동했는데, 저항 래더 판독값이 흔들려 한참 고생했습니다. 스텝업의 스위칭 전류가 5V 레일과
> GND 에 리플을 싣고, 래더는 같은 3.3V·GND 를 기준으로 분압을 재기 때문에 기준 자체가
> 움직입니다. ECM 처럼 상위 값 간격이 28카운트뿐인 래더에서는 그대로 오인식이 됩니다.
> DC 어댑터로 바꾸면 백라이트 전류 경로가 Teensy 전원에서 완전히 분리됩니다.
> 덤으로 USB 예산에서 풀려나 스트링을 넉넉히 달 수 있습니다 (현재 31스트링 422mA).

**양쪽 모두 어댑터 GND ↔ Teensy GND를 단일점(star)으로 반드시 연결하세요.** MOSFET Gate 기준이 없으면 백라이트가 동작하지 않습니다.

> 어댑터를 공유하므로 두 보드의 12V GND가 이어집니다. 두 Teensy는 PC의 USB GND로도 이미
> 연결돼 있어 **접지 루프가 생깁니다.** 백라이트 전류(수십 mA 수준)에서는 문제가 없지만,
> 래더 값이 보드 간섭처럼 흔들리면 이 경로를 먼저 의심하십시오.

## 밝기 제어

| 상태 | 동작 |
|---|---|
| BMS online | 브릿지가 `instrLight` → `ledBits` byte 2로 brightness 0~255 전송 |
| DCS online | Teensy가 `LIGHT_INST_PNL`(0x4484) 0~65535 → >>8 → PWM 0~255 직접 변환 |
| Offline 수동 (AUX) | DN LOCK REL 누른 채 HMCS Symbology pot(A15)로 밝기 조절 (방향 반전) |
| Offline 수동 (콘솔) | UHF STATUS 누른 채 UHF VOL pot(A9)로 밝기 조절 |
| Idle 30분 | 자동 꺼짐. 아무 입력으로 복귀 |
| USB Suspend | LED + 백라이트 소등, MCU 절전 |

## LED 배치
- PC Flights 패널은 2중 구조 (전면: 검정 도색 + 흰색 각인 / 후면: 투명)
- 후면 투명 패널 뒤쪽 1~2cm 간격에서 LED를 쏘면 전면 각인 글자가 빛남
- LED 3개 + 220Ω 저항 1개 = 직렬 스트링. 고휘도 녹색(Vf ≈ 3.0V) 기준 스트링당 약 13.6mA
- 콘솔 16스트링(48 LED, 218mA) · AUX 12스트링(36 LED, 163mA) · MISC 3스트링(9 LED, 41mA)
- 합 31스트링 93 LED, 약 422mA — 12V 1A 어댑터 하나로 충분

![Backlight LED 배치](backlight_photo.jpg)
