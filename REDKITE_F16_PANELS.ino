/* REDKITE_F16_PANELS
   Teensy 4.1 USB Joystick for Falcon BMS F-16 Left Console Panel

   USB Type: Keyboard + Mouse + Joystick (Tools > USB Type)

   Hardware configuration is data-driven.
   To add/remove/change hardware, edit the HARDWARE CONFIGURATION section only.
   Joystick button numbers are auto-assigned at runtime.
   To disable a panel, comment out its entries in the config arrays.
*/

// ================================================================
//  General Settings
// ================================================================

#define BAUDRATE      1000000
#define ALLOW_DEBUG   false
#define MAX_PIN       55        // Teensy 4.1 max digital pin
#define LOOP_DELAY_MS 50
#define SERIAL_TIMEOUT 6        // Serial heartbeat timeout in seconds
#define BACKLIGHT_PIN  0        // Backlight PWM (MOSFET: 0=off, 255=full)
#define IDLE_TIMEOUT_MS 30000   // offline idle timeout for backlight auto-off (30s for test)


// ================================================================
//  Type Definitions
// ================================================================

enum SwitchType { SW_ON_OFF, SW_ON_OFF_ON };

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
// Set 'values' to expected analogRead per button (ascending). 'tolerance' is +/- match window.
struct AnalogBtnArrayDef {
  const char*        groupName;    // group name for logging
  Panel              panel;
  uint8_t            pin;          // analog input pin
  uint8_t            numButtons;
  const char* const* btnNames;     // array of button names, length = numButtons
  const int*         values;       // expected analogRead per button, length = numButtons
  int                tolerance;    // +/- matching window
};

// ================================================================
//
//  >>> HARDWARE CONFIGURATION - Edit this section <<<
//
// ================================================================

// --- Switch state references ---
// Declare variables here for switches that need to be read by other logic.
// Then set stateRef in switches[] to link them.
int swLandingLight = 0;   // used by pedal brake mode
int swGear = 0;           // used by offline LED simulation

const SwitchDef switches[] = {
  // name                   panel           type         mcpIdx pin1 pin2  stateRef
  //                                                     (-1 = Teensy direct, >= 0 = MCP device index)

  // ---- MISC Panel (MCP23017 device 0, addr 0x20) ----
  // MCP pin mapping: GPA0–7 = 0–7, GPB0–7 = 8–15
  {"RF",                    PNL_MISC,       SW_ON_OFF_ON,    0,   4,   5,  NULL},   // GPA4, GPA5
  {"Laser ARM",             PNL_MISC,       SW_ON_OFF,       0,   3,   0,  NULL},   // GPA3
  {"ALT REL",               PNL_MISC,       SW_ON_OFF,       0,   2,   0,  NULL},   // GPA2
  {"Master ARM",            PNL_MISC,       SW_ON_OFF_ON,    0,   0,   1,  NULL},   // GPA0, GPA1
  {"ADV MODE",              PNL_MISC,       SW_ON_OFF,       0,   10,  0,  NULL},   // GPB2
  {"Roll AP",               PNL_MISC,       SW_ON_OFF_ON,    0,   11,  12,  NULL},  // GPB3, GPB4
  {"Pitch AP",              PNL_MISC,       SW_ON_OFF_ON,    0,   13,  14,  NULL},  // GPB5, GPB6

  // ---- Gear Panel (left aux console) ----
  {"EMER Jettison",         PNL_GEAR,       SW_ON_OFF,      -1,   10,   0,  NULL},
  {"Store CAT",             PNL_GEAR,       SW_ON_OFF,      -1,   5,   0,  NULL},   // CAT I / CAT III
  {"Horn Silencer",         PNL_GEAR,       SW_ON_OFF,      -1,   2,   0,  NULL},
  {"Landing Light",         PNL_GEAR,       SW_ON_OFF_ON,   -1,   3,   4,  &swLandingLight},
  {"Hook",                  PNL_GEAR,       SW_ON_OFF,      -1,   11,   0,  NULL},   // Up / Down
  {"Landing Gear",          PNL_GEAR,       SW_ON_OFF_ON,   -1,   28,   29,  &swGear},  // UP / DN
  {"DN LOCK REL",           PNL_GEAR,       SW_ON_OFF,      -1,   1,   0,  NULL},
  {"GND JETT ENABLE",       PNL_GEAR,       SW_ON_OFF,      -1,   9,   0,  NULL},   // ENABLE / OFF
  {"ANTI SKID",             PNL_GEAR,       SW_ON_OFF_ON,   -1,   6,  7,  NULL},   // PARKING BRAKE / ANTI SKID / OFF
  {"BRAKES Channel",        PNL_GEAR,       SW_ON_OFF,      -1,   8,   0,  NULL},   // CHAN 1 / CHAN 2

  // ---- CMDS Panel (left aux console) ----
  {"CMDS RWR",              PNL_CMDS,       SW_ON_OFF,      -1,  17,   0,  NULL},
  {"CMDS JMR",              PNL_CMDS,       SW_ON_OFF,      -1,  16,   0,  NULL},
  {"CMDS MWS",              PNL_CMDS,       SW_ON_OFF,      -1,  15,   0,  NULL},
  {"CMDS O1",               PNL_CMDS,       SW_ON_OFF,      -1,  20,   0,  NULL},
  {"CMDS O2",               PNL_CMDS,       SW_ON_OFF,      -1,  21,   0,  NULL},
  {"CMDS CH",               PNL_CMDS,       SW_ON_OFF,      -1,  22,   0,  NULL},
  {"CMDS FL",               PNL_CMDS,       SW_ON_OFF,      -1,  23,   0,  NULL},
  {"CMDS JETT",             PNL_CMDS,       SW_ON_OFF,      -1,  14,   0,  NULL},

  // ---- Alt Gear Panel (left aux console) ----
  {"ALT GEAR Handle",       PNL_ALT_GEAR,   SW_ON_OFF,      -1,  33,   0,  NULL},     // wire too short for other than pin 33
  {"ALT GEAR Reset",        PNL_ALT_GEAR,   SW_ON_OFF,      -1,  13,   0,  NULL},

};

