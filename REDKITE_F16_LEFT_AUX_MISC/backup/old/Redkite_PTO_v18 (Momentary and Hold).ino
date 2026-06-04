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

#define BAUDRATE    1000000 /* fastest speed in bps */
// #define BAUDRATE    115200 /* fastest speed in bps */

#define ALLOW_DEBUG false
#define BUFFERSIZE  1024
#define DEADZONE    300     // deadzone for systhetic brake and rudder 
#define NUMINPUT    45  
#define MAXPIN      55      // for Teensy 4.1
#define DELAY       100       // in miliseconds
#define F4TSTIMEOUT 6       // timeout in seconds for F4TS gear LED

#define tgl_hold    true       // switch_mode = false for momentary, true for hold

#include <ArduinoJson.h>                                                            // Install "Arduinojson by Benoit" with "Manage Library" Tool Menu, before compile
#include <usb_keyboard.h>

/*
#include <usb_names.h>

#undef MANUFACTURER_NAME
#undef MANUFACTURER_NAME_LEN
#undef PRODUCT_NAME
#undef PRODUCT_NAME_LEN
#define MANUFACTURER_NAME	{'R','e','d','k','i','t','e'}
#define MANUFACTURER_NAME_LEN	7
#define PRODUCT_NAME		  {'F','1','6','-','P','a','n','e','l'}
#define PRODUCT_NAME_LEN	9

struct usb_string_descriptor_struct usb_string_manufacturer_name = {
  2 + MANUFACTURER_NAME_LEN * 2,
  3, 
  MANUFACTURER_NAME
};
struct usb_string_descriptor_struct usb_string_product_name = {
  2 + PRODUCT_NAME_LEN * 2,
  3,
  PRODUCT_NAME
};
struct usb_string_descriptor_struct usb_string_serial_number = {
  12,
  3,
  { 0,0,7,0,0,0,7,0,0,7  }
};
*/

#include "F4TS/MemoryFree.h"
#include "F4TS/F4ToSerialCommons.h"
#include "F4TS/F4ToSerialLightBits.h"

