/* Redkite_PTO
   Teensy becomes a USB joystick with 16 or 32 buttons and 6 axis input

   You must select Keyborad.Mouse.Joystick from the "Tools > USB Type" menu

   Pushbuttons should be connected between the digital pins and ground.
   Potentiometers should be connected to analog inputs 0 to 5.

   This code is in the public domain.
*/

// Configure the number of buttons.  Be careful not
// to use a pin for both a digital button and analog
// axis.  The pullup resistor will interfere with
// the analog voltage.

#define F4TS        1
#define BAUDRATE    1000000 /* fastest speed in bps */
#define ALLOW_DEBUG false
#define BUFFERSIZE  1024

#include <ArduinoJson.h>                                                            // Install "Arduinojson by Benoit" with "Manage Library" Tool Menu, before compile
#include "F4TS/MemoryFree.h"
#include "F4TS/F4ToSerialCommons.h"
#include "F4TS/F4ToSerialLightBits.h"

const int numInputs = 45;  
const int maxPins = 55;     // for Teensy 4.1
const int deadzone = 500;    // deadzone for systhetic brake and rudder 

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

  pinMode(8, OUTPUT);         // Nose Gear LED
  pinMode(9, OUTPUT);         // Left Gear LED
  pinMode(10, OUTPUT);        // Right Gear LED
  pinMode(11, OUTPUT);        // ECM LED

  pinMode(A10, INPUT);        // Left Pedal
  pinMode(A11, INPUT);        // Right Pedal

  pinMode(A15, INPUT);        // Analog Knob1
  pinMode(A16, INPUT);        // Analog Knob2
  pinMode(A17, INPUT);        // Analog Knob3
  
  Serial.println("Begin Redkite_PTO");
}

int Push(int *btn, int pin)
{
  int i1;

  Joystick.button((*btn)++, 1 - (i1 = digitalRead(pin)));                     

  return i1;
}

int Toggle2P(int *btn, int pin)
{
  int i1;

  Joystick.button((*btn)++, 1 - (i1 = digitalRead(pin)));                  
  Joystick.button((*btn)++, i1);                                           

  return i1;                      // 1 for pin on (low on), o for pin off (high off)
}

int Toggle3P(int *btn, int pin1, int pin2)
{
  int i1, i2;

  Joystick.button((*btn)++, 1 - (i1 = digitalRead(pin1)));                
  Joystick.button((*btn)++, 1 - i1 - (i2 = digitalRead(pin2)) );          
  Joystick.button((*btn)++, 1 - i2);                                       

  return -i1 + i2;                // -1 for pin1 on, 1 for pin2 on, 0 for both off
}

int Rotary2Hat(int pin1, int pin2) {
  // only 7 digital input pins are sufficient for 8 POS
  int i, angle = 0;

  for ( i = pin1 ; i < pin2 ; i++ ) {
    angle += (1 - digitalRead(i)) * 45;					  
  }

  Joystick.hat(angle);

  return angle;
}

int RudderPedal(int a1, int a2)
{
  // analog inputs, 0 to 1023

  int lb = analogRead(a1);
  int rb = analogRead(a2);

  if ( lb > deadzone && rb > deadzone ) {                               // if 2 pedal pressed simultaneously more than deadzone, act as left and right brake 
    Joystick.sliderLeft(lb);                                            // left brake
    Joystick.sliderRight(rb);                                           // right brake
    Joystick.Zrotate(1024 / 2);                                         // rudder at center position
  } else {                                                              // else, act as a synthetic rudder
    Joystick.sliderLeft(0);                                             // left brake
    Joystick.sliderRight(0);                                            // right brake
    Joystick.Zrotate( (1023 - lb + rb) / 2 );                           // calculated rudder position
  }

  return 1;
}

