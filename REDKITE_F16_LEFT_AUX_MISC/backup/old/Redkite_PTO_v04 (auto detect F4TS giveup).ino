/* Complete USB Joystick Example
   Teensy becomes a USB joystick with 16 or 32 buttons and 6 axis input

   You must select Joystick from the "Tools > USB Type" menu

   Pushbuttons should be connected between the digital pins and ground.
   Potentiometers should be connected to analog inputs 0 to 5.

   This example code is in the public domain.
*/

// Configure the number of buttons.  Be careful not
// to use a pin for both a digital button and analog
// axis.  The pullup resistor will interfere with
// the analog voltage.

#define F4TS        1
#define BAUDRATE    1000000 /* in bps */
#define ALLOW_DEBUG false
#define BUFFERSIZE  1024

#include <ArduinoJson.h>
#include "F4TS/MemoryFree.h"
#include "F4TS/F4ToSerialCommons.h"
#include "F4TS/F4ToSerialLightBits.h"

const int numInputs = 45;  
const int maxPins = 55;    // for Teensy 4.1

void setup() {
  int i;

  // you can print to the serial monitor while the joystick is active!
  Serial.begin(BAUDRATE);

  // configure the joystick to manual send mode.  This gives precise
  // control over when the computer receives updates, but it does
  // require you to manually call Joystick.send_now().
  Joystick.useManualSend(true);
  for (i=0; i<numInputs; i++) {
    pinMode(i, INPUT_PULLUP);   // All switch needs built-in PULLUP mode
  }

  // To reduce power consumption, unused pins and LED pins set to output mode
  for ( ; i < maxPins; i++ ) {
    pinMode(i, OUTPUT);
  }

  pinMode(8, OUTPUT);
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
  pinMode(11, OUTPUT);

  pinMode(A15, INPUT_PULLUP);
  pinMode(A16, INPUT_PULLUP);
  pinMode(A17, INPUT_PULLUP);
  
  Serial.println("Begin Redkite_PTO");
}

