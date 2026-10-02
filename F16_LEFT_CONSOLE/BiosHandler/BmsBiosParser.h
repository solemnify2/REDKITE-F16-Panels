/*
  BmsBiosParser.h — BMS-BIOS binary frame parser for Teensy

  BMS-BIOS protocol (unified, from bmsbios_bridge.py):
    Sync:     0xAA 0xBB          (2 bytes)
    ledBits:  uint32 LE          (bits 0-N for direct GPIO LEDs)
    srData:   uint32 LE          (ECM shift register, 32 outputs)
    uhfFreq:  uint32 LE          (BUP UHF frequency, kHz — FlightData2 +52)
    uhfPreset:uint8              (BUP UHF preset channel 1~20 — FlightData2 +48)
    checksum: XOR of 13 payload bytes
    Total: 16 bytes per frame

  브릿지는 모든 Teensy 장치에 같은 16바이트 프레임을 보냅니다.
  LEFT_AUX_MISC 는 ledBits 만 쓰고 나머지는 무시합니다.
  ⚠ 길이는 LEFT_AUX_MISC 의 BmsBiosParser.h 와 반드시 동일해야 합니다.
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

static void bmsBiosApply() {
  uint32_t ledBits = bbBuf[0] | ((uint32_t)bbBuf[1] << 8) |
                     ((uint32_t)bbBuf[2] << 16) | ((uint32_t)bbBuf[3] << 24);

  // ELEC panel LEDs (bits 0-7, driven via MCP23017)
  for (unsigned int i = 0; i < NUM_LEDS; i++) {
    writeElecLed(i, (ledBits >> i) & 1);
  }

  // Byte 2 (bits 16~23): backlight brightness from instrLight (0=off, 1~255=brightness).
  // LEFT_AUX_MISC uses bit 16 as on/off — 밝기 값이 들어가도 AUX 호환 유지.
  uint8_t brightness = (ledBits >> 16) & 0xFF;
  setBacklightBrightness(brightness);

  // ECM panel shift register LEDs (32 bits in logical order)
  uint32_t ecmBits = bbBuf[4] | ((uint32_t)bbBuf[5] << 8) |
                     ((uint32_t)bbBuf[6] << 16) | ((uint32_t)bbBuf[7] << 24);
  for (int i = 0; i < SR_NUM_OUTPUTS; i++) {
    srWrite(i, (ecmBits >> i) & 1);
  }
  srFlush();

  // UHF 7세그 디스플레이 — 주파수(kHz)와 프리셋 채널
#if HAS_UHF_DISPLAY
  uint32_t uhfFreq = bbBuf[8]  | ((uint32_t)bbBuf[9]  << 8) |
                     ((uint32_t)bbBuf[10] << 16) | ((uint32_t)bbBuf[11] << 24);
  displayOn(true);
  displayFrequency(uhfFreq);     // 범위를 벗어나면 드라이버가 대시를 표시
  displayChannel(bbBuf[12]);
#endif
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
