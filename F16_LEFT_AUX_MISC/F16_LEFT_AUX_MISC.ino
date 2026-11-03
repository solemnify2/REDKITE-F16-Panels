/* REDKITE_F16_PANELS
   Teensy 4.1 USB Joystick for Falcon BMS F-16 Left Console Panel

   USB Type: Keyboard + Mouse + Joystick (Tools > USB Type)

   Hardware configuration is data-driven.
   To add/remove/change hardware, edit the HARDWARE CONFIGURATION section only.
   Joystick button numbers are auto-assigned at runtime.
   To disable a panel, comment out its entries in the config arrays.
*/


// ================================================================
//  Build Checks
// ================================================================

#if JOYSTICK_SIZE < 64
  #error "JOYSTICK_SIZE must be 64. Edit USB_SERIAL_HID section in %LOCALAPPDATA%/Arduino15/packages/teensy/hardware/avr/<version>/cores/teensy4/usb_desc.h"
#endif

#if PRODUCT_ID != 0x0487
  #error "PRODUCT_ID must be 0x0487 for Left Aux Misc. Edit USB_SERIAL_HID section in %LOCALAPPDATA%/Arduino15/packages/teensy/hardware/avr/<version>/cores/teensy4/usb_desc.h"
#endif

// ================================================================
//  General Settings
// ================================================================

#define BAUDRATE      1000000
#define ALLOW_DEBUG   false
#define MAX_PIN       55        // Teensy 4.1 max digital pin
#define LOOP_DELAY_MS 50
#define SERIAL_TIMEOUT 6        // Serial heartbeat timeout in seconds
#define BACKLIGHT_PIN       13  // Console backlight PWM (MOSFET: 0=off, 255=full)
#define MISC_BACKLIGHT_PIN  12  // MISC (instr panel) backlight PWM (MOSFET on freed Gear Warn pin)
#define IDLE_TIMEOUT_MS (1000 * 60 * 30)  // offline idle timeout for backlight auto-off (30min)


// ================================================================
//  Type Definitions
// ================================================================

enum SwitchType { SW_ON_OFF, SW_ON_OFF_ON, SW_ON_OFF_NC };

enum JoyAxis {
  AXIS_X, AXIS_Y, AXIS_Z,
  AXIS_Zr,                      // Zrotate
  AXIS_SL, AXIS_SR,             // sliderLeft/Right  (JOYSTICK_SIZE 12)
  AXIS_Xr, AXIS_Yr              // Xrotate/Yrotate   (JOYSTICK_SIZE 64)
};

enum Panel {
  PNL_NONE,       // standalone (not part of a panel)
  PNL_MISC,       // MISC Armament panel (center console, left of left MFD)
  PNL_GEAR,       // Landing Gear panel (left aux console)
  PNL_ALT_GEAR,   // Alt Gear panel (left aux console)
  PNL_CMDS,       // Countermeasures Dispenser (left aux console)
  PNL_TWA,        // Threat Warning Aux (left aux console)
  PNL_HMCS,       // HMCS (Helmet Mounted Cueing System)
  PNL_COUNT
};

const char* const panelNames[] = {
  "Standalone", "MISC", "Gear", "AltGear", "CMDS", "TWA", "HMCS"
};

struct SwitchDef {
  const char* name;
  Panel       panel;
  SwitchType  type;
  int8_t      mcpIdx;     // -1 = direct Teensy pin, >= 0 = index into mcpDevices[]
  uint8_t     pin1;
  uint8_t     pin2;       // only used for SW_ON_OFF_ON
  int*        stateRef;   // if non-NULL, switch state is written here
};

// NOTE: PotDef and AnalogBtnArrayDef have no mcpIdx — MCP23017 does not support analog input.
struct PotDef {
  const char* name;
  Panel       panel;
  uint8_t     pin;
  JoyAxis     axis;
};

struct LedDef {
  const char* name;
  Panel       panel;
  uint8_t     pin;
  int8_t      mcpIdx;   // -1 = direct Teensy pin, >= 0 = index into mcpDevices[]
};

// --- MCP23017 I/O Expander ---

struct McpDeviceDef {
  const char* name;
  uint8_t     addr;     // I2C address (0x20–0x27)
};


