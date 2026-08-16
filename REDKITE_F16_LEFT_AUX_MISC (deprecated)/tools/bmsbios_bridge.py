#!/usr/bin/env python3
"""
BMS-BIOS Bridge — Falcon BMS Shared Memory → Teensy Serial

Reads Falcon BMS FlightData from shared memory, extracts LED states,
and sends them to Teensy via the BMS-BIOS binary protocol.

Protocol (BMS-BIOS):
  Sync:     0xAA 0xBB          (2 bytes)
  ledBits:  uint32 LE          (bits 0–16 for 17 leds[], rest reserved)
  checksum: XOR of 4 payload bytes  (1 byte)
  Total: 7 bytes per frame

Usage:
  python bms_bridge.py COM4
  python bms_bridge.py COM4 --hz 20
"""

import sys
import time
import struct
import argparse
import mmap
import ctypes

# ================================================================
#  Falcon BMS Shared Memory
# ================================================================

SHM_NAME  = "FalconSharedMemoryArea"
SHM_SIZE  = 1024  # we only need the first ~300 bytes
SHM2_NAME = "FalconSharedMemoryArea2"
SHM2_SIZE = 1200  # need ~1105 bytes for instrLight

# FlightData field offsets (BMS 4.33 / 4.37)
OFF_LIGHTBITS  = 108   # unsigned int (see FlightData.h)
OFF_LIGHTBITS2 = 124   # unsigned int (after headPitch/Roll/Yaw)
OFF_LIGHTBITS3 = 128   # unsigned int

# --- LightBits (offset 108) ---
LB_ADV_STANDBY      = 0x80000000  # bit 31 — ADV Standby indicator

# --- LightBits2 (offset 124) ---
LB2_ECM_PWR         = 0x00010000  # bit 16 — ECM power indicator
LB2_ADV_ACTIVE      = 0x20000000  # bit 29 — ADV Active indicator
LB_GEARHANDLE       = 0x40000000  # bit 30 — gear handle lamp

# --- LightBits2 (offset 124, continued) ---
LB2_AUX_SRCH        = 0x00001000  # bit 12 — TWA Search
LB2_AUX_ACT         = 0x00002000  # bit 13 — TWA Activity
LB2_AUX_LOW         = 0x00004000  # bit 14 — TWA Low Alt
LB2_AUX_PWR         = 0x00008000  # bit 15 — TWA Power

# --- LightBits3 (offset 128) ---
LB3_NOSE_GEAR_DN    = 0x00010000  # bit 16
LB3_LEFT_GEAR_DN    = 0x00020000  # bit 17
LB3_RIGHT_GEAR_DN   = 0x00040000  # bit 18

# --- FlightData2 instrLight (offset 1104, unsigned char) ---
# InstrLight enum: OFF=0, DIM=1, BRT=2
OFF_FD2_INSTRLIGHT  = 1104

# ================================================================
#  LED Index Mapping (matches LedIdx enum in .ino)
# ================================================================

LI_NOSE_GEAR        = 0
LI_LEFT_GEAR        = 1
LI_RIGHT_GEAR       = 2
LI_GEAR_WARN        = 3
LI_TWA_POWER        = 4
LI_TWA_LOW          = 5
LI_TWA_SEARCH       = 6
LI_TWA_ACT          = 7
LI_ECM              = 8
LI_ADV_ACTIVE       = 9
LI_ADV_STANDBY      = 10

# LED mapping table: (LedIdx, lightBits_offset, mask)
LED_MAP = [
    (LI_NOSE_GEAR,         OFF_LIGHTBITS3, LB3_NOSE_GEAR_DN),
    (LI_LEFT_GEAR,         OFF_LIGHTBITS3, LB3_LEFT_GEAR_DN),
    (LI_RIGHT_GEAR,        OFF_LIGHTBITS3, LB3_RIGHT_GEAR_DN),
    (LI_GEAR_WARN,         OFF_LIGHTBITS2, LB_GEARHANDLE),
    (LI_TWA_POWER,         OFF_LIGHTBITS2, LB2_AUX_PWR),
    (LI_TWA_LOW,           OFF_LIGHTBITS2, LB2_AUX_LOW),
    (LI_TWA_SEARCH,        OFF_LIGHTBITS2, LB2_AUX_SRCH),
    (LI_TWA_ACT,           OFF_LIGHTBITS2, LB2_AUX_ACT),
    (LI_ECM,               OFF_LIGHTBITS2, LB2_ECM_PWR),
    (LI_ADV_ACTIVE,        OFF_LIGHTBITS2, LB2_ADV_ACTIVE),
    (LI_ADV_STANDBY,       OFF_LIGHTBITS,  LB_ADV_STANDBY),
]

# ================================================================
#  BMS-BIOS Protocol
# ================================================================

SYNC = b'\xAA\xBB'

def build_frame(led_bits: int) -> bytes:
    """Build a BMS-BIOS protocol frame."""
    payload = struct.pack('<I', led_bits)
    checksum = 0
    for b in payload:
        checksum ^= b
    return SYNC + payload + bytes([checksum])

# ================================================================
#  Shared Memory Reader
# ================================================================

