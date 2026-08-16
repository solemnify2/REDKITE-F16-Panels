// ================================================================
//  REDKITE F16 LEFT CONSOLE — USB Joystick
// ================================================================
//
//  Two build stages share this sketch. Set BOARD_REV below.
//
//  ── STAGE_T40 : Teensy 4.0, 임시 구성 ────────────────────────────
//     Panels : ECM / ELEC / AVTR / EPU / ENGINE START / MPO / AUDIO 1-2 / UHF(엔코더 제외)
//     I2C    : Wire1 (SDA1=17, SCL1=16) ← 헤더 핀. 4.0의 Wire2(24/25)는
//                                          하단 SMT 패드라 납땜이 어려움
//     Buttons: 41,  축 7
//     사용 핀: 19 / 24 (헤더),  여유 5
//     백라이트: pin 13 — 온보드 LED가 상태 표시등이 됨
//
//  ── STAGE_T41 : Teensy 4.1, 최종 구성 ────────────────────────────
//     Panels : + UHF 엔코더 6개 (나머지는 T40과 동일)
//     I2C    : Wire2 (SDA2=25, SCL2=24)
//     Buttons: 53,  축 7,  엔코더 6
//     사용 핀: 31 / 42 (헤더),  여유 11
//
//  버튼 1~41 과 축 7개가 양쪽 단계에서 완전히 동일합니다.
//  확장 시 추가되는 것은 엔코더 6개(버튼 42~53)뿐이라
//  **BMS 재바인딩이 전혀 필요 없습니다.**
//
//  USB Type: Serial + Keyboard + Mouse + Joystick
//  PID:      0x048E, JOYSTICK_SIZE 64 (usb_desc.h) — 양쪽 단계 공통
//
//  Hardware is data-driven. To add/remove hardware, edit the
//  HARDWARE CONFIGURATION section only. Joystick button numbers
//  are auto-assigned at runtime.
//
//  공통 확장 하드웨어:
//    MCP23017 x3 @ 100kHz
//      0x20  UHF switches + AUDIO1 COMM 1/2 모드   [UHF 패널 실장]
//      0x21  ELEC switches + EPU + ELEC LED 8 (GPB) + EPU LED 3 (GPA5~7)
//      0x22  ECM switches + AVTR
//    74HC595 x4 — ECM 32 LEDs (direct, high-speed shift)
//    Resistor ladder — ECM 8 buttons (direct, analog)
// ================================================================


// ================================================================
//  >>> BOARD REVISION — 확장 단계 선택 <<<
// ================================================================

#define STAGE_T40   0     // Teensy 4.0 — 엔코더를 제외한 전 패널
#define STAGE_T41   1     // Teensy 4.1 — 전 패널 + UHF 엔코더 6

#define BOARD_REV   STAGE_T40      // <<<< 확장 시 STAGE_T41 로 변경

#if BOARD_REV != STAGE_T40 && BOARD_REV != STAGE_T41
  #error "BOARD_REV must be STAGE_T40 or STAGE_T41"
#endif


// ================================================================
//  Build Checks
// ================================================================

// 양쪽 단계 모두 64를 씁니다. T40은 41버튼이라 12(32버튼)로는 부족하고,
// 64로 통일하면 LEFT_AUX_MISC 와 usb_desc.h 를 공유할 수 있고
// 4.1 확장 시 헤더를 다시 고칠 일도 없습니다.
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

// BACKLIGHT_PIN 은 단계별 핀 배정 블록에서 정의합니다 (양 단계 모두 13).
// MOSFET gate: HIGH = backlight ON (ON/OFF only, no dimming)
#define IDLE_TIMEOUT_MS   (1000UL * 60 * 30)   // offline idle -> backlight auto-off (30min)

#if BOARD_REV == STAGE_T41
  #define LOOP_DELAY_MS   10        // 100Hz — encoder pulse throughput
  #define MCP_WIRE        Wire2     // SCL2 = pin 24, SDA2 = pin 25
#else
  #define LOOP_DELAY_MS   20        // 50Hz — 엔코더가 없어 100Hz까지 필요 없음
  // Wire1 을 쓰면 케이블 I1(16/17)이 C6(10~12, 14) 바로 옆에 붙어
  // 커넥터를 기판 하단 한 곳에 모을 수 있습니다.
  #define MCP_WIRE        Wire1     // SDA1 = pin 17, SCL1 = pin 16  (헤더 핀)