void setup() {
  int i;

  // you can print to the serial monitor while the joystick is active!
  Serial.begin(BAUDRATE);

  // configure the joystick to manual send mode.  This gives precise
  // control over when the computer receives updates, but it does
  // require you to manually call Joystick.send_now().
  Joystick.useManualSend(true);

  Joystick.hat(-1);
  
  for (i=0; i<NUMINPUT; i++) {
    pinMode(i, INPUT_PULLUP);   // All switch needs built-in PULLUP mode
  }

  // To reduce power consumption, unused pins and LED pins set to output mode
  for ( ; i < MAXPIN ; i++ ) {
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

int prev[MAXPIN];

int Toggle2P(int *btn, int pin)
{
  int in = digitalRead(pin);

  if (tgl_hold) {
    Joystick.button((*btn)++, 1 - in);
  } else {
    int dx1, dx2;

    dx1 = prev[pin] == HIGH && in == LOW; 
    dx2 = prev[pin] == LOW && in == HIGH; 
    prev[pin] = in;

    Joystick.button((*btn)++, dx1);                  
    Joystick.button((*btn)++, dx2);
  }

  return in;                      // 1 for pin on (low on), o for pin off (high off)
}

int Toggle3P(int *btn, int pin1, int pin2)
{
  int i1 = digitalRead(pin1), i2 = digitalRead(pin2);

  if (tgl_hold) {
    Joystick.button((*btn)++, 1 - i1);
    Joystick.button((*btn)++, 1 - i2);          
  } else {
    int dx1, dx2, dx3;

    dx1 = prev[pin1] == HIGH && i1 == LOW; 
    dx3 = prev[pin2] == HIGH && i2 == LOW; 
    dx2 = prev[pin1] == LOW && i1 == HIGH || prev[pin2] == LOW && i2 == HIGH;

    prev[pin1] = i1;
    prev[pin2] = i2;

    Joystick.button((*btn)++, dx1);                
    Joystick.button((*btn)++, dx2);          
    Joystick.button((*btn)++, dx3);                                       
  }

  return -i1 + i2;                // -1 for pin1 on, 1 for pin2 on, 0 for both off
}

int Rotary(int *btn, int pin1, int pin2) {
  int i, in[8];
  static int prev_pos;

  // NOTE: Following ugly code is due to the bad soldering pin sequences.
  in[0] = digitalRead(pin1+4);
  in[1] = digitalRead(pin1+3);
  in[2] = digitalRead(pin1+2);
  in[3] = digitalRead(pin1+1);
  in[4] = digitalRead(pin1+0);
  in[5] = digitalRead(pin1+7);
  in[6] = digitalRead(pin1+6);
  in[7] = digitalRead(pin1+5);

  for ( i = 0 ; i < 8 ; i++ ) {
    // Serial.printf("%d ", in[i]);
    if (tgl_hold) {
      Joystick.button((*btn)++, 1 - in[i]);
    } else {
      if ( in[i] == LOW ) {
        // Joystick.hat(angle);
        if ( i < 8 && i != prev_pos ) {
          // Map POS to CTRL+SHIFT+1, 2, ... , 8
          usb_keyboard_press(KEY_1+i, KEY_LEFT_CTRL | KEY_LEFT_SHIFT);
          // usb_keyboard_press(KEY_1+i, 0);
          prev_pos = i;
          Serial.print("key = ");
          Serial.println(i+1);
        }
        break;
      }      
    }
  }

  return i;
}

int RudderPedal(int a1, int a2)
{
  // analog inputs, 0 to 1023
  static int lb_min = 1024, lb_max = 0, rb_min = 1024, rb_max = 0;
  // static int prev_rudder = 1024 / 2;

  int lb = analogRead(a1);
  int rb = analogRead(a2);

  // Min, Max Detection
  lb_min = min(lb_min, lb);
  rb_min = min(rb_min, rb);
  lb_max = max(lb_max, lb);
  rb_max = max(rb_max, rb);

  // Auto calibration with min, max
  lb = (lb - lb_min) * 1024 / (lb_max - lb_min);
  rb = (rb - rb_min) * 1024 / (rb_max - rb_min);

  // Serial.printf("%d < %d < %d, %d < %d < %d\n", lb_min, lb, lb_max, rb_min, rb, rb_max);

  if ( lb > DEADZONE && rb > DEADZONE ) {                               // if 2 pedal pressed simultaneously more than deadzone, act as left and right brake 
    Joystick.sliderLeft(lb);                                            // left brake
    Joystick.sliderRight(rb);                                           // right brake
    Joystick.Zrotate( (1023 - lb + rb) / 2 );                           // opt1) calculated rudder position while braking
    // Joystick.Zrotate( 1024 / 2 );                                    // opt2) rudder at center position while braking
 } else {                                                               // else, act as a synthetic rudder
    Joystick.sliderLeft(0);                                             // left brake
    Joystick.sliderRight(0);                                            // right brake
    Joystick.Zrotate( (1023 - lb + rb) / 2 );                           // calculated rudder position
  }

  return 1;
}

int ProcessF4TS(int gearSW)                                              // this code is from F4TS arduino code
{
  int ret;

  static char buffer[BUFFERSIZE];
  if (readline(Serial.read(), buffer, BUFFERSIZE) > 0) {
      DynamicJsonDocument doc(BUFFERSIZE);
      DeserializationError error = deserializeJson(doc, buffer);
      if (error) {
          if(ALLOW_DEBUG) {
            Serial.println("Deserialization Error ");
            Serial.println(error.c_str());           
          }
          return 0;
      }

      ret = 1;
      
      #ifdef USE_MOTORS
      if(doc.containsKey("setup_stepper")) {
          parse_setup_command(doc["setup_stepper"]);
      }
      
      if(doc.containsKey("setstep")) {
          parse_setstep_command(doc["setstep"]);
          ret = 2;
      }
      #endif

      #ifdef USE_BCD
      if(doc.containsKey("setup_bcd") && doc.containsKey("digitOn") && doc.containsKey("digitOff")) {
          parse_setup_bcd(doc);           
      }
      if(doc.containsKey("set_seg")) {
          parse_set_seg_command(doc["set_seg"]);
          ret = 3;
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
          ret = 4;
      }
      #endif

      #ifdef USE_LIGHTBITS
      if(doc.containsKey("setup_LightBit")) {
          parse_destroy_lightBits();
          parse_setup_LightBit(doc["setup_LightBit"]);
      }
      else if(doc.containsKey("set_LightBit")) {
        parse_set_LightBit(doc["set_LightBit"]);
        ret = 5;
      } 
      #endif

      #ifdef USE_MATRIX
      if(doc.containsKey("setup_matrix")) {
        parse_setup_matrice(doc["setup_matrix"]);
      }
      else if(doc.containsKey("destroy_matrix")) {
        parse_destroy_matrix();
        ret = 6;
      }
      else if(doc.containsKey("update_matrix")){
        parse_set_matrice(doc["update_matrix"]);
      }
      #endif 

      if(ALLOW_DEBUG) { Serial.print("Free Memory = ");Serial.println(freeMemory()); }

      return ret;
  }

  return 0;
}

void lightBitSet(int gearSW) 
{
  // Gear toggle switch changed, but F4TS setLightbit not received within 6 second timeout
  // So, simulate Gear LED

  digitalWrite(8, gearSW); digitalWrite(9, gearSW); digitalWrite(10, gearSW); 
  digitalWrite(11, LOW);                                                  // ECM LED is always off

  return;
}

void loop() {
  // Max 32 output buttons
  int btn = 1;
  int gearSW;

  // Pin sequences considering ease of physical cabling
  // Gear Panel
  Push(&btn, 0);                                                          // Eject 
  Push(&btn, 1);                                                          // EMER Store Jettison 
  Toggle2P(&btn, 2);                                                      // Store Config CAT I, CAT III 
  Push(&btn, 3);                                                          // Horn Silencer
  Toggle3P(&btn, 4, 5);                                                   // Light Landing, Off, Taxi
  Toggle2P(&btn, 6);                                                      // Hook Up (TG), Down
  gearSW = Toggle2P(&btn, 7);                                             // LG Up, Down

  // Weapon, RF, A/P Panel
  Toggle2P(&btn, 28);                                                     // Laser ARM on, off
  Toggle3P(&btn, 29, 30);                                                 // RF NORM, QUIET, SILENCE
  Toggle3P(&btn, 31, 32);                                                 // MASTER ARM, OFF, SIM
  Toggle3P(&btn, 33, 34);                                                 // PITCH ALT HOLD, A/P OFF, ATT HOLD
  Toggle3P(&btn, 35, 36);                                                 // ROLL HDG SEL, ATT HOLD, STRG SEL

  // Light, NAV panel 
  Toggle3P(&btn, 20, 21);                                                 // FUSELAGE  BRT, OFF, DIM
  Toggle3P(&btn, 22, 23);                                                 // WING/TAIL BRT, OFF, DIM

  // First Plan: 8 POS Rotary to Hat: "angle" is 0,45,90,135,180,225,270,315 (-1: not mapped). but failed. BMS only support hat from main stick and throttle.
  // So, 8 POS Rotary to keyboard
  Rotary(&btn, 12, 20);                                                     // Mode 0~7

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

  // static int activeF4TS = false;
  static int prevGearSW = -1, heartbeat;
  int ret;

  if ( (ret = ProcessF4TS(gearSW)) ) {                                     // something was received from F4TS
    heartbeat = 0;                                                         // F4TS is online. Reset heartbeat to 0 (DED message is received for every 1 second. DED should be set in F4TS config for correct F4TS detection)
    if (ret == 5) {                                                        // lightbitSet received
      prevGearSW = gearSW;  
    }
  } 

  if (prevGearSW != gearSW && heartbeat++ >= (1000/DELAY) * F4TSTIMEOUT ) { // Gear changed and F4TS is offline
    // set Gear LED
    lightBitSet(gearSW);

    prevGearSW = gearSW;  
  }
  heartbeat = min(heartbeat, (1000/DELAY) * F4TSTIMEOUT); // waiting count max truncate

  // a brief delay, so this runs "only" 200 times per second
  delay(DELAY);
}