def open_shm(name, size):
    """Open existing Falcon BMS shared memory (never creates new).
    Returns mmap object or None."""
    try:
        kernel32 = ctypes.windll.kernel32
        FILE_MAP_READ = 0x0004
        handle = kernel32.OpenFileMappingW(FILE_MAP_READ, False, name)
        if not handle:
            return None
        kernel32.CloseHandle(handle)
        shm = mmap.mmap(-1, size, tagname=name, access=mmap.ACCESS_READ)
        return shm
    except Exception:
        return None

def read_int32(shm, offset):
    """Read a signed 32-bit int from shared memory at given offset."""
    shm.seek(offset)
    return struct.unpack('<i', shm.read(4))[0]

def read_byte(shm, offset):
    """Read an unsigned byte from shared memory."""
    shm.seek(offset)
    return struct.unpack('B', shm.read(1))[0]

def read_led_states(shm, shm2):
    """Read all lightBits and return led_bits (bit 16 = backlight)."""
    lb  = read_int32(shm, OFF_LIGHTBITS)
    lb2 = read_int32(shm, OFF_LIGHTBITS2)
    lb3 = read_int32(shm, OFF_LIGHTBITS3)

    led_bits = 0
    lbits = {OFF_LIGHTBITS: lb, OFF_LIGHTBITS2: lb2, OFF_LIGHTBITS3: lb3}
    for idx, offset, mask in LED_MAP:
        if lbits[offset] & mask:
            led_bits |= (1 << idx)

    # Backlight: instrLight from FlightData2 (0=OFF, 1=DIM, 2=BRT)
    if shm2 is not None:
        instr = read_byte(shm2, OFF_FD2_INSTRLIGHT)
        if instr > 0:
            led_bits |= (1 << 16)  # bit 16 = backlight ON

    return led_bits

# ================================================================
#  Main Loop
# ================================================================

def main():
    parser = argparse.ArgumentParser(description='BMS-BIOS Bridge')
    parser.add_argument('port', nargs='?', default='COM4', help='Serial port (default: COM4)')
    parser.add_argument('--baud', type=int, default=1000000, help='Baud rate (default: 1000000)')
    parser.add_argument('--hz', type=int, default=20, help='Update rate in Hz (default: 20)')
    parser.add_argument('--debug', action='store_true', help='Print raw shared memory values')
    args = parser.parse_args()

    import serial
    ser = serial.Serial(args.port, args.baud, timeout=0.1)
    print(f"[BMS-BIOS] Serial: {args.port} @ {args.baud}")
    print(f"[BMS-BIOS] Update rate: {args.hz} Hz")
    print(f"[BMS-BIOS] Waiting for Falcon BMS shared memory...")

    interval = 1.0 / args.hz
    prev_led = -1
    shm = None
    shm2 = None

    try:
        while True:
            # Try to open shared memory if not open
            if shm is None:
                shm = open_shm(SHM_NAME, SHM_SIZE)
                if shm is not None:
                    print("[BMS-BIOS] BMS shared memory connected!")
            if shm2 is None:
                shm2 = open_shm(SHM2_NAME, SHM2_SIZE)
                if shm2 is not None:
                    print("[BMS-BIOS] FlightData2 connected (instrLight available)")

            if shm is not None:
                try:
                    led_bits = read_led_states(shm, shm2)

                    if args.debug:
                        lb  = read_int32(shm, OFF_LIGHTBITS)
                        lb2 = read_int32(shm, OFF_LIGHTBITS2)
                        lb3 = read_int32(shm, OFF_LIGHTBITS3)
                        bl  = 1 if (led_bits & (1 << 16)) else 0
                        raw = (lb, lb2, lb3, bl)
                        if not hasattr(main, '_prev_raw'):
                            main._prev_raw = raw
                        if raw != main._prev_raw:
                            print(f"\n  LB=0x{lb:08X}  LB2=0x{lb2:08X}  LB3=0x{lb3:08X}  BL={bl}  → ledBits=0x{led_bits:08X}")
                            main._prev_raw = raw
                        else:
                            print(f"  LB=0x{lb:08X}  LB2=0x{lb2:08X}  LB3=0x{lb3:08X}  BL={bl}  → ledBits=0x{led_bits:08X}", end="\r")

                    # Only send if state changed (or first frame)
                    if led_bits != prev_led:
                        frame = build_frame(led_bits)
                        ser.write(frame)
                        prev_led = led_bits
                        if args.debug:
                            print(f"\n  [SEND] ledBits=0x{led_bits:08X} frame={frame.hex(' ')}")

                    # Also send periodic heartbeat even if unchanged
                    elif int(time.time() * args.hz) % args.hz == 0:
                        frame = build_frame(led_bits)
                        ser.write(frame)

                except Exception as e:
                    print(f"[BMS-BIOS] SHM read error: {e}, reconnecting...")
                    try: shm.close()
                    except: pass
                    try: shm2.close()
                    except: pass
                    shm = None
                    shm2 = None
                    prev_led = -1

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n[BMS-BIOS] Stopped.")
    finally:
        ser.close()
        if shm:
            shm.close()
        if shm2:
            shm2.close()

if __name__ == '__main__':
    main()