#endif

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
//  T40 는 ADC가 A0~A9 (핀 14~23) 10채널뿐입니다. 여기에 I2C 2 + 래더 1 +
//  AUDIO 포트 6 + UHF VOL 1 = 10채널이 전부 들어가므로, 74HC595 제어 3선을
//  ADC가 아닌 핀(10~12)으로 내려야 합니다. T41 은 ADC가 18채널이라
//  SR 3선이 ADC 핀(14~16)을 차지해도 여유가 있습니다.
//
//  ※ 확장 시 SR 3선과 ENGINE/MPO 4선의 Teensy 쪽 핀이 바뀝니다.
//    패널·케이블은 그대로이고 메인보드 커넥터 배선만 달라지는데,
//    4.1 용 메인보드는 어차피 새로 제작하므로 실질 비용은 없습니다.

#if BOARD_REV == STAGE_T41
  #define HAS_ENCODERS      1

  // T40과 동일하게 13 — 출력이면 온보드 LED 공유가 무해하고, LED가 상태 표시등이 됩니다.
  #define BACKLIGHT_PIN     13

  // 우측 엣지는 위에서부터 C2(23) → C1(18~22) → C6(14~17) 케이블별 연속 블록입니다.
  #define PIN_SR_LATCH      14      // ST_CP
  #define PIN_SR_CLOCK      15      // SH_CP
  #define PIN_SR_DATA       16      // DS
  #define PIN_LADDER        A3      // pin 17  ⚠ 필터 캡은 A3 에

  // C1 은 18~22 연속 블록. 물리 순서(위→아래)는 T40과 동일하게
  // MPO, JFS1, JFS2, RUN LED, ENG CONT — 엣지가 반대라 핀 번호는 역순입니다.
  #define PIN_JFS1          21
  #define PIN_JFS2          20
  #define PIN_ENG_CONT      18
  #define PIN_MPO           22
  #define PIN_LED_JFS_RUN   19      // ENGINE START RUN 램프

  #define PIN_POT_COMM1     A17     // pin 41
  #define PIN_POT_COMM2     A16     // pin 40
  #define PIN_POT_MSL       A15     // pin 39
  #define PIN_POT_THREAT    A14     // pin 38
  #define PIN_POT_INTCOM    A13     // pin 27
  #define PIN_POT_ILS       A12     // pin 26
  #define PIN_POT_UHFVOL    A9      // pin 23
#else   // STAGE_T40
  #define HAS_ENCODERS      0

  // 핀 13은 Teensy 온보드 LED와 공유됩니다. 입력으로 쓰면 LED 경로 때문에
  // 상시 눌림으로 읽힐 수 있어 피해야 하지만, 출력이면 원래 용도라 문제없고
  // 온보드 LED가 백라이트 상태 표시등이 됩니다.
  #define BACKLIGHT_PIN     13

  // 케이블 C6(SR 3선 + 래더)를 기판 하단 한 곳에 모으기 위한 배치입니다.
  // Teensy 4.0 엣지는 왼쪽 GND,0~12 / 오른쪽 Vin,GND,3.3V,23~13 이라
  // SR(10~12, 왼쪽 맨 아래)과 래더(14, 오른쪽 맨 아래)가 마주 봅니다.
  // SR 물리 순서(위→아래)는 T41과 동일: DS, SH_CP, ST_CP — 엣지가 반대라 핀 번호는 역순
  #define PIN_SR_LATCH      12      // ST_CP   (ADC 자리를 비우려고 이동)
  #define PIN_SR_CLOCK      11      // SH_CP
  #define PIN_SR_DATA       10      // DS
  #define PIN_LADDER        A0      // pin 14  ⚠ 필터 캡은 A0 에

  // C1 물리 순서(위→아래)는 T41과 동일: MPO, JFS1, JFS2, RUN LED, ENG CONT
  #define PIN_JFS1           1
  #define PIN_JFS2           2
  #define PIN_ENG_CONT       4
  #define PIN_MPO            0
  #define PIN_LED_JFS_RUN    3      // ENGINE START RUN 램프

  // AUDIO 6개가 핀 18~23 완전 연속이 됩니다.
  #define PIN_POT_COMM1     A9      // pin 23   ┐
  #define PIN_POT_COMM2     A8      // pin 22   │ AUDIO 1
  #define PIN_POT_MSL       A7      // pin 21   │
  #define PIN_POT_THREAT    A6      // pin 20   ┘
  #define PIN_POT_ILS       A5      // pin 19   ┐ AUDIO 2
  #define PIN_POT_INTCOM    A4      // pin 18   ┘
  #define PIN_POT_UHFVOL    A1      // pin 15
