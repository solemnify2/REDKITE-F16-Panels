/*
  DcsBiosParser.h — DCS-BIOS binary frame parser for Teensy

  DCS-BIOS protocol:
    Sync: 0x55 0x55 0x55 0x55
    Then repeating: ADDR_LOW ADDR_HIGH COUNT_LOW COUNT_HIGH DATA[count]
    Frame end marker: address=0x5555, count=0x5555

  Only output addresses (LED control) are handled here.
  Switch input is handled via USB joystick (no DCS-BIOS write needed).
*/

#ifndef DCSBIOS_PARSER_H
#define DCSBIOS_PARSER_H

// ================================================================
//  DCS-BIOS F-16C Address Map
// ================================================================
// Source: DCS-BIOS F-16C_50.json (local)

// --- ELEC Panel Caution Lights (from DCS-BIOS F-16C_50.json) ---
// Address 0x447C: FLCS PMG, MAIN GEN, STBY GEN, EPU GEN, EPU PMG, TO FLCS
#define DCSBIOS_ELEC_GRP1_ADDR     0x447C
#define DCSBIOS_FLCS_PMG_MASK      0x0200  // bit 9
#define DCSBIOS_MAIN_GEN_MASK      0x0400  // bit 10
#define DCSBIOS_STBY_GEN_MASK      0x0800  // bit 11
#define DCSBIOS_EPU_GEN_MASK       0x2000  // bit 13
#define DCSBIOS_EPU_PMG_MASK       0x4000  // bit 14
#define DCSBIOS_BATT_TO_FLCS_MASK  0x8000  // bit 15

// Address 0x447E: FLCS RLY, BATT FAIL
#define DCSBIOS_ELEC_GRP2_ADDR     0x447E
#define DCSBIOS_FLCS_RLY_MASK      0x0001  // bit 0
#define DCSBIOS_BATT_FAIL_MASK     0x0002  // bit 1

// --- ECM Panel Indicator Lights (74HC595 shift register) ---
// Address 0x4480: ECM 1 S/A/F
#define DCSBIOS_ECM_GRP1_ADDR      0x4480
#define DCSBIOS_ECM_1_S_MASK       0x2000  // bit 13
#define DCSBIOS_ECM_1_A_MASK       0x4000  // bit 14
#define DCSBIOS_ECM_1_F_MASK       0x8000  // bit 15

// Address 0x448A: ECM 1T, 2 S/A/F/T, 3 S/A/F/T, 4 S/A/F/T, 5 S/A/F
#define DCSBIOS_ECM_GRP2_ADDR      0x448A
#define DCSBIOS_ECM_1_T_MASK       0x0001  // bit 0
#define DCSBIOS_ECM_2_S_MASK       0x0002  // bit 1
#define DCSBIOS_ECM_2_A_MASK       0x0004  // bit 2
#define DCSBIOS_ECM_2_F_MASK       0x0008  // bit 3
#define DCSBIOS_ECM_2_T_MASK       0x0010  // bit 4
#define DCSBIOS_ECM_3_S_MASK       0x0020  // bit 5
#define DCSBIOS_ECM_3_A_MASK       0x0040  // bit 6
#define DCSBIOS_ECM_3_F_MASK       0x0080  // bit 7
#define DCSBIOS_ECM_3_T_MASK       0x0100  // bit 8
#define DCSBIOS_ECM_4_S_MASK       0x0200  // bit 9
#define DCSBIOS_ECM_4_A_MASK       0x0400  // bit 10
#define DCSBIOS_ECM_4_F_MASK       0x0800  // bit 11
#define DCSBIOS_ECM_4_T_MASK       0x1000  // bit 12
#define DCSBIOS_ECM_5_S_MASK       0x2000  // bit 13
#define DCSBIOS_ECM_5_A_MASK       0x4000  // bit 14
#define DCSBIOS_ECM_5_F_MASK       0x8000  // bit 15

