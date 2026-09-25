// ================================================================
//  REDKITE F16 LEFT CONSOLE — USB Joystick
// ================================================================
//
//  Board  : Teensy 4.1
//  Panels : ECM / ELEC / EPU / AVTR / UHF(엔코더 6) / ENGINE START / MPO / AUDIO 1-2
//  I2C    : Wire2 (SDA2=25, SCL2=24)
//  Buttons: 58,  축 10,  엔코더 6
//  사용 핀: 40 / 42 (헤더),  여유 2
//  백라이트: pin 13 — 온보드 LED가 상태 표시등이 됨
//
//  DX 버튼 배정 순서: switches[](39) → analogBtnArrays[](8) → encoders[](12) = 59
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
//    B  41     UHF STATUS (C13)
//    여유: 12, 39(A15)
//  ※ docs/LEFT_CONSOLE_PIN_TREE2.md 의 핀 배열도는 바닥면(납땜면) 기준이라
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
  const int*         values[2];   // [0]=BL OFF, [1]=BL ON
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

  // ---- ELEC Panel (MCP 0x21, GPB0~2) ----                  btn 7~9
  {"ELEC MAIN PWR",       PNL_ELEC,    SW_ON_OFF_ON,     1,   8,   9,  0},  // GPB0/GPB1  MAIN/OFF
  {"ELEC CAUTION RST",    PNL_ELEC,    SW_ON_OFF,        1,  10,   0,  0},  // GPB2  momentary (CAUTION RST)

  // ---- AVTR Panel (MCP 0x22) ----                        btn 10~11
  {"AVTR",                PNL_AVTR,    SW_ON_OFF_ON,     2,   6,   7,  0},  // GPA6/GPA7  OFF/AUTO/ON

  // ---- ENGINE START Panel (Teensy direct) ----           btn 12~14
  {"JFS",       PNL_ENGINE, SW_ON_OFF_ON, -1, PIN_JFS1, PIN_JFS2, 0},  // OFF/START1/START2
  {"ENG CONT",  PNL_ENGINE, SW_ON_OFF,    -1, PIN_ENG_CONT,   0,  0},  // PRI/SEC

  // ---- MPO (Teensy direct) ----                          btn 15
  {"MPO",       PNL_MPO,    SW_ON_OFF,    -1, PIN_MPO,        0,  0},  // NORM/OVRD

  // ---- EPU Panel (MCP 0x21) ----                         btn 16~17
  {"EPU",                 PNL_EPU,     SW_ON_OFF_ON,     1,  14,  15,  0},  // GPB6/GPB7  OFF/NORM/ON

  // ---- UHF Panel (MCP 0x20, 패널 실장) ----               btn 18~27
  // SW_ROTARY 는 pin1 부터 numPos 개 연속 GPIO 를 읽습니다.
  // 실제 배선: FUNCTION(PB4~7) → MODE(PB1~3) → STATUS(PB0)
  // SW_ROTARY 는 오름차순 고정이라 DX 를 뒤집으려면 개별 SW_ON_OFF 로 분리
  {"UHF FUNC ADF",   PNL_UHF, SW_ON_OFF, 0, 15, 0, 0},  // PB7
  {"UHF FUNC BOTH",  PNL_UHF, SW_ON_OFF, 0, 14, 0, 0},  // PB6
  {"UHF FUNC MAIN",  PNL_UHF, SW_ON_OFF, 0, 13, 0, 0},  // PB5
  {"UHF FUNC OFF",   PNL_UHF, SW_ON_OFF, 0, 12, 0, 0},  // PB4
  {"UHF MODE GRD",   PNL_UHF, SW_ON_OFF, 0, 11, 0, 0},  // PB3
  {"UHF MODE PRE",   PNL_UHF, SW_ON_OFF, 0, 10, 0, 0},  // PB2
  {"UHF MODE MNL",   PNL_UHF, SW_ON_OFF, 0,  9, 0, 0},  // PB1
  {"UHF SQUELCH",  PNL_UHF, SW_ON_OFF, -1, PIN_UHF_SQUELCH, 0, 0},  // Teensy 33
  {"UHF T-TONE",   PNL_UHF, SW_ON_OFF, -1, PIN_UHF_TTONE,   0, 0},  // Teensy 34  momentary
  {"UHF STATUS",  PNL_UHF, SW_ON_OFF, -1, PIN_UHF_STATUS,  0, 0},  // Teensy 41  momentary

  // ---- AUDIO 1 모드 로터리 (MCP 0x20, 케이블 C8 로 UHF 패널까지 점퍼) ----  btn 28~33
  // 실제 배선: COMM1 PA4=OFF PA3=SQL PA2=GD, COMM2 PA7=OFF PA6=SQL PA5=GD
  // SW_ROTARY 는 오름차순 고정이라 DX 를 뒤집으려면 개별 SW_ON_OFF 로 분리
  {"COMM1 OFF",   PNL_AUDIO1, SW_ON_OFF, 0, 4, 0, 0},  // PA4
  {"COMM1 SQL",   PNL_AUDIO1, SW_ON_OFF, 0, 3, 0, 0},  // PA3
  {"COMM1 GD",    PNL_AUDIO1, SW_ON_OFF, 0, 2, 0, 0},  // PA2
  {"COMM2 OFF",   PNL_AUDIO1, SW_ON_OFF, 0, 7, 0, 0},  // PA7
  {"COMM2 SQL",   PNL_AUDIO1, SW_ON_OFF, 0, 6, 0, 0},  // PA6
  {"COMM2 GD",    PNL_AUDIO1, SW_ON_OFF, 0, 5, 0, 0},  // PA5

  // ---- ENGINE START 추가 스위치 (Teensy direct) ----      btn 34~36
  {"AB RESET",  PNL_ENGINE, SW_ON_OFF,    -1, PIN_ABRESET,    0,  0},
  {"ENG DATA",  PNL_ENGINE, SW_ON_OFF,    -1, PIN_ENGDATA,    0,  0},
  {"MAX POWER", PNL_ENGINE, SW_ON_OFF,    -1, PIN_MAXPOWER,   0,  0},

  // ---- AUDIO 2 스위치 (Teensy direct) ----                btn 37~38
  {"HOT MIC",   PNL_AUDIO2, SW_ON_OFF,     0,   0,            0,  0},  // MCP#0 PA0
  {"CIPHER",    PNL_AUDIO2, SW_ON_OFF,     0,   1,            0,  0},  // MCP#0 PA1
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
  // BMS 바인딩 가능 7개 → DirectInput 인식 축 우선 배치 (6 named + slider 1~2)
  // name                 panel        pin              axis
  {"AUDIO COMM CH1",      PNL_AUDIO1,  PIN_POT_COMM1,   AXIS_X},
  {"AUDIO COMM CH2",      PNL_AUDIO1,  PIN_POT_COMM2,   AXIS_Y},
  {"AUDIO MSL VOL",       PNL_AUDIO1,  PIN_POT_MSL,     AXIS_Z},
  {"AUDIO THREAT VOL",    PNL_AUDIO1,  PIN_POT_THREAT,  AXIS_Xr},
  {"AUDIO INTERCOM",      PNL_AUDIO2,  PIN_POT_INTCOM,  AXIS_Yr},
  {"UHF VOL",             PNL_UHF,     PIN_POT_UHFVOL,  AXIS_Zr},
  {"AUDIO ILS VOL",       PNL_AUDIO2,  PIN_POT_ILS,     AXIS_S1},
  // BMS 바인딩 불가 3개 → slider 2 까지만 DirectInput 인식
  {"AUDIO SECURE VOL",    PNL_AUDIO1,  PIN_POT_SECURE,  AXIS_S2},
  {"AUDIO TF VOL",        PNL_AUDIO1,  PIN_POT_TF,      AXIS_S3},    // DirectInput 미인식
  {"AUDIO TACAN VOL",     PNL_AUDIO2,  PIN_POT_TACAN,   AXIS_S4},    // DirectInput 미인식
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
const int ecmBtnValues[] = {1023, 679, 509, 406, 338, 289, 253, 225};  // measured, idle~0