// Resistor-ladder analog button array: multiple buttons on a single analog pin.
// Each button adds a 220Ω resistor, producing a unique analogRead value.
// values[] in descending order.
// Matching: nearest-value, reject if below 100 (noise floor).
struct AnalogBtnArrayDef {
  const char*        groupName;    // group name for logging
  Panel              panel;
  uint8_t            pin;          // analog input pin
  uint8_t            numButtons;
  const char* const* btnNames;     // array of button names, length = numButtons
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
//
//  예) {"My Switch",  PNL_GEAR, SW_ON_OFF, -1, 5, 0, NULL}   Teensy 핀 5
//      {"MCP Switch", PNL_MISC, SW_ON_OFF,  0, 5, 0, NULL}   MCP#0 GPA5
//
//  ※ 이 배열의 순서는 DX 번호와 무관합니다. 배선대로 두고, 새 하드웨어를
//    추가하면 `dxOrder[]` 에 한 줄 넣으십시오 — 빠뜨리면 컴파일이 막힙니다.
//


// --- Switch state references ---
// Declare variables here for switches that need to be read by other logic.
// Then set stateRef in switches[] to link them.
int swLandingLight = 0;   // used by pedal brake mode
int swGear = 0;           // used by offline LED simulation

const SwitchDef switches[] = {
  // name                   panel           type         mcpIdx pin1 pin2  stateRef
  //                                                     (-1 = Teensy direct, >= 0 = MCP device index)
  //
  // ※ 이 배열의 순서는 **읽기 좋으라고** 실기 배치를 따릅니다. DX 번호와는
  //   무관합니다 — 번호는 `dxOrder[]` 가 정합니다.

  // ---- MISC Panel — 전방 계기판, 좌측 MFD 왼쪽 (MCP23017 device 0, addr 0x20) ----
  // MCP pin mapping: GPA0–7 = 0–7, GPB0–7 = 8–15
  {"RF",                    PNL_MISC,       SW_ON_OFF_ON,    0,   5,   4,  NULL},   // GPA5(NORM), GPA4(SILENT)
  {"Laser ARM",             PNL_MISC,       SW_ON_OFF,       0,   3,   0,  NULL},   // GPA3
  {"ALT REL",               PNL_MISC,       SW_ON_OFF_NC,    0,   2,   0,  NULL},   // GPA2 (normally closed)
  {"Master ARM",            PNL_MISC,       SW_ON_OFF_ON,    0,   1,   0,  NULL},   // GPA1(ARM), GPA0(SIM)
  {"ADV MODE",              PNL_MISC,       SW_ON_OFF,       0,   10,  0,  NULL},   // GPB2
  {"Roll AP",               PNL_MISC,       SW_ON_OFF_ON,    0,   11,  12,  NULL},  // GPB3, GPB4
  {"Pitch AP",              PNL_MISC,       SW_ON_OFF_ON,    0,   13,  14,  NULL},  // GPB5, GPB6

  // ---- Gear Panel — 좌측 보조 콘솔 전방 (Teensy direct) ----
  // 패널 3행: EMER JETT·HOOK / GND JETT·BRAKES·ANTI-SKID·DN LOCK·기어핸들
  //           / STORES CONFIG·HORN SILENCER·LIGHTS LANDING
  {"EMER Jettison",         PNL_GEAR,       SW_ON_OFF,      -1,   10,   0,  NULL},
  {"Hook",                  PNL_GEAR,       SW_ON_OFF,      -1,   11,   0,  NULL},   // Up / Down
  {"GND JETT ENABLE",       PNL_GEAR,       SW_ON_OFF,      -1,   9,   0,  NULL},   // ENABLE / OFF
  {"BRAKES Channel",        PNL_GEAR,       SW_ON_OFF,      -1,   8,   0,  NULL},   // CHAN 1 / CHAN 2
  {"ANTI SKID",             PNL_GEAR,       SW_ON_OFF_ON,   -1,   6,  7,  NULL},   // PARKING BRAKE / ANTI SKID / OFF
  {"DN LOCK REL",           PNL_GEAR,       SW_ON_OFF,      -1,   1,   0,  NULL},   // SW_IDX_DN_LOCK_REL
  {"Landing Gear",          PNL_GEAR,       SW_ON_OFF_ON,   -1,   34,   35,  &swGear},  // UP / DN (swapped with TWA Power/Low for PWM)
  {"Store CAT",             PNL_GEAR,       SW_ON_OFF,      -1,   5,   0,  NULL},   // CAT I / CAT III
  {"Horn Silencer",         PNL_GEAR,       SW_ON_OFF,      -1,   2,   0,  NULL},
  {"Landing Light",         PNL_GEAR,       SW_ON_OFF_ON,   -1,   4,   3,  &swLandingLight},  // pin4(LANDING), pin3(TAXI)

  // ---- CMDS Panel (Teensy direct) ----
  {"CMDS RWR",              PNL_CMDS,       SW_ON_OFF,      -1,  17,   0,  NULL},
  {"CMDS JMR",              PNL_CMDS,       SW_ON_OFF,      -1,  16,   0,  NULL},
  {"CMDS MWS",              PNL_CMDS,       SW_ON_OFF,      -1,  15,   0,  NULL},
  // 핀 23~20 이 O1·O2·CH·FL 입니다 — RWR·JMR·MWS(17·16·15)와 같은 내림차순.
  // 전에는 오름차순으로 적혀 있어 네 스위치의 이름이 통째로 뒤바뀌어 있었습니다.
  {"CMDS O1",               PNL_CMDS,       SW_ON_OFF,      -1,  23,   0,  NULL},
  {"CMDS O2",               PNL_CMDS,       SW_ON_OFF,      -1,  22,   0,  NULL},
  {"CMDS CH",               PNL_CMDS,       SW_ON_OFF,      -1,  21,   0,  NULL},
  {"CMDS FL",               PNL_CMDS,       SW_ON_OFF,      -1,  20,   0,  NULL},
  {"CMDS JETT",             PNL_CMDS,       SW_ON_OFF,      -1,  14,   0,  NULL},

  // ---- Alt Gear Panel (Teensy direct) ----
  {"ALT GEAR Handle",       PNL_ALT_GEAR,   SW_ON_OFF,      -1,  33,   0,  NULL},     // wire too short for other than pin 33
};

// --- Analog Button Arrays (resistor ladder, multiple buttons on 1 analog pin) ---
// Each button adds 220Ω in series → unique analogRead value per button.
// values[] = expected analogRead per button (descending order).
// TODO: calibrate values[] by reading actual analogRead with ALLOW_DEBUG = true.

// Resistor ladder: 1kΩ series chain + 4.7kΩ pulldown per ladder.
// ADC_k = 1023 × 4700 / (k × 1000 + 4700).  Calibrate with ALLOW_DEBUG = true.

const char* const twaBtnNames[] = {"TWA ACT/PWR","TWA SEARCH","TWA ALT","TWA SYS PWR"};
const int         twaBtnValues[] = {839, 711, 617, 545};       // measured (BL OFF/ON identical within ±4)

const char* const cmdsModeBtnNames[] = {"MODE 1","MODE 2","MODE 3","MODE 4","MODE 5","MODE 6","MODE 7"};
const int         cmdsModeBtnValues[] = {847, 722, 629, 558, 501, 454, 415};

const char* const cmdsPrgmBtnNames[] = {"PRGM BIT","PRGM 1","PRGM 2","PRGM 3","PRGM 4","PRGM 5","PRGM 6"};
const int         cmdsPrgmBtnValues[] = {844, 719, 625, 554, 497, 452, 413};

const AnalogBtnArrayDef analogBtnArrays[] = {
  // groupName       panel     pin  numBtn  btnNames           values
  {"TWA Buttons",    PNL_TWA,  A10, 4,      twaBtnNames,       twaBtnValues},
  {"CMDS MODE",      PNL_CMDS, A11, 7,      cmdsModeBtnNames,  cmdsModeBtnValues},
  {"CMDS PRGM",      PNL_CMDS, A12, 7,      cmdsPrgmBtnNames,  cmdsPrgmBtnValues},
};

#define NUM_ANALOG_ARRAYS (sizeof(analogBtnArrays) / sizeof(analogBtnArrays[0]))


// --- Analog Pots ---
const PotDef pots[] = {
  // name              panel       pin   axis
  {"HMCS Symbology",   PNL_HMCS,   A15,  AXIS_Z},
};

// --- LEDs ---
enum LedIdx {
  // leds[] 와 **같은 순서**여야 합니다 — 이 값이 그대로 BMS-BIOS ledBits 의
  // 비트 번호이고, tools/bmsbios_bridge.py 의 AUX_LED_MAP 과 짝입니다.
  LI_ECM, LI_ADV_ACTIVE, LI_ADV_STANDBY,                      // MISC   bit 0~2
  LI_NOSE_GEAR, LI_LEFT_GEAR, LI_RIGHT_GEAR, LI_GEAR_WARN,    // Gear   bit 3~6
  LI_TWA_SEARCH, LI_TWA_ACT, LI_TWA_LOW, LI_TWA_POWER,        // TWA    bit 7~10
  LI_CMDS_DISP_12, LI_CMDS_DISP_3, LI_CMDS_RDY,               // CMDS   bit 11~15
  LI_CMDS_NOGO, LI_CMDS_GO,
};

// pin 번호가 direct LED와 MCP LED에서 중복될 경우, MCP 쪽이 우선 적용됩니다.
// (mcpIdx >= 0 이면 MCP LED로 처리, -1 이면 direct LED로 처리)
const LedDef leds[] = {
  // name          panel      pin  mcpIdx

  // ---- MISC 패널 (MCP 0x20) — 전방 계기판 ----
  {"ECM",          PNL_MISC,  7,   0},    // MCP device 0, GPA7
  {"ADV Active",   PNL_MISC,  9,   0},   // MCP device 0, GPB0
  {"ADV Standby",  PNL_MISC,  8,   0},   // MCP device 0, GPB1

  // ---- Gear 패널 (Teensy 직결) ----
  {"Nose Gear",    PNL_GEAR,  30,  -1},
  {"Left Gear",    PNL_GEAR,  31,  -1},
  {"Right Gear",   PNL_GEAR,  32,  -1},
  {"Gear Warn",    PNL_GEAR,  27,  -1},

  // ---- TWA 패널 (Teensy 직결) — 패널 배치 SEARCH·ACT / LOW·SYS PWR ----
  {"TWA Search",   PNL_TWA,   36,  -1},
  {"TWA Act",      PNL_TWA,   37,  -1},
  {"TWA Low",      PNL_TWA,   28,  -1},  // swapped with Power
  {"TWA Power",    PNL_TWA,   29,  -1},  // swapped with Low

  // ---- CMDS 패널 (하단 SD 패드 → 15핀 FPC) ----
  {"CMDS DISP 12", PNL_CMDS,  45,  -1},   // CMD /SCK2  µSD 3, FPC  6 — 2 LEDs parallel
  {"CMDS DISP 3",  PNL_CMDS,  46,  -1},   // DAT3       µSD 2, FPC  4 — 1 LED
  {"CMDS RDY",     PNL_CMDS,  47,  -1},   // DAT2       µSD 1, FPC  2 — 2 LEDs parallel
  {"CMDS NO GO",   PNL_CMDS,  43,  -1},   // DAT0/MOSI2 µSD 7, FPC 12 — 2 LEDs parallel
  {"CMDS GO",      PNL_CMDS,  44,  -1},   // CLK /CS2   µSD 5, FPC 10 — 1 LED
};

// --- MCP23017 Devices ---
// Wire (SDA=18, SCL=19)
#define MCP_WIRE  Wire

const McpDeviceDef mcpDevices[] = {
  // name              addr
  {"MISC Panel",       0x20},
};

// --- Pedal ---
#define PEDAL_ENABLED         true
#define PEDAL_PIN_LEFT        A16
#define PEDAL_PIN_RIGHT       A17
#define PEDAL_DEADZONE        300

#if JOYSTICK_SIZE == 12
  #define PEDAL_AXIS_LBRAKE   AXIS_SL
  #define PEDAL_AXIS_RBRAKE   AXIS_SR
#else
  #define PEDAL_AXIS_LBRAKE   AXIS_Xr
  #define PEDAL_AXIS_RBRAKE   AXIS_Yr
#endif
#define PEDAL_AXIS_RUDDER     AXIS_Zr

// Brake mode activates when this switch equals this value (or both pedals > deadzone)
// Pedal brake mode: activates when *PEDAL_BRAKE_SW_REF equals PEDAL_BRAKE_SW_VALUE
// Set PEDAL_BRAKE_SW_REF to NULL to disable switch-linked brake mode
#define PEDAL_BRAKE_SW_REF    (&swLandingLight)
#define PEDAL_BRAKE_SW_VALUE  (-1)   // landing light LANDING position (pin1)

// DN LOCK REL switch index (used as modifier key for combos)
#define SW_IDX_DN_LOCK_REL    12


// ================================================================
//  End of Hardware Configuration
// ================================================================

#define NUM_SWITCHES      (sizeof(switches)      / sizeof(switches[0]))
#define NUM_MCP_DEVICES   (sizeof(mcpDevices)    / sizeof(mcpDevices[0]))
#define NUM_POTS          (sizeof(pots)          / sizeof(pots[0]))
#define NUM_LEDS          (sizeof(leds)          / sizeof(leds[0]))

// ================================================================
//  Includes
// ================================================================

#include <Keyboard.h>
#include <Wire.h>
#include <usb_dev.h>

extern volatile uint8_t usb_configuration;

// ================================================================
//  MCP23017 I/O Expander Driver
// ================================================================

// Register addresses (IOCON.BANK = 0, default)
#define MCP_IODIRA  0x00
#define MCP_IODIRB  0x01
#define MCP_GPPUA   0x0C
#define MCP_GPPUB   0x0D
#define MCP_GPIOA   0x12
#define MCP_GPIOB   0x13
#define MCP_OLATA   0x14
#define MCP_OLATB   0x15

// Per-device state
static bool     mcpConnected[NUM_MCP_DEVICES];
static uint16_t mcpPortCache[NUM_MCP_DEVICES];
static uint8_t  mcpOutputA[NUM_MCP_DEVICES];
static uint8_t  mcpOutputB[NUM_MCP_DEVICES];

void mcpWriteReg(uint8_t addr, uint8_t reg, uint8_t val) {
  MCP_WIRE.beginTransmission(addr);
  MCP_WIRE.write(reg);
  MCP_WIRE.write(val);
  MCP_WIRE.endTransmission();
}

void mcpInit(uint8_t deviceIdx) {
  uint8_t addr = mcpDevices[deviceIdx].addr;

  // Probe: check if device responds on I2C bus
  MCP_WIRE.beginTransmission(addr);
  if (MCP_WIRE.endTransmission() != 0) {
    mcpConnected[deviceIdx] = false;
    mcpPortCache[deviceIdx] = 0xFFFF;  // all pins HIGH = all switches unpressed
    Serial.printf("  [MCP@0x%02X] %s — NOT DETECTED, skipping\n", addr, mcpDevices[deviceIdx].name);
    return;
  }
  mcpConnected[deviceIdx] = true;

  // Default: all pins input with pull-up
  uint8_t dirA = 0xFF, dirB = 0xFF;
  uint8_t pullA = 0xFF, pullB = 0xFF;

  // Set LED pins as output (no pull-up)
  for (unsigned int i = 0; i < NUM_LEDS; i++) {
    if (leds[i].mcpIdx == (int8_t)deviceIdx) {
      uint8_t p = leds[i].pin;
      if (p < 8) { dirA &= ~(1 << p); pullA &= ~(1 << p); }
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
  Serial.printf("  [MCP@0x%02X] %s — OK\n", addr, mcpDevices[deviceIdx].name);
}

// Read both ports and cache (skips disconnected devices)
// On I2C failure, keeps previous cache value (all switches unchanged).
void mcpReadPorts(uint8_t deviceIdx) {
  if (!mcpConnected[deviceIdx]) return;
  uint8_t addr = mcpDevices[deviceIdx].addr;
  MCP_WIRE.beginTransmission(addr);
  MCP_WIRE.write(MCP_GPIOA);
  if (MCP_WIRE.endTransmission() != 0) {
    bool wasConnected = mcpConnected[deviceIdx];
    mcpConnected[deviceIdx] = false;
    mcpPortCache[deviceIdx] = 0xFFFF;
    if (wasConnected) writeLed(LI_GEAR_WARN, true);
    return;
  }
  if (MCP_WIRE.requestFrom(addr, (uint8_t)2) != 2) {
    bool wasConnected = mcpConnected[deviceIdx];
    mcpConnected[deviceIdx] = false;
    mcpPortCache[deviceIdx] = 0xFFFF;
    if (wasConnected) writeLed(LI_GEAR_WARN, true);
    return;
  }
  uint8_t a = MCP_WIRE.read();
  uint8_t b = MCP_WIRE.read();
  mcpPortCache[deviceIdx] = a | ((uint16_t)b << 8);
}

// Read cached pin (call mcpReadPorts first)
bool mcpReadPin(uint8_t deviceIdx, uint8_t pin) {
  return (mcpPortCache[deviceIdx] >> pin) & 1;
}

// Write a single MCP output pin (skips disconnected devices)
void mcpWritePin(uint8_t deviceIdx, uint8_t pin, bool state) {
  if (!mcpConnected[deviceIdx]) return;
  uint8_t addr = mcpDevices[deviceIdx].addr;
  if (pin < 8) {
    if (state) mcpOutputA[deviceIdx] |= (1 << pin);
    else       mcpOutputA[deviceIdx] &= ~(1 << pin);
    mcpWriteReg(addr, MCP_OLATA, mcpOutputA[deviceIdx]);
  } else {
    uint8_t bit = pin - 8;
    if (state) mcpOutputB[deviceIdx] |= (1 << bit);
    else       mcpOutputB[deviceIdx] &= ~(1 << bit);
    mcpWriteReg(addr, MCP_OLATB, mcpOutputB[deviceIdx]);
  }
}

// Unified LED write — handles both direct and MCP LEDs
#define TWA_BRIGHT_PIN A14  // pin 38 — pot for TWA LED dimming
uint8_t twaBrightness = 128;
bool twaLedState[4] = {false};  // LI_TWA_POWER ~ LI_TWA_ACT
void writeLed(uint8_t idx, bool state) {
  if (leds[idx].mcpIdx >= 0) {
    mcpWritePin(leds[idx].mcpIdx, leds[idx].pin, state);
  } else if (idx >= LI_TWA_POWER && idx <= LI_TWA_ACT) {
    twaLedState[idx - LI_TWA_POWER] = state;
    analogWrite(leds[idx].pin, state ? twaBrightness : 0);
  } else {
    digitalWrite(leds[idx].pin, state ? HIGH : LOW);
  }
}

#include "BiosHandler/DcsBiosParser.h"
#include "BiosHandler/BmsBiosParser.h"

// ================================================================
//  Protocol Auto-Detection
// ================================================================

enum Protocol { PROTO_UNKNOWN, PROTO_DCSBIOS, PROTO_BMS_BIOS };

static Protocol  currentProto     = PROTO_UNKNOWN;
static uint8_t   syncCount        = 0;       // consecutive 0x55 bytes seen
static bool      bmsBiosSync1     = false;   // true after seeing 0xAA
static uint32_t  protoDetectStart = 0;       // millis() when first byte arrived

// ================================================================
//  Global State
// ================================================================

// Runtime button mapping (auto-assigned in setup)
static uint8_t switchBtnStart[NUM_SWITCHES];
static uint8_t analogBtnStart[NUM_ANALOG_ARRAYS];
static int     totalButtons = 0;
static uint8_t prevBtnState[128];  // debug: previous button states
static bool backlightIdleOff = false;  // true when backlight is off due to idle
static bool backlightManualOff = false; // true when manually turned off via DN LOCK REL + HMCS pot
static bool backlightState = false;
static uint8_t manualBrightness = 0;

void setBacklight(bool on) {
  analogWrite(BACKLIGHT_PIN, on ? 255 : 0);
  analogWrite(MISC_BACKLIGHT_PIN, on ? 255 : 0);
  backlightState = on;
}

// Console backlight (pin 13) — online: console lighting knob
void setBacklightBrightness(uint8_t brightness) {
  analogWrite(BACKLIGHT_PIN, brightness);
  backlightState = (brightness > 0);
}

// MISC backlight (pin 12) — online: instr panel knob
void setMiscBacklightBrightness(uint8_t brightness) {
  analogWrite(MISC_BACKLIGHT_PIN, brightness);
  if (brightness > 0) backlightState = true;
}
static uint32_t lastInputTime = 0;    // millis() of last switch/button activity

// ================================================================
//  Button Count Helper
// ================================================================

int switchButtonCount(SwitchType type) {
  switch (type) {
    case SW_ON_OFF:     return 1;
    case SW_ON_OFF_NC:  return 1;
    case SW_ON_OFF_ON:  return 2;
  }
  return 1;
}

// ================================================================
//  DX 배정 순서 — dxOrder[]
// ================================================================
//
//  이 표의 **줄 순서**가 그대로 DX 번호 순서입니다. 번호는 적지 않습니다.
//  각 항목이 몇 개를 차지하는지는 그 항목의 타입에서 나옵니다
//  (SW_ON_OFF / SW_ON_OFF_NC 1, SW_ON_OFF_ON 2, 래더 numButtons).
//  주석의 xN 이 그 폭입니다.
//
//  idx 는 해당 배열의 인덱스입니다. switches[] / analogBtnArrays[] 의
//  순서는 배선 정보라 건드리지 않고, DX 순서만 여기서 따로 정합니다 —
//  핀 배치는 그대로 둔 채 번호만 바뀝니다.
//
//  ※ 줄을 옮기면 그 뒤 DX 가 전부 밀립니다. 바인딩 파일을 손으로
//    유지하지 말고 다시 생성하십시오. 현재 번호는 기동 시 시리얼
//    요약이 이 순서 그대로 찍어 줍니다.

enum DxKind { DX_SW, DX_LADDER };

struct DxEntry {
  DxKind  kind;
  uint8_t idx;
};

// Forward declarations (prevent Arduino IDE auto-prototype insertion before DxEntry)
uint8_t dxEntryCount(const DxEntry& e);
const char* dxEntryName(const DxEntry& e);
uint8_t dxEntryStart(const DxEntry& e);

const DxEntry dxOrder[] = {
  // ---- MISC — 전방 계기판, 좌측 MFD 왼쪽 ----
  {DX_SW,      0},   // RF                   x2
  {DX_SW,      1},   // Laser ARM            x1
  {DX_SW,      2},   // ALT REL              x1
  {DX_SW,      3},   // Master ARM           x2
  {DX_SW,      4},   // ADV MODE             x1
  {DX_SW,      5},   // Roll AP              x2
  {DX_SW,      6},   // Pitch AP             x2

  // ---- LANDING GEAR — 좌측 보조 콘솔 전방 ----
  {DX_SW,      7},   // EMER Jettison        x1
  {DX_SW,      8},   // Hook                 x1
  {DX_SW,      9},   // GND JETT ENABLE      x1
  {DX_SW,     10},   // BRAKES Channel       x1
  {DX_SW,     11},   // ANTI SKID            x2
  {DX_SW,     12},   // DN LOCK REL          x1
  {DX_SW,     13},   // Landing Gear         x2
  {DX_SW,     14},   // Store CAT            x1
  {DX_SW,     15},   // Horn Silencer        x1
  {DX_SW,     16},   // Landing Light        x2

  // ---- THREAT WARNING AUX ----
  {DX_LADDER,  0},   // TWA Buttons          x4

  // ---- CMDS ----
  {DX_SW,     17},   // CMDS RWR             x1
  {DX_SW,     18},   // CMDS JMR             x1
  {DX_SW,     19},   // CMDS MWS             x1
  {DX_SW,     20},   // CMDS O1              x1
  {DX_SW,     21},   // CMDS O2              x1
  {DX_SW,     22},   // CMDS CH              x1
  {DX_SW,     23},   // CMDS FL              x1
  {DX_SW,     24},   // CMDS JETT            x1
  {DX_LADDER,  2},   // CMDS PRGM            x7
  {DX_LADDER,  1},   // CMDS MODE            x7

  // ---- ALT GEAR ----
  {DX_SW,     25},   // ALT GEAR Handle      x1
};
#define NUM_DX_ORDER (sizeof(dxOrder) / sizeof(dxOrder[0]))

// 항목을 빠뜨리면 그 컨트롤의 BtnStart 가 0 으로 남아 조용히 DX 0 을
// 누르게 됩니다. 개수는 여기서, 누락/중복은 assignButtons() 에서 잡습니다.
static_assert(NUM_DX_ORDER == NUM_SWITCHES + NUM_ANALOG_ARRAYS,
              "dxOrder[] 항목 수가 하드웨어 총 개수와 맞지 않습니다");

uint8_t dxEntryCount(const DxEntry& e) {
  return (e.kind == DX_SW) ? switchButtonCount(switches[e.idx].type)
                           : analogBtnArrays[e.idx].numButtons;
}

const char* dxEntryName(const DxEntry& e) {
  return (e.kind == DX_SW) ? switches[e.idx].name
                           : analogBtnArrays[e.idx].groupName;
}

// assignButtons() 가 배정한 이 항목의 첫 DX 번호
uint8_t dxEntryStart(const DxEntry& e) {
  return (e.kind == DX_SW) ? switchBtnStart[e.idx] : analogBtnStart[e.idx];
}

// Auto-assign joystick button numbers
void assignButtons() {
  int btn = 1;

  memset(switchBtnStart, 0, sizeof(switchBtnStart));
  memset(analogBtnStart, 0, sizeof(analogBtnStart));

  for (unsigned int i = 0; i < NUM_DX_ORDER; i++) {
    const DxEntry& e = dxOrder[i];
    if (e.kind == DX_SW) switchBtnStart[e.idx] = btn;
    else                 analogBtnStart[e.idx] = btn;
    btn += dxEntryCount(e);
  }

  totalButtons = btn - 1;

  // Check joystick button limit
  int maxButtons = (JOYSTICK_SIZE == 64) ? 128 : 32;
  if (totalButtons > maxButtons) {
    Serial.printf("ERROR: %d buttons assigned, but max is %d (JOYSTICK_SIZE=%d)\n",
      totalButtons, maxButtons, JOYSTICK_SIZE);
  }

  // 개수가 맞아도 한 항목이 두 번 들어가면 다른 하나가 0 으로 남습니다
  for (unsigned int i = 0; i < NUM_SWITCHES; i++)
    if (!switchBtnStart[i])
      Serial.printf("ERROR: switches[%u] (%s) not in dxOrder[]\n", i, switches[i].name);
  for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++)
    if (!analogBtnStart[i])
      Serial.printf("ERROR: ladder %s not in dxOrder[]\n", analogBtnArrays[i].groupName);
}

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
//  Joystick Axis Helper
// ================================================================

void setJoystickAxis(JoyAxis axis, int rawValue) {
#if JOYSTICK_SIZE == 64
  int value = rawValue * 64;
#else
  int value = rawValue;
#endif
  switch (axis) {
    case AXIS_X:  Joystick.X(value);          break;
    case AXIS_Y:  Joystick.Y(value);          break;
    case AXIS_Z:  Joystick.Z(value);          break;
    case AXIS_Zr: Joystick.Zrotate(value);    break;
#if JOYSTICK_SIZE == 12
    case AXIS_SL: Joystick.sliderLeft(value);  break;
    case AXIS_SR: Joystick.sliderRight(value); break;
#endif
#if JOYSTICK_SIZE >= 64
    case AXIS_Xr: Joystick.Xrotate(value);    break;
    case AXIS_Yr: Joystick.Yrotate(value);     break;
#endif
    default: break;
  }
}

// ================================================================
//  Switch Processing
// ================================================================

// Helper: read a switch pin (direct or MCP)
inline int readSwPin(const SwitchDef& sw, uint8_t pin) {
  return (sw.mcpIdx >= 0) ? mcpReadPin(sw.mcpIdx, pin) : digitalRead(pin);
}

void processSwitches() {
  // Cache MCP ports before reading switches
  for (unsigned int d = 0; d < NUM_MCP_DEVICES; d++) {
    mcpReadPorts(d);
  }

  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    int btn = switchBtnStart[i];
    const SwitchDef& sw = switches[i];

    switch (sw.type) {
      case SW_ON_OFF:
      case SW_ON_OFF_NC: {
        int raw = readSwPin(sw, sw.pin1);
        int state = (sw.type == SW_ON_OFF_NC) ? raw : !raw;  // NC: LOW=OFF, NO: LOW=ON
        if (prevBtnState[btn] != state) {
          //if (ALLOW_DEBUG) Serial.printf("[SW] btn %d %s = %s\n", btn, sw.name, state ? "ON" : "OFF");
          prevBtnState[btn] = state;
          lastInputTime = millis();
        }
        Joystick.button(btn, state);
        if (sw.stateRef) *sw.stateRef = state;
        break;
      }

      case SW_ON_OFF_ON: {
        int s1 = readSwPin(sw, sw.pin1);
        int s2 = readSwPin(sw, sw.pin2);
        if (prevBtnState[btn] != !s1 || prevBtnState[btn + 1] != !s2) {
          //if (ALLOW_DEBUG) Serial.printf("[SW] btn %d~%d %s = %d/%d\n", btn, btn + 1, sw.name, !s1, !s2);
          prevBtnState[btn] = !s1;
          prevBtnState[btn + 1] = !s2;
          lastInputTime = millis();
        }
        Joystick.button(btn,     !s1);
        Joystick.button(btn + 1, !s2);
        if (sw.stateRef) *sw.stateRef = -(!s1) + (!s2);   // -1 = dn, 0 = center, 1 = up
        break;
      }
    }
  }
}

// ================================================================
//  Analog Button Array Processing (resistor ladder)
// ================================================================

static int analogDebugRaw[NUM_ANALOG_ARRAYS];
static int analogDebugBest[NUM_ANALOG_ARRAYS];

void processAnalogButtons() {
  for (unsigned int a = 0; a < NUM_ANALOG_ARRAYS; a++) {
    int btn = analogBtnStart[a];
    const AnalogBtnArrayDef& arr = analogBtnArrays[a];
    const int* vals = arr.values;
    int raw = 0;
    for (int s = 0; s < 8; s++) raw += analogRead(arr.pin);
    raw /= 8;

    // Nearest-value match; reject below lower boundary (last value - half gap)
    int best = -1;
    int bestDist = 32767;
    for (int i = 0; i < arr.numButtons; i++) {
      int dist = abs(raw - vals[i]);
      if (dist < bestDist) { bestDist = dist; best = i; }
    }
    // Reject: below 100 (noise floor)
    if (raw < 100) best = -1;
    for (int i = 0; i < arr.numButtons; i++) {
      Joystick.button(btn + i, (i == best));
    }

    analogDebugRaw[a] = raw;
    analogDebugBest[a] = best;
  }

  if (ALLOW_DEBUG) {
    static int lastBest[NUM_ANALOG_ARRAYS] = {-2, -2, -2};
    bool changed = (analogDebugBest[0] != lastBest[0] ||
                    analogDebugBest[1] != lastBest[1] ||
                    analogDebugBest[2] != lastBest[2]);
    if (changed) {
      lastBest[0] = analogDebugBest[0];
      lastBest[1] = analogDebugBest[1];
      lastBest[2] = analogDebugBest[2];
      // order: TWA(0), PRGM(2), MODE(1)
      char twa[32], prgm[32], mode[32];
      auto ref = [&](int a) { return analogBtnArrays[a].values[analogDebugBest[a]]; };
      if (analogDebugBest[0] >= 0) snprintf(twa,  sizeof(twa),  "btn%d(%d/%d)", analogDebugBest[0], analogDebugRaw[0], ref(0)); else snprintf(twa,  sizeof(twa),  "NONE(%d)", analogDebugRaw[0]);
      if (analogDebugBest[2] >= 0) snprintf(prgm, sizeof(prgm), "btn%d(%d/%d)", analogDebugBest[2], analogDebugRaw[2], ref(2)); else snprintf(prgm, sizeof(prgm), "NONE(%d)", analogDebugRaw[2]);
      if (analogDebugBest[1] >= 0) snprintf(mode, sizeof(mode), "btn%d(%d/%d)", analogDebugBest[1], analogDebugRaw[1], ref(1)); else snprintf(mode, sizeof(mode), "NONE(%d)", analogDebugRaw[1]);
      Serial.printf("[Ladder] TWA=%s PRGM=%s MODE=%s BL=%s\n",
        twa, prgm, mode,
        backlightState ? "ON" : "OFF");
    }
  }
}

// ================================================================
//  Pot Processing
// ================================================================

void processPots() {
  for (unsigned int i = 0; i < NUM_POTS; i++) {
    int raw = analogRead(pots[i].pin);
    setJoystickAxis(pots[i].axis, raw);
    //if (ALLOW_DEBUG) Serial.printf("[Pot] %s = %d\n", pots[i].name, raw);
  }
}

// ================================================================
//  Pedal Processing (brake + rudder synthesis)
// ================================================================

void processPedal() {
#if PEDAL_ENABLED
  static int lbMin = 300, lbMax = 750;
  static int rbMin = 300, rbMax = 750;

  int rawLb = analogRead(PEDAL_PIN_LEFT);
  int rawRb = analogRead(PEDAL_PIN_RIGHT);

  // Calibration reset: both pedals fully pressed + EMER Jettison held for 2 seconds
  {
    static uint32_t calResetStart = 0;
    bool bothPedals = (rawLb > 600 && rawRb > 600);
    bool dnLockRel = !digitalRead(switches[SW_IDX_DN_LOCK_REL].pin1);  // DN LOCK REL (active-low)
    if (bothPedals && dnLockRel) {
      if (calResetStart == 0) calResetStart = millis();
      else if (millis() - calResetStart >= 2000) {
        lbMin = rawLb; lbMax = rawLb;
        rbMin = rawRb; rbMax = rawRb;
        calResetStart = 0;
        Serial.println("[Pedal] Calibration RESET");
        welcomeCeremony();
      }
    } else {
      calResetStart = 0;
    }
  }

  // Auto calibration
  lbMin = min(lbMin, rawLb);  lbMax = max(lbMax, rawLb);
  rbMin = min(rbMin, rawRb);  rbMax = max(rbMax, rawRb);

  int lb = (lbMax > lbMin) ? (rawLb - lbMin) * 1024 / (lbMax - lbMin) : 0;
  int rb = (rbMax > rbMin) ? (rawRb - rbMin) * 1024 / (rbMax - rbMin) : 0;

  // Brake mode: linked switch active OR both pedals beyond deadzone
  bool brakeMode = (lb > PEDAL_DEADZONE && rb > PEDAL_DEADZONE);
  if (PEDAL_BRAKE_SW_REF)
    brakeMode = brakeMode || (*PEDAL_BRAKE_SW_REF == PEDAL_BRAKE_SW_VALUE);

  // if (ALLOW_DEBUG) {
  //   Serial.printf("[Pedal] raw L=%d R=%d  cal L=%d R=%d  range L=[%d,%d] R=[%d,%d]  brake=%d  rudder=%d\n",
  //     rawLb, rawRb, lb, rb, lbMin, lbMax, rbMin, rbMax, brakeMode,
  //     (1023 - lb + rb) / 2);
  // }

  setJoystickAxis(PEDAL_AXIS_LBRAKE, brakeMode ? lb : 0);
  setJoystickAxis(PEDAL_AXIS_RBRAKE, brakeMode ? rb : 0);
  setJoystickAxis(PEDAL_AXIS_RUDDER, (1023 - lb + rb) / 2);
#endif
}

// ================================================================
//  LED Control
// ================================================================

void turnOffAllLeds() {
  for (unsigned int i = 0; i < NUM_LEDS; i++) {
    writeLed(i, false);
  }
}

void welcomeCeremony() {
  setBacklight(true);             // ceremony 동안 백라이트 ON
  turnOffAllLeds();

  // Group sequential light-up: Gear → TWA → MISC
  const unsigned int groups[][4] = {
    {LI_GEAR_WARN, LI_NOSE_GEAR, LI_LEFT_GEAR, LI_RIGHT_GEAR},  // Gear
    {LI_TWA_POWER, LI_TWA_LOW, LI_TWA_SEARCH, LI_TWA_ACT},      // TWA
    {LI_ECM, LI_ADV_ACTIVE, LI_ADV_STANDBY, 0xFF},               // MISC (0xFF = unused)
  };
  const unsigned int groupSizes[] = {4, 4, 3};

  for (int g = 0; g < 3; g++) {
    for (unsigned int j = 0; j < groupSizes[g]; j++) {
      writeLed(groups[g][j], true);
      delay(80);
    }
  }

  // All on — hold briefly
  delay(300);

  // Blink all 2 times
  for (int b = 0; b < 2; b++) {
    turnOffAllLeds();
    delay(150);
    for (unsigned int i = 0; i < NUM_LEDS; i++) writeLed(i, true);
    delay(150);
  }

  turnOffAllLeds();
  setBacklight(false);            // ceremony 끝 → 백라이트 OFF (bridge/수동으로 켜짐)
}

void miscReconnectCeremony() {
  // MISC LEDs only: ECM → ADV Active → ADV Standby
  const unsigned int miscLeds[] = {LI_ECM, LI_ADV_ACTIVE, LI_ADV_STANDBY};
  for (int i = 0; i < 3; i++) {
    writeLed(miscLeds[i], true);
    delay(80);
  }
  delay(300);
  for (int b = 0; b < 2; b++) {
    for (int i = 0; i < 3; i++) writeLed(miscLeds[i], false);
    delay(150);
    for (int i = 0; i < 3; i++) writeLed(miscLeds[i], true);
    delay(150);
  }
  for (int i = 0; i < 3; i++) writeLed(miscLeds[i], false);
}


void updateLedsOffline() {
  static int blinkCounter = 0;
  const int ticksPerSecond = 1000 / LOOP_DELAY_MS;

  // Gear: trigger only on center→UP/DN transition (ignore center state)
  static int prevGearState = 0;
  static int gearWarnTicks = 0;
  static int gearDelayTicks = 0;     // countdown to first gear LED
  static bool gearTarget = false;    // target state: true=DN, false=UP
  static int gearSeqTicks = 0;       // countdown for sequential 0.5s intervals
  static int gearSeqIdx = 0;         // 0=none done, 1=nose, 2=left, 3=right (all done)
  static bool gearLedOn[3] = {false, false, false};  // nose, left, right

  const int halfSecTicks = ticksPerSecond / 2;  // 0.5s

  if (swGear != 0 && swGear != prevGearState) {
    prevGearState = swGear;
    gearWarnTicks = 5 * ticksPerSecond;   // 5 seconds
    gearDelayTicks = 2 * ticksPerSecond;  // 2 seconds delay
    gearTarget = (swGear == 1);           // DN = on, UP = off
    gearSeqIdx = 0;
    gearSeqTicks = 0;
  }
  if (gearDelayTicks > 0) {
    gearDelayTicks--;
    if (gearDelayTicks == 0) {
      // Start sequential: first gear immediately
      gearLedOn[0] = gearTarget;  // nose
      gearSeqIdx = 1;
      gearSeqTicks = halfSecTicks;
    }
  }
  if (gearSeqIdx >= 1 && gearSeqIdx < 3 && gearSeqTicks > 0) {
    gearSeqTicks--;
    if (gearSeqTicks == 0) {
      gearLedOn[gearSeqIdx] = gearTarget;  // left(1), then right(2)
      gearSeqIdx++;
      if (gearSeqIdx < 3) gearSeqTicks = halfSecTicks;
    }
  }

  for (unsigned int i = 0; i < NUM_LEDS; i++) {
    if (i >= LI_NOSE_GEAR && i <= LI_RIGHT_GEAR)
      writeLed(i, gearLedOn[i - LI_NOSE_GEAR]);
    else if (i == LI_GEAR_WARN) {
      bool mcpDisconnected = false;
      for (uint8_t d = 0; d < NUM_MCP_DEVICES; d++) { if (!mcpConnected[d]) mcpDisconnected = true; }
      writeLed(i, gearWarnTicks > 0 || mcpDisconnected);
    }
    else if (i >= LI_TWA_POWER && i <= LI_TWA_ACT)
      writeLed(i, 0);
    else
      writeLed(i, 0);
  }

  if (gearWarnTicks > 0) gearWarnTicks--;

  blinkCounter = (blinkCounter + 1) % ticksPerSecond;
}

// ================================================================
//  Protocol Detection & Serial Routing
// ================================================================

void resetProtocol() {
  currentProto = PROTO_UNKNOWN;
  syncCount    = 0;
  bmsBiosSync1 = false;
  protoDetectStart = 0;
  dcsBiosReset();
  bmsBiosReset();
  turnOffAllLeds();
  manualBrightness = 0;
  setBacklight(false);    // bridge offline → backlight off (수동 조절로 복원 가능)
  //if (ALLOW_DEBUG) Serial.println("[Proto] Reset to UNKNOWN");
}

// ================================================================
//  Host Request — DX 맵 덤프
// ================================================================
//
//  브리지가 붙지 않은 상태(PROTO_UNKNOWN)에서 "?DX" 한 줄을 받으면
//  현재 DX 배정을 기계가 읽을 수 있는 형태로 내보냅니다.
//  tools/gen_bms_setup_xml.py 가 이걸 읽어 BMS 바인딩을 만듭니다 —
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
//    #DX BEGIN device=AUX pid=0x0487 entries=29 total=51
//    #DX <첫 DX 번호> <차지하는 개수> <컨트롤 이름>
//    #DX END

#define DX_DEVICE_NAME "AUX"

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


// Read all available serial bytes, auto-detect protocol, and route.
// Returns true if any data was received (heartbeat reset).
bool detectAndRouteSerial() {
  bool received = false;

  while (Serial.available()) {
    int ch = Serial.read();
    if (ch < 0) break;
    received = true;

    switch (currentProto) {

      case PROTO_UNKNOWN: {
        // Start detection timer on first byte
        if (protoDetectStart == 0) protoDetectStart = millis();

        uint8_t b = (uint8_t)ch;
        if (b == 0x55) {
          syncCount++;
          bmsBiosSync1 = false;
          if (syncCount >= 4) {
            currentProto = PROTO_DCSBIOS;
            syncCount = 0;
            turnOffAllLeds();
            writeLed(LI_TWA_LOW, 1);
            //if (ALLOW_DEBUG) Serial.println("[Proto] Detected DCS-BIOS");
            // The 4 sync bytes are consumed; parser starts at ADDR_LOW
            dcsBiosReset();
            dcsBiosState = DCS_ADDR_LOW;  // already past sync
          }
        } else if (b == 0xAA) {
          syncCount = 0;
          bmsBiosSync1 = true;
        } else if (b == 0xBB && bmsBiosSync1) {
          // 0xAA 0xBB → BMS-BIOS protocol
          currentProto = PROTO_BMS_BIOS;
          bmsBiosSync1 = false;
          turnOffAllLeds();
          writeLed(LI_TWA_POWER, 1);
          writeLed(LI_TWA_LOW, 1);
          //if (ALLOW_DEBUG) Serial.println("[Proto] Detected BMS-BIOS");
          bmsBiosReset();
          // First frame sync already consumed; start at payload
          bbBufIdx = 0;
          bbState = BB_PAYLOAD;
        } else {
          syncCount = 0;
          bmsBiosSync1 = false;
          feedHostRequest(b);   // ASCII 요청 — 브리지가 안 붙은 동안에만
        }
        break;
      }

      case PROTO_DCSBIOS:
        processDcsBiosByte((uint8_t)ch);
        break;

      case PROTO_BMS_BIOS:
        processBmsBiosByte((uint8_t)ch);
        break;
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

  Serial.printf("..\n");

#if JOYSTICK_SIZE == 12
  Joystick.hat(-1);
#elif JOYSTICK_SIZE == 64
  Joystick.hat(1, 360);  // 360 = 중립 (val=15). -1은 NE로 인식됨
  Joystick.hat(2, 360);
  Joystick.hat(3, 360);
  Joystick.hat(4, 360);
#endif

  // Default all pins to OUTPUT (reduce power)
  for (int i = 0; i < MAX_PIN; i++)
    pinMode(i, OUTPUT);

  // Configure switch pins (direct only; MCP switches are configured by mcpInit)
  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    if (switches[i].mcpIdx >= 0) continue;
    pinMode(switches[i].pin1, INPUT_PULLUP);
    if (switches[i].type == SW_ON_OFF_ON)
      pinMode(switches[i].pin2, INPUT_PULLUP);
  }

  // Configure analog button array pins + flush ADC after OUTPUT→INPUT transition
  for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++) {
    pinMode(analogBtnArrays[i].pin, INPUT);
    for (int d = 0; d < 16; d++) analogRead(analogBtnArrays[i].pin);
  }

  // Configure pot pins
  for (unsigned int i = 0; i < NUM_POTS; i++) {
    pinMode(pots[i].pin, INPUT);
  }

  // Configure LED pins (direct only; MCP LEDs are configured by mcpInit)
  for (unsigned int i = 0; i < NUM_LEDS; i++) {
    if (leds[i].mcpIdx < 0)
      pinMode(leds[i].pin, OUTPUT);
  }

  // Initialize MCP23017 I/O expanders
  MCP_WIRE.begin();
  MCP_WIRE.setClock(100000);  // 100kHz (Standard Mode)
  for (unsigned int i = 0; i < NUM_MCP_DEVICES; i++) {
    mcpInit(i);
  }

  // Configure backlight PWM (MOSFET gate: 0=off, 255=full brightness)
  analogWriteFrequency(BACKLIGHT_PIN, 1000);       // 1kHz PWM — console backlight
  analogWriteFrequency(MISC_BACKLIGHT_PIN, 1000);  // 1kHz PWM — MISC backlight
  setBacklight(false);  // 시작 시 꺼짐 — bridge 또는 수동 조절로만 켜짐
  lastInputTime = millis();

  // Configure pedal pins
#if PEDAL_ENABLED
  pinMode(PEDAL_PIN_LEFT,  INPUT);
  pinMode(PEDAL_PIN_RIGHT, INPUT);
#endif

  // Auto-assign joystick button numbers
  assignButtons();

  // Print configuration summary
  Serial.println("=== REDKITE_F16_PANELS ===");
  for (int p = 0; p < PNL_COUNT; p++) {
    int nSw = 0, nPot = 0, nLed = 0, nAna = 0;
    for (unsigned int i = 0; i < NUM_SWITCHES;      i++) if (switches[i].panel        == p) nSw++;
    for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++) if (analogBtnArrays[i].panel == p) nAna++;
    for (unsigned int i = 0; i < NUM_POTS;          i++) if (pots[i].panel            == p) nPot++;
    for (unsigned int i = 0; i < NUM_LEDS;          i++) if (leds[i].panel            == p) nLed++;
    if (nSw + nAna + nPot + nLed == 0) continue;
    Serial.printf("  [%s] sw:%d ana:%d pot:%d led:%d\n",
      panelNames[p], nSw, nAna, nPot, nLed);
  }
  Serial.printf("  Total buttons: %d\n", totalButtons);
  Serial.println("=========================");

