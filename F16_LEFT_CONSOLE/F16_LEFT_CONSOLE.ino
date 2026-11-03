// ================================================================
//  REDKITE F16 LEFT CONSOLE — USB Joystick
// ================================================================
//
//  Board  : Teensy 4.1
//  Panels : ECM / ELEC / EPU / AVTR / UHF(엔코더 6) / ENGINE START / MPO / AUDIO 1-2
//  I2C    : Wire2 (SDA2=25, SCL2=24)
//  Buttons: 64,  축 10,  엔코더 6
//  사용 핀: 41 / 42 (헤더),  여유 1
//  백라이트: pin 13 — 온보드 LED가 상태 표시등이 됨
//
//  DX 버튼 배정 순서: dxOrder[] 표의 줄 순서 그대로 (총 64)
//                     실기 콘솔 전→후, 패널 안에서는 좌→우 / 상→하
//  축 10개: AUDIO 1 x6 + AUDIO 2 x3 + UHF VOL x1
//
//  USB Type: Serial + Keyboard + Mouse + Joystick
//  PID:      0x048E, JOYSTICK_SIZE 64 (usb_desc.h)
//
//  Hardware is data-driven. To add/remove hardware, edit the
//  HARDWARE CONFIGURATION section only. Joystick button numbers
//  are auto-assigned at runtime.
//
//  확장 하드웨어:
//    MCP23017 x3 @ 100kHz
//      0x20  UHF switches + AUDIO1 COMM 모드 + AUDIO2 HOT MIC/CIPHER  [UHF 패널 실장]
//      0x21  ELEC switches (GPB0~2) + EPU switches (GPB6~7) + ELEC LED 8 (GPA) + EPU LED 3 (GPB3~5)
//      0x22  ECM switches + AVTR
//    74HC595 x4 — ECM 32 LEDs (direct, high-speed shift)
//    Resistor ladder — ECM 8 buttons (direct, analog)
// ================================================================


// ================================================================
//  Build Checks
// ================================================================

// 58버튼이라 12(32버튼)로는 부족합니다. 64로 통일하면 LEFT_AUX_MISC 와
// usb_desc.h 를 공유할 수 있습니다.
#if JOYSTICK_SIZE != 64
  #error "JOYSTICK_SIZE must be 64. Edit USB_SERIAL_HID section in %LOCALAPPDATA%/Arduino15/packages/teensy/hardware/avr/<version>/cores/teensy4/usb_desc.h"
#endif

#if PRODUCT_ID != 0x048E
  #error "PRODUCT_ID must be 0x048E for Left Console. Edit USB_SERIAL_HID section in usb_desc.h"
#endif

// ================================================================
//  General Settings
// ================================================================

#define BAUDRATE          1000000
#define ALLOW_DEBUG       false
#define SERIAL_TIMEOUT    3         // seconds before protocol reset

// BACKLIGHT_PIN 은 아래 핀 배정 블록에서 정의합니다 (13).
// MOSFET gate: PWM dimming (0=off, 255=full brightness)
#define IDLE_TIMEOUT_MS   (1000UL * 60 * 30)   // offline idle -> backlight auto-off (30min)

#define LOOP_DELAY_MS     10        // 100Hz — encoder pulse throughput
#define MCP_WIRE          Wire2     // SCL2 = pin 24, SDA2 = pin 25

// 100kHz (Standard Mode).
// I2C 는 데이지 체인입니다 — Teensy -I1-> 0x20(UHF) -I2-> 0x21(ELEC) -I3-> 0x22(ECM).
// MCP23017 모듈의 2열 7핀 헤더로 받아서 넘깁니다. 단일 버스이므로
// 풀업과 용량을 체인 전체 기준으로 계산해야 합니다.
//
//   풀업 : 모듈 온보드 4.7kΩ("472") x3 병렬 = 약 1.57kΩ
//   용량 : Cat5e 약 50pF/m x 체인 총 길이 + 소자/패턴
//          예) 2m + 2m + 0.3m = 4.3m => 약 215pF + 50pF = 265pF
//   tr   : 0.847 x 1570 x 265p = 약 352ns
//
// 352ns 는 400kHz 규격(300ns)을 넘고 100kHz 규격(1000ns)에는 여유가 큽니다.
// 버스 점유율도 T41 기준 11% 수준이라 속도를 올릴 이유가 없고,
// LEFT_AUX_MISC 보드도 같은 이유로 100kHz를 씁니다.
// 400kHz로 올리려면 스터브를 짧게 하고 모듈 풀업 일부를 제거한 뒤 실측해야 합니다.
//
// 주의: 모듈을 4장 이상 병렬로 달면 풀업 합성이 1.2kΩ 아래로 내려가
// 싱크 전류가 I2C 규격(3mA)에 근접하므로 일부 모듈의 풀업을 제거해야 합니다.
#define MCP_I2C_CLOCK     100000


// ================================================================
//  단계별 핀 배정
// ================================================================
//
//  T41 핀 배치 — 엣지 A = 0~12 + 24~32,  엣지 B = 13~23 + 33~41
//    A  0~11   엔코더 6 (C2, C3)
//    A  26~32  ENGINE 스위치 + JFS RUN LED (C1) — MPO 만 엣지 B 의 40
//    B  14~23  POT 10 (C2 UHF VOL, C4 AUDIO 1 x6, C5 AUDIO 2 x3)
//    B  33~34  UHF T-TONE / SQUELCH (C13, Teensy→UHF 신설)
//    B  35~38  74HC595 3선 + ECM 래더 (C6)
//    B  40     MPO (C1)
//    B  13     백라이트 MOSFET
//    B  39     UHF TEST (C13)
//    B  41     UHF STATUS (C13)
//    하단 SD  43/44/45 = MOSI2/CS2/SCK2 -> UHF 7세그 디스플레이 (C14)
//             SD 확장 케이블로 빼냅니다. 엣지 핀은 쓰지 않습니다.
//    여유: 12
//  ※ docs/REF_LEFT_CONSOLE_WIRING.md 의 핀 배열도는 바닥면(납땜면) 기준이라
//    엣지 A 가 그림의 오른쪽 열, 엣지 B 가 왼쪽 열로 나옵니다.

// 출력이면 온보드 LED 공유가 무해하고, LED가 상태 표시등이 됩니다.
#define BACKLIGHT_PIN     13

// C6: 74HC595 3선 + ECM 래더 (핀 35~38, 엣지 B 하단 블록)
#define PIN_SR_LATCH      37      // ST_CP
#define PIN_SR_CLOCK      36      // SH_CP
#define PIN_SR_DATA       35      // DS
#define PIN_LADDER        A14     // pin 38  ⚠ 필터 캡은 A14 에

// C1: ENGINE START (핀 26~32, 엣지 A 하단 블록) + MPO(40)
// 엣지 A 하단 블록이 7핀뿐이라 MPO 만 엣지 B 의 40 에 남습니다.
#define PIN_MPO           40      // A16
#define PIN_LED_JFS_RUN   26      // A12  ENGINE START RUN 램프
#define PIN_JFS1          27      // A13
#define PIN_JFS2          28
#define PIN_ENG_CONT      29
#define PIN_ABRESET       30
#define PIN_ENGDATA       31
#define PIN_MAXPOWER      32

// C2: UHF VOL (핀 23)
#define PIN_POT_UHFVOL    A9      // pin 23

// C4: AUDIO 1 POT x6 (핀 17~22)
#define PIN_POT_COMM1     A8      // pin 22
#define PIN_POT_COMM2     A7      // pin 21
#define PIN_POT_SECURE    A6      // pin 20
#define PIN_POT_MSL       A5      // pin 19
#define PIN_POT_TF        A4      // pin 18
#define PIN_POT_THREAT    A3      // pin 17

// C5: AUDIO 2 POT x3 (핀 14~16) — HOT MIC/CIPHER 는 MCP#0 PA0/PA1 로 이설
#define PIN_POT_INTCOM    A2      // pin 16
#define PIN_POT_TACAN     A1      // pin 15
#define PIN_POT_ILS       A0      // pin 14

// C13: UHF T-TONE / SQUELCH — MCP#0 에서 Teensy 직결로 이설 (핀 33~34)
#define PIN_UHF_TTONE     34
#define PIN_UHF_SQUELCH   33

// UHF STATUS (핀 41)
#define PIN_UHF_STATUS    41      // A17

// UHF TEST (핀 39)
#define PIN_UHF_TEST      39      // A15

// ---- C14: UHF 7세그 디스플레이 (MAX7219) ----------------------------------
// Teensy 4.1 하단 SD 카드 인터페이스의 SPI2 를 SD 확장 케이블로 빼내 씁니다.
// 엣지 핀(0~41)은 전혀 쓰지 않으므로 기존 배치가 그대로 유지됩니다.
// ⚠ SD 카드를 쓰게 되면 충돌합니다.
// 핀↔µSD 접점 대응은 핀아웃 카드 card11b_rev4 기준. MOSI2·SCK2 는 실리콘 고정이고
// CS 만 자유로운데, 46 에 두면 FPC 도선이 J1.2->J1.5 순서로 15 -> 12 -> 6 -> 4
// 내림차순이 되어 리본이 교차하지 않습니다 (오름차순은 MOSI2/SCK2 위치상 불가능).
#define PIN_DISP_DIN      43      // MOSI2 / SD DAT0 (µSD 7, FPC 12) -> J1.3 DIN
#define PIN_DISP_CLK      45      // SCK2  / SD CMD  (µSD 3, FPC  6) -> J1.4 CLK
#define PIN_DISP_CS       46      // GPIO  / SD DAT3 (µSD 2, FPC  4) -> J1.5 CS (소프트웨어 토글)

// Encoder -> DX pulse timing (in main-loop ticks)
#define ENC_PULSE_TICKS   4         // pulse held ~40ms @100Hz
#define ENC_PENDING_MAX   30        // queue cap, prevents runaway lag


// ================================================================
//  Type Definitions
// ================================================================

enum SwitchType {
  SW_ON_OFF,      // 1 pin  -> 1 button
  SW_ON_OFF_ON,   // 2 pins -> 2 buttons (center = both off)
  SW_ROTARY       // numPos consecutive pins -> numPos buttons (one active)
};

