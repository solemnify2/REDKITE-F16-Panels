# 디바이스 구성

Teensy 4.1 기반 USB 디바이스 **2대**가 핵심이고, 각각 별도의 스케치를 씁니다.
여기에 PC 에 직접 붙는 **MFD · LCD** 가 더해집니다.

| 디바이스 | 폴더 | PID | 규모 | 담당 |
|---|---|---|---|---|
| **Left Aux + MISC** | `F16_LEFT_AUX_MISC/` | `0x0487` | DX 51 · 축 4 | Gear, CMDS, TWA, Alt Gear, MISC, HMCS, Pedal |
| **Left Console** | `F16_LEFT_CONSOLE/` | `0x048E` | DX 64 · 축 10 | ECM, ELEC, EPU, AVTR, UHF, ENGINE START, MPO, AUDIO 1/2 |
| **MFD + LCD** | — | — | — | Thrustmaster MFD ×2 (USB) · 7.6인치 정사각 LCD ×2 (HDMI). PC에 직접 연결. MFD 백라이트는 브리지가 동기화 |
| **ICP** | — | — | — | SimGears ICP (USB). PC에 직접 연결하며, 백라이트는 자체 조절합니다 |

MFD·LCD·ICP는 PC에 직접 연결합니다. Teensy 펌웨어는 두 패널 보드만 담당합니다.
브리지는 Cougar MFD(VID `0x044F`, PID `0xB351`·`0xB352`)의 백라이트를 HID feature report로 제어합니다.
`hidapi`가 없으면 MFD 밝기 동기화만 건너뜁니다. ICP 백라이트는 자체 조절을 사용합니다.

| 참고 항목 | 문서 |
|---|---|
| MFD·LCD 장착 | [REF_MFD_LCD.md](REF_MFD_LCD.md) |
| AUX·MISC 배선과 DX 번호 | [REF_LEFT_AUX_WIRING.md](REF_LEFT_AUX_WIRING.md) |
| 콘솔 배선과 DX 번호 | [REF_LEFT_CONSOLE_WIRING.md](REF_LEFT_CONSOLE_WIRING.md) |
| LED 프로토콜과 주소 | [REF_PROTOCOL.md](REF_PROTOCOL.md) |
| 게임 입력 매핑 | [REF_KEYMAP.md](REF_KEYMAP.md) |

---

## Left Aux + MISC (`0x0487`) — DX 51, 축 4

| Panel | Type | Description |
|-------|------|-------------|
| Gear | Switch, LED | Landing Gear, Hook, Anti-skid, Landing Light, Gear Warning 등 |
| Alt Gear | Switch | ALT Gear Handle |
| MISC | Switch, LED (MCP23017) | Master ARM, Laser ARM, RF, Autopilot Pitch/Roll, ECM LED 등 |
| CMDS | Switch, Analog Ladder, LED | RWR, JMR, MWS, JETT, MODE (7-pos), PRGM (7-pos), GO/NO GO/RDY EWS 램프 |
| TWA | Analog Ladder, LED | Threat Warning Aux — Search, Act/Pwr, Low, Power |
| HMCS | Analog | Symbology 포텐셔미터 |
| Pedal | Analog | Rudder + Left/Right Brake (auto calibration) |

## Left Console (`0x048E`) — DX 64, 축 10

| Panel | Type | Description |
|-------|------|-------------|
| ECM | Switch (MCP23017), Analog Ladder, LED (74HC595) | OPR/STBY, XMIT, BIT, RESET + 8버튼 래더 + S/A/F/T 32 LED |
| ELEC | Switch, LED (MCP23017) | MAIN PWR, CAUTION RST + 경고등 8개 |
| EPU | Switch (MCP23017) | OFF / NORM / ON |
| AVTR | Switch (MCP23017) | OFF / ON / AUTO — 가운데 ON |
| UHF | Switch, Encoder ×6, Analog, 7-seg | FUNCTION(4), MODE(3), SQUELCH, T-TONE, STATUS, TEST + 주파수 엔코더 + VOL + MAX7219 디스플레이 |
| ENGINE START | Switch | JFS, ENG CONT, MAX PWR, AB RESET, ENG DATA |
| MPO | Switch | Manual Pitch Override |
| AUDIO 1/2 | Analog, Switch (MCP23017) | 볼륨 9개 + COMM 1/2 모드 로터리 2개 + HOT MIC/OFF/CIPHER 토글 |

DX 번호는 `dxOrder[]` 순서로 배정합니다. 커버 개폐와 COMM1/COMM2 전원처럼 펌웨어가 합성하는 DX도 포함됩니다.
COMM 전원 DX는 볼륨 ADC가 임계값 이상인 동안 눌린 상태를 유지합니다.
전체 번호는 [콘솔 DX 맵](REF_LEFT_CONSOLE_WIRING.md#dx-버튼-맵-64--128)을 참고하십시오.

프로토콜 자동 판별은 LED·백라이트 동기화에 사용합니다. 스위치와 자동화 DX는 어느 시뮬레이터에서나 동일하게 출력하며,
해당 게임에 대응 기능이 없으면 매핑을 비워 둡니다.
