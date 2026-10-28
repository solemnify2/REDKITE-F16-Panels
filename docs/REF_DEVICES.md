# 디바이스 구성

Teensy 4.1 기반 USB 디바이스 **2대**가 핵심이고, 각각 별도의 스케치를 씁니다.
여기에 PC 에 직접 붙는 **MFD · LCD** 가 더해집니다.

| 디바이스 | 폴더 | PID | 규모 | 담당 |
|---|---|---|---|---|
| **Left Aux + MISC** | `F16_LEFT_AUX_MISC/` | `0x0489` | DX 51 · 축 4 | Gear, CMDS, TWA, Alt Gear, MISC, HMCS, Pedal |
| **Left Console** | `F16_LEFT_CONSOLE/` | `0x048E` | DX 64 · 축 10 | ECM, ELEC, EPU, AVTR, UHF, ENGINE START, MPO, AUDIO 1/2 |
| **MFD + LCD** | — | — | — | Thrustmaster MFD ×2 (USB) · 7.6인치 정사각 LCD ×2 (HDMI). **Teensy 와 연결되지 않습니다** — 다만 MFD 백라이트는 이 프로젝트의 브릿지가 인게임 조명에 맞춰 줍니다 |
| **ICP** | — | — | — | SimGears ICP (USB). 역시 Teensy 와 무관하며, **백라이트 연동은 포기**했습니다 |

MFD 와 LCD 는 Teensy 에 물리지 않습니다. MFD 는 Thrustmaster 자체 USB 장치이고,
LCD 는 HDMI 로 PC 에 붙는 모니터입니다.

**MFD 백라이트만은 이 프로젝트가 건드립니다.** `tools/` 의 브릿지가 Cougar MFD
(VID `0x044F`, PID `0xB351` · `0xB352`)를 HID 로 열어, 인게임 조명값에 맞춘 밝기를
feature report 로 보냅니다. 패널 백라이트와 같이 어두워지므로 쓰는 사람 입장에서는
한 콕핏으로 묶입니다. `hidapi` 가 없으면 이 부분만 건너뜁니다.

**SimGears ICP 는 포기했습니다.** 같이 쓰고 있지만 MFD 와 달리 HID feature report 로
밝기를 받지 않아, 브릿지에서 손댈 방법이 없었습니다. 백라이트는 자체 조절만 가능합니다.

장착은 [REF_MFD_LCD.md](REF_MFD_LCD.md) 참조.

배선도는 [REF_LEFT_AUX_WIRING.md](REF_LEFT_AUX_WIRING.md) · [REF_LEFT_CONSOLE_WIRING.md](REF_LEFT_CONSOLE_WIRING.md),
DX 번호와 BMS/DCS 주소 매핑은 [REF_PROTOCOL.md](REF_PROTOCOL.md) 를 보십시오.

---

## Left Aux + MISC (`0x0489`) — DX 51, 축 4

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
| AVTR | Switch (MCP23017) | OFF / AUTO / ON |
| UHF | Switch, Encoder ×6, Analog, 7-seg | FUNCTION(4), MODE(3), SQUELCH, T-TONE, STATUS, TEST + 주파수 엔코더 + VOL + MAX7219 디스플레이 |
| ENGINE START | Switch | JFS, ENG CONT, MAX PWR, AB RESET, ENG DATA |
| MPO | Switch | Manual Pitch Override |
| AUDIO 1/2 | Analog, Switch (MCP23017) | 볼륨 6개 + COMM 1/2 모드 로터리 2개 |

DX 59~61은 ENG CONT·EPU 커버 자동화용으로 **DCS에서만** 사용됩니다. DX 62~63은 **BMS 의 COMM1/COMM2 전원 자동화**로, 볼륨 노브를 끝까지 내리면 OFF, 올리면 ON 인 지속형 DX 입니다(pot ADC 임계값 감지). 64는 UHF TEST 입니다.