enum JoyAxis {
  AXIS_X = 0, AXIS_Y, AXIS_Z, AXIS_Xr, AXIS_Yr, AXIS_Zr,   // analog16(0..5)
  AXIS_S1, AXIS_S2, AXIS_S3, AXIS_S4, AXIS_S5, AXIS_S6,    // slider(1..17)
  AXIS_S7, AXIS_S8, AXIS_S9, AXIS_S10
};

enum Panel {
  PNL_ECM, PNL_ELEC, PNL_EPU, PNL_AVTR,
  PNL_UHF, PNL_ENGINE, PNL_MPO, PNL_AUDIO1, PNL_AUDIO2,
  PNL_COUNT
};

const char* const panelNames[] = {
  "ECM", "ELEC", "EPU", "AVTR", "UHF", "ENGINE", "MPO", "AUDIO1", "AUDIO2"
};

struct McpDeviceDef {
  const char* name;
  uint8_t     addr;     // I2C address (0x20-0x27)
};

struct SwitchDef {
  const char* name;
  Panel       panel;
  SwitchType  type;
  int8_t      mcpIdx;   // -1 = direct Teensy pin, >= 0 = index into mcpDevices[]
  uint8_t     pin1;
  uint8_t     pin2;     // SW_ON_OFF_ON only
  uint8_t     numPos;   // SW_ROTARY only: consecutive pins starting at pin1
};

// LEDs live on MCP23017 (mcpIdx >= 0) or direct Teensy pins (mcpIdx = -1).
struct LedDef {
  const char* name;
  Panel       panel;
  uint8_t     pin;
  int8_t      mcpIdx;
};

// NOTE: pots have no mcpIdx — MCP23017 has no ADC.
struct PotDef {
  const char* name;
  Panel       panel;
  uint8_t     pin;
  JoyAxis     axis;
};

// NOTE: encoders have no mcpIdx — I2C polling is too slow, pulses would be lost.
// 디텐트는 그대로 CW/CCW 펄스로 배출됩니다 — 자리 순환·경계 처리는 BMS 가 합니다.
struct EncoderDef {
  const char* name;
  Panel       panel;
  uint8_t     pinA;
  uint8_t     pinB;
};

// Resistor-ladder button array: multiple buttons on one analog pin.
// Nearest-value match; reject if below last value - (adjacent gap / 2).
struct AnalogBtnArrayDef {
  const char*        groupName;
  Panel              panel;
  uint8_t            pin;
  uint8_t            numButtons;
  const char* const* btnNames;
  const int*         values;
};


// ================================================================
//
//  >>> HARDWARE CONFIGURATION - Edit this section <<<
//
// ================================================================
//
//  하드웨어를 바꿀 때는 아래 config 배열만 고칩니다. DX 버튼 번호는 런타임에
//  자동 배정되므로 직접 매기지 않습니다. 패널을 빼려면 해당 항목을 주석 처리하면 됩니다.
//
//    switches[]          디지털 스위치 — mcpIdx -1 = Teensy 직결, 0+ = mcpDevices[] 인덱스
//    analogBtnArrays[]   저항 래더 그룹 (아날로그 핀 1개에 버튼 여러 개)
//    pots[]              포텐셔미터 -> 조이스틱 축
//    leds[]              LED — mcpIdx 규칙은 switches[] 와 동일
//    mcpDevices[]        MCP23017 I2C 주소. 새 확장 칩은 여기 등록
//    encoders[]          로터리 엔코더 (콘솔 전용)
//    srMap[]             74HC595 논리 -> 물리 출력 리맵 (콘솔 전용)
//
//  예) {"My Switch",  PNL_GEAR, SW_ON_OFF, -1, 5, 0, NULL}   Teensy 핀 5
//      {"MCP Switch", PNL_MISC, SW_ON_OFF,  0, 5, 0, NULL}   MCP#0 GPA5
//
//  ※ 이 배열의 순서는 DX 번호와 무관합니다. 배선대로 두고, 새 하드웨어를
//    추가하면 `dxOrder[]` 에 한 줄 넣으십시오 — 빠뜨리면 컴파일이 막힙니다.
//


// --- MCP23017 I/O Expanders (Wire2: SCL2=24, SDA2=25) ---
// MCP pin numbering: GPA0-7 = 0-7, GPB0-7 = 8-15
const McpDeviceDef mcpDevices[] = {
  // name                    addr
  {"UHF",                    0x20},   // idx 0 — UHF panel mounted, I2C chain head
  {"ELEC+EPU",               0x21},   // idx 1 — ELEC panel mounted
  {"ECM+AVTR",               0x22},   // idx 2 — ECM panel mounted
};

// --- Digital Switches ---
//
const SwitchDef switches[] = {
  // name                 panel        type           mcpIdx pin1 pin2 numPos
  //
  // ※ 이 배열의 순서는 **읽기 좋으라고** 실기 배치를 따릅니다. DX 번호와는
  //   무관합니다 — 번호는 `dxOrder[]` 가 정합니다. 새 하드웨어를 넣을 때는
  //   배선상 맞는 자리에 넣고, `dxOrder[]` 에도 한 줄 추가하십시오.

  // ---- MANUAL PITCH — 최전방 인보드 (Teensy direct) ----
  {"MPO",       PNL_MPO,    SW_ON_OFF,    -1, PIN_MPO,        0,  0},  // NORM/OVRD

  // ---- UHF Panel — 최전방 아웃보드 (MCP 0x20 PB + Teensy direct, 패널 실장) ----
  // 실제 배선: FUNCTION(PB4~7) → MODE(PB1~3) → STATUS(PB0)
  // SW_ROTARY 는 pin1 부터 numPos 개를 오름차순으로만 읽어 패널 순서대로
  // 늘어놓을 수 없습니다. 그래서 개별 SW_ON_OFF 로 분리했습니다.
  {"UHF TEST",  PNL_UHF,    SW_ON_OFF,    -1, PIN_UHF_TEST,   0,  0},  // Teensy 39 (A15) momentary
  {"UHF STATUS",  PNL_UHF, SW_ON_OFF, -1, PIN_UHF_STATUS,  0, 0},  // Teensy 41  momentary
  {"UHF FUNC OFF",   PNL_UHF, SW_ON_OFF, 0, 12, 0, 0},  // PB4
  {"UHF FUNC MAIN",  PNL_UHF, SW_ON_OFF, 0, 13, 0, 0},  // PB5
  {"UHF FUNC BOTH",  PNL_UHF, SW_ON_OFF, 0, 14, 0, 0},  // PB6
  {"UHF FUNC ADF",   PNL_UHF, SW_ON_OFF, 0, 15, 0, 0},  // PB7
  {"UHF MODE MNL",   PNL_UHF, SW_ON_OFF, 0,  9, 0, 0},  // PB1
  {"UHF MODE PRE",   PNL_UHF, SW_ON_OFF, 0, 10, 0, 0},  // PB2
  {"UHF MODE GRD",   PNL_UHF, SW_ON_OFF, 0, 11, 0, 0},  // PB3
  {"UHF T-TONE",   PNL_UHF, SW_ON_OFF, -1, PIN_UHF_TTONE,   0, 0},  // Teensy 34  momentary
  {"UHF SQUELCH",  PNL_UHF, SW_ON_OFF, -1, PIN_UHF_SQUELCH, 0, 0},  // Teensy 33

  // ---- ENG & JET START Panel (Teensy direct) ----
  {"JFS",       PNL_ENGINE, SW_ON_OFF_ON, -1, PIN_JFS1, PIN_JFS2, 0},  // OFF/START1/START2
  {"ENG CONT",  PNL_ENGINE, SW_ON_OFF,    -1, PIN_ENG_CONT,   0,  0},  // PRI/SEC
  // 3단 토글 하나입니다 (AB RESET / NORM / ENG DATA). 중립은 양쪽 다 열림.
  {"AB RESET/ENG DATA", PNL_ENGINE, SW_ON_OFF_ON, -1, PIN_ABRESET, PIN_ENGDATA, 0},
  {"MAX POWER", PNL_ENGINE, SW_ON_OFF,    -1, PIN_MAXPOWER,   0,  0},

  // ---- AUDIO 1 모드 로터리 (MCP 0x20 PA, 케이블 C8 로 UHF 패널까지 점퍼) ----
  // 실제 배선: COMM1 PA4=OFF PA3=SQL PA2=GD, COMM2 PA7=OFF PA6=SQL PA5=GD
  {"COMM1 OFF",   PNL_AUDIO1, SW_ON_OFF, 0, 4, 0, 0},  // PA4
  {"COMM1 SQL",   PNL_AUDIO1, SW_ON_OFF, 0, 3, 0, 0},  // PA3
  {"COMM1 GD",    PNL_AUDIO1, SW_ON_OFF, 0, 2, 0, 0},  // PA2
  {"COMM2 OFF",   PNL_AUDIO1, SW_ON_OFF, 0, 7, 0, 0},  // PA7
  {"COMM2 SQL",   PNL_AUDIO1, SW_ON_OFF, 0, 6, 0, 0},  // PA6
  {"COMM2 GD",    PNL_AUDIO1, SW_ON_OFF, 0, 5, 0, 0},  // PA5

  // ---- AUDIO 2 Panel (MCP 0x20 PA) ----
  // 실제 하드웨어는 3단 토글 하나입니다 (HOT MIC / OFF / CIPHER).
  // 양쪽 접점이 PA0·PA1 이고 중립은 둘 다 열림 — SW_ON_OFF_ON 과 같은 모양입니다.
  {"HOT MIC/CIPHER",      PNL_AUDIO2,  SW_ON_OFF_ON,     0,   0,   1,  0},  // PA0/PA1

  // ---- ECM Panel (MCP 0x22, GPB) ----
  {"ECM OPR/STBY",        PNL_ECM,     SW_ON_OFF_ON,     2,  11,  10,  0},  // GPB3/GPB2  (OPR/OFF)
  {"ECM XMIT",            PNL_ECM,     SW_ON_OFF_ON,     2,  13,  12,  0},  // GPB5/GPB4  (XMIT1/XMIT3)
  {"ECM RESET",           PNL_ECM,     SW_ON_OFF,        2,  15,   0,  0},  // GPB7  momentary
  {"ECM BIT",             PNL_ECM,     SW_ON_OFF,        2,  14,   0,  0},  // GPB6  momentary

  // ---- EPU Panel (MCP 0x21) ----
  {"EPU",                 PNL_EPU,     SW_ON_OFF_ON,     1,   8,   9,  0},  // GPB0/GPB1  OFF/NORM/ON (배선 교차)

  // ---- ELEC Panel (MCP 0x21) ----
  {"ELEC MAIN PWR",       PNL_ELEC,    SW_ON_OFF_ON,     1,  14,  15,  0},  // GPB6/GPB7  MAIN/OFF (배선 교차)
  {"ELEC CAUTION RST",    PNL_ELEC,    SW_ON_OFF,        1,  10,   0,  0},  // GPB2  momentary (CAUTION RST)

  // ---- AVTR Panel (MCP 0x22) ----
  {"AVTR",                PNL_AVTR,    SW_ON_OFF_ON,     2,   8,   9,  0},  // GPB0/GPB1  UNTHRD/RECORD/EVENT MRK
};