#endif

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
// Matching is nearest-value (not window overlap), so adjacent values may
// sit closer together than maxDist without causing double presses.
struct AnalogBtnArrayDef {
  const char*        groupName;
  Panel              panel;
  uint8_t            pin;
  uint8_t            numButtons;
  const char* const* btnNames;
  const int*         values;      // expected analogRead per button
  int                maxDist;     // reject match if distance exceeds this
};


// ================================================================
//
//  >>> HARDWARE CONFIGURATION - Edit this section <<<
//
// ================================================================

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
// 순서 주의: ECM -> ELEC -> AVTR 를 먼저 두어 버튼 1~11 이 두 단계에서
// 동일하게 유지되도록 했습니다. T41 전용 패널은 그 뒤에 붙습니다.
const SwitchDef switches[] = {
  // name                 panel        type           mcpIdx pin1 pin2 numPos

  // ---- ECM Panel (MCP 0x22, GPB) ----                     btn 1~6
  {"ECM OPR/STBY",        PNL_ECM,     SW_ON_OFF_ON,     2,  11,  10,  0},  // GPB3/GPB2  (OPR/OFF)
  {"ECM XMIT",            PNL_ECM,     SW_ON_OFF_ON,     2,  13,  12,  0},  // GPB5/GPB4  (XMIT1/XMIT3)
  {"ECM BIT",             PNL_ECM,     SW_ON_OFF,        2,  14,   0,  0},  // GPB6  momentary
  {"ECM RESET",           PNL_ECM,     SW_ON_OFF,        2,  15,   0,  0},  // GPB7  momentary

  // ---- ELEC Panel (MCP 0x21) ----                        btn 7~9
  {"ELEC MAIN PWR",       PNL_ELEC,    SW_ON_OFF_ON,     1,   0,   1,  0},  // GPA0/GPA1  MAIN/OFF
  {"ELEC CAUTION RST",    PNL_ELEC,    SW_ON_OFF,        1,   2,   0,  0},  // GPA2  momentary (CAUTION RST)

  // ---- AVTR Panel (MCP 0x22) ----                        btn 10~11
  {"AVTR",                PNL_AVTR,    SW_ON_OFF_ON,     2,   6,   7,  0},  // GPA6/GPA7  OFF/AUTO/ON

  // ---- ENGINE START Panel (Teensy direct) ----           btn 12~14
  {"JFS",       PNL_ENGINE, SW_ON_OFF_ON, -1, PIN_JFS1, PIN_JFS2, 0},  // OFF/START1/START2
  {"ENG CONT",  PNL_ENGINE, SW_ON_OFF,    -1, PIN_ENG_CONT,   0,  0},  // PRI/SEC

  // ---- MPO (Teensy direct) ----                          btn 15
  {"MPO",       PNL_MPO,    SW_ON_OFF,    -1, PIN_MPO,        0,  0},  // NORM/OVRD

  // ---- EPU Panel (MCP 0x21) ----                         btn 16~17
  {"EPU",                 PNL_EPU,     SW_ON_OFF_ON,     1,   3,   4,  0},  // GPA3/GPA4  OFF/NORM/ON

  // ---- UHF Panel (MCP 0x20, 패널 실장) ----               btn 18~27
  // SW_ROTARY 는 pin1 부터 numPos 개 연속 GPIO 를 읽습니다.
  // 패널 배선 순서 필수: FUNCTION = GPA0~3, MODE = GPA4~6.
  {"UHF FUNCTION",        PNL_UHF,     SW_ROTARY,        0,   0,   0,  4},  // GPA0-3  OFF/MAIN/BOTH/ADF
  {"UHF MODE",            PNL_UHF,     SW_ROTARY,        0,   4,   0,  3},  // GPA4-6  MNL/PRESET/GRD
  {"UHF SQUELCH",         PNL_UHF,     SW_ON_OFF,        0,   7,   0,  0},  // GPA7
  {"UHF T-TONE",          PNL_UHF,     SW_ON_OFF,        0,   8,   0,  0},  // GPB0  momentary
  {"UHF STATUS",          PNL_UHF,     SW_ON_OFF,        0,   9,   0,  0},  // GPB1  momentary

  // ---- AUDIO 1 모드 로터리 (MCP 0x20, 케이블 C8 로 UHF 패널까지 점퍼) ----  btn 28~33
  // AUDIO 1 은 볼륨 6개(pots[])와 별개로 COMM 1/2 각각 3단 셀렉터를 가집니다.
  // 패널 배선 순서 필수: COMM1 = GPB2~4, COMM2 = GPB5~7.
  {"AUDIO COMM1 MODE",    PNL_AUDIO1,  SW_ROTARY,        0,  10,   0,  3},  // GPB2-4  OFF/SQL/GD XMT
  {"AUDIO COMM2 MODE",    PNL_AUDIO1,  SW_ROTARY,        0,  13,   0,  3},  // GPB5-7  OFF/SQL/GD XMT
};