// Address 0x448C: ECM 5T, 6 S/A/F/T, FRM S/A/F/T, SPL S/A/F/T
#define DCSBIOS_ECM_GRP3_ADDR      0x448C
#define DCSBIOS_ECM_5_T_MASK       0x0001  // bit 0
#define DCSBIOS_ECM_6_S_MASK       0x0002  // bit 1  (LIGHT_ECM_S)
#define DCSBIOS_ECM_6_A_MASK       0x0004  // bit 2  (LIGHT_ECM_A)
#define DCSBIOS_ECM_6_F_MASK       0x0008  // bit 3  (LIGHT_ECM_F)
#define DCSBIOS_ECM_6_T_MASK       0x0010  // bit 4  (LIGHT_ECM_T)
#define DCSBIOS_ECM_FRM_S_MASK     0x0020  // bit 5
#define DCSBIOS_ECM_FRM_A_MASK     0x0040  // bit 6
#define DCSBIOS_ECM_FRM_F_MASK     0x0080  // bit 7
#define DCSBIOS_ECM_FRM_T_MASK     0x0100  // bit 8
#define DCSBIOS_ECM_SPL_S_MASK     0x0200  // bit 9
#define DCSBIOS_ECM_SPL_A_MASK     0x0400  // bit 10
#define DCSBIOS_ECM_SPL_F_MASK     0x0800  // bit 11
#define DCSBIOS_ECM_SPL_T_MASK     0x1000  // bit 12

// ================================================================
//  Parser State Machine
// ================================================================

enum DcsBiosState {
  DCS_SYNC_1,
  DCS_SYNC_2,
  DCS_SYNC_3,
  DCS_SYNC_4,
  DCS_ADDR_LOW,
  DCS_ADDR_HIGH,
  DCS_COUNT_LOW,
  DCS_COUNT_HIGH,
  DCS_DATA
};

static DcsBiosState dcsBiosState = DCS_SYNC_1;
static uint16_t     dcsBiosAddr  = 0;
static uint16_t     dcsBiosCount = 0;
static uint16_t     dcsBiosSkip  = 0;
static uint8_t      dcsBiosDataBuf[2];
static bool         dcsBiosCapture = false;
static uint8_t      dcsBiosSyncRun = 0;
static uint32_t     dcsBiosLastByte = 0;

// ================================================================
//  Address Interest Check
// ================================================================

static const uint16_t dcsBiosWatchAddrs[] = {
  DCSBIOS_ELEC_GRP1_ADDR, DCSBIOS_ELEC_GRP2_ADDR,
  DCSBIOS_ECM_GRP1_ADDR, DCSBIOS_ECM_GRP2_ADDR, DCSBIOS_ECM_GRP3_ADDR,
};
#define DCSBIOS_NUM_WATCH (sizeof(dcsBiosWatchAddrs) / sizeof(dcsBiosWatchAddrs[0]))

static bool dcsBiosIsInteresting(uint16_t addr) {
  for (unsigned int i = 0; i < DCSBIOS_NUM_WATCH; i++)
    if (addr == dcsBiosWatchAddrs[i]) return true;
  return false;
}

static bool dcsBiosChunkIsInteresting(uint16_t addr, uint16_t count) {
  uint16_t end = addr + count;
  for (unsigned int i = 0; i < DCSBIOS_NUM_WATCH; i++)
    if (dcsBiosWatchAddrs[i] >= addr && dcsBiosWatchAddrs[i] < end) return true;
  return false;
}

// ================================================================
//  Update Callback — called when a watched address has new data
// ================================================================