// --- Rotary Encoders (Teensy direct, interrupt-polled) ---
// Each encoder emits 2 buttons: CW then CCW.
//
// Pin pairs must stay on the SAME board edge — an encoder's A/B are two wires
// from one knob. The two Teensy 4.1 edges are 0-12 + 24-32 and 13-23 + 33-41.
// The six encoders fill 0-11 in the panel's knob order (PRESET, then the
// frequency digits). C2 lands contiguous on 4-9; C3 is split 0-3 + 10-11.
// The encoder cables' only line on the other edge is VOL (pin 23).
const EncoderDef encoders[] = {
  // name              panel     pinA pinB
  // 순서는 이미 패널 배치 그대로입니다 — PRESET(우상단) 다음 주파수 노브 좌→우.
  {"UHF PRESET",       PNL_UHF,    1,   0},   // C3  pinA/B swapped
  {"UHF 100MHz",       PNL_UHF,    2,   3},   // C3
  {"UHF 10MHz",        PNL_UHF,    4,   5},   // C2
  {"UHF 1MHz",         PNL_UHF,    6,   7},   // C2
  {"UHF 0.1MHz",       PNL_UHF,    8,   9},   // C2
  {"UHF 0.025MHz",     PNL_UHF,   10,  11},   // C3
};
#define NUM_ENCODERS  (sizeof(encoders) / sizeof(encoders[0]))

// --- Analog Pots ---
const PotDef pots[] = {
  // name                 panel        pin              axis
  //
  // ※ 순서는 실기 배치(전→후, 좌→우)를 따릅니다. **축 배정과는 무관합니다** —
  //   축은 각 항목의 `axis` 열이 직접 지정하므로 줄을 옮겨도 그대로입니다.
  //   AXIS_S3·S4 (TF·TACAN) 는 DirectInput 이 인식하지 못해 BMS 바인딩 불가.

  // ---- UHF Panel — 최전방 아웃보드 ----
  {"UHF VOL",             PNL_UHF,     PIN_POT_UHFVOL,  AXIS_Zr},

  // ---- AUDIO 1 — 상단 COMM1·COMM2·SECURE·MSL / 하단 TF·THREAT ----
  {"AUDIO COMM CH1",      PNL_AUDIO1,  PIN_POT_COMM1,   AXIS_X},
  {"AUDIO COMM CH2",      PNL_AUDIO1,  PIN_POT_COMM2,   AXIS_Y},
  {"AUDIO SECURE VOL",    PNL_AUDIO1,  PIN_POT_SECURE,  AXIS_S2},
  {"AUDIO MSL VOL",       PNL_AUDIO1,  PIN_POT_MSL,     AXIS_Z},
  {"AUDIO TF VOL",        PNL_AUDIO1,  PIN_POT_TF,      AXIS_S3},    // DirectInput 미인식
  {"AUDIO THREAT VOL",    PNL_AUDIO1,  PIN_POT_THREAT,  AXIS_Xr},

  // ---- AUDIO 2 — INTERCOM·TACAN·ILS ----
  {"AUDIO INTERCOM",      PNL_AUDIO2,  PIN_POT_INTCOM,  AXIS_Yr},
  {"AUDIO TACAN VOL",     PNL_AUDIO2,  PIN_POT_TACAN,   AXIS_S4},    // DirectInput 미인식
  {"AUDIO ILS VOL",       PNL_AUDIO2,  PIN_POT_ILS,     AXIS_S1},
};
#define NUM_POTS      (sizeof(pots) / sizeof(pots[0]))

// --- ECM Resistor Ladder (8 buttons on A9) ---
// PCB is fixed: 10k series chain + 20k pulldown.
// ADC_k = 1023 * 20000 / (k * 10000 + 20000)   (k = 0..7)
// Matching is nearest-value, so the tight 253/225 pair (gap 28) is safe:
// the decision boundary sits at 239, giving +/-14 noise margin.
// 8x oversampling keeps ADC noise around +/-2 counts.
const char* const ecmBtnNames[] = {
  "ECM 1", "ECM 2", "ECM 3", "ECM 4",
  "ECM 5", "ECM 6", "ECM FRM", "ECM SPL"
};
const int ecmBtnValues[] = {1013, 674, 504, 402, 335, 287, 251, 223};  // measured, BL OFF/ON identical

const AnalogBtnArrayDef analogBtnArrays[] = {
  // groupName      panel     pin  numBtn  btnNames      values
  {"ECM Buttons",   PNL_ECM,  PIN_LADDER, 8,      ecmBtnNames,  ecmBtnValues},
};

// --- ELEC Panel LEDs (MCP 0x21, GPA port) ---
// All 8 on GPA so the whole port updates in one I2C write.
// NOTE: LEDs are sourced (cathode common to GND), so the binding limit is
//       VDD inflow 125mA — not the VSS 150mA figure. 0x21 carries 11 LEDs
//       (ELEC 8 + EPU 3), so keep each at or below 10mA (11 x 10 = 110mA).
enum LedIdx {
  // leds[] 와 **같은 순서**여야 합니다 — 이 값이 그대로 BMS-BIOS ledBits 의
  // 비트 번호이고, tools/bmsbios_bridge.py 의 CONSOLE_LED_MAP 과 짝입니다.
  // ---- ENGINE START (bit 0) ----
  LI_JFS_RUN,
  // ---- EPU 패널 (bit 1~3) ----
  LI_EPU_HYDRAZN, LI_EPU_AIR, LI_EPU_RUN,
  // ---- ELEC 패널 경고등 (bit 4~11) ----
  LI_FLCS_PMG, LI_MAIN_GEN, LI_STBY_GEN, LI_EPU_GEN,
  LI_EPU_PMG, LI_BATT_TO_FLCS, LI_FLCS_RLY, LI_BATT_FAIL,
};

const LedDef leds[] = {
  // name               panel      pin  mcpIdx

  // ---- ENGINE START 패널 (Teensy 직결, 케이블 1에 탑승) ----
  {"JFS RUN",           PNL_ENGINE, PIN_LED_JFS_RUN, -1},

  // ---- EPU 패널 (MCP 0x21 GPB3~4 + 0x22 GPA7) ----
  {"EPU HYDRAZN",       PNL_EPU,   11,   1},   // GPB3
  {"EPU AIR",           PNL_EPU,   12,   1},   // GPB4
  {"EPU RUN",           PNL_EPU,    7,   2},   // MCP 0x22 GPA7 (0x21 GPB5 핀 불량으로 이설)

  // ---- ELEC 패널 경고등 8 (MCP 0x21 GPA0~7) ----
  // GPA 한 포트에 몰아 두어 I2C 한 번에 전체가 갱신됩니다.
  {"FLCS PMG",          PNL_ELEC,   0,   1},   // GPA0
  {"MAIN GEN",          PNL_ELEC,   1,   1},   // GPA1
  {"STBY GEN",          PNL_ELEC,   2,   1},   // GPA2
  {"EPU GEN",           PNL_ELEC,   3,   1},   // GPA3
  {"EPU PMG",           PNL_ELEC,   4,   1},   // GPA4
  {"BATT TO FLCS",      PNL_ELEC,   5,   1},   // GPA5
  {"FLCS RLY",          PNL_ELEC,   6,   1},   // GPA6
  {"BATT FAIL",         PNL_ELEC,   7,   1},   // GPA7
};

// --- ECM Panel LEDs (74HC595 x4, daisy-chained, 32 outputs) ---
#define SR_DATA_PIN    PIN_SR_DATA    // DS
#define SR_CLOCK_PIN   PIN_SR_CLOCK   // SH_CP
#define SR_LATCH_PIN   PIN_SR_LATCH   // ST_CP
#define SR_NUM_CHIPS   4
#define SR_NUM_OUTPUTS (SR_NUM_CHIPS * 8)  // 32

static uint8_t srData[SR_NUM_CHIPS];

const char* const ecmSrLedNames[] = {
  "ECM_1_S", "ECM_1_A", "ECM_1_F", "ECM_1_T",
  "ECM_2_S", "ECM_2_A", "ECM_2_F", "ECM_2_T",
  "ECM_3_S", "ECM_3_A", "ECM_3_F", "ECM_3_T",
  "ECM_4_S", "ECM_4_A", "ECM_4_F", "ECM_4_T",
  "ECM_5_S", "ECM_5_A", "ECM_5_F", "ECM_5_T",
  "ECM_6_S", "ECM_6_A", "ECM_6_F", "ECM_6_T",
  "ECM_FRM_S", "ECM_FRM_A", "ECM_FRM_F", "ECM_FRM_T",
  "ECM_SPL_S", "ECM_SPL_A", "ECM_SPL_F", "ECM_SPL_T",
};

