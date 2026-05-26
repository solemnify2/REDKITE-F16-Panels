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

#include <Joystick.h>

// ================================================================
//  Constants
// ================================================================

#define ALLOW_DEBUG       false
#define LOOP_DELAY_MS     50        // 20Hz main loop

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
  {"ECM OPR/STBY",     SW_ON_OFF_ON,    0,    1},   // OPR / OFF / STBY
  {"ECM XMIT",         SW_ON_OFF_ON,    2,    3},   // 1 / 2 / 3
  {"ELEC MAIN PWR",    SW_ON_OFF_ON,    4,    5},   // BATT / OFF / MAIN
};

// --- Resistor Ladder (ECM 8-button) ---
// TODO: calibrate values[] by reading actual analogRead with ALLOW_DEBUG = true.
// Resistor ladder: 1kOhm series chain + 4.7kOhm pulldown.
// ADC_k = 1023 * 4700 / (k * 1000 + 4700)

const char* const ecmBtnNames[] = {
  "ECM 1", "ECM 2", "ECM 3", "ECM 4",
  "ECM 5", "ECM 6", "ECM FRM", "ECM SPL"
};
const int ecmBtnValues[] = {843, 724, 634, 563, 506, 459, 419, 385};

const AnalogBtnArrayDef analogBtnArrays[] = {
  // groupName       pin   numBtn  btnNames      values          tolerance
  {"ECM Buttons",    A0,   8,      ecmBtnNames,  ecmBtnValues,  20},
};

// --- ELEC Panel LEDs (direct GPIO) ---
// TODO: assign actual Teensy 4.0 pin numbers after wiring
enum LedIdx {
  LI_FLCS_PMG, LI_MAIN_GEN, LI_STBY_GEN,
  LI_EPU_GEN, LI_EPU_PMG, LI_FLCS_RLY,
  LI_BATT_FAIL, LI_BATT_TO_FLCS, LI_ELEC_SYS,
};

const LedDef leds[] = {
  // name               pin
  {"FLCS PMG",           6},
  {"MAIN GEN",           7},
  {"STBY GEN",           8},
  {"EPU GEN",            9},
  {"EPU PMG",           10},
  {"FLCS RLY",          11},
  {"BATT FAIL",         15},
  {"BATT TO FLCS",      16},
  {"ELEC SYS",          17},
};

#define NUM_LEDS (sizeof(leds) / sizeof(leds[0]))

// --- ECM Panel LEDs (74HC595 x4, daisy-chained, 32 outputs) ---
// TODO: assign actual Teensy 4.0 pin numbers after wiring
#define SR_DATA_PIN    18   // SER (serial data input)
#define SR_CLOCK_PIN   19   // SRCLK (shift register clock)
#define SR_LATCH_PIN   20   // RCLK (storage register clock / latch)
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

// ================================================================
//  End of Hardware Configuration
// ================================================================

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
  // Shift out all chips (last chip first = MSB-first order)
  digitalWrite(SR_LATCH_PIN, LOW);
  for (int i = SR_NUM_CHIPS - 1; i >= 0; i--) {
    shiftOut(SR_DATA_PIN, SR_CLOCK_PIN, MSBFIRST, srData[i]);
  }
  digitalWrite(SR_LATCH_PIN, HIGH);
}

void srWrite(uint8_t idx, bool state) {
  if (idx >= SR_NUM_OUTPUTS) return;
  uint8_t chip = idx / 8;
  uint8_t bit  = idx % 8;
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
        if (!s1 != prevBtnState[btn] || !s2 != prevBtnState[btn + 1]) {
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
//  Setup
// ================================================================

void setup() {
  Serial.begin(115200);

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
}

// ================================================================
//  Main Loop
// ================================================================

void loop() {
  processSwitches();
  processAnalogButtons();
  Joystick.send_now();

  // Flush shift register (ECM LEDs) — call after any srWrite/writeEcmLed
  srFlush();

  delay(LOOP_DELAY_MS);
}