static void dcsBiosOnUpdate(uint16_t addr, uint16_t value) {
  // --- ELEC Panel Caution Lights ---
  if (addr == DCSBIOS_ELEC_GRP1_ADDR || addr == DCSBIOS_ELEC_GRP2_ADDR) {
    if (ALLOW_DEBUG) Serial.printf("[DCS-ELEC] addr=0x%04X val=0x%04X\n", addr, value);
  }
  if (addr == DCSBIOS_ELEC_GRP1_ADDR) {
    writeElecLed(LI_FLCS_PMG,    (value & DCSBIOS_FLCS_PMG_MASK));
    writeElecLed(LI_MAIN_GEN,    (value & DCSBIOS_MAIN_GEN_MASK));
    writeElecLed(LI_STBY_GEN,    (value & DCSBIOS_STBY_GEN_MASK));
    writeElecLed(LI_EPU_GEN,     (value & DCSBIOS_EPU_GEN_MASK));
    writeElecLed(LI_EPU_PMG,     (value & DCSBIOS_EPU_PMG_MASK));
    writeElecLed(LI_BATT_TO_FLCS,(value & DCSBIOS_BATT_TO_FLCS_MASK));
  }
  else if (addr == DCSBIOS_ELEC_GRP2_ADDR) {
    writeElecLed(LI_FLCS_RLY,    (value & DCSBIOS_FLCS_RLY_MASK));
    writeElecLed(LI_BATT_FAIL,   (value & DCSBIOS_BATT_FAIL_MASK));
  }
  // --- ECM Panel Indicator Lights (shift register) ---
  // SR index: ecmSrLedNames[] order = ECM_1_S(0), ECM_1_A(1), ECM_1_F(2), ECM_1_T(3), ...
  //if (ALLOW_DEBUG && (addr == DCSBIOS_ECM_GRP1_ADDR || addr == DCSBIOS_ECM_GRP2_ADDR || addr == DCSBIOS_ECM_GRP3_ADDR)) {
  //  Serial.printf("[DCS-ECM] addr=0x%04X val=0x%04X\n", addr, value);
  //}
  if (addr == DCSBIOS_ECM_GRP1_ADDR) {
    srWrite(0,  (value & DCSBIOS_ECM_1_S_MASK));  // ECM_1_S
    srWrite(1,  (value & DCSBIOS_ECM_1_A_MASK));  // ECM_1_A
    srWrite(2,  (value & DCSBIOS_ECM_1_F_MASK));  // ECM_1_F
  }
  else if (addr == DCSBIOS_ECM_GRP2_ADDR) {
    srWrite(3,  (value & DCSBIOS_ECM_1_T_MASK));  // ECM_1_T
    srWrite(4,  (value & DCSBIOS_ECM_2_S_MASK));  // ECM_2_S
    srWrite(5,  (value & DCSBIOS_ECM_2_A_MASK));  // ECM_2_A
    srWrite(6,  (value & DCSBIOS_ECM_2_F_MASK));  // ECM_2_F
    srWrite(7,  (value & DCSBIOS_ECM_2_T_MASK));  // ECM_2_T
    srWrite(8,  (value & DCSBIOS_ECM_3_S_MASK));  // ECM_3_S
    srWrite(9,  (value & DCSBIOS_ECM_3_A_MASK));  // ECM_3_A
    srWrite(10, (value & DCSBIOS_ECM_3_F_MASK));  // ECM_3_F
    srWrite(11, (value & DCSBIOS_ECM_3_T_MASK));  // ECM_3_T
    srWrite(12, (value & DCSBIOS_ECM_4_S_MASK));  // ECM_4_S
    srWrite(13, (value & DCSBIOS_ECM_4_A_MASK));  // ECM_4_A
    srWrite(14, (value & DCSBIOS_ECM_4_F_MASK));  // ECM_4_F
    srWrite(15, (value & DCSBIOS_ECM_4_T_MASK));  // ECM_4_T
    srWrite(16, (value & DCSBIOS_ECM_5_S_MASK));  // ECM_5_S
    srWrite(17, (value & DCSBIOS_ECM_5_A_MASK));  // ECM_5_A
    srWrite(18, (value & DCSBIOS_ECM_5_F_MASK));  // ECM_5_F
  }
  else if (addr == DCSBIOS_ECM_GRP3_ADDR) {
    srWrite(19, (value & DCSBIOS_ECM_5_T_MASK));  // ECM_5_T
    srWrite(20, (value & DCSBIOS_ECM_6_S_MASK));  // ECM_6_S
    srWrite(21, (value & DCSBIOS_ECM_6_A_MASK));  // ECM_6_A
    srWrite(22, (value & DCSBIOS_ECM_6_F_MASK));  // ECM_6_F
    srWrite(23, (value & DCSBIOS_ECM_6_T_MASK));  // ECM_6_T
    srWrite(24, (value & DCSBIOS_ECM_FRM_S_MASK));  // ECM_FRM_S
    srWrite(25, (value & DCSBIOS_ECM_FRM_A_MASK));  // ECM_FRM_A
    srWrite(26, (value & DCSBIOS_ECM_FRM_F_MASK));  // ECM_FRM_F
    srWrite(27, (value & DCSBIOS_ECM_FRM_T_MASK));  // ECM_FRM_T
    srWrite(28, (value & DCSBIOS_ECM_SPL_S_MASK));  // ECM_SPL_S
    srWrite(29, (value & DCSBIOS_ECM_SPL_A_MASK));  // ECM_SPL_A
    srWrite(30, (value & DCSBIOS_ECM_SPL_F_MASK));  // ECM_SPL_F
    srWrite(31, (value & DCSBIOS_ECM_SPL_T_MASK));  // ECM_SPL_T
  }
}

// ================================================================
//  Reset Parser State
// ================================================================