// Logical index -> physical SR output (PCB wiring is not in shift order)
const uint8_t srMap[SR_NUM_OUTPUTS] = {
  17, 16, 19, 18,  // ECM 1: S, A, F, T
  23, 22, 21, 20,  // ECM 2
  25, 24, 27, 26,  // ECM 3
  31, 30, 29, 28,  // ECM 4
  13, 12, 15, 14,  // ECM 5
  11, 10,  9,  8,  // ECM 6
   5,  4,  7,  6,  // ECM FRM
   3,  2,  1,  0,  // ECM SPL
};


// ================================================================
//  End of Hardware Configuration
// ================================================================

// NUM_ENCODERS / NUM_POTS 는 위 HARDWARE CONFIGURATION 에서 단계별로 정의됩니다.
#define NUM_MCP_DEVICES   (sizeof(mcpDevices)      / sizeof(mcpDevices[0]))
#define NUM_SWITCHES      (sizeof(switches)        / sizeof(switches[0]))
#define NUM_LEDS          (sizeof(leds)            / sizeof(leds[0]))
#define NUM_ANALOG_ARRAYS (sizeof(analogBtnArrays) / sizeof(analogBtnArrays[0]))


// ================================================================
//  Includes
// ================================================================

#include <Wire.h>
#include <usb_dev.h>

extern volatile uint8_t usb_configuration;


// ================================================================
//  Backlight (PWM dimming)
// ================================================================

static bool backlightState = false;
static uint8_t manualBrightness = 0;
static bool backlightIdleOff = false;

void setBacklight(bool on) {
  analogWrite(BACKLIGHT_PIN, on ? 255 : 0);
  backlightState = on;
}

void setBacklightBrightness(uint8_t brightness) {
  analogWrite(BACKLIGHT_PIN, brightness);
  backlightState = (brightness > 0);
}

// 수동 밝기 조절: UHF TEST + STATUS 동시에 누른 채 UHF VOL 으로 조절
void checkManualBacklight() {
  if (!digitalRead(PIN_UHF_TEST) && !digitalRead(PIN_UHF_STATUS)) {
    int raw = analogRead(PIN_POT_UHFVOL);
    uint8_t brightness = raw >> 2;     // 10-bit → 8-bit
    if (brightness != manualBrightness) {
      manualBrightness = brightness;
      setBacklightBrightness(manualBrightness);
      backlightIdleOff = false;
    }
  }
}


// ================================================================
//  MCP23017 I/O Expander Driver
// ================================================================

#define MCP_IODIRA  0x00
#define MCP_IODIRB  0x01
#define MCP_GPPUA   0x0C
#define MCP_GPPUB   0x0D
#define MCP_GPIOA   0x12
#define MCP_OLATA   0x14
#define MCP_OLATB   0x15

static bool     mcpConnected[NUM_MCP_DEVICES];
static uint16_t mcpPortCache[NUM_MCP_DEVICES];
static uint8_t  mcpOutputA[NUM_MCP_DEVICES];
static uint8_t  mcpOutputB[NUM_MCP_DEVICES];
static bool     mcpOutDirty[NUM_MCP_DEVICES];

void mcpWriteReg(uint8_t addr, uint8_t reg, uint8_t val) {
  MCP_WIRE.beginTransmission(addr);
  MCP_WIRE.write(reg);
  MCP_WIRE.write(val);
  MCP_WIRE.endTransmission();
}

void mcpInit(uint8_t deviceIdx, bool verbose = true) {
  uint8_t addr = mcpDevices[deviceIdx].addr;

  MCP_WIRE.beginTransmission(addr);
  if (MCP_WIRE.endTransmission() != 0) {
    mcpConnected[deviceIdx] = false;
    mcpPortCache[deviceIdx] = 0xFFFF;   // all HIGH = all switches released
    if (verbose)
      Serial.printf("  [MCP@0x%02X] %s - NOT DETECTED\n", addr, mcpDevices[deviceIdx].name);
    return;
  }
  mcpConnected[deviceIdx] = true;

  // Default: input with pull-up. LED pins become outputs.
  uint8_t dirA = 0xFF, dirB = 0xFF;
  uint8_t pullA = 0xFF, pullB = 0xFF;

  for (unsigned int i = 0; i < NUM_LEDS; i++) {
    if (leds[i].mcpIdx == (int8_t)deviceIdx) {
      uint8_t p = leds[i].pin;
      if (p < 8) { dirA &= ~(1 << p);       pullA &= ~(1 << p); }
      else       { dirB &= ~(1 << (p - 8)); pullB &= ~(1 << (p - 8)); }
    }
  }

  mcpWriteReg(addr, MCP_IODIRA, dirA);
  mcpWriteReg(addr, MCP_IODIRB, dirB);
  mcpWriteReg(addr, MCP_GPPUA,  pullA);
  mcpWriteReg(addr, MCP_GPPUB,  pullB);
  mcpWriteReg(addr, MCP_OLATA,  0x00);
  mcpWriteReg(addr, MCP_OLATB,  0x00);

  mcpOutputA[deviceIdx] = 0;
  mcpOutputB[deviceIdx] = 0;
  mcpOutDirty[deviceIdx] = false;
  Serial.printf("  [MCP@0x%02X] %s - OK\n", addr, mcpDevices[deviceIdx].name);
}

// Read both ports into cache. On I2C failure the device is marked
// disconnected and all its switches read as released.
void mcpReadPorts(uint8_t deviceIdx) {
  if (!mcpConnected[deviceIdx]) return;
  uint8_t addr = mcpDevices[deviceIdx].addr;

  MCP_WIRE.beginTransmission(addr);
  MCP_WIRE.write(MCP_GPIOA);
  if (MCP_WIRE.endTransmission() != 0) {
    mcpConnected[deviceIdx] = false;
    mcpPortCache[deviceIdx] = 0xFFFF;
    return;
  }
  if (MCP_WIRE.requestFrom(addr, (uint8_t)2) != 2) {
    mcpConnected[deviceIdx] = false;
    mcpPortCache[deviceIdx] = 0xFFFF;
    return;
  }
  uint8_t a = MCP_WIRE.read();
  uint8_t b = MCP_WIRE.read();
  mcpPortCache[deviceIdx] = a | ((uint16_t)b << 8);
}

bool mcpReadPin(uint8_t deviceIdx, uint8_t pin) {
  return (mcpPortCache[deviceIdx] >> pin) & 1;
}

// Buffered output write — actual I2C happens in mcpFlushOutputs().
void mcpWritePin(uint8_t deviceIdx, uint8_t pin, bool state) {
  if (!mcpConnected[deviceIdx]) return;
  uint8_t before;
  if (pin < 8) {
    before = mcpOutputA[deviceIdx];
    if (state) mcpOutputA[deviceIdx] |=  (1 << pin);
    else       mcpOutputA[deviceIdx] &= ~(1 << pin);
    if (before != mcpOutputA[deviceIdx]) mcpOutDirty[deviceIdx] = true;
  } else {
    uint8_t bit = pin - 8;
    before = mcpOutputB[deviceIdx];
    if (state) mcpOutputB[deviceIdx] |=  (1 << bit);
    else       mcpOutputB[deviceIdx] &= ~(1 << bit);
    if (before != mcpOutputB[deviceIdx]) mcpOutDirty[deviceIdx] = true;
  }
}

// One I2C write per port instead of one per LED.
void mcpFlushOutputs() {
  for (unsigned int d = 0; d < NUM_MCP_DEVICES; d++) {
    if (!mcpConnected[d] || !mcpOutDirty[d]) continue;
    uint8_t addr = mcpDevices[d].addr;
    mcpWriteReg(addr, MCP_OLATA, mcpOutputA[d]);
    mcpWriteReg(addr, MCP_OLATB, mcpOutputB[d]);
    mcpOutDirty[d] = false;
  }
}


// ================================================================
//  74HC595 Shift Register Driver (ECM LEDs)
// ================================================================

void srFlush() {
  digitalWrite(SR_LATCH_PIN, LOW);
  for (int i = SR_NUM_CHIPS - 1; i >= 0; i--) {
    for (int b = 0; b < 8; b++) {
      digitalWrite(SR_DATA_PIN, (srData[i] >> b) & 1);
      delayMicroseconds(10);
      digitalWrite(SR_CLOCK_PIN, HIGH);
      delayMicroseconds(10);
      digitalWrite(SR_CLOCK_PIN, LOW);
    }
  }
  digitalWrite(SR_LATCH_PIN, HIGH);
}

void srWrite(uint8_t idx, bool state) {
  if (idx >= SR_NUM_OUTPUTS) return;
  uint8_t hw   = srMap[idx];
  uint8_t chip = hw / 8;
  uint8_t bit  = hw % 8;
  if (state) srData[chip] |=  (1 << bit);
  else       srData[chip] &= ~(1 << bit);
}

void srClear() {
  memset(srData, 0, sizeof(srData));
  srFlush();
}


// ================================================================
//  LED Control
// ================================================================

// ELEC panel LEDs (MCP or direct). Name kept for BiosHandler compatibility.
void writeElecLed(uint8_t idx, bool state) {
  if (idx >= NUM_LEDS) return;
  if (leds[idx].mcpIdx >= 0) mcpWritePin(leds[idx].mcpIdx, leds[idx].pin, state);
  else                       digitalWrite(leds[idx].pin, state ? HIGH : LOW);
}

void writeEcmLed(uint8_t idx, bool state) { srWrite(idx, state); }

void turnOffAllLeds() {
  for (unsigned int i = 0; i < NUM_LEDS; i++) writeElecLed(i, false);
  mcpFlushOutputs();
  srClear();
}


// ================================================================
//  BIOS Handlers (DCS-BIOS + BMS-BIOS)
// ================================================================

#include "Display/Max7219Display.h"

#include "BiosHandler/DcsBiosParser.h"
#include "BiosHandler/BmsBiosParser.h"


// ================================================================
//  USB Suspend Detection (SOF-based, Teensy 4.x)
// ================================================================

#define USB_SUSPEND_THRESHOLD_MS  50

static uint32_t lastFrameIndex = 0;
static uint32_t lastSOFActiveTime = 0;

