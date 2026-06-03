// ================================================================
//  REDKITE F16 ECM + ELEC Panel — Teensy 4.0 USB Joystick
// ================================================================
//
//  Standalone USB joystick for ECM and ELEC panels.
//  - ECM: OPR/OFF/STBY toggle, XMIT 1/2/3 toggle, 8-button resistor ladder
//  - ELEC: MAIN PWR OFF/BATT/MAIN toggle
//
//  Board: Teensy 4.0
//  USB Type: Serial + Keyboard + Mouse + Joystick
// ================================================================

// #include <Joystick.h>

// ================================================================
//  Build Checks
// ================================================================

#if JOYSTICK_SIZE > 12
  #warning "JOYSTICK_SIZE > 12 is unnecessary for Left Console. Consider setting it to 12 in usb_desc.h."
#endif

// ================================================================
//  Constants
// ================================================================

#define ALLOW_DEBUG       false
#define LOOP_DELAY_MS     50        // 20Hz main loop
#define SERIAL_TIMEOUT    3         // seconds before protocol reset
#define BAUDRATE          1000000

// ================================================================
//  Type Definitions
// ================================================================

enum SwitchType { SW_ON_OFF, SW_ON_OFF_ON };

struct LedDef {
  const char* name;
  uint8_t     pin;
};

struct SwitchDef {
  const char* name;
  SwitchType  type;
  uint8_t     pin1;
  uint8_t     pin2;       // only used for SW_ON_OFF_ON
};

// Resistor-ladder analog button array
struct AnalogBtnArrayDef {
  const char*        groupName;
  uint8_t            pin;          // analog input pin
  uint8_t            numButtons;
  const char* const* btnNames;
  const int*         values;       // expected analogRead per button
  int                tolerance;    // +/- matching window
};

// ================================================================
//  HARDWARE CONFIGURATION
// ================================================================

// --- Digital Switches ---
const SwitchDef switches[] = {
  // name              type           pin1  pin2
  // ECM (pin 18~13, descending)
  {"ECM OPR/STBY",     SW_ON_OFF_ON,   18,   17},   // OPR / OFF / STBY       [ECM]
  {"ECM XMIT",         SW_ON_OFF_ON,   16,   15},   // 1 / 2 / 3              [ECM]
  {"ECM BIT",           SW_ON_OFF,     14,    0},   // momentary              [ECM]
  {"ECM RESET",         SW_ON_OFF,     13,    0},   // momentary              [ECM]
  // ELEC (pin 0~2)
  {"ELEC MAIN PWR",    SW_ON_OFF_ON,    0,    1},   // BATT / OFF / MAIN      [ELEC]
  {"ELEC CAUTION RST", SW_ON_OFF,      2,    0},   // momentary              [ELEC]
};

// --- Resistor Ladder (ECM 8-button) ---                              [ECM]
// TODO: calibrate values[] by reading actual analogRead with ALLOW_DEBUG = true.
// Resistor ladder: 10kOhm series chain + 20kOhm pulldown.
// ADC_k = 1023 * 20000 / (k * 10000 + 20000)  (k=0..7)

const char* const ecmBtnNames[] = {
  "ECM 1", "ECM 2", "ECM 3", "ECM 4",
  "ECM 5", "ECM 6", "ECM FRM", "ECM SPL"
};
const int ecmBtnValues[] = {1024, 680, 509, 406, 338, 290, 253, 225};

const AnalogBtnArrayDef analogBtnArrays[] = {
  // groupName       pin   numBtn  btnNames      values          tolerance
  {"ECM Buttons",    A9,   8,      ecmBtnNames,  ecmBtnValues,  20},
};

// --- ELEC Panel LEDs (direct GPIO) ---                               [ELEC]
// TODO: assign actual Teensy 4.0 pin numbers after wiring
enum LedIdx {
  LI_FLCS_PMG, LI_MAIN_GEN, LI_STBY_GEN,
  LI_EPU_GEN, LI_EPU_PMG, LI_FLCS_RLY,
  LI_BATT_FAIL, LI_BATT_TO_FLCS,
};

const LedDef leds[] = {
  // name               pin
  {"FLCS PMG",           3},
  {"MAIN GEN",           4},
  {"STBY GEN",           5},
  {"EPU GEN",            6},
  {"EPU PMG",            7},
  {"FLCS RLY",           8},
  {"BATT FAIL",          9},
  {"BATT TO FLCS",      10},
};

#define NUM_LEDS (sizeof(leds) / sizeof(leds[0]))

// --- ECM Panel LEDs (74HC595 x4, daisy-chained, 32 outputs) ---      [ECM]
// TODO: assign actual Teensy 4.0 pin numbers after wiring
#define SR_DATA_PIN    22   // DS (serial data input)
#define SR_CLOCK_PIN   21   // SH_CP (shift register clock)
#define SR_LATCH_PIN   20   // ST_CP (storage register clock / latch)
#define SR_NUM_CHIPS   4
#define SR_NUM_OUTPUTS (SR_NUM_CHIPS * 8)  // 32