  // Print button mapping detail — dxOrder[] 순서 그대로 = 실제 DX 순서
  for (unsigned int i = 0; i < NUM_DX_ORDER; i++) {
    const DxEntry& e = dxOrder[i];
    uint8_t cnt = dxEntryCount(e);
    uint8_t dx  = dxEntryStart(e);
    char loc[16] = "";
    if (e.kind == DX_LADDER)             snprintf(loc, sizeof(loc), " [ladder]");
    else if (switches[e.idx].mcpIdx >= 0) snprintf(loc, sizeof(loc), " [MCP@0x%02X]",
                                                   mcpDevices[switches[e.idx].mcpIdx].addr);
    if (cnt == 1) Serial.printf("  btn %-3d     : %s%s\n", dx, dxEntryName(e), loc);
    else          Serial.printf("  btn %-3d~%-3d : %s%s\n", dx, dx + cnt - 1, dxEntryName(e), loc);
  }
  Serial.println("=========================");

  welcomeCeremony();
}

// ================================================================
//  Main Loop
// ================================================================

void loop() {
  if (isUSBSuspended()) {
    turnOffAllLeds();
    if (!backlightIdleOff) {
      setBacklight(false);
      backlightIdleOff = true;
    }
    asm("wfi");   // CPU sleep until next interrupt (USB resume, timer, etc.)
    return;       // USB resume: backlight stays off until online or switch input
  }

  // --- MCP hotplug: periodic reconnect check (every 500ms) ---
  {
    static uint32_t lastMcpCheck = 0;
    if (millis() - lastMcpCheck > 500) {
      lastMcpCheck = millis();
      for (uint8_t d = 0; d < NUM_MCP_DEVICES; d++) {
        if (!mcpConnected[d]) {
          mcpInit(d);
          if (mcpConnected[d]) {
            Serial.printf("  [MCP@0x%02X] %s — RECONNECTED\n", mcpDevices[d].addr, mcpDevices[d].name);
            writeLed(LI_GEAR_WARN, false);
            miscReconnectCeremony();
          }
        }
      }
    }
  }

  // --- TWA LED dimming from pot ---
  {
    uint8_t newBright = 255 - (analogRead(TWA_BRIGHT_PIN) >> 2);
    if (newBright != twaBrightness) {
      twaBrightness = newBright;
      for (uint8_t i = 0; i < 4; i++) {
        if (twaLedState[i])
          analogWrite(leds[LI_TWA_POWER + i].pin, twaBrightness);
      }
    }
  }

  // --- Read all inputs ---
  processSwitches();
  processAnalogButtons();
  processPots();
  processPedal();

  // --- Send joystick state ---
  Joystick.send_now();

  // --- Serial communication & LED control ---
  static int heartbeat = 0;
  const int timeoutTicks = (1000 / LOOP_DELAY_MS) * SERIAL_TIMEOUT;

  if (currentProto == PROTO_DCSBIOS) dcsBiosCheckTimeout();

  if (detectAndRouteSerial()) {
    heartbeat = 0;
  }

  if (heartbeat >= timeoutTicks) {
    // Timeout: reset protocol so we can re-detect after sim switch
    if (currentProto != PROTO_UNKNOWN) {
      resetProtocol();
    }
    updateLedsOffline();

    // Manual backlight control (offline): hold DN LOCK REL + turn HMCS Brightness pot
    bool dnLockRel = !digitalRead(switches[SW_IDX_DN_LOCK_REL].pin1);  // DN LOCK REL (active-low)
    if (dnLockRel) {
      uint8_t brightness = (1023 - analogRead(A15)) >> 2;  // 10-bit → 8-bit, reversed (HMCS Symbology pot)
      if (brightness != manualBrightness) {
        manualBrightness = brightness;
        setBacklightBrightness(manualBrightness);   // pin 13 (console)
        setMiscBacklightBrightness(manualBrightness); // pin 12 (MISC) — offline: 통합 조절
        backlightManualOff = (manualBrightness == 0);
      }
    }
  }

  ++heartbeat;
  heartbeat = min(heartbeat, timeoutTicks);

  // Backlight idle auto-off: offline + no input for IDLE_TIMEOUT_MS → turn off
  if (heartbeat >= timeoutTicks) {
    if (!backlightIdleOff && !backlightManualOff && (millis() - lastInputTime > IDLE_TIMEOUT_MS)) {
      setBacklight(false);
      backlightIdleOff = true;
    }
  }
  // Wake from idle/manual-off: bridge online → always wake; offline input → wake only if not manual-off
  if (heartbeat < timeoutTicks && (backlightIdleOff || backlightManualOff)) {
    backlightManualOff = false;
    welcomeCeremony();
    backlightIdleOff = false;
  } else if (backlightIdleOff && !backlightManualOff && millis() - lastInputTime < IDLE_TIMEOUT_MS) {
    welcomeCeremony();
    backlightIdleOff = false;
  }

  delay(LOOP_DELAY_MS);
}
