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
#define BUFFERSIZE    1024
#define MAX_PIN       55        // Teensy 4.1 max digital pin
#define LOOP_DELAY_MS 50
#define F4TS_TIMEOUT  6         // F4TS heartbeat timeout in seconds


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
  PNL_ECM,        // Electronic Countermeasures (left console)
  PNL_ELEC,       // Electrical panel (left console)
  PNL_EXT_LIGHT,  // External Lighting panel (left console)
  PNL_ICP,        // ICP / Instrument panel area
  PNL_COUNT
};

const char* const panelNames[] = {
  "Standalone", "MISC", "Gear", "AltGear", "CMDS", "TWA", "ECM", "ELEC", "ExtLight", "ICP"
};

struct SwitchDef {
  const char* name;
  Panel       panel;
  SwitchType  type;
  uint8_t     pin1;
  uint8_t     pin2;       // only used for SW_ON_OFF_ON
  int*        stateRef;   // if non-NULL, switch state is written here
  // Button count: SW_ON_OFF=1, SW_ON_OFF_ON=2
};

struct RotaryDef {
  const char*    name;
  Panel          panel;
  uint8_t        numPos;     // number of positions mapped to joystick buttons
  uint8_t        numPins;    // number of physical pins (>= numPos)
  const uint8_t* pins;
};

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
  // name                   panel           type          pin1 pin2  stateRef

  // ---- Standalone ----
  {"Eject",                 PNL_NONE,       SW_ON_OFF,       0,   0,  NULL},

  // ---- Gear Panel (left aux console) ----
  {"EMER Jettison",         PNL_GEAR,       SW_ON_OFF,       1,   0,  NULL},
  {"Store CAT",             PNL_GEAR,       SW_ON_OFF,      2,   0,  NULL},   // CAT I / CAT III
  {"Horn Silencer",         PNL_GEAR,       SW_ON_OFF,       3,   0,  NULL},
  {"Landing Light",         PNL_GEAR,       SW_ON_OFF_ON,  4,   5,  &swLandingLight},
  {"Hook",                  PNL_GEAR,       SW_ON_OFF,      6,   0,  NULL},   // Up / Down
  {"Landing Gear",          PNL_GEAR,       SW_ON_OFF,      7,   0,  &swGear},
  // {"DN LOCK REL",           PNL_GEAR,       SW_ON_OFF,       0,   0,  NULL},   // TODO: assign pin
  // {"GND JETT ENABLE",       PNL_GEAR,       SW_ON_OFF,      0,   0,  NULL},   // ENABLE / OFF — TODO: assign pin
  // {"ANTI SKID",             PNL_GEAR,       SW_ON_OFF_ON,  0,   0,  NULL},   // PARKING BRAKE / ANTI SKID / OFF — TODO: assign pin
  // {"BRAKES Channel",        PNL_GEAR,       SW_ON_OFF,      0,   0,  NULL},   // CHAN 1 / CHAN 2 — TODO: assign pin

  // ---- Alt Gear Panel (left aux console) ----
  // {"ALT GEAR Handle",       PNL_ALT_GEAR,   SW_ON_OFF,       0,   0,  NULL},   // TODO: assign pin
  // {"ALT GEAR Reset",        PNL_ALT_GEAR,   SW_ON_OFF,       0,   0,  NULL},   // TODO: assign pin

  // ---- MISC Panel (center console, left of left MFD) — commented out ----
  {"Laser ARM",             PNL_MISC,       SW_ON_OFF,     28,   0,  NULL},
  {"RF",                    PNL_MISC,       SW_ON_OFF_ON, 29,  30,  NULL},
  {"Master ARM",            PNL_MISC,       SW_ON_OFF_ON, 31,  32,  NULL},
  {"Pitch AP",              PNL_MISC,       SW_ON_OFF_ON, 33,  34,  NULL},
  {"Roll AP",               PNL_MISC,       SW_ON_OFF_ON, 35,  36,  NULL},
  // {"ALT REL",               PNL_MISC,       SW_ON_OFF,       0,   0,  NULL},
  // {"ADV MODE",              PNL_MISC,       SW_ON_OFF,       0,   0,  NULL},

  // ---- EXT LIGHTING Panel (left console) — commented out ----
  {"Fuselage Light",        PNL_EXT_LIGHT,  SW_ON_OFF_ON, 20,  21,  NULL},
  {"Wing/Tail Light",       PNL_EXT_LIGHT,  SW_ON_OFF_ON, 22,  23,  NULL},

  // ---- CMDS Panel (left aux console) — commented out ----
  // {"CMDS RWR",              PNL_CMDS,       SW_ON_OFF,      0,   0,  NULL},
  // {"CMDS JMR",              PNL_CMDS,       SW_ON_OFF,      0,   0,  NULL},
  // {"CMDS MWS",              PNL_CMDS,       SW_ON_OFF,      0,   0,  NULL},
  // {"CMDS O1",               PNL_CMDS,       SW_ON_OFF,      0,   0,  NULL},
  // {"CMDS O2",               PNL_CMDS,       SW_ON_OFF,      0,   0,  NULL},
  // {"CMDS CH",               PNL_CMDS,       SW_ON_OFF,      0,   0,  NULL},
  // {"CMDS FL",               PNL_CMDS,       SW_ON_OFF,      0,   0,  NULL},
  // {"CMDS JETT",             PNL_CMDS,       SW_ON_OFF,      0,   0,  NULL},

  // ---- ECM Panel (left console) ----
  // {"ECM OPR",               PNL_ECM,        SW_ON_OFF_ON,  0,   0,  NULL},   // OPR / STBY / OFF — TODO: assign pin
  // {"ECM XMIT",              PNL_ECM,        SW_ON_OFF_ON,  0,   0,  NULL},   // 1 / 2 / 3 — TODO: assign pin
  // {"ECM RESET",             PNL_ECM,        SW_ON_OFF,       0,   0,  NULL},
  // {"ECM BIT",               PNL_ECM,        SW_ON_OFF,       0,   0,  NULL},
  // ECM 1~5, BLANK, FRM, SPL → moved to analogBtnArrays[] (resistor ladder)

  // ---- ELEC Panel (left console) ----
  // {"MAIN PWR",              PNL_ELEC,       SW_ON_OFF_ON,  0,   0,  NULL},   // MAIN PWR / BATT / OFF — TODO: assign pin
  // {"ELEC CAUTION RESET",    PNL_ELEC,       SW_ON_OFF,       0,   0,  NULL},
};