// --- Rotary Encoders (Teensy direct, interrupt-polled) ---
// Each encoder emits 2 buttons: CW then CCW.
//
// Pin pairs must stay on the SAME board edge — an encoder's A/B are two wires
// from one knob. Teensy 4.1 edges are 0-12 + 24-32 (left) and 13-23 + 33-41
// (right). The six encoders fill 0-11 in one run — C2 on 0-5, C3 on 6-11 —
// so the encoder cables' only right-edge line is VOL (pin 23).
#if HAS_ENCODERS
const EncoderDef encoders[] = {
  // name              panel     pinA pinB
  {"UHF PRESET",       PNL_UHF,    6,   7},   // 6-11: C3 encoder block
  {"UHF 100MHz",       PNL_UHF,    8,   9},
  {"UHF 10MHz",        PNL_UHF,    0,   1},   // 0-5: C2 encoder block
  {"UHF 1MHz",         PNL_UHF,    2,   3},
  {"UHF 0.1MHz",       PNL_UHF,    4,   5},
  {"UHF 0.025MHz",     PNL_UHF,   10,  11},
};
#define NUM_ENCODERS  (sizeof(encoders) / sizeof(encoders[0]))
#else
#define NUM_ENCODERS  0     // T40: 엔코더 없음
#endif