void dcsBiosReset() {
  dcsBiosState   = DCS_SYNC_1;
  dcsBiosAddr    = 0;
  dcsBiosCount   = 0;
  dcsBiosSkip    = 0;
  dcsBiosCapture = false;
  dcsBiosSyncRun = 0;
  dcsBiosLastByte = 0;
}

#define DCS_INTRA_FRAME_TIMEOUT_MS  200

void dcsBiosCheckTimeout() {
  if (dcsBiosState > DCS_SYNC_4 && dcsBiosLastByte != 0) {
    if (millis() - dcsBiosLastByte > DCS_INTRA_FRAME_TIMEOUT_MS) {
      //if (ALLOW_DEBUG) Serial.println("[DCS] Intra-frame timeout, resync");
      dcsBiosState = DCS_SYNC_1;
      dcsBiosSyncRun = 0;
    }
  }
}

// ================================================================
//  Process One Byte
// ================================================================

void processDcsBiosByte(uint8_t b) {
  dcsBiosLastByte = millis();

  if (dcsBiosState > DCS_SYNC_4) {
    if (b == 0x55) {
      dcsBiosSyncRun++;
      if (dcsBiosSyncRun >= 4) {
        //if (ALLOW_DEBUG) Serial.println("[DCS] Resync: found 0x55x4 in data stream");
        dcsBiosState = DCS_ADDR_LOW;
        dcsBiosSyncRun = 0;
        return;
      }
    } else {
      dcsBiosSyncRun = 0;
    }
  }

  switch (dcsBiosState) {
    case DCS_SYNC_1:
      if (b == 0x55) dcsBiosState = DCS_SYNC_2;
      break;
    case DCS_SYNC_2:
      dcsBiosState = (b == 0x55) ? DCS_SYNC_3 : DCS_SYNC_1;
      break;
    case DCS_SYNC_3:
      dcsBiosState = (b == 0x55) ? DCS_SYNC_4 : DCS_SYNC_1;
      break;
    case DCS_SYNC_4:
      dcsBiosState = (b == 0x55) ? DCS_ADDR_LOW : DCS_SYNC_1;
      break;

    case DCS_ADDR_LOW:
      dcsBiosAddr = b;
      dcsBiosState = DCS_ADDR_HIGH;
      break;
    case DCS_ADDR_HIGH:
      dcsBiosAddr |= (uint16_t)b << 8;
      if ((dcsBiosAddr & 1) && dcsBiosAddr != 0x5555) {
        //if (ALLOW_DEBUG) Serial.printf("[DCS] Bad addr 0x%04X, resync\n", dcsBiosAddr);
        dcsBiosState = DCS_SYNC_1;
        break;
      }
      dcsBiosState = DCS_COUNT_LOW;
      break;
    case DCS_COUNT_LOW:
      dcsBiosCount = b;
      dcsBiosState = DCS_COUNT_HIGH;
      break;
    case DCS_COUNT_HIGH:
      dcsBiosCount |= (uint16_t)b << 8;
      if (dcsBiosAddr == 0x5555 && dcsBiosCount == 0x5555) {
        dcsBiosState = DCS_SYNC_1;
        break;
      }
      if ((dcsBiosCount & 1) || dcsBiosCount == 0 || dcsBiosCount > 1024) {
        //if (ALLOW_DEBUG) Serial.printf("[DCS] Bad count %u @ 0x%04X, resync\n", dcsBiosCount, dcsBiosAddr);
        dcsBiosState = DCS_SYNC_1;
        break;
      }
      dcsBiosCapture = dcsBiosChunkIsInteresting(dcsBiosAddr, dcsBiosCount);
      dcsBiosSkip    = 0;
      dcsBiosState   = DCS_DATA;
      break;

    case DCS_DATA:
      if (dcsBiosCapture) {
        if ((dcsBiosSkip & 1) == 0) {
          dcsBiosDataBuf[0] = b;
        } else {
          dcsBiosDataBuf[1] = b;
          uint16_t wordAddr = dcsBiosAddr + (dcsBiosSkip & ~1u);
          if (dcsBiosIsInteresting(wordAddr)) {
            uint16_t value = dcsBiosDataBuf[0] | ((uint16_t)dcsBiosDataBuf[1] << 8);
            dcsBiosOnUpdate(wordAddr, value);
          }
        }
      }
      dcsBiosSkip++;
      if (dcsBiosSkip >= dcsBiosCount) {
        dcsBiosState = DCS_ADDR_LOW;
      }
      break;
  }
}

#endif // DCSBIOS_PARSER_H