void UpdateLED(int gearSW)
{
  // F4TS for Gear, ECM LED status from F4BMS
  static int activeF4TS = false;
  static int prevGearSW, needLightBitSet = true, lightBitTimeout;

  if ( prevGearSW != gearSW ) {                                            // Gear SW changed
    needLightBitSet = true;
    prevGearSW = gearSW;  
    lightBitTimeout = 0;
  }

  static char buffer[BUFFERSIZE];
  if (readline(Serial.read(), buffer, BUFFERSIZE) > 0) {
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
          // parse_set_display(doc["set_display"]);                             // DED is used as a heartbeat.  If you connect a real DED, uncomment this line
          lightBitTimeout = 0;
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

  if (needLightBitSet == true) {                                          // last gear state not set yet
    if ( !activeF4TS || lightBitTimeout++ > (1000/5) * 6 ) {              
      // Gear toggle switch changed, but F4TS setLightbit not received within 6 second timeout
      // So, simulate Gear LED

      if (gearSW) {     
          digitalWrite(8, LOW); digitalWrite(9, LOW); digitalWrite(10, LOW); 
      } else {                                                              
          digitalWrite(8, HIGH); digitalWrite(9, HIGH); digitalWrite(10, HIGH);
      }
      digitalWrite(11, LOW);                                             // ECM LED is on always off

      lightBitTimeout = 0;
      needLightBitSet = false;                                            // last gear state was set
      activeF4TS = false;                                                 // Mark F4TS is not active
    }
  }

  return;
}

void loop() {
  // Max 32 output buttons
  int btn = 1;
  int gearSW;

  // Pin sequences considering ease of physical cabling
  // Gear Panel
  Push(&btn, 0);                                                          // B1. Eject (PB)
  Push(&btn, 1);                                                          // B2. EMER Store Jettison (PB)
  Toggle2P(&btn, 2);                                                      // B3. Store Config CAT I (TG), B4.  CAT III 
  Push(&btn, 3);                                                          // B5. Horn Silencer (PB)
  Toggle3P(&btn, 4, 5);                                                   // B6. Light Landing (TG), B7. Off, B8. Taxi
  Toggle2P(&btn, 6);                                                      // B9. Hook Up (TG)
  gearSW = Toggle2P(&btn, 7);                                             // B11. LG Up, B12. Down

  // Weapon, RF, A/P Panel
  Toggle2P(&btn, 28);                                                     // B13. Laser ARM
  Toggle3P(&btn, 29, 30);                                                 // B15. RF NORM, B16. QUIET, B17. SILENCE
  Toggle3P(&btn, 31, 32);                                                 // B18. MASTER ARM, B19 OFF, B20 SIM
  Toggle3P(&btn, 33, 34);                                                 // B21. PITCH ALT HOLD, B22. A/P OFF, B23. ATT HOLD
  Toggle3P(&btn, 35, 36);                                                 // B24. ROLL HDG SEL, B25. ATT HOLD, B26. STRG SEL

  // Light, NAV panel 
  Toggle3P(&btn, 20, 21);                                                 // B30. FUSELAGE  BRT, B31. OFF, B32. DIM
  Toggle3P(&btn, 22, 23);                                                 // B27. WING/TAIL BRT, B28. OFF

  // 8 POS Rotary to Hat: "angle" is 0,45,90,135,180,225,270,315 (-1: not mapped)
  Rotary2Hat(13, 20);

  // Simulate Brake and rudder pedal with just 2 pedal
  RudderPedal(A10, A11);

  // Analog knobs
  Joystick.X(analogRead(A15));                                            // HDG knob
  Joystick.Y(analogRead(A16));                                            // CRS knob
  Joystick.Z(analogRead(A17));                                            // ALT knob

  // Because setup configured the Joystick manual send,
  // the computer does not see any of the changes yet.
  // This send_now() transmits everything all at once.
  Joystick.send_now();

  // Gear and ECM LED status from F4BMS. If not F4BMS active, just simulate it from gearSW position
  UpdateLED(gearSW);

  // a brief delay, so this runs "only" 200 times per second
  delay(5);
}

