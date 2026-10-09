/*
  BmsBiosParser.h — BMS-BIOS binary frame parser for Teensy

  BMS-BIOS protocol (unified, from bmsbios_bridge.py):
    Sync:     0xAA 0xBB          (2 bytes)
    ledBits:  uint32 LE          (bits 0-N for leds[])
    srData:   uint32 LE          (ECM shift register, ignored on this device)
    uhfFreq:  uint32 LE          (BUP UHF frequency, ignored on this device)
    uhfPreset:uint8              (BUP UHF preset,    ignored on this device)
    checksum: XOR of 13 payload bytes
    Total: 16 bytes per frame

  The bridge sends the same unified frame to all Teensy devices.
  This device uses only ledBits; the rest is parsed but ignored.
  ⚠ 길이는 LEFT_CONSOLE 의 BmsBiosParser.h 와 반드시 동일해야 합니다.
*/

#ifndef BMSBIOS_PARSER_H
#define BMSBIOS_PARSER_H

// ================================================================
//  Protocol Constants
// ================================================================

#define BB_FRAME_PAYLOAD  13  // ledBits(4) + srData(4) + uhfFreq(4) + uhfPreset(1)

// ================================================================
//  Parser State Machine
// ================================================================

enum BmsBiosState { BB_SYNC_AA, BB_SYNC_BB, BB_PAYLOAD, BB_CHECKSUM };

static BmsBiosState bbState  = BB_SYNC_AA;
static uint8_t      bbBuf[BB_FRAME_PAYLOAD];
static uint8_t      bbBufIdx = 0;

// ================================================================
//  Reset Parser State
// ================================================================

void bmsBiosReset() {
  bbState  = BB_SYNC_AA;
  bbBufIdx = 0;
}

// ================================================================
//  Apply — write received LED bits to hardware
// ================================================================

// Forward-declared LED array and writeLed() from main .ino
static void bmsBiosApply() {
  uint32_t ledBits = bbBuf[0] | ((uint32_t)bbBuf[1] << 8) |
                     ((uint32_t)bbBuf[2] << 16) | ((uint32_t)bbBuf[3] << 24);

  for (unsigned int i = 0; i < NUM_LEDS; i++) {
    writeLed(i, (ledBits >> i) & 1);
  }

  // Byte 2 (bits 16~23): backlight brightness from instrLight (0=off, 1~255=brightness).
  uint8_t brightness = (ledBits >> 16) & 0xFF;
  setBacklightBrightness(brightness);
}

// ================================================================
//  Process One Byte
// ================================================================

void processBmsBiosByte(uint8_t b) {
  switch (bbState) {
    case BB_SYNC_AA:
      if (b == 0xAA) bbState = BB_SYNC_BB;
      break;

    case BB_SYNC_BB:
      if (b == 0xBB) { bbBufIdx = 0; bbState = BB_PAYLOAD; }
      else            bbState = BB_SYNC_AA;
      break;

    case BB_PAYLOAD:
      bbBuf[bbBufIdx++] = b;
      if (bbBufIdx >= BB_FRAME_PAYLOAD) bbState = BB_CHECKSUM;
      break;

    case BB_CHECKSUM: {
      uint8_t xor_check = 0;
      for (uint8_t i = 0; i < BB_FRAME_PAYLOAD; i++) xor_check ^= bbBuf[i];
      if (xor_check == b) bmsBiosApply();
      bbState = BB_SYNC_AA;
      break;
    }
  }
}

#endif // BMSBIOS_PARSER_H