// --- Analog Button Arrays (resistor ladder, multiple buttons on 1 analog pin) ---
// Each button adds 220Ω in series → unique analogRead value per button.
// values[] = expected analogRead per button. tolerance = +/- matching window.
// TODO: calibrate values[] by reading actual analogRead with ALLOW_DEBUG = true.

// Resistor ladder: 1kΩ series chain + 4.7kΩ pulldown per ladder.
// ADC_k = 1023 × 4700 / (k × 1000 + 4700).  Calibrate with ALLOW_DEBUG = true.

const char* const twaBtnNames[] = {"TWA SEARCH","TWA ACT/PWR","TWA ALT","TWA SYS PWR"};
const int         twaBtnValues[] = {839, 710, 615, 543};

const char* const cmdsModeBtnNames[] = {"MODE 1","MODE 2","MODE 3","MODE 4","MODE 5","MODE 6"};
const int         cmdsModeBtnValues[] = {850, 728, 637, 567, 510, 464};

const char* const cmdsPrgmBtnNames[] = {"PRGM BIT","PRGM 1","PRGM 2","PRGM 3","PRGM 4"};
const int         cmdsPrgmBtnValues[] = {848, 725, 632, 562, 506};

const AnalogBtnArrayDef analogBtnArrays[] = {
  // groupName       panel     pin  numBtn  btnNames           values              tolerance
  {"TWA Buttons",    PNL_TWA,  A10, 4,      twaBtnNames,       twaBtnValues,      30},
  {"CMDS MODE",      PNL_CMDS, A11, 6,      cmdsModeBtnNames,  cmdsModeBtnValues, 25},
  {"CMDS PRGM",      PNL_CMDS, A12, 5,      cmdsPrgmBtnNames,  cmdsPrgmBtnValues, 25},
};

#define NUM_ANALOG_ARRAYS (sizeof(analogBtnArrays) / sizeof(analogBtnArrays[0]))


// --- Analog Pots ---
const PotDef pots[] = {
  // name              panel       pin   axis
  {"HMCS Brightness",  PNL_HMCS,   A13,  AXIS_X},
  {"HMCS Contrast",    PNL_HMCS,   A14,  AXIS_Y},
  {"HMCS Symbology",   PNL_HMCS,   A15,  AXIS_Z},
};

// --- LEDs ---
enum LedIdx {
  LI_NOSE_GEAR, LI_LEFT_GEAR, LI_RIGHT_GEAR, LI_GEAR_WARN,
  LI_TWA_POWER, LI_TWA_LOW, LI_TWA_SEARCH, LI_TWA_ACT,
  LI_ECM, LI_ADV_ACTIVE, LI_ADV_STANDBY,
};