bool isUSBSuspended() {
  if (!usb_configuration) return true;

  uint32_t frame = USB1_FRINDEX;
  if (frame != lastFrameIndex) {
    lastFrameIndex = frame;
    lastSOFActiveTime = millis();
    return false;
  }
  return (millis() - lastSOFActiveTime > USB_SUSPEND_THRESHOLD_MS);
}


// ================================================================
//  Protocol Auto-Detection
// ================================================================

enum Protocol { PROTO_UNKNOWN, PROTO_DCSBIOS, PROTO_BMS_BIOS };

static Protocol  currentProto     = PROTO_UNKNOWN;
static uint8_t   syncCount        = 0;
static bool      bmsBiosSync1     = false;
static uint32_t  protoDetectStart = 0;


// ================================================================
//  Button Assignment
// ================================================================

#define NUM_COVERS 3                      // ENG CONT, EPU OFF, EPU ON
#define NUM_COMM_PWR 2                    // COMM1, COMM2 — 채널당 1 (유지형)

static uint8_t switchBtnStart[NUM_SWITCHES];
static uint8_t analogBtnStart[NUM_ANALOG_ARRAYS];
static uint8_t encoderBtnStart[NUM_ENCODERS];
static uint8_t coverBtnStart[NUM_COVERS];      // 커버 자동화 DX — dxOrder[] 가 배정
static uint8_t commPwrBtnStart[NUM_COMM_PWR];  // COMM 전원 DX — dxOrder[] 가 배정
static int     totalButtons = 0;

static uint8_t prevBtnState[128];
static uint32_t lastInputTime = 0;

int switchButtonCount(const SwitchDef& sw) {
  switch (sw.type) {
    case SW_ON_OFF:    return 1;
    case SW_ON_OFF_ON: return 2;
    case SW_ROTARY:    return sw.numPos;
  }
  return 1;
}

// 커버 / COMM 전원은 물리 스위치가 아니라 펌웨어가 합성하는 DX 라
// 이름이 배열에 없습니다. dxOrder[] 와 기동 요약에서 쓰려고 여기 둡니다.
static const char* const coverNames[NUM_COVERS] = {
  "ENG CONT COVER", "EPU OFF COVER", "EPU ON COVER"
};
static const char* const commPwrNames[NUM_COMM_PWR] = {
  "COMM1 PWR", "COMM2 PWR"
};


// ================================================================
//  DX 배정 순서 — dxOrder[]
// ================================================================
//
//  이 표의 **줄 순서**가 그대로 DX 번호 순서입니다. 번호는 적지 않습니다.
//  각 항목이 몇 개를 차지하는지는 그 항목의 타입에서 나옵니다
//  (SW_ON_OFF 1, SW_ON_OFF_ON 2, SW_ROTARY numPos, 엔코더 2(CW/CCW),
//   래더 numButtons, 커버/COMM 전원 각 1). 주석의 xN 이 그 폭입니다.
//
//  idx 는 해당 배열의 인덱스입니다. switches[] / encoders[] /
//  analogBtnArrays[] 의 순서는 배선 정보라 건드리지 않고, DX 순서만
//  여기서 따로 정합니다 — 핀 배치는 그대로 둔 채 번호만 바뀝니다.
//
//  커버 자동화 DX 는 자기가 덮는 토글 **바로 앞**에 둡니다 — 커버가 먼저
//  열리고 스위치가 움직이는 실제 순서와 같습니다.
//
//  ※ 줄을 옮기면 그 뒤 DX 가 전부 밀립니다. 바인딩 파일을 손으로
//    유지하지 말고 다시 생성하십시오. 현재 번호는 기동 시 시리얼
//    요약이 이 순서 그대로 찍어 줍니다.

enum DxKind { DX_SW, DX_LADDER, DX_ENC, DX_COVER, DX_COMMPWR };

struct DxEntry {
  DxKind  kind;
  uint8_t idx;
};

const DxEntry dxOrder[] = {
  // ---- MANUAL PITCH (MPO) — 최전방 인보드 ----
  {DX_SW,       0},   // MPO                  x1

  // ---- UHF — 최전방 아웃보드 ----
  {DX_ENC,      0},   // UHF PRESET           x2
  {DX_SW,       1},   // UHF TEST             x1
  {DX_SW,       2},   // UHF STATUS           x1
  {DX_ENC,      1},   // UHF 100MHz           x2
  {DX_ENC,      2},   // UHF 10MHz            x2
  {DX_ENC,      3},   // UHF 1MHz             x2
  {DX_ENC,      4},   // UHF 0.1MHz           x2
  {DX_ENC,      5},   // UHF 0.025MHz         x2
  {DX_SW,       3},   // UHF FUNC OFF         x1
  {DX_SW,       4},   // UHF FUNC MAIN        x1
  {DX_SW,       5},   // UHF FUNC BOTH        x1
  {DX_SW,       6},   // UHF FUNC ADF         x1
  {DX_SW,       7},   // UHF MODE MNL         x1
  {DX_SW,       8},   // UHF MODE PRE         x1
  {DX_SW,       9},   // UHF MODE GRD         x1
  {DX_SW,      10},   // UHF T-TONE           x1
  {DX_SW,      11},   // UHF SQUELCH          x1

  // ---- ENG & JET START ----
  {DX_SW,      12},   // JFS                  x2
  {DX_COVER,    0},   // ENG CONT COVER       x1
  {DX_SW,      13},   // ENG CONT             x1
  {DX_SW,      14},   // AB RESET/ENG DATA    x2
  {DX_SW,      15},   // MAX POWER            x1

  // ---- AUDIO 1 ----
  {DX_COMMPWR,  0},   // COMM1 PWR            x1
  {DX_COMMPWR,  1},   // COMM2 PWR            x1
  {DX_SW,      16},   // COMM1 OFF            x1
  {DX_SW,      17},   // COMM1 SQL            x1
  {DX_SW,      18},   // COMM1 GD             x1
  {DX_SW,      19},   // COMM2 OFF            x1
  {DX_SW,      20},   // COMM2 SQL            x1
  {DX_SW,      21},   // COMM2 GD             x1

  // ---- AUDIO 2 ----
  {DX_SW,      22},   // HOT MIC/CIPHER       x2

  // ---- ECM ----
  {DX_SW,      23},   // ECM OPR/STBY         x2
  {DX_SW,      24},   // ECM XMIT             x2
  {DX_LADDER,   0},   // ECM Buttons          x8
  {DX_SW,      25},   // ECM RESET            x1
  {DX_SW,      26},   // ECM BIT              x1

  // ---- EPU ----
  {DX_COVER,    1},   // EPU OFF COVER        x1
  {DX_COVER,    2},   // EPU ON COVER         x1
  {DX_SW,      27},   // EPU                  x2

  // ---- ELEC ----
  {DX_SW,      28},   // ELEC MAIN PWR        x2
  {DX_SW,      29},   // ELEC CAUTION RST     x1

  // ---- AVTR ----
  {DX_SW,      30},   // AVTR                 x2
};
#define NUM_DX_ORDER (sizeof(dxOrder) / sizeof(dxOrder[0]))

// 항목을 빠뜨리면 그 컨트롤의 BtnStart 가 0 으로 남아 조용히 DX 0 을
// 누르게 됩니다. 개수는 여기서, 누락/중복은 assignButtons() 에서 잡습니다.
static_assert(NUM_DX_ORDER == NUM_SWITCHES + NUM_ANALOG_ARRAYS + NUM_ENCODERS
                              + NUM_COVERS + NUM_COMM_PWR,
              "dxOrder[] 항목 수가 하드웨어 총 개수와 맞지 않습니다");

uint8_t dxEntryCount(const DxEntry& e) {
  switch (e.kind) {
    case DX_SW:     return switchButtonCount(switches[e.idx]);
    case DX_LADDER: return analogBtnArrays[e.idx].numButtons;
    case DX_ENC:    return 2;                    // CW, CCW
    default:        return 1;                    // DX_COVER, DX_COMMPWR
  }
}

const char* dxEntryName(const DxEntry& e) {
  switch (e.kind) {
    case DX_SW:     return switches[e.idx].name;
    case DX_LADDER: return analogBtnArrays[e.idx].groupName;
    case DX_ENC:    return encoders[e.idx].name;
    case DX_COVER:  return coverNames[e.idx];
    default:        return commPwrNames[e.idx];
  }
}

// assignButtons() 가 배정한 이 항목의 첫 DX 번호
uint8_t dxEntryStart(const DxEntry& e) {
  switch (e.kind) {
    case DX_SW:      return switchBtnStart[e.idx];
    case DX_LADDER:  return analogBtnStart[e.idx];
    case DX_ENC:     return encoderBtnStart[e.idx];
    case DX_COVER:   return coverBtnStart[e.idx];
    default:         return commPwrBtnStart[e.idx];
  }
}

void assignButtons() {
  int btn = 1;

  memset(switchBtnStart,  0, sizeof(switchBtnStart));
  memset(analogBtnStart,  0, sizeof(analogBtnStart));
  memset(encoderBtnStart, 0, sizeof(encoderBtnStart));
  memset(coverBtnStart,   0, sizeof(coverBtnStart));
  memset(commPwrBtnStart, 0, sizeof(commPwrBtnStart));

  for (unsigned int i = 0; i < NUM_DX_ORDER; i++) {
    const DxEntry& e = dxOrder[i];
    switch (e.kind) {
      case DX_SW:      switchBtnStart[e.idx]  = btn; break;
      case DX_LADDER:  analogBtnStart[e.idx]  = btn; break;
      case DX_ENC:     encoderBtnStart[e.idx] = btn; break;
      case DX_COVER:   coverBtnStart[e.idx]   = btn; break;
      case DX_COMMPWR: commPwrBtnStart[e.idx] = btn; break;
    }
    btn += dxEntryCount(e);
  }

  totalButtons = btn - 1;
  if (totalButtons > 128)
    Serial.printf("ERROR: %d buttons assigned, max is 128\n", totalButtons);

  // 개수가 맞아도 한 항목이 두 번 들어가면 다른 하나가 0 으로 남습니다
  for (unsigned int i = 0; i < NUM_SWITCHES; i++)
    if (!switchBtnStart[i])
      Serial.printf("ERROR: switches[%u] (%s) not in dxOrder[]\n", i, switches[i].name);
  for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++)
    if (!analogBtnStart[i])
      Serial.printf("ERROR: ladder %s not in dxOrder[]\n", analogBtnArrays[i].groupName);
  for (unsigned int i = 0; i < NUM_ENCODERS; i++)
    if (!encoderBtnStart[i])
      Serial.printf("ERROR: encoder %s not in dxOrder[]\n", encoders[i].name);
  for (unsigned int i = 0; i < NUM_COVERS; i++)
    if (!coverBtnStart[i])
      Serial.printf("ERROR: cover %s not in dxOrder[]\n", coverNames[i]);
  for (unsigned int i = 0; i < NUM_COMM_PWR; i++)
    if (!commPwrBtnStart[i])
      Serial.printf("ERROR: %s not in dxOrder[]\n", commPwrNames[i]);
}


