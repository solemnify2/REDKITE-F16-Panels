/*
  BmsBiosParser.h — BMS-BIOS binary frame parser for Teensy

  BMS-BIOS protocol (from bmsbios_bridge.py):
    Sync:     0xAA 0xBB          (2 bytes)
    ledBits:  uint32 LE          (bits 0–N for leds[])
    checksum: XOR of 4 payload bytes
    Total: 7 bytes per frame

  The bridge reads Falcon BMS shared memory (lightBits/lightBits2/lightBits3)
  and packs LED states into a single uint32.
*/

#ifndef BMSBIOS_PARSER_H
#define BMSBIOS_PARSER_H

// ================================================================
//  Protocol Constants
// ================================================================

#define BB_FRAME_PAYLOAD  4   // 4 bytes (ledBits)

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

  // Bit 16: backlight from instrLight (0=off, 1=on)
  analogWrite(BACKLIGHT_PIN, (ledBits & (1 << 16)) ? 255 : 0);
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