const AnalogBtnArrayDef analogBtnArrays[] = {
  // groupName      panel     pin  numBtn  btnNames      values{BL_OFF, BL_ON}
  {"ECM Buttons",   PNL_ECM,  PIN_LADDER, 8,      ecmBtnNames,  {ecmBtnValues, ecmBtnValues}},
};

// --- ELEC Panel LEDs (MCP 0x21, GPA port) ---
// All 8 on GPA so the whole port updates in one I2C write.
// NOTE: LEDs are sourced (cathode common to GND), so the binding limit is
//       VDD inflow 125mA — not the VSS 150mA figure. 0x21 carries 11 LEDs
//       (ELEC 8 + EPU 3), so keep each at or below 10mA (11 x 10 = 110mA).
enum LedIdx {
  // ELEC 패널 경고등 8 (MCP 0x21 GPA0~7) — ledBits bit 0~7
  LI_FLCS_PMG, LI_MAIN_GEN, LI_STBY_GEN,
  LI_EPU_GEN, LI_EPU_PMG, LI_BATT_TO_FLCS,
  LI_FLCS_RLY, LI_BATT_FAIL,
  // EPU 패널 3 (MCP 0x21 GPB3~5) — ledBits bit 8~10
  LI_EPU_HYDRAZN, LI_EPU_AIR, LI_EPU_RUN,
  // ENGINE START 패널 1 (Teensy 직결) — ledBits bit 11
  LI_JFS_RUN,
};