// pin 번호가 direct LED와 MCP LED에서 중복될 경우, MCP 쪽이 우선 적용됩니다.
// (mcpIdx >= 0 이면 MCP LED로 처리, -1 이면 direct LED로 처리)
const LedDef leds[] = {
  // name          panel      pin  mcpIdx
  {"Nose Gear",    PNL_GEAR,  30,  -1},
  {"Left Gear",    PNL_GEAR,  31,  -1},
  {"Right Gear",   PNL_GEAR,  32,  -1},
  {"Gear Warn",    PNL_GEAR,  27,  -1},   // alt gear wire was too short. so pin 33 is for alt gear
  {"TWA Power",    PNL_TWA,   34,  -1},
  {"TWA Low",      PNL_TWA,   35,  -1},
  {"TWA Search",   PNL_TWA,   36,  -1},
  {"TWA Act",      PNL_TWA,   37,  -1},
  {"ECM",          PNL_MISC,  7,   0},    // MCP device 0, GPA7
  {"ADV Active",   PNL_MISC,  9,   0},   // MCP device 0, GPB0
  {"ADV Standby",  PNL_MISC,  8,   0},   // MCP device 0, GPB1
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
#define PEDAL_BRAKE_SW_VALUE  (1)    // landing light UP position


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
  if (MCP_WIRE.endTransmission() != 0) return;   // write failed — keep previous cache
  if (MCP_WIRE.requestFrom(addr, (uint8_t)2) != 2) return;  // read failed — keep previous cache
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
void writeLed(uint8_t idx, bool state) {
  if (leds[idx].mcpIdx >= 0) {
    mcpWritePin(leds[idx].mcpIdx, leds[idx].pin, state);
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
static uint32_t lastInputTime = 0;    // millis() of last switch/button activity

// ================================================================
//  Button Count Helper
// ================================================================

int switchButtonCount(SwitchType type) {
  switch (type) {
    case SW_ON_OFF:     return 1;
    case SW_ON_OFF_ON:  return 2;
  }
  return 1;
}

// Auto-assign joystick button numbers
void assignButtons() {
  int btn = 1;

  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    switchBtnStart[i] = btn;
    btn += switchButtonCount(switches[i].type);
  }

  for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++) {
    analogBtnStart[i] = btn;
    btn += analogBtnArrays[i].numButtons;
  }

  totalButtons = btn - 1;

  // Check joystick button limit
  int maxButtons = (JOYSTICK_SIZE == 64) ? 128 : 32;
  if (totalButtons > maxButtons) {
    Serial.printf("ERROR: %d buttons assigned, but max is %d (JOYSTICK_SIZE=%d)\n",
      totalButtons, maxButtons, JOYSTICK_SIZE);
  }
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
      case SW_ON_OFF: {
        int state = !readSwPin(sw, sw.pin1);
        if (prevBtnState[btn] != state) {
          if (ALLOW_DEBUG) Serial.printf("[SW] btn %d %s = %s\n", btn, sw.name, state ? "ON" : "OFF");
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
          if (ALLOW_DEBUG) Serial.printf("[SW] btn %d~%d %s = %d/%d\n", btn, btn + 1, sw.name, !s1, !s2);
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

void processAnalogButtons() {
  for (unsigned int a = 0; a < NUM_ANALOG_ARRAYS; a++) {
    int btn = analogBtnStart[a];

    const AnalogBtnArrayDef& arr = analogBtnArrays[a];
    int raw = analogRead(arr.pin);

    for (int i = 0; i < arr.numButtons; i++) {
      bool matched = (raw >= arr.values[i] - arr.tolerance) &&
                     (raw <= arr.values[i] + arr.tolerance);
      Joystick.button(btn + i, matched);
    }

    if (ALLOW_DEBUG && raw > 10)
      Serial.printf("[%s] raw=%d\n", arr.groupName, raw);
  }
}

// ================================================================
//  Pot Processing
// ================================================================

void processPots() {
  for (unsigned int i = 0; i < NUM_POTS; i++) {
    setJoystickAxis(pots[i].axis, analogRead(pots[i].pin));
  }
}

// ================================================================
//  Pedal Processing (brake + rudder synthesis)
// ================================================================

void processPedal() {
#if PEDAL_ENABLED
  static int lbMin = 300, lbMax = 750;
  static int rbMin = 300, rbMax = 750;

  int lb = analogRead(PEDAL_PIN_LEFT);
  int rb = analogRead(PEDAL_PIN_RIGHT);

  // Auto calibration
  lbMin = min(lbMin, lb);  lbMax = max(lbMax, lb);
  rbMin = min(rbMin, rb);  rbMax = max(rbMax, rb);

  lb = (lb - lbMin) * 1024 / (lbMax - lbMin);
  rb = (rb - rbMin) * 1024 / (rbMax - rbMin);

  // Brake mode: linked switch active OR both pedals beyond deadzone
  bool brakeMode = (lb > PEDAL_DEADZONE && rb > PEDAL_DEADZONE);
  if (PEDAL_BRAKE_SW_REF)
    brakeMode = brakeMode || (*PEDAL_BRAKE_SW_REF == PEDAL_BRAKE_SW_VALUE);

  setJoystickAxis(PEDAL_AXIS_LBRAKE, brakeMode ? lb : 0);
  setJoystickAxis(PEDAL_AXIS_RBRAKE, brakeMode ? rb : 0);
  setJoystickAxis(PEDAL_AXIS_RUDDER, brakeMode ? (1024 / 2) : ((1023 - lb + rb) / 2));
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
  analogWrite(BACKLIGHT_PIN, 255);
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
    else if (i == LI_GEAR_WARN)
      writeLed(i, gearWarnTicks > 0);
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
  if (ALLOW_DEBUG) Serial.println("[Proto] Reset to UNKNOWN");
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
            if (ALLOW_DEBUG) Serial.println("[Proto] Detected DCS-BIOS");
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
          if (ALLOW_DEBUG) Serial.println("[Proto] Detected BMS-BIOS");
          bmsBiosReset();
          // First frame sync already consumed; start at payload
          bbBufIdx = 0;
          bbState = BB_PAYLOAD;
        } else {
          syncCount = 0;
          bmsBiosSync1 = false;
          // else: non-sync byte → ignore, keep detecting
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
  Joystick.hat(0, -1);
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

  // Configure analog button array pins
  for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++) {
    pinMode(analogBtnArrays[i].pin, INPUT);
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
  analogWriteFrequency(BACKLIGHT_PIN, 1000);  // 1kHz PWM
  analogWrite(BACKLIGHT_PIN, 255);            // Full brightness
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

  // Print button mapping detail
  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    int cnt = switchButtonCount(switches[i].type);
    if (switches[i].mcpIdx >= 0) {
      if (cnt == 1)
        Serial.printf("  btn %d      : %s [MCP@0x%02X]\n", switchBtnStart[i], switches[i].name, mcpDevices[switches[i].mcpIdx].addr);
      else
        Serial.printf("  btn %d~%d   : %s [MCP@0x%02X]\n", switchBtnStart[i], switchBtnStart[i] + cnt - 1, switches[i].name, mcpDevices[switches[i].mcpIdx].addr);
    } else {
      if (cnt == 1)
        Serial.printf("  btn %d      : %s\n", switchBtnStart[i], switches[i].name);
      else
        Serial.printf("  btn %d~%d   : %s\n", switchBtnStart[i], switchBtnStart[i] + cnt - 1, switches[i].name);
    }
  }
  for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++) {
    Serial.printf("  btn %d~%d   : %s (%d-btn analog ladder)\n",
      analogBtnStart[i], analogBtnStart[i] + analogBtnArrays[i].numButtons - 1,
      analogBtnArrays[i].groupName, analogBtnArrays[i].numButtons);
  }
  Serial.println("=========================");
}

// ================================================================
//  Main Loop
// ================================================================

void loop() {
  if (isUSBSuspended()) {
    turnOffAllLeds();
    if (!backlightIdleOff) {
      analogWrite(BACKLIGHT_PIN, 0);
      backlightIdleOff = true;
    }
    asm("wfi");   // CPU sleep until next interrupt (USB resume, timer, etc.)
    return;       // USB resume: backlight stays off until online or switch input
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

  if (detectAndRouteSerial()) {
    heartbeat = 0;
  }

  if (heartbeat >= timeoutTicks) {
    // Timeout: reset protocol so we can re-detect after sim switch
    if (currentProto != PROTO_UNKNOWN) {
      resetProtocol();
    }
    updateLedsOffline();
  }

  ++heartbeat;
  heartbeat = min(heartbeat, timeoutTicks);

  // Backlight idle auto-off: offline + no input for IDLE_TIMEOUT_MS → turn off
  if (heartbeat >= timeoutTicks) {
    if (!backlightIdleOff && (millis() - lastInputTime > IDLE_TIMEOUT_MS)) {
      analogWrite(BACKLIGHT_PIN, 0);
      backlightIdleOff = true;
    }
  }
  // Wake from idle: USB resume, switch input, or bridge online → ceremony + ON
  if (backlightIdleOff && (heartbeat < timeoutTicks || millis() - lastInputTime < IDLE_TIMEOUT_MS)) {
    welcomeCeremony();
    backlightIdleOff = false;
  }

  delay(LOOP_DELAY_MS);
}