void loop() {

  // Max 32 output buttons
  int btn = 1;
  int i1, i2;

// Pin sequences considering ease of physical cabling
// Gear Panel
  Joystick.button(btn++, 1 - (i1= digitalRead(0)));                     // B1. Eject (PB)
  Joystick.button(btn++, 1 - (i1= digitalRead(1)));                     // B2. EMER Store Jettison (PB)

  Joystick.button(btn++, 1 - (i1 = digitalRead(2)));                    // B3. Store Config CAT I (TG)
  Joystick.button(btn++, i1);                                           // B4.              CAT III 

  Joystick.button(btn++, 1 - (i1 = digitalRead(3)));                    // B5. Horn Silencer (PB)

  Joystick.button(btn++, 1 - (i1 = digitalRead(4)));                    // B6. Light Landing (TG)
  Joystick.button(btn++, 1 - i1 - (i2 = digitalRead(5)) );              // B7.      Off
  Joystick.button(btn++, 1 - i2);                                       // B8.      Taxi

  Joystick.button(btn++, 1 - (i1 = digitalRead(6)));                    // B9. Hook Up (TG)
  Joystick.button(btn++, i1);                                           // B10.     Down

  Joystick.button(btn++, 1 - (i1 = digitalRead(7)));                    // B11. LG Up
  Joystick.button(btn++, i1);                                           // B12.     Down

  int gearSW = i1;                                                 // -1 (going down) or 1 (going up)
  static int prevGearSW, needLightBitSet = true;
  static int lightBitTimeout;

  if ( prevGearSW != gearSW ) {                                               // Gear SW changed
    needLightBitSet = true;
    prevGearSW = gearSW;  
    lightBitTimeout = 0;
  }

// Weapon, RF, A/P Panel

  Joystick.button(btn++, 1 - (i1 = digitalRead(28)));                   // B13. Laser ARM
  Joystick.button(btn++, i1);                                           // B14.       Off

  Joystick.button(btn++, 1 - (i1 = digitalRead(29)));                   // B15. RF NORM
  Joystick.button(btn++, 1 - i1 - (i2 = digitalRead(30)) );             // B16.      QUIET
  Joystick.button(btn++, 1 - i2);                                       // B17.      SILENCE

  Joystick.button(btn++, 1 - (i1 = digitalRead(31)));                   // B18. MASTER ARM
  Joystick.button(btn++, 1 - i1 - (i2 = digitalRead(32)));              // B19       OFF
  Joystick.button(btn++, 1 - i2);                                       // B20       SIM

  Joystick.button(btn++, 1 - (i1= digitalRead(33)));                    // B21. PITCH ALT HOLD
  Joystick.button(btn++, 1 - i1 - (i2= digitalRead(34)));               // B22.      A/P OFF
  Joystick.button(btn++, 1 - i2);                                       // B23.      ATT HOLD

  Joystick.button(btn++, 1 - (i1 = digitalRead(35)));                   // B24. ROLL HDG SEL
  Joystick.button(btn++, 1 - i1 - (i2= digitalRead(36)));               // B25.     ATT HOLD
  Joystick.button(btn++, 1 - i2);                                       // B26.     STRG SEL

// Light, NAV panel 

  Joystick.button(btn++, 1 - (i1= digitalRead(23)));                     // B27. WING/TAIL BRT
  Joystick.button(btn++, 1 - i1 - (i2= digitalRead(22)) );               // B28.      OFF
  Joystick.button(btn++, 1 - i2);                                        // B29.      DIM

  Joystick.button(btn++, 1 - (i1= digitalRead(21)));                     // B30. FUSELAGE  BRT
  Joystick.button(btn++, 1 - i1 - (i2= digitalRead(20)) );               // B31.           OFF
  Joystick.button(btn++, 1 - i2);                                        // B32.           DIM

  // 8 POS Rotary to Hat: "angle" is 0,45,90,135,180,225,270,315 (-1: not mapped)
  // only 7 digital pins are sufficient for 8 POS
  int angle = 0;                                                             // Hat
  angle += (1 - digitalRead(19)) * 45;				    
  angle += (1 - digitalRead(18)) * 45;            
  angle += (1 - digitalRead(17)) * 45;					  
  angle += (1 - digitalRead(16)) * 45;					  
  angle += (1 - digitalRead(15)) * 45;					  
  angle += (1 - digitalRead(14)) * 45;					  
  angle += (1 - digitalRead(13)) * 45;					  
  
  Joystick.hat(angle);

  // read 6 analog inputs and use them for the joystick axis, 0 to 1023
  Joystick.Zrotate(analogRead(A15));                                      // i38, HDG
  Joystick.sliderLeft(analogRead(A16));                                   // i37, CRS
  Joystick.sliderRight(analogRead(A17));                                  // i36, ALT

  Joystick.X(analogRead(A10));                                            // LB
  Joystick.Y(analogRead(A11));                                            // RB
  Joystick.Z(analogRead(A12));                                            // Rudder

  // Because setup configured the Joystick manual send,
  // the computer does not see any of the changes yet.
  // This send_now() transmits everything all at once.
  Joystick.send_now();

  static int activeF4TS = false;

  // F4TS for Gear, ECM LED status from F4BMS
  static char buffer[BUFFERSIZE];
  if (readline(Serial.read(), buffer, BUFFERSIZE) > 0) {
      if (!activeF4TS) {                                                 // Signal F4TS is now active
        digitalWrite(11, LOW);                                             // ECM LED is controlled by F4TS from now on...
      }
      activeF4TS = true;

      DynamicJsonDocument doc(BUFFERSIZE);
      DeserializationError error = deserializeJson(doc, buffer);
      if (error) {
          if(ALLOW_DEBUG) {
            Serial.println("Deserialization Error ");
            Serial.println(error.c_str());           
          }
          return;
      }
      
      #ifdef USE_MOTORS
      if(doc.containsKey("setup_stepper")) {
          parse_setup_command(doc["setup_stepper"]);
      }
      
      if(doc.containsKey("setstep")) {
          parse_setstep_command(doc["setstep"]);
      }
      #endif

      #ifdef USE_BCD
      if(doc.containsKey("setup_bcd") && doc.containsKey("digitOn") && doc.containsKey("digitOff")) {
          parse_setup_bcd(doc);           
      }
      if(doc.containsKey("set_seg")) {
          parse_set_seg_command(doc["set_seg"]);
      }
      if(doc.containsKey("destroy_all_bcd")) {
          parse_destroy_bcd();
      }
      #endif
      
      #ifdef USE_OLED_DISPLAY
      if(doc.containsKey("setup_display")) {
          parse_setup_display(doc["setup_display"]);
      }
      else if(doc.containsKey("set_display")){
        parse_set_display(doc["set_display"]);
      }
      #endif

      #ifdef USE_LIGHTBITS
      if(doc.containsKey("setup_LightBit")) {
          parse_destroy_lightBits();
          parse_setup_LightBit(doc["setup_LightBit"]);
      }
      else if(doc.containsKey("set_LightBit")) {
        parse_set_LightBit(doc["set_LightBit"]);

        needLightBitSet = false;                                               // F4TS updated LED status. No more gear LED simulation is needed
        lightBitTimeout = 0;
      } 
      #endif

      #ifdef USE_MATRIX
      if(doc.containsKey("setup_matrix")) {
        parse_setup_matrice(doc["setup_matrix"]);
      }
      else if(doc.containsKey("destroy_matrix")) {
        parse_destroy_matrix();
      }
      else if(doc.containsKey("update_matrix")){
        parse_set_matrice(doc["update_matrix"]);
      }
      #endif 

      if(ALLOW_DEBUG) { Serial.print("Free Memory = ");Serial.println(freeMemory()); }
  }

  if (needLightBitSet == true) {
//    if ( !activeF4TS || lightBitTimeout++ > (1000/5) * 10 ) {
    if ( !activeF4TS ) {
      // Gear toggle switch changed, but F4TS setLightbit not received within 5 second timeout
      // So, simulate Gear and ECM LED

      if (gearSW) {     
          digitalWrite(8, LOW); digitalWrite(9, LOW); digitalWrite(10, LOW); 
      } else {                                                              // going up (off almost immediately)
          digitalWrite(8, HIGH); digitalWrite(9, HIGH); digitalWrite(10, HIGH);
      }
      digitalWrite(11, HIGH);                                             // ECM LED is on always to signal F4TS inactive

      lightBitTimeout = 0;
      needLightBitSet = false;
      activeF4TS = false;                                                 // Mark F4TS is not active
    }
  }

  // a brief delay, so this runs "only" 200 times per second
  delay(5);
}