const LedDef leds[] = {
  // name               panel      pin  mcpIdx
  {"FLCS PMG",          PNL_ELEC,   0,   1},   // GPA0
  {"MAIN GEN",          PNL_ELEC,   1,   1},   // GPA1
  {"STBY GEN",          PNL_ELEC,   2,   1},   // GPA2
  {"EPU GEN",           PNL_ELEC,   3,   1},   // GPA3
  {"EPU PMG",           PNL_ELEC,   4,   1},   // GPA4
  {"BATT TO FLCS",      PNL_ELEC,   5,   1},   // GPA5
  {"FLCS RLY",          PNL_ELEC,   6,   1},   // GPA6
  {"BATT FAIL",         PNL_ELEC,   7,   1},   // GPA7
  // ---- EPU 패널 (MCP 0x21 GPB3~5) ----
  {"EPU HYDRAZN",       PNL_EPU,   11,   1},   // GPB3
  {"EPU AIR",           PNL_EPU,   12,   1},   // GPB4
  {"EPU RUN",           PNL_EPU,   13,   1},   // GPB5
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
//  Backlight (PWM dimming)
// ================================================================

static bool backlightState = true;
static uint8_t manualBrightness = 255;  // offline 수동 밝기 (기본 최대)
static bool backlightIdleOff = false;

void setBacklight(bool on) {
  analogWrite(BACKLIGHT_PIN, on ? 255 : 0);
  backlightState = on;
}

void setBacklightBrightness(uint8_t brightness) {
  analogWrite(BACKLIGHT_PIN, brightness);
  backlightState = (brightness > 0);
}

// Offline 수동 밝기 조절: UHF STATUS 누른 채 TF pot 으로 조절
void checkManualBacklight() {
  if (!digitalRead(PIN_UHF_STATUS)) {  // active-low: 눌림 = LOW
    int raw = analogRead(PIN_POT_TF);
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
static uint8_t encoderBtnStart[NUM_ENCODERS];
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
  for (unsigned int i = 0; i < NUM_ENCODERS; i++) {
    encoderBtnStart[i] = btn;
    btn += 2;                       // CW, CCW
  }

  totalButtons = btn - 1;
  if (totalButtons > 128)
    Serial.printf("ERROR: %d buttons assigned, max is 128\n", totalButtons);
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
    const int* vals = arr.values[0];  // TODO: arr.values[blOn] when backlight added
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
  //if (ALLOW_DEBUG) Serial.println("[Proto] Reset to UNKNOWN");
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

  // --- Backlight PWM ---
  analogWriteFrequency(BACKLIGHT_PIN, 1000);  // 1kHz PWM
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
  for (unsigned int i = 0; i < NUM_ENCODERS; i++)
    Serial.printf("  btn %-3d~%-3d : %-20s [enc CW/CCW]\n", encoderBtnStart[i],
                  encoderBtnStart[i] + 1, encoders[i].name);
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

    // Offline 수동 밝기 조절 (UHF STATUS + TF pot)
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