// --- Rotary Switches ---
// Define pin array separately, then reference it. Order = read order.
const uint8_t cmdsPrgmPins[] = {0, 0, 0, 0, 0};                          // TODO: assign pins
const uint8_t cmdsModePins[] = {16, 15, 14, 13, 12, 19 , 18, 17};                               // TODO: assign pins

const RotaryDef rotaries[] = {
  // name           panel      numPos numPins  pins
  // {"CMDS PRGM",    PNL_CMDS,  5,     5,       cmdsPrgmPins},   // BIT / 1 / 2 / 3 / 4
  {"CMDS MODE",    PNL_CMDS,  8,     8,       cmdsModePins},   // 8 pins, 8 mapped (원본 Mode Select과 동일)
};

// --- Analog Button Arrays (resistor ladder, multiple buttons on 1 analog pin) ---
// Each button adds 220Ω in series → unique analogRead value per button.
// values[] = expected analogRead per button. tolerance = +/- matching window.
// TODO: calibrate values[] by reading actual analogRead with ALLOW_DEBUG = true.

const char* const ecmBtnNames[] = {"ECM 1","ECM 2","ECM 3","ECM 4","ECM 5","ECM 6","ECM FRM","ECM SPL"};
const int         ecmBtnValues[] = {100, 200, 300, 400, 500, 600, 700, 800};  // TODO: calibrate

const char* const twaBtnNames[] = {"TWA SEARCH","TWA ACT/PWR","TWA ALT","TWA SYS PWR"};
const int         twaBtnValues[] = {100, 300, 500, 700};                       // TODO: calibrate

const AnalogBtnArrayDef analogBtnArrays[] = {
  // groupName       panel     pin  numBtn  btnNames      values          tolerance
//  {"ECM Buttons",    PNL_ECM,  A0,  8,      ecmBtnNames,  ecmBtnValues,  50},  // TODO: assign pin
//  {"TWA Buttons",    PNL_TWA,  A0,  4,      twaBtnNames,  twaBtnValues,  50},  // TODO: assign pin
};