// ================================================================
//  Cover Automation
// ================================================================
//
//  ENG CONT, EPU 스위치 커버를 자동 제어합니다.
//  ON 시: 커버 먼저 열림 → COVER_DELAY_TICKS 후 스위치 ON
//  OFF 시: 스위치 먼저 OFF → COVER_DELAY_TICKS 후 커버 닫힘
//
//  이 DX 는 심과 무관하게 항상 나갑니다. 다만 커버를 따로 여닫는
//  개념이 있는 것은 DCS 쪽이라, 실제로 바인딩할 대상은 DCS 에만
//  있습니다. BMS 는 스위치를 올리면 커버가 알아서 열려 비워 두면 됩니다.
//
//  DX 번호는 dxOrder[] 가 정합니다. 세 커버가 연속일 필요는 없습니다.

#define SW_IDX_ENG_CONT  13    // switches[] 인덱스 — 배열 순서 변경 시 함께 수정
#define SW_IDX_EPU       27

#define COVER_DELAY_TICKS 10  // 100ms @ 100Hz — 커버/스위치 간 시차

struct CoverDef {
  uint8_t switchIdx;
  uint8_t btnOffset;   // ON_OFF_ON: 0=pin1, 1=pin2
};
static const CoverDef coverDefs[NUM_COVERS] = {
  {SW_IDX_ENG_CONT, 0},   // ENG CONT COVER
  {SW_IDX_EPU,      0},   // EPU OFF COVER
  {SW_IDX_EPU,      1},   // EPU ON COVER
};

struct CoverRuntime {
  uint8_t openTicks;    // >0: 커버 열림 대기, 스위치 억제
  uint8_t closeTicks;   // >0: 커버 닫힘 대기, 커버 유지
  uint8_t lastSwState;
};
static CoverRuntime coverRt[NUM_COVERS];

void processCovers() {
  for (uint8_t i = 0; i < NUM_COVERS; i++) {
    uint8_t swBtn   = switchBtnStart[coverDefs[i].switchIdx] + coverDefs[i].btnOffset;
    uint8_t swState = prevBtnState[swBtn];
    CoverRuntime& rt = coverRt[i];

    // 전환 감지
    if (swState && !rt.lastSwState)  rt.openTicks  = COVER_DELAY_TICKS;
    if (!swState && rt.lastSwState)  rt.closeTicks = COVER_DELAY_TICKS;
    rt.lastSwState = swState;

    if (rt.openTicks > 0) {
      // Opening: 커버 ON, 스위치 억제 (DCS가 커버 열릴 시간 확보)
      Joystick.button(coverBtnStart[i], 1);
      Joystick.button(swBtn, 0);
      rt.openTicks--;
    } else if (rt.closeTicks > 0) {
      // Closing: 스위치 OFF (이미 processSwitches에서 처리), 커버는 아직 ON 유지
      Joystick.button(coverBtnStart[i], 1);
      rt.closeTicks--;
    } else {
      // 정상: 커버 = 스위치 상태 미러링
      Joystick.button(coverBtnStart[i], swState);
    }
  }
}


// ================================================================
//  COMM1/COMM2 Power (pot threshold → 유지형 DX)
// ================================================================
//
//  COMM1, COMM2 볼륨 노브 끝에 전원 스위치가 있어,
//  pot ADC 값이 threshold 미만이면 OFF, 이상이면 ON.
//  채널당 DX 하나를, 노브가 켜져 있는 **동안 계속** 누른 상태로 둡니다.
//
//  펄스가 아니라 유지형인 이유: 펄스는 전환 순간에만 나가므로, 심을
//  나중에 띄우거나 재접속하면 이미 올라가 있는 노브를 심이 알 방법이
//  없어 상태가 어긋납니다. 유지형이면 심이 언제 보든 현재 상태입니다.
//  BMS 자신의 기본 키 파일도 2단 스위치를 같은 DX 두 줄(press/release)로
//  바인딩합니다 — 예: SimFuelDoorOpen/Close.
//
//  이 DX 는 심과 무관하게 항상 나갑니다. 볼륨 노브 끝에 전원을 둔
//  것은 BMS 의 모델링을 따른 것입니다.
//
//  DX 번호는 dxOrder[] 가 정합니다. 둘이 연속일 필요는 없습니다.

#define COMM_PWR_THRESHOLD  5     // ADC threshold (10-bit, 0~1023)

static bool commPwrOn[2];                    // [0]=COMM1, [1]=COMM2
static const uint8_t commPotIdx[] = {1, 2};  // pots[] index: COMM1, COMM2

void processCommPower() {
  for (int ch = 0; ch < 2; ch++) {
    int raw = 0;
    for (int s = 0; s < 4; s++) raw += analogRead(pots[commPotIdx[ch]].pin);
    raw /= 4;

    bool isOn = (raw >= COMM_PWR_THRESHOLD);
    if (isOn != commPwrOn[ch]) {
      commPwrOn[ch] = isOn;
      lastInputTime = millis();
    }
    Joystick.button(commPwrBtnStart[ch], isOn ? 1 : 0);
  }
}


// ================================================================
//  Joystick Axis Helper
// ================================================================

void setJoystickAxis(JoyAxis axis, int rawValue) {
  unsigned int value = rawValue * 64;   // 10-bit ADC -> 16-bit axis
  switch (axis) {
    case AXIS_X:  Joystick.X(value);       break;
    case AXIS_Y:  Joystick.Y(value);       break;
    case AXIS_Z:  Joystick.Z(value);       break;
    case AXIS_Xr: Joystick.Xrotate(value); break;
    case AXIS_Yr: Joystick.Yrotate(value); break;
    case AXIS_Zr: Joystick.Zrotate(value); break;
    default:      // AXIS_S1..S10 → slider(1..10)
      Joystick.slider(axis - AXIS_S1 + 1, value);
      break;
  }
}


// ================================================================
//  Rotary Encoder — 1kHz ISR quadrature decode
// ================================================================
//
//  Encoders cannot live on the MCP23017: I2C polling would drop pulses.
//  A 1kHz timer poll handles ~250 detents/sec, far beyond hand speed.

static const int8_t QUAD_TABLE[16] = {
   0, -1, +1,  0,
  +1,  0,  0, -1,
  -1,  0,  0, +1,
   0, +1, -1,  0
};

static IntervalTimer   encTimer;
static uint8_t         encPrevState[NUM_ENCODERS];
static int8_t          encSubCount[NUM_ENCODERS];   // quarter-steps within a detent
static volatile int16_t encDelta[NUM_ENCODERS];     // detents pending, ISR -> loop

struct EncRuntime {
  int16_t pending;      // signed DX pulses still to emit
  uint8_t holdTicks;    // remaining ticks the current pulse stays pressed
};
static EncRuntime encRt[NUM_ENCODERS];

void encoderPollISR() {
  for (unsigned int i = 0; i < NUM_ENCODERS; i++) {
    uint8_t curr = (digitalRead(encoders[i].pinA) << 1) | digitalRead(encoders[i].pinB);
    if (curr == encPrevState[i]) continue;

    int8_t d = QUAD_TABLE[(encPrevState[i] << 2) | curr];
    encPrevState[i] = curr;
    if (d == 0) continue;           // invalid transition (bounce) — ignore

    encSubCount[i] += d;
    if (encSubCount[i] >= 4)       { encDelta[i]++; encSubCount[i] = 0; }
    else if (encSubCount[i] <= -4) { encDelta[i]--; encSubCount[i] = 0; }
  }
}

void processEncoders() {
  for (unsigned int i = 0; i < NUM_ENCODERS; i++) {
    EncRuntime& rt = encRt[i];

    // --- Drain ISR delta ---
    noInterrupts();
    int16_t d = encDelta[i];
    encDelta[i] = 0;
    interrupts();

    // --- Queue detents as DX pulses (range wrap/clamp is BMS's job) ---
    rt.pending += d;
    if (rt.pending >  ENC_PENDING_MAX) rt.pending =  ENC_PENDING_MAX;
    if (rt.pending < -ENC_PENDING_MAX) rt.pending = -ENC_PENDING_MAX;

    // --- Emit one DX pulse per drain cycle ---
    uint8_t btnCCW = encoderBtnStart[i];
    uint8_t btnCW  = btnCCW + 1;

    if (rt.holdTicks > 0) {
      if (--rt.holdTicks == 0) {    // release, leaving a 1-tick gap
        Joystick.button(btnCW,  0);
        Joystick.button(btnCCW, 0);
      }
    } else if (rt.pending != 0) {
      int8_t dir = (rt.pending > 0) ? 1 : -1;
      rt.pending -= dir;
      Joystick.button(dir > 0 ? btnCW : btnCCW, 1);
      rt.holdTicks = ENC_PULSE_TICKS;
      lastInputTime = millis();
    }
  }
}



// ================================================================
//  Switch Processing
// ================================================================

inline int readSwPin(const SwitchDef& sw, uint8_t pin) {
  return (sw.mcpIdx >= 0) ? mcpReadPin(sw.mcpIdx, pin) : digitalRead(pin);
}