static uint8_t srData[SR_NUM_CHIPS];  // shift register output state (chip 0 = first in chain)

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

// Hardware SR index mapping: logical index → physical SR output
// (PCB wiring does not follow standard shift order)
const uint8_t srMap[SR_NUM_OUTPUTS] = {
  17, 16, 19, 18,  // ECM 1: S, A, F, T
  23, 22, 21, 20,  // ECM 2: S, A, F, T
  25, 24, 27, 26,  // ECM 3: S, A, F, T
  31, 30, 29, 28,  // ECM 4: S, A, F, T
  13, 12, 15, 14,  // ECM 5: S, A, F, T
  11, 10,  9,  8,  // ECM 6: S, A, F, T
   5,  4,  7,  6,  // ECM FRM: S, A, F, T
   3,  2,  1,  0,  // ECM SPL: S, A, F, T
};

// ================================================================
//  End of Hardware Configuration
// ================================================================

// Forward declarations for BIOS handlers
void writeElecLed(uint8_t idx, bool state);
void srWrite(uint8_t idx, bool state);
void srFlush();

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

#define NUM_SWITCHES      (sizeof(switches)      / sizeof(switches[0]))
#define NUM_ANALOG_ARRAYS (sizeof(analogBtnArrays) / sizeof(analogBtnArrays[0]))

// Runtime button number assignment
static int switchBtnStart[NUM_SWITCHES];
static int analogBtnStart[NUM_ANALOG_ARRAYS];

int switchButtonCount(SwitchType type) {
  switch (type) {
    case SW_ON_OFF:     return 1;
    case SW_ON_OFF_ON:  return 2;
  }
  return 1;
}

// ================================================================
//  74HC595 Shift Register Driver
// ================================================================

void srFlush() {
  // Shift out all chips
  digitalWrite(SR_LATCH_PIN, LOW);
  for (int i = SR_NUM_CHIPS - 1; i >= 0; i--) {
    shiftOut(SR_DATA_PIN, SR_CLOCK_PIN, LSBFIRST, srData[i]);
  }
  digitalWrite(SR_LATCH_PIN, HIGH);
}

void srWrite(uint8_t idx, bool state) {
  if (idx >= SR_NUM_OUTPUTS) return;
  uint8_t hw  = srMap[idx];
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

// Direct GPIO LEDs (ELEC panel)
void writeElecLed(uint8_t idx, bool state) {
  if (idx < NUM_LEDS) digitalWrite(leds[idx].pin, state ? HIGH : LOW);
}

// Shift register LEDs (ECM panel)
void writeEcmLed(uint8_t idx, bool state) {
  srWrite(idx, state);
}

void turnOffAllLeds() {
  for (unsigned int i = 0; i < NUM_LEDS; i++) writeElecLed(i, false);
  srClear();
}

// ================================================================
//  Welcome Ceremony (ECM LEDs)
// ================================================================

void welcomeCeremony() {
  // Sweep on: each group S→A→F→T one by one
  for (int grp = 0; grp < 8; grp++) {
    for (int col = 0; col < 4; col++) {
      srWrite(grp * 4 + col, true);
      srFlush();
      delay(40);
    }
  }
  for (unsigned int i = 0; i < NUM_LEDS; i++) {
    writeElecLed(i, true);
    delay(40);
  }
  delay(300);

  // Blink all twice
  for (int blink = 0; blink < 2; blink++) {
    turnOffAllLeds();
    delay(150);
    for (int i = 0; i < SR_NUM_OUTPUTS; i++) srWrite(i, true);
    srFlush();
    for (unsigned int i = 0; i < NUM_LEDS; i++) writeElecLed(i, true);
    delay(150);
  }

  // All off
  turnOffAllLeds();
}

// ================================================================
//  Switch Processing
// ================================================================

static uint8_t prevBtnState[64];  // previous button states for change detection

void processSwitches() {
  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    const SwitchDef& sw = switches[i];
    int btn = switchBtnStart[i];

    switch (sw.type) {
      case SW_ON_OFF: {
        int state = !digitalRead(sw.pin1);  // active-low
        if (state != prevBtnState[btn]) {
          if (ALLOW_DEBUG) Serial.printf("[SW] btn %d %s = %s\n", btn, sw.name, state ? "ON" : "OFF");
          prevBtnState[btn] = state;
        }
        Joystick.button(btn, state);
        break;
      }

      case SW_ON_OFF_ON: {
        int s1 = digitalRead(sw.pin1);
        int s2 = digitalRead(sw.pin2);
        if ((!s1) != prevBtnState[btn] || (!s2) != prevBtnState[btn + 1]) {
          if (ALLOW_DEBUG) Serial.printf("[SW] btn %d~%d %s = %d/%d\n", btn, btn+1, sw.name, !s1, !s2);
          prevBtnState[btn] = !s1;
          prevBtnState[btn + 1] = !s2;
        }
        Joystick.button(btn,     !s1);
        Joystick.button(btn + 1, !s2);
        break;
      }
    }
  }
}