#define NUM_ANALOG_ARRAYS (sizeof(analogBtnArrays) / sizeof(analogBtnArrays[0]))

// --- Analog Pots ---
const PotDef pots[] = {
  // name      panel     pin   axis
//  {"HDG",      PNL_ICP,  A15,  AXIS_X},
//  {"CRS",      PNL_ICP,  A16,  AXIS_Y},
//  {"ALT",      PNL_ICP,  A17,  AXIS_Z},
//  {"ECM DIM",  PNL_ECM,  A0,   AXIS_Zr},   // ECM brightness — TODO: assign pin & axis
};

// --- LEDs ---
enum LedIdx { LI_NOSE_GEAR, LI_LEFT_GEAR, LI_RIGHT_GEAR, LI_ECM };

const LedDef leds[] = {
  // name          panel      pin
  {"Nose Gear",    PNL_GEAR,   8},
  {"Left Gear",    PNL_GEAR,   9},
  {"Right Gear",   PNL_GEAR,  10},
  {"ECM",          PNL_MISC,  11},   // ECM indicator is on the MISC panel
};

// --- Pedal ---
#define PEDAL_ENABLED         true
#define PEDAL_PIN_LEFT        A10
#define PEDAL_PIN_RIGHT       A11
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
#define PEDAL_BRAKE_SW_VALUE  (-1)    // landing light UP position

// --- Offline LED ---
#define ECM_LED_IDX           LI_ECM

// ================================================================
//  End of Hardware Configuration
// ================================================================

#define NUM_SWITCHES  (sizeof(switches)  / sizeof(switches[0]))
#define NUM_ROTARIES  (sizeof(rotaries)  / sizeof(rotaries[0]))
#define NUM_POTS      (sizeof(pots)      / sizeof(pots[0]))
#define NUM_LEDS      (sizeof(leds)      / sizeof(leds[0]))

// ================================================================
//  Includes
// ================================================================

#include <ArduinoJson.h>
#include <Keyboard.h>
#include <usb_dev.h>

extern volatile uint8_t usb_configuration;

#include "F4TS/MemoryFree.h"
#include "F4TS/F4ToSerialCommons.h"
#include "F4TS/F4ToSerialLightBits.h"
#include "DcsBios/DcsBiosParser.h"

// ================================================================
//  Protocol Auto-Detection
// ================================================================

enum Protocol { PROTO_UNKNOWN, PROTO_F4TS, PROTO_DCSBIOS };

static Protocol  currentProto     = PROTO_UNKNOWN;
static uint8_t   syncCount        = 0;       // consecutive 0x55 bytes seen
static uint32_t  protoDetectStart = 0;       // millis() when first byte arrived

// ================================================================
//  Global State
// ================================================================

// Runtime button mapping (auto-assigned in setup)
static uint8_t switchBtnStart[NUM_SWITCHES];
static uint8_t rotaryBtnStart[NUM_ROTARIES];
static uint8_t analogBtnStart[NUM_ANALOG_ARRAYS];
static int     totalButtons = 0;

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

  for (unsigned int i = 0; i < NUM_ROTARIES; i++) {
    rotaryBtnStart[i] = btn;
    btn += rotaries[i].numPos;
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

void processSwitches() {
  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    int btn = switchBtnStart[i];

    const SwitchDef& sw = switches[i];

    switch (sw.type) {
      case SW_ON_OFF: {
        int state = !digitalRead(sw.pin1);
        Joystick.button(btn, state);
        if (sw.stateRef) *sw.stateRef = state;
        break;
      }

      case SW_ON_OFF_ON: {
        int s1 = digitalRead(sw.pin1);
        int s2 = digitalRead(sw.pin2);
        Joystick.button(btn,     !s1);
        Joystick.button(btn + 1, !s2);
        if (sw.stateRef) *sw.stateRef = -(!s1) + (!s2);   // -1 = up, 0 = center, 1 = down
        break;
      }
    }
  }
}

// ================================================================
//  Rotary Processing
// ================================================================