void processSwitches() {
  // mcpReadPorts()는 loop() 상단에서 호출 완료
  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    const SwitchDef& sw = switches[i];
    int btn = switchBtnStart[i];

    switch (sw.type) {
      case SW_ON_OFF: {
        int state = !readSwPin(sw, sw.pin1);          // active-low
        if (prevBtnState[btn] != state) {
          //if (ALLOW_DEBUG) Serial.printf("[SW] btn %d %s = %s\n", btn, sw.name, state ? "ON" : "OFF");
          prevBtnState[btn] = state;
          lastInputTime = millis();
        }
        Joystick.button(btn, state);
        break;
      }

      case SW_ON_OFF_ON: {
        int s1 = !readSwPin(sw, sw.pin1);
        int s2 = !readSwPin(sw, sw.pin2);
        if (prevBtnState[btn] != s1 || prevBtnState[btn + 1] != s2) {
          //if (ALLOW_DEBUG) Serial.printf("[SW] btn %d~%d %s = %d/%d\n", btn, btn + 1, sw.name, s1, s2);
          prevBtnState[btn]     = s1;
          prevBtnState[btn + 1] = s2;
          lastInputTime = millis();
        }
        Joystick.button(btn,     s1);
        Joystick.button(btn + 1, s2);
        break;
      }

      case SW_ROTARY: {
        for (uint8_t p = 0; p < sw.numPos; p++) {
          int state = !readSwPin(sw, sw.pin1 + p);
          if (prevBtnState[btn + p] != state) {
            //if (ALLOW_DEBUG && state) Serial.printf("[SW] %s = pos %d\n", sw.name, p);
            prevBtnState[btn + p] = state;
            lastInputTime = millis();
          }
          Joystick.button(btn + p, state);
        }
        break;
      }
    }
  }
}


// ================================================================
//  Analog Button Array (resistor ladder, nearest-value match)
// ================================================================

void processAnalogButtons() {
  for (unsigned int a = 0; a < NUM_ANALOG_ARRAYS; a++) {
    const AnalogBtnArrayDef& arr = analogBtnArrays[a];
    int btn = analogBtnStart[a];

    int raw = 0;
    for (int s = 0; s < 8; s++) raw += analogRead(arr.pin);
    raw /= 8;                       // 8x oversample -> ~+/-2 counts of noise

    int best = -1;
    int bestDist = 32767;
    const int* vals = arr.values;
    for (int b = 0; b < arr.numButtons; b++) {
      int dist = abs(raw - vals[b]);
      if (dist < bestDist) { bestDist = dist; best = b; }
    }
    // Reject: below last value minus half the gap to its neighbor
    if (best >= 0 && arr.numButtons >= 2) {
      int lastGap = vals[arr.numButtons - 2] - vals[arr.numButtons - 1];
      int lowerBound = vals[arr.numButtons - 1] - lastGap / 2;
      if (raw < lowerBound) best = -1;
    }
    for (int b = 0; b < arr.numButtons; b++) {
      int state = (b == best);
      if (prevBtnState[btn + b] != state) {
        prevBtnState[btn + b] = state;
        lastInputTime = millis();
      }
      Joystick.button(btn + b, state);
    }

    if (ALLOW_DEBUG) {
      static int lastBest = -2;
      if (best != lastBest) {
        lastBest = best;
        if (best >= 0)
          Serial.printf("[Ladder] ECM btn%d (raw=%d ref=%d)\n", best, raw, vals[best]);
        else
          Serial.printf("[Ladder] ECM NONE (raw=%d)\n", raw);
      }
    }
  }
}


// ================================================================
//  Pot Processing
// ================================================================

void processPots() {
  for (unsigned int i = 0; i < NUM_POTS; i++) {
    int raw = 0;
    for (int s = 0; s < 4; s++) raw += analogRead(pots[i].pin);
    raw /= 4;
    setJoystickAxis(pots[i].axis, raw);
  }
}


// ================================================================
//  Welcome Ceremony
// ================================================================
//
//  피크 전류 설계
//    Teensy 4.1 의 3.3V 레귤레이터는 외부 부하에 약 250mA 까지만 내줍니다.
//    ECM LED 는 직렬저항 220옴, 74HC595 를 3.3V 로 구동 — 595 의 출력 내부저항
//    (3.3V 에서 대략 60~100옴)까지 넣으면 LED 당 (3.3-2.0)/(220+70) 약 4.5mA 입니다.
//    전부 켜면 ECM 32 + 패널 12 = 44 개, 약 200mA 로 예산의 80% 를 씁니다.
//    세리머니까지 그 피크를 만들 이유가 없으므로 ECM 은 항상 "한 열(8개)" 단위로만 켭니다.
//    열(S/A/F/T)은 8개 그룹에 흩어져 있어 74HC595 4장에 칩당 2개씩 고르게 분산됩니다
//    (칩당 약 9mA — 74HC595 의 패키지 한계 70mA 대비 충분).
//    최대 동시 점등은 패널 12 + ECM 8 = 20 개, 약 90mA 입니다.

// ECM 열 단위 스윕. 한 번에 한 열(8개)만 켜고 이전 열은 끕니다.
// 원래 동작과 같이 마지막 열은 켜진 채로 남습니다 (turnOffAllLeds 로 정리).
static void ecmSweep(uint16_t holdMs) {
  for (int col = 0; col < 4; col++) {
    for (int i = 0; i < SR_NUM_OUTPUTS; i++) srWrite(i, (i % 4) == col);
    srFlush();
    delay(holdMs);
  }
}

void welcomeCeremony() {
  setBacklight(true);             // ceremony 동안 백라이트 ON
  displayOn(true);
  displayLampTest(true);        // 전 세그먼트 점등

  // ECM sweep: column by column (S -> A -> F -> T), previous column off
  ecmSweep(200);

  // ELEC LEDs in sequence
  for (unsigned int i = 0; i < NUM_LEDS; i++) {
    writeElecLed(i, true);
    mcpFlushOutputs();
    delay(40);
  }
  delay(300);

  // 피날레 — 패널 LED 를 두 번 점멸시키면서 ECM 을 열 단위로 훑습니다.
  // (예전에는 44개를 동시에 켰습니다 — 3.3V 예산 초과)
  for (int b = 0; b < 2; b++) {
    turnOffAllLeds();
    delay(120);
    for (unsigned int i = 0; i < NUM_LEDS; i++) writeElecLed(i, true);
    mcpFlushOutputs();
    ecmSweep(60);
  }

  turnOffAllLeds();
  displayLampTest(false);
  displayOn(false);             // 번인 방지: 브릿지 수신 전까지 꺼둠
  setBacklight(false);            // ceremony 끝 → 백라이트 OFF (bridge/수동으로 켜짐)
}


// ================================================================
//  Protocol Detection & Serial Routing
// ================================================================

void resetProtocol() {
  currentProto     = PROTO_UNKNOWN;
  syncCount        = 0;
  bmsBiosSync1     = false;
  protoDetectStart = 0;
  dcsBiosReset();
  bmsBiosReset();
  turnOffAllLeds();
  manualBrightness = 0;
  setBacklight(false);    // bridge offline → backlight off (수동 조절로 복원 가능)
  displayOn(false);         // 번인 방지: 브릿지 오프라인 시 디스플레이 OFF
  //if (ALLOW_DEBUG) Serial.println("[Proto] Reset to UNKNOWN");
}

// ================================================================
//  Host Request — DX 맵 덤프
// ================================================================
//
//  브리지가 붙지 않은 상태(PROTO_UNKNOWN)에서 "?DX" 한 줄을 받으면
//  현재 DX 배정을 기계가 읽을 수 있는 형태로 내보냅니다.
//  tools/gen_bms_keyfile.py 가 이걸 읽어 BMS 키 파일을 만듭니다 —
//  소스가 없는 PC(심 PC)에서도 보드만 꽂혀 있으면 됩니다.
//
//  요청에만 응답하는 이유: Teensy USB CDC 는 읽는 호스트가 없으면
//  출력을 버리므로, 기동 시 찍어 두면 대개 아무도 못 받습니다.
//
//  PROTO_UNKNOWN 에서만 받는 이유: BIOS 프레임이 흐르는 중에
//  ASCII 를 섞으면 프레임 해석을 망칩니다. Windows 는 COM 포트를
//  한 프로세스만 열 수 있으므로, 어차피 브리지를 끄고 써야 합니다.
//
//  출력 형식 (각 줄 '#DX' 로 시작):
//    #DX BEGIN device=CONSOLE pid=0x048E entries=43 total=64
//    #DX <첫 DX 번호> <차지하는 개수> <컨트롤 이름>
//    #DX END

#define DX_DEVICE_NAME "CONSOLE"

static char    reqBuf[16];
static uint8_t reqLen = 0;

void dumpDxMap() {
  Serial.printf("#DX BEGIN device=%s pid=0x%04X entries=%u total=%d\n",
                DX_DEVICE_NAME, PRODUCT_ID, (unsigned)NUM_DX_ORDER, totalButtons);
  for (unsigned int i = 0; i < NUM_DX_ORDER; i++) {
    const DxEntry& e = dxOrder[i];
    Serial.printf("#DX %u %u %s\n",
                  (unsigned)dxEntryStart(e), (unsigned)dxEntryCount(e), dxEntryName(e));
  }
  Serial.println("#DX END");
}

void feedHostRequest(uint8_t b) {
  if (b == '\n' || b == '\r') {
    reqBuf[reqLen] = '\0';
    if (reqLen && strcmp(reqBuf, "?DX") == 0) dumpDxMap();
    reqLen = 0;
  } else if (b >= 0x20 && b < 0x7F && reqLen < sizeof(reqBuf) - 1) {
    reqBuf[reqLen++] = (char)b;
  }
}