// ================================================================
//  Analog Button Processing (Resistor Ladder)
// ================================================================

void processAnalogButtons() {
  for (unsigned int a = 0; a < NUM_ANALOG_ARRAYS; a++) {
    const AnalogBtnArrayDef& arr = analogBtnArrays[a];
    int raw = analogRead(arr.pin);
    int matched = -1;

    for (int b = 0; b < arr.numButtons; b++) {
      if (abs(raw - arr.values[b]) <= arr.tolerance) {
        matched = b;
        break;
      }
    }

    if (ALLOW_DEBUG) {
      static int debugCounter = 0;
      if (++debugCounter >= 20) {  // print every ~1s
        Serial.printf("[Analog] %s: raw=%d matched=%d\n", arr.groupName, raw, matched);
        debugCounter = 0;
      }
    }

    for (int b = 0; b < arr.numButtons; b++) {
      Joystick.button(analogBtnStart[a] + b, (b == matched));
    }
  }
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
          bbState = BB_PAYLOAD;
        } else {
          syncCount = 0;
          bmsBiosSync1 = false;
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

  // Configure LED pins (direct GPIO)
  for (unsigned int i = 0; i < NUM_LEDS; i++) {
    pinMode(leds[i].pin, OUTPUT);
    digitalWrite(leds[i].pin, LOW);
  }

  // Configure 74HC595 shift register pins
  pinMode(SR_DATA_PIN,  OUTPUT);
  pinMode(SR_CLOCK_PIN, OUTPUT);
  pinMode(SR_LATCH_PIN, OUTPUT);
  srClear();

  // Configure switch pins
  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    pinMode(switches[i].pin1, INPUT_PULLUP);
    if (switches[i].type == SW_ON_OFF_ON)
      pinMode(switches[i].pin2, INPUT_PULLUP);
  }

  // Configure analog pins
  for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++) {
    pinMode(analogBtnArrays[i].pin, INPUT);
  }

  // Assign joystick button numbers sequentially
  int nextBtn = 1;
  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    switchBtnStart[i] = nextBtn;
    nextBtn += switchButtonCount(switches[i].type);
  }
  for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++) {
    analogBtnStart[i] = nextBtn;
    nextBtn += analogBtnArrays[i].numButtons;
  }

  Joystick.useManualSend(true);
  memset(prevBtnState, 0, sizeof(prevBtnState));

  // Startup info
  Serial.println("=========================");
  Serial.println(" REDKITE F16 ECM+ELEC");
  Serial.println(" Teensy 4.0 Joystick");
  Serial.println("=========================");
  Serial.printf("  Switches: %d\n", NUM_SWITCHES);
  Serial.printf("  Analog arrays: %d\n", NUM_ANALOG_ARRAYS);
  Serial.printf("  Total buttons: %d\n", nextBtn - 1);

  for (unsigned int i = 0; i < NUM_SWITCHES; i++) {
    int cnt = switchButtonCount(switches[i].type);
    if (cnt == 1)
      Serial.printf("  btn %d      : %s\n", switchBtnStart[i], switches[i].name);
    else
      Serial.printf("  btn %d~%d   : %s\n", switchBtnStart[i], switchBtnStart[i] + cnt - 1, switches[i].name);
  }
  for (unsigned int i = 0; i < NUM_ANALOG_ARRAYS; i++) {
    Serial.printf("  btn %d~%d   : %s (%d-btn analog ladder)\n",
      analogBtnStart[i], analogBtnStart[i] + analogBtnArrays[i].numButtons - 1,
      analogBtnArrays[i].groupName, analogBtnArrays[i].numButtons);
  }
  Serial.println("=========================");

  welcomeCeremony();
}

// ================================================================
//  Main Loop
// ================================================================

void loop() {
  static bool wasSuspended = false;

  if (isUSBSuspended()) {
    turnOffAllLeds();
    wasSuspended = true;
    asm("wfi");   // CPU sleep until next interrupt (USB resume, timer, etc.)
    return;
  }

  if (wasSuspended) {
    wasSuspended = false;
    welcomeCeremony();
  }

  processSwitches();
  processAnalogButtons();
  Joystick.send_now();

  // --- Serial communication & LED control ---
  static int heartbeat = 0;
  static bool wasOffline = true;
  const int timeoutTicks = (1000 / LOOP_DELAY_MS) * SERIAL_TIMEOUT;

  if (currentProto == PROTO_DCSBIOS) dcsBiosCheckTimeout();

  if (detectAndRouteSerial()) {
    heartbeat = 0;
  }

  if (heartbeat >= timeoutTicks) {
    if (currentProto != PROTO_UNKNOWN) {
      resetProtocol();
    }
    wasOffline = true;
  }

  // Bridge online: welcome ceremony on offline → online transition
  if (heartbeat < timeoutTicks && wasOffline) {
    wasOffline = false;
    welcomeCeremony();
  }

  ++heartbeat;
  heartbeat = min(heartbeat, timeoutTicks);

  // Flush shift register (ECM LEDs)
  srFlush();

  delay(LOOP_DELAY_MS);
}