// --- Analog Pots ---
// 축 배정(X~Zrotate)은 두 단계에서 동일하므로 BMS 축 바인딩이 유지됩니다.
const PotDef pots[] = {
  // name                 panel        pin              axis
  {"AUDIO COMM CH1",      PNL_AUDIO1,  PIN_POT_COMM1,   AXIS_X},
  {"AUDIO COMM CH2",      PNL_AUDIO1,  PIN_POT_COMM2,   AXIS_Y},
  {"AUDIO MSL VOL",       PNL_AUDIO1,  PIN_POT_MSL,     AXIS_Z},
  {"AUDIO THREAT VOL",    PNL_AUDIO1,  PIN_POT_THREAT,  AXIS_Xr},
  {"AUDIO INTERCOM",      PNL_AUDIO2,  PIN_POT_INTCOM,  AXIS_Yr},
  {"AUDIO ILS VOL",       PNL_AUDIO2,  PIN_POT_ILS,     AXIS_Zr},
  {"UHF VOL",             PNL_UHF,     PIN_POT_UHFVOL,  AXIS_S1},
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
const int ecmBtnValues[] = {1024, 680, 509, 406, 338, 290, 253, 225};

const AnalogBtnArrayDef analogBtnArrays[] = {
  // groupName      panel     pin  numBtn  btnNames      values         maxDist
  {"ECM Buttons",   PNL_ECM,  PIN_LADDER, 8,      ecmBtnNames,  ecmBtnValues,  60},
};

// --- ELEC Panel LEDs (MCP 0x21, GPB port) ---
// All 8 on GPB so the whole port updates in one I2C write.
// NOTE: LEDs are sourced (cathode common to GND), so the binding limit is
//       VDD inflow 125mA — not the VSS 150mA figure. 0x21 carries 11 LEDs
//       (ELEC 8 + EPU 3), so keep each at or below 10mA (11 x 10 = 110mA).
enum LedIdx {
  // ELEC 패널 경고등 8 (MCP 0x21 GPB0~7) — ledBits bit 0~7
  LI_FLCS_PMG, LI_MAIN_GEN, LI_STBY_GEN,
  LI_EPU_GEN, LI_EPU_PMG, LI_FLCS_RLY,
  LI_BATT_FAIL, LI_BATT_TO_FLCS,
  // EPU 패널 3 (MCP 0x21 GPA5~7) — ledBits bit 8~10
  LI_EPU_HYDRAZN, LI_EPU_AIR, LI_EPU_RUN,
  // ENGINE START 패널 1 (Teensy 직결) — ledBits bit 11
  LI_JFS_RUN,
};

const LedDef leds[] = {
  // name               panel      pin  mcpIdx
  {"FLCS PMG",          PNL_ELEC,  15,   1},   // GPB7
  {"MAIN GEN",          PNL_ELEC,  14,   1},   // GPB6
  {"STBY GEN",          PNL_ELEC,  13,   1},   // GPB5
  {"EPU GEN",           PNL_ELEC,  12,   1},   // GPB4
  {"EPU PMG",           PNL_ELEC,  11,   1},   // GPB3
  {"FLCS RLY",          PNL_ELEC,   8,   1},   // GPB0
  {"BATT FAIL",         PNL_ELEC,  10,   1},   // GPB2
  {"BATT TO FLCS",      PNL_ELEC,   9,   1},   // GPB1
  // ---- EPU 패널 (MCP 0x21 GPA5~7) ----
  {"EPU HYDRAZN",       PNL_EPU,    5,   1},   // GPA5
  {"EPU AIR",           PNL_EPU,    6,   1},   // GPA6
  {"EPU RUN",           PNL_EPU,    7,   1},   // GPA7
  // ---- ENGINE START 패널 (Teensy 직결, 케이블 1에 탑음) ----
  {"JFS RUN",           PNL_ENGINE, PIN_LED_JFS_RUN, -1},
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
//  Backlight (ON/OFF only — no dimming)
// ================================================================

static bool backlightState = true;

void setBacklight(bool on) {
  digitalWrite(BACKLIGHT_PIN, on ? HIGH : LOW);
  backlightState = on;
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

void mcpInit(uint8_t deviceIdx) {
  uint8_t addr = mcpDevices[deviceIdx].addr;

  MCP_WIRE.beginTransmission(addr);
  if (MCP_WIRE.endTransmission() != 0) {
    mcpConnected[deviceIdx] = false;
    mcpPortCache[deviceIdx] = 0xFFFF;   // all HIGH = all switches released
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
    shiftOut(SR_DATA_PIN, SR_CLOCK_PIN, LSBFIRST, srData[i]);
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

static uint8_t switchBtnStart[NUM_SWITCHES];
static uint8_t analogBtnStart[NUM_ANALOG_ARRAYS];
#if HAS_ENCODERS
static uint8_t encoderBtnStart[NUM_ENCODERS];
#endif
static int     totalButtons = 0;

static uint8_t prevBtnState[128];
static uint32_t lastInputTime = 0;
static bool backlightIdleOff = false;

int switchButtonCount(const SwitchDef& sw) {
  switch (sw.type) {
    case SW_ON_OFF:    return 1;
    case SW_ON_OFF_ON: return 2;
    case SW_ROTARY:    return sw.numPos;
  }
  return 1;
}

void assignButtons() {
  int btn = 1;

  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    switchBtnStart[i] = btn;
    btn += switchButtonCount(switches[i]);
  }
  for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++) {
    analogBtnStart[i] = btn;
    btn += analogBtnArrays[i].numButtons;
  }
#if HAS_ENCODERS
  for (unsigned int i = 0; i < NUM_ENCODERS; i++) {
    encoderBtnStart[i] = btn;
    btn += 2;                       // CW, CCW
  }
#endif

  totalButtons = btn - 1;
  if (totalButtons > 128)
    Serial.printf("ERROR: %d buttons assigned, max is 128\n", totalButtons);
}


// ================================================================
//  Joystick Axis Helper
// ================================================================

void setJoystickAxis(JoyAxis axis, int rawValue) {
  int value = rawValue * 64;        // 10-bit ADC -> 16-bit axis
  switch (axis) {
    case AXIS_X:  Joystick.X(value);       break;
    case AXIS_Y:  Joystick.Y(value);       break;
    case AXIS_Z:  Joystick.Z(value);       break;
    case AXIS_Xr: Joystick.Xrotate(value); break;
    case AXIS_Yr: Joystick.Yrotate(value); break;
    case AXIS_Zr: Joystick.Zrotate(value); break;
    default:      Joystick.slider(axis - AXIS_S1 + 1, value); break;
  }
}


// ================================================================
//  Rotary Encoder — 1kHz ISR quadrature decode
// ================================================================
//
//  Encoders cannot live on the MCP23017: I2C polling would drop pulses.
//  A 1kHz timer poll handles ~250 detents/sec, far beyond hand speed.
//  STAGE_T40 에는 엔코더가 없으므로 이 블록 전체가 컴파일되지 않습니다.

#if HAS_ENCODERS

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
    const EncoderDef& e = encoders[i];
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
    uint8_t btnCW  = encoderBtnStart[i];
    uint8_t btnCCW = btnCW + 1;

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
      if (ALLOW_DEBUG)
        Serial.printf("[ENC] %s %s\n", e.name, dir > 0 ? "CW" : "CCW");
    }
  }
}