bool detectAndRouteSerial() {
  bool received = false;

  while (Serial.available()) {
    int ch = Serial.read();
    if (ch < 0) break;
    received = true;

    switch (currentProto) {
      case PROTO_UNKNOWN: {
        if (protoDetectStart == 0) protoDetectStart = millis();

        uint8_t b = (uint8_t)ch;
        if (b == 0x55) {
          syncCount++;
          bmsBiosSync1 = false;
          if (syncCount >= 4) {
            currentProto = PROTO_DCSBIOS;
            syncCount = 0;
            turnOffAllLeds();
            //if (ALLOW_DEBUG) Serial.println("[Proto] Detected DCS-BIOS");
            dcsBiosReset();
            dcsBiosState = DCS_ADDR_LOW;
          }
        } else if (b == 0xAA) {
          syncCount = 0;
          bmsBiosSync1 = true;
        } else if (b == 0xBB && bmsBiosSync1) {
          currentProto = PROTO_BMS_BIOS;
          bmsBiosSync1 = false;
          turnOffAllLeds();
          //if (ALLOW_DEBUG) Serial.println("[Proto] Detected BMS-BIOS");
          bmsBiosReset();
          bbBufIdx = 0;
          bbState  = BB_PAYLOAD;
        } else {
          syncCount = 0;
          bmsBiosSync1 = false;
          feedHostRequest(b);   // ASCII 요청 — 브리지가 안 붙은 동안에만
        }
        break;
      }

      case PROTO_DCSBIOS:  processDcsBiosByte((uint8_t)ch); break;
      case PROTO_BMS_BIOS: processBmsBiosByte((uint8_t)ch); break;
    }
  }

  return received;
}


// ================================================================
//  Setup
// ================================================================

void setup() {
  Serial.begin(BAUDRATE);
  Joystick.useManualSend(true);
  Joystick.hat(1, 360);  // 360 = 중립 (val=15). -1은 NE로 인식됨
  Joystick.hat(2, 360);
  Joystick.hat(3, 360);
  Joystick.hat(4, 360);

  // --- Backlight PWM ---
  analogWriteFrequency(BACKLIGHT_PIN, 1000);  // 1kHz PWM
  setBacklight(false);  // 시작 시 꺼짐 — bridge 또는 수동 조절로만 켜짐
  lastInputTime = millis();

  // --- Direct switch pins ---
  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    if (switches[i].mcpIdx >= 0) continue;
    pinMode(switches[i].pin1, INPUT_PULLUP);
    if (switches[i].type == SW_ON_OFF_ON) pinMode(switches[i].pin2, INPUT_PULLUP);
    if (switches[i].type == SW_ROTARY)
      for (uint8_t p = 1; p < switches[i].numPos; p++)
        pinMode(switches[i].pin1 + p, INPUT_PULLUP);
  }

  // --- Encoder pins ---
  for (unsigned int i = 0; i < NUM_ENCODERS; i++) {
    pinMode(encoders[i].pinA, INPUT_PULLUP);
    pinMode(encoders[i].pinB, INPUT_PULLUP);
    encPrevState[i] = (digitalRead(encoders[i].pinA) << 1) | digitalRead(encoders[i].pinB);
    encSubCount[i]  = 0;
    encDelta[i]     = 0;
    encRt[i].pending    = 0;
    encRt[i].holdTicks  = 0;
  }
  encTimer.begin(encoderPollISR, 1000);   // 1kHz

  // --- Analog pins (flush ADC after mode change) ---
  for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++) {
    pinMode(analogBtnArrays[i].pin, INPUT);
    for (int d = 0; d < 16; d++) analogRead(analogBtnArrays[i].pin);
  }
  for (unsigned int i = 0; i < NUM_POTS; i++) {
    pinMode(pots[i].pin, INPUT);
    for (int d = 0; d < 8; d++) analogRead(pots[i].pin);
  }

  // --- Direct LED pins (if any) ---
  for (unsigned int i = 0; i < NUM_LEDS; i++)
    if (leds[i].mcpIdx < 0) pinMode(leds[i].pin, OUTPUT);

  // --- UHF 7세그 디스플레이 (MAX7219) ---
  displayBegin();
  displayOn(false);         // 번인 방지: 브릿지 연결 전까지 꺼둠

  // --- 74HC595 ---
  pinMode(SR_DATA_PIN,  OUTPUT);
  pinMode(SR_CLOCK_PIN, OUTPUT);
  pinMode(SR_LATCH_PIN, OUTPUT);
  srClear();

  // --- MCP23017 ---
  MCP_WIRE.begin();
  MCP_WIRE.setClock(MCP_I2C_CLOCK);
  for (unsigned int i = 0; i < NUM_MCP_DEVICES; i++) mcpInit(i);

  assignButtons();
  memset(prevBtnState, 0, sizeof(prevBtnState));

  // COMM power: read initial pot state to avoid false trigger at startup
  for (int ch = 0; ch < 2; ch++) {
    int raw = 0;
    for (int s = 0; s < 4; s++) raw += analogRead(pots[commPotIdx[ch]].pin);
    commPwrOn[ch] = (raw / 4 >= COMM_PWR_THRESHOLD);
  }

  // --- Startup summary ---
  Serial.println("=========================");
  Serial.println(" F16 LEFT CONSOLE");
  Serial.println(" Teensy 4.1");
  Serial.println(" I2C: Wire2  SCL2=24 SDA2=25");
  Serial.println("=========================");
  for (int p = 0; p < PNL_COUNT; p++) {
    int nSw = 0, nEnc = 0, nPot = 0, nLed = 0, nAna = 0;
    for (unsigned int i = 0; i < NUM_SWITCHES;      i++) if (switches[i].panel        == p) nSw++;
    for (unsigned int i = 0; i < NUM_ENCODERS;      i++) if (encoders[i].panel        == p) nEnc++;
    for (unsigned int i = 0; i < NUM_POTS;          i++) if (pots[i].panel            == p) nPot++;
    for (unsigned int i = 0; i < NUM_LEDS;          i++) if (leds[i].panel            == p) nLed++;
    for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++) if (analogBtnArrays[i].panel == p) nAna++;
    if (nSw + nEnc + nPot + nLed + nAna == 0) continue;
    Serial.printf("  [%s] sw:%d enc:%d pot:%d led:%d ladder:%d\n",
                  panelNames[p], nSw, nEnc, nPot, nLed, nAna);
  }
  Serial.printf("  Total buttons: %d\n", totalButtons);
  Serial.println("=========================");

  // dxOrder[] 순서 그대로 = 실제 DX 순서. 커버·COMM 전원까지 전부 나옵니다.
  for (unsigned int i = 0; i < NUM_DX_ORDER; i++) {
    const DxEntry& e = dxOrder[i];
    uint8_t cnt = dxEntryCount(e);
    uint8_t dx  = dxEntryStart(e);
    const char* kindStr;
    switch (e.kind) {
      case DX_SW:      kindStr = (switches[e.idx].mcpIdx >= 0) ? "MCP" : "DIR"; break;
      case DX_LADDER:  kindStr = "ladder";     break;
      case DX_ENC:     kindStr = "enc CW/CCW"; break;
      case DX_COVER:   kindStr = "cover auto"; break;
      default:         kindStr = "pot hold";   break;
    }
    if (cnt == 1) Serial.printf("  btn %-3d     : %-20s [%s]\n", dx, dxEntryName(e), kindStr);
    else          Serial.printf("  btn %-3d~%-3d : %-20s [%s]\n", dx, dx + cnt - 1,
                                dxEntryName(e), kindStr);
  }
  Serial.println("=========================");

  welcomeCeremony();
}


// ================================================================
//  Main Loop
// ================================================================

void loop() {
  static bool ledsOff = false;

  if (isUSBSuspended()) {
    turnOffAllLeds();
    displayOn(false);
    if (!backlightIdleOff) {
      setBacklight(false);
      backlightIdleOff = true;
    }
    ledsOff = true;
    asm("wfi");
    return;
  }

  // --- MCP hotplug: reconnect check every 500ms ---
  {
    static uint32_t lastMcpCheck = 0;
    if (millis() - lastMcpCheck > 500) {
      lastMcpCheck = millis();
      for (unsigned int d = 0; d < NUM_MCP_DEVICES; d++) {
        if (!mcpConnected[d]) {
          mcpInit(d, false);
          if (mcpConnected[d])
            Serial.printf("  [MCP@0x%02X] %s - RECONNECTED\n",
                          mcpDevices[d].addr, mcpDevices[d].name);
        }
      }
    }
  }

  // --- Inputs ---
  uint8_t prevSnapshot[128];
  if (ledsOff) memcpy(prevSnapshot, prevBtnState, sizeof(prevSnapshot));

  for (unsigned int d = 0; d < NUM_MCP_DEVICES; d++) mcpReadPorts(d);
  processSwitches();
  processCovers();    // 커버 자동화: 스위치보다 커버가 먼저 열리고, 나중에 닫힘
  processAnalogButtons();
  processPots();
  processCommPower();
  processEncoders();
  Joystick.send_now();

  // Wake on input while LEDs are off
  if (ledsOff && memcmp(prevSnapshot, prevBtnState, sizeof(prevSnapshot)) != 0) {
    ledsOff = false;
    backlightIdleOff = false;
    welcomeCeremony();
  }

  // --- Serial / LED sync ---
  static int  heartbeat  = 0;
  static bool wasOffline = false;
  const int timeoutTicks = (1000 / LOOP_DELAY_MS) * SERIAL_TIMEOUT;

  if (currentProto == PROTO_DCSBIOS) dcsBiosCheckTimeout();

  if (detectAndRouteSerial()) heartbeat = 0;

  if (heartbeat >= timeoutTicks) {
    if (currentProto != PROTO_UNKNOWN) resetProtocol();
    wasOffline = true;

    // Offline 수동 밝기 조절 (UHF STATUS + UHF VOL)
    checkManualBacklight();

    // Backlight idle auto-off (offline only)
    if (!backlightIdleOff && (millis() - lastInputTime > IDLE_TIMEOUT_MS)) {
      setBacklight(false);
      backlightIdleOff = true;
      ledsOff = true;
    }
  }

  // Bridge online: offline -> online transition
  if (heartbeat < timeoutTicks && wasOffline) {
    wasOffline = false;
    ledsOff = false;
    backlightIdleOff = false;
    welcomeCeremony();
  }

  ++heartbeat;
  if (heartbeat > timeoutTicks) heartbeat = timeoutTicks;

  // --- Flush outputs ---
  mcpFlushOutputs();
  srFlush();

  delay(LOOP_DELAY_MS);
}
