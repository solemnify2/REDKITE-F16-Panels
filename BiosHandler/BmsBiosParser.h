/*
  BmsBiosParser.h — BMS-BIOS binary frame parser for Teensy

  BMS-BIOS protocol (from bmsbios_bridge.py):
    Sync:     0xAA 0xBB          (2 bytes)
    ledBits:  uint32 LE          (bits 0-8 for ELEC leds[], bits 16-23 reserved for ECM SR)
    srData:   uint8[4]           (ECM shift register raw data, 32 outputs)
    checksum: XOR of 8 payload bytes
    Total: 12 bytes per frame

  The bridge reads Falcon BMS shared memory (lightBits/lightBits2/lightBits3)
  and packs LED states into the frame.
*/

#ifndef BMSBIOS_PARSER_H
#define BMSBIOS_PARSER_H

// ================================================================
//  Protocol Constants
// ================================================================

#define BB_FRAME_PAYLOAD  8   // 4 bytes (ledBits) + 4 bytes (srData)

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

static void bmsBiosApply() {
  uint32_t ledBits = bbBuf[0] | ((uint32_t)bbBuf[1] << 8) |
                     ((uint32_t)bbBuf[2] << 16) | ((uint32_t)bbBuf[3] << 24);

  // ELEC panel direct GPIO LEDs (bits 0-8)
  for (unsigned int i = 0; i < NUM_LEDS; i++) {
    writeElecLed(i, (ledBits >> i) & 1);
  }

  // ECM panel shift register LEDs (32 bits in logical order)
  uint32_t ecmBits = bbBuf[4] | ((uint32_t)bbBuf[5] << 8) |
                     ((uint32_t)bbBuf[6] << 16) | ((uint32_t)bbBuf[7] << 24);
  for (int i = 0; i < SR_NUM_OUTPUTS; i++) {
    srWrite(i, (ecmBits >> i) & 1);
  }
  srFlush();
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