void processRotaries() {
  for (unsigned int r = 0; r < NUM_ROTARIES; r++) {
    int btn = rotaryBtnStart[r];

    const RotaryDef& rot = rotaries[r];
    for (int i = 0; i < rot.numPos; i++) {
      Joystick.button(btn + i, !digitalRead(rot.pins[i]));
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

    if (ALLOW_DEBUG) {
      Serial.printf("[%s] raw=%d\n", arr.groupName, raw);
    }
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
    digitalWrite(leds[i].pin, LOW);
  }

#ifdef USE_LIGHTBITS
  for (int i = 0; i < LightBitCount; i++) {
    digitalWriteFast(lightBits[i].pin, LOW);
    lightBits[i].mode = false;
  }
#endif
}

void updateLedsOffline() {
  static int blinkCounter = 0;
  const int ticksPerSecond = 1000 / LOOP_DELAY_MS;

  int gearState = swGear;

  for (unsigned int i = 0; i < NUM_LEDS; i++) {
    if ((int)i == ECM_LED_IDX)
      digitalWrite(leds[i].pin, blinkCounter / (ticksPerSecond / 2));
    else
      digitalWrite(leds[i].pin, gearState);
  }

  blinkCounter = (blinkCounter + 1) % ticksPerSecond;
}

// ================================================================
//  F4TS Serial Communication
// ================================================================

/*
int readSerialLine(int readch, char *buffer, int len) {
  static int pos = 0;
  int rpos;

  if (readch > 0) {
    switch (readch) {
      case '\n': break;
      case '\r':
        rpos = pos;
        pos = 0;
        return rpos;
      default:
        if (pos < len - 1) {
          buffer[pos++] = readch;
          buffer[pos] = 0;
        }
    }
    return 0;
  }
  return -1;
}
*/

// Process one byte through the F4TS JSON readline parser.
// Returns: >0 = complete JSON processed, 0 = partial, -1 = no data
int processF4TSByte(int ch) {
  static char buffer[BUFFERSIZE];
  int ret = readline(ch, buffer, BUFFERSIZE);

  if (ret <= 0) return ret;

  DynamicJsonDocument doc(BUFFERSIZE);
  DeserializationError error = deserializeJson(doc, buffer);
  if (error) {
    if (ALLOW_DEBUG) { Serial.print("Deserialization Error: "); Serial.println(error.c_str()); }
    return 0;
  }

  ret = 1;

#ifdef USE_MOTORS
  if (doc.containsKey("setup_stepper"))  parse_setup_command(doc["setup_stepper"]);
  if (doc.containsKey("setstep"))      { parse_setstep_command(doc["setstep"]); ret = 2; }
#endif

#ifdef USE_BCD
  if (doc.containsKey("setup_bcd") && doc.containsKey("digitOn") && doc.containsKey("digitOff"))
    parse_setup_bcd(doc);
  if (doc.containsKey("set_seg"))        { parse_set_seg_command(doc["set_seg"]); ret = 3; }
  if (doc.containsKey("destroy_all_bcd")) parse_destroy_bcd();
#endif

#ifdef USE_OLED_DISPLAY
  if (doc.containsKey("setup_display"))       parse_setup_display(doc["setup_display"]);
  else if (doc.containsKey("set_display"))  { parse_set_display(doc["set_display"]); ret = 4; }
#endif

#ifdef USE_LIGHTBITS
  if (doc.containsKey("setup_LightBit")) {
    parse_destroy_lightBits();
    parse_setup_LightBit(doc["setup_LightBit"]);
  }
  else if (doc.containsKey("set_LightBit")) { parse_set_LightBit(doc["set_LightBit"]); ret = 5; }
#endif

#ifdef USE_MATRIX
  if (doc.containsKey("setup_matrix"))        parse_setup_matrice(doc["setup_matrix"]);
  else if (doc.containsKey("destroy_matrix")) { parse_destroy_matrix(); ret = 6; }
  else if (doc.containsKey("update_matrix"))  parse_set_matrice(doc["update_matrix"]);
#endif

  if (ALLOW_DEBUG) { Serial.print("Free Memory = "); Serial.println(freeMemory()); }

  return ret;
}

// ================================================================
//  Protocol Detection & Serial Routing
// ================================================================

void resetProtocol() {
  currentProto = PROTO_UNKNOWN;
  syncCount    = 0;
  protoDetectStart = 0;
  resetReadline();
  dcsBiosReset();
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
          if (syncCount >= 4) {
            currentProto = PROTO_DCSBIOS;
            syncCount = 0;
            if (ALLOW_DEBUG) Serial.println("[Proto] Detected DCS-BIOS");
            // The 4 sync bytes are consumed; parser starts at ADDR_LOW
            dcsBiosReset();
            dcsBiosState = DCS_ADDR_LOW;  // already past sync
          }
        } else {
          syncCount = 0;
          // Printable ASCII or JSON start → F4TS
          if (b >= 0x20 && b < 0x7F) {
            currentProto = PROTO_F4TS;
            if (ALLOW_DEBUG) Serial.println("[Proto] Detected F4TS");
            // Feed this first byte to F4TS
            processF4TSByte(ch);
          }
          // else: non-printable, non-0x55 → ignore, keep detecting
        }
        break;
      }

      case PROTO_F4TS:
        processF4TSByte(ch);
        break;

      case PROTO_DCSBIOS:
        dcsBiosProcessByte((uint8_t)ch);
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