#else   // HAS_ENCODERS == 0  (STAGE_T40)

void processEncoders() {}

#endif  // HAS_ENCODERS


// ================================================================
//  Switch Processing
// ================================================================

inline int readSwPin(const SwitchDef& sw, uint8_t pin) {
  return (sw.mcpIdx >= 0) ? mcpReadPin(sw.mcpIdx, pin) : digitalRead(pin);
}

void processSwitches() {
  for (unsigned int d = 0; d < NUM_MCP_DEVICES; d++) mcpReadPorts(d);

  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    const SwitchDef& sw = switches[i];
    int btn = switchBtnStart[i];

    switch (sw.type) {
      case SW_ON_OFF: {
        int state = !readSwPin(sw, sw.pin1);          // active-low
        if (prevBtnState[btn] != state) {
          if (ALLOW_DEBUG) Serial.printf("[SW] btn %d %s = %s\n", btn, sw.name, state ? "ON" : "OFF");
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
          if (ALLOW_DEBUG) Serial.printf("[SW] btn %d~%d %s = %d/%d\n", btn, btn + 1, sw.name, s1, s2);
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
            if (ALLOW_DEBUG && state) Serial.printf("[SW] %s = pos %d\n", sw.name, p);
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

    // Nearest value wins. Overlapping tolerance windows cannot produce
    // simultaneous or ambiguous matches this way.
    int best = -1;
    int bestDist = arr.maxDist + 1;
    for (int b = 0; b < arr.numButtons; b++) {
      int dist = abs(raw - arr.values[b]);
      if (dist < bestDist) { bestDist = dist; best = b; }
    }

    for (int b = 0; b < arr.numButtons; b++) {
      int state = (b == best);
      if (prevBtnState[btn + b] != state) {
        if (ALLOW_DEBUG && state)
          Serial.printf("[Ladder] %s raw=%d -> %s\n", arr.groupName, raw, arr.btnNames[b]);
        prevBtnState[btn + b] = state;
        lastInputTime = millis();
      }
      Joystick.button(btn + b, state);
    }

    if (ALLOW_DEBUG && best < 0 && raw > 100)
      Serial.printf("[Ladder] %s raw=%d (no match)\n", arr.groupName, raw);
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
//  NOTE: peak current. All 32 SR LEDs + 8 ELEC LEDs light together in the
//  blink phase. If running on a USB 2.0 port (500mA), stagger these instead.

void welcomeCeremony() {
  setBacklight(true);

  // ECM sweep: column by column (S -> A -> F -> T), previous column off
  for (int col = 0; col < 4; col++) {
    if (col > 0)
      for (int grp = 0; grp < 8; grp++) srWrite(grp * 4 + (col - 1), false);
    for (int grp = 0; grp < 8; grp++) srWrite(grp * 4 + col, true);
    srFlush();
    delay(200);
  }

  // ELEC LEDs in sequence
  for (unsigned int i = 0; i < NUM_LEDS; i++) {
    writeElecLed(i, true);
    mcpFlushOutputs();
    delay(40);
  }
  delay(300);

  // Blink all twice
  for (int b = 0; b < 2; b++) {
    turnOffAllLeds();
    delay(150);
    for (int i = 0; i < SR_NUM_OUTPUTS; i++) srWrite(i, true);
    srFlush();
    for (unsigned int i = 0; i < NUM_LEDS; i++) writeElecLed(i, true);
    mcpFlushOutputs();
    delay(150);
  }

  turnOffAllLeds();
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
  if (ALLOW_DEBUG) Serial.println("[Proto] Reset to UNKNOWN");
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
            if (ALLOW_DEBUG) Serial.println("[Proto] Detected DCS-BIOS");
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
          if (ALLOW_DEBUG) Serial.println("[Proto] Detected BMS-BIOS");
          bmsBiosReset();
          bbBufIdx = 0;
          bbState  = BB_PAYLOAD;
        } else {
          syncCount = 0;
          bmsBiosSync1 = false;
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
  Joystick.hat(1, -1);

  // --- Backlight ---
  pinMode(BACKLIGHT_PIN, OUTPUT);
  setBacklight(true);
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
#if HAS_ENCODERS
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
#endif

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

  // --- Startup summary ---
  Serial.println("=========================");
  Serial.println(" F16 LEFT CONSOLE");
#if BOARD_REV == STAGE_T41
  Serial.println(" STAGE_T41 - Teensy 4.1 (full)");
  Serial.println(" I2C: Wire2  SCL2=24 SDA2=25");
#else
  Serial.println(" STAGE_T40 - Teensy 4.0 (interim)");
  Serial.println(" Panels: all except UHF encoders");
  Serial.println(" I2C: Wire1  SDA1=17 SCL1=16");
#endif
  Serial.println("=========================");
  for (int p = 0; p < PNL_COUNT; p++) {
    int nSw = 0, nEnc = 0, nPot = 0, nLed = 0, nAna = 0;
    for (unsigned int i = 0; i < NUM_SWITCHES;      i++) if (switches[i].panel        == p) nSw++;
#if HAS_ENCODERS
    for (unsigned int i = 0; i < NUM_ENCODERS;      i++) if (encoders[i].panel        == p) nEnc++;
#endif
    for (unsigned int i = 0; i < NUM_POTS;          i++) if (pots[i].panel            == p) nPot++;
    for (unsigned int i = 0; i < NUM_LEDS;          i++) if (leds[i].panel            == p) nLed++;
    for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++) if (analogBtnArrays[i].panel == p) nAna++;
    if (nSw + nEnc + nPot + nLed + nAna == 0) continue;
    Serial.printf("  [%s] sw:%d enc:%d pot:%d led:%d ladder:%d\n",
                  panelNames[p], nSw, nEnc, nPot, nLed, nAna);
  }
  Serial.printf("  Total buttons: %d\n", totalButtons);
  Serial.println("=========================");

  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    int cnt = switchButtonCount(switches[i]);
    const char* loc = (switches[i].mcpIdx >= 0) ? "MCP" : "DIR";
    if (cnt == 1) Serial.printf("  btn %-3d     : %-20s [%s]\n", switchBtnStart[i], switches[i].name, loc);
    else          Serial.printf("  btn %-3d~%-3d : %-20s [%s]\n", switchBtnStart[i],
                                switchBtnStart[i] + cnt - 1, switches[i].name, loc);
  }
  for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++)
    Serial.printf("  btn %-3d~%-3d : %-20s [ladder %d]\n", analogBtnStart[i],
                  analogBtnStart[i] + analogBtnArrays[i].numButtons - 1,
                  analogBtnArrays[i].groupName, analogBtnArrays[i].numButtons);
#if HAS_ENCODERS
  for (unsigned int i = 0; i < NUM_ENCODERS; i++)
    Serial.printf("  btn %-3d~%-3d : %-20s [enc CW/CCW]\n", encoderBtnStart[i],
                  encoderBtnStart[i] + 1, encoders[i].name);
#endif
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
          mcpInit(d);
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

  processSwitches();
  processAnalogButtons();
  processPots();
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