#if JOYSTICK_SIZE == 12
  Joystick.hat(-1);
#elif JOYSTICK_SIZE == 64
  Joystick.hat(0, -1);
#endif

  // Default all pins to OUTPUT (reduce power)
  for (int i = 0; i < MAX_PIN; i++)
    pinMode(i, OUTPUT);

  // Configure switch pins
  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    pinMode(switches[i].pin1, INPUT_PULLUP);
    if (switches[i].type == SW_ON_OFF_ON)
      pinMode(switches[i].pin2, INPUT_PULLUP);
  }

  // Configure rotary pins
  for (unsigned int i = 0; i < NUM_ROTARIES; i++) {
    for (int j = 0; j < rotaries[i].numPins; j++)
      pinMode(rotaries[i].pins[j], INPUT_PULLUP);
  }

  // Configure analog button array pins
  for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++) {
    pinMode(analogBtnArrays[i].pin, INPUT);
  }

  // Configure pot pins
  for (unsigned int i = 0; i < NUM_POTS; i++) {
    pinMode(pots[i].pin, INPUT);
  }

  // Configure LED pins
  for (unsigned int i = 0; i < NUM_LEDS; i++) {
    pinMode(leds[i].pin, OUTPUT);
  }

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
    int nSw = 0, nRot = 0, nPot = 0, nLed = 0, nAna = 0;
    for (unsigned int i = 0; i < NUM_SWITCHES;      i++) if (switches[i].panel        == p) nSw++;
    for (unsigned int i = 0; i < NUM_ROTARIES;      i++) if (rotaries[i].panel        == p) nRot++;
    for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++) if (analogBtnArrays[i].panel == p) nAna++;
    for (unsigned int i = 0; i < NUM_POTS;          i++) if (pots[i].panel            == p) nPot++;
    for (unsigned int i = 0; i < NUM_LEDS;          i++) if (leds[i].panel            == p) nLed++;
    if (nSw + nRot + nAna + nPot + nLed == 0) continue;
    Serial.printf("  [%s] sw:%d rot:%d ana:%d pot:%d led:%d\n",
      panelNames[p], nSw, nRot, nAna, nPot, nLed);
  }
  Serial.printf("  Total buttons: %d\n", totalButtons);
  Serial.println("=========================");

  // Print button mapping detail
  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    int cnt = switchButtonCount(switches[i].type);
    if (cnt == 1)
      Serial.printf("  btn %d      : %s\n", switchBtnStart[i], switches[i].name);
    else
      Serial.printf("  btn %d~%d   : %s\n", switchBtnStart[i], switchBtnStart[i] + cnt - 1, switches[i].name);
  }
  for (unsigned int i = 0; i < NUM_ROTARIES; i++) {
    Serial.printf("  btn %d~%d   : %s (%d-pos)\n",
      rotaryBtnStart[i], rotaryBtnStart[i] + rotaries[i].numPos - 1, rotaries[i].name, rotaries[i].numPos);
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
    asm("wfi");   // CPU sleep until next interrupt (USB resume, timer, etc.)
    return;
  }

  // --- Read all inputs ---
  processSwitches();
  processRotaries();
  processAnalogButtons();
  processPots();
  processPedal();

  // --- Send joystick state ---
  Joystick.send_now();

  // --- Serial communication & LED control ---
  static int heartbeat = 0;
  const int timeoutTicks = (1000 / LOOP_DELAY_MS) * F4TS_TIMEOUT;

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

  heartbeat = min(++heartbeat, timeoutTicks);

  delay(LOOP_DELAY_MS);
}
