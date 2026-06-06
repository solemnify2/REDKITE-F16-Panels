#!/usr/bin/env python3
"""
BMS-BIOS Bridge (통합) — Falcon BMS Shared Memory -> 여러 Teensy Serial

디바이스별 프레임 포맷:
  LEFT_AUX:     sync(2) + ledBits(4) + checksum(1)                = 7 bytes
  LEFT_CONSOLE: sync(2) + ledBits(4) + srData(4) + checksum(1)    = 12 bytes

사용법:
  python bmsbios_bridge.py                              (자동 감지)
  python bmsbios_bridge.py COM3:AUX COM4:CONSOLE        (수동 지정)
  python bmsbios_bridge.py --hz 20 --debug
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
SHM_SIZE  = 1024
SHM2_NAME = "FalconSharedMemoryArea2"
SHM2_SIZE = 1200

OFF_LIGHTBITS  = 108
OFF_LIGHTBITS2 = 124
OFF_LIGHTBITS3 = 128
OFF_FD2_INSTRLIGHT = 1104
OFF_FD2_ECMBITS    = 1180   # unsigned int ecmBits[5] (VERSION 19)
OFF_FD2_ECMOPER    = 1200   # unsigned char ecmOper   (VERSION 19)

# --- LightBits (offset 108) ---
LB_FLCS_RLY         = 0x00000100  # bit 8
LB_ADV_STANDBY      = 0x80000000  # bit 31

# --- LightBits2 (offset 124) ---
LB2_FLCS_PMG        = 0x00000001  # bit 0
LB2_MAIN_GEN        = 0x00000002  # bit 1
LB2_STBY_GEN        = 0x00000004  # bit 2
LB2_EPU_GEN         = 0x00000008  # bit 3
LB2_EPU_PMG         = 0x00000010  # bit 4
LB2_AUX_SRCH        = 0x00001000  # bit 12
LB2_AUX_ACT         = 0x00002000  # bit 13
LB2_AUX_LOW         = 0x00004000  # bit 14
LB2_AUX_PWR         = 0x00008000  # bit 15
LB2_ECM_PWR         = 0x00010000  # bit 16
LB2_ADV_ACTIVE      = 0x20000000  # bit 29
LB_GEARHANDLE       = 0x40000000  # bit 30

# --- LightBits3 (offset 128) ---
LB3_NOSE_GEAR_DN    = 0x00010000  # bit 16
LB3_LEFT_GEAR_DN    = 0x00020000  # bit 17
LB3_RIGHT_GEAR_DN   = 0x00040000  # bit 18

# ================================================================
#  Device Profiles
# ================================================================

# LEFT_AUX: 11 direct GPIO LEDs + backlight (bit 16)
AUX_LED_MAP = [
    (0,  OFF_LIGHTBITS3, LB3_NOSE_GEAR_DN),  # NOSE GEAR
    (1,  OFF_LIGHTBITS3, LB3_LEFT_GEAR_DN),  # LEFT GEAR
    (2,  OFF_LIGHTBITS3, LB3_RIGHT_GEAR_DN), # RIGHT GEAR
    (3,  OFF_LIGHTBITS2, LB_GEARHANDLE),     # GEAR WARN
    (4,  OFF_LIGHTBITS2, LB2_AUX_PWR),       # TWA POWER
    (5,  OFF_LIGHTBITS2, LB2_AUX_LOW),       # TWA LOW
    (6,  OFF_LIGHTBITS2, LB2_AUX_SRCH),      # TWA SEARCH
    (7,  OFF_LIGHTBITS2, LB2_AUX_ACT),       # TWA ACT
    (8,  OFF_LIGHTBITS2, LB2_ECM_PWR),       # ECM
    (9,  OFF_LIGHTBITS2, LB2_ADV_ACTIVE),    # ADV ACTIVE
    (10, OFF_LIGHTBITS,  LB_ADV_STANDBY),    # ADV STANDBY
]

# LEFT_CONSOLE: 9 direct GPIO LEDs (ELEC panel)
CONSOLE_LED_MAP = [
    (0,  OFF_LIGHTBITS2, LB2_FLCS_PMG),     # FLCS PMG
    (1,  OFF_LIGHTBITS2, LB2_MAIN_GEN),     # MAIN GEN
    (2,  OFF_LIGHTBITS2, LB2_STBY_GEN),     # STBY GEN
    (3,  OFF_LIGHTBITS2, LB2_EPU_GEN),      # EPU GEN
    (4,  OFF_LIGHTBITS2, LB2_EPU_PMG),      # EPU PMG
    (5,  OFF_LIGHTBITS,  LB_FLCS_RLY),      # FLCS RLY
    # (6, ..., ...),  # BATT FAIL — TODO: find BMS shared memory bit
    # (7, ..., ...),  # BATT TO FLCS — TODO
    # (8, ..., ...),  # ELEC SYS — TODO
]

# --- EcmBits enum (mutually exclusive states per program) ---
ECM_UNPRESSED_NO_LIT  = 0x01
ECM_UNPRESSED_ALL_LIT = 0x02
ECM_PRESSED_NO_LIT    = 0x04
ECM_PRESSED_STANDBY   = 0x08
ECM_PRESSED_ACTIVE    = 0x10
ECM_PRESSED_TRANSMIT  = 0x20
ECM_PRESSED_FAIL      = 0x40
ECM_PRESSED_ALL_LIT   = 0x80

MAX_ECM_PROGRAMS = 5

SYNC = b'\xAA\xBB'

# ================================================================
#  Frame Builders
# ================================================================

def build_aux_frame(led_bits: int) -> bytes:
    """LEFT_AUX: 7 bytes (sync + ledBits + checksum)"""
    payload = struct.pack('<I', led_bits)
    checksum = 0
    for b in payload:
        checksum ^= b
    return SYNC + payload + bytes([checksum])


def build_console_frame(led_bits: int, sr_data: bytes) -> bytes:
    """LEFT_CONSOLE: 12 bytes (sync + ledBits + srData + checksum)"""
    payload = struct.pack('<I', led_bits) + sr_data
    checksum = 0
    for b in payload:
        checksum ^= b
    return SYNC + payload + bytes([checksum])

# ================================================================
#  Shared Memory Reader
# ================================================================

def open_shm(name, size):
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenFileMappingW(0x0004, False, name)
        if not handle:
            return None
        kernel32.CloseHandle(handle)
        return mmap.mmap(-1, size, tagname=name, access=mmap.ACCESS_READ)
    except Exception:
        return None


def read_int32(shm, offset):
    shm.seek(offset)
    return struct.unpack('<i', shm.read(4))[0]


def read_byte(shm, offset):
    shm.seek(offset)
    return struct.unpack('B', shm.read(1))[0]


def compute_led_bits(led_map, lbits):
    """LED 매핑 테이블로부터 ledBits 계산"""
    led_bits = 0
    for idx, offset, mask in led_map:
        if lbits[offset] & mask:
            led_bits |= (1 << idx)
    return led_bits


def ecm_bits_to_saft(ecm_state):
    """EcmBits 상태를 S/A/F/T LED 4비트로 변환.
    Returns (s, a, f, t) as bools.
    S=Standby, A=Active, F=Fail, T=Transmit
    ALL_LIT = all four on.
    """
    if ecm_state == ECM_PRESSED_STANDBY:
        return (True, False, False, False)
    elif ecm_state == ECM_PRESSED_ACTIVE:
        return (False, True, False, False)
    elif ecm_state == ECM_PRESSED_FAIL:
        return (False, False, True, False)
    elif ecm_state == ECM_PRESSED_TRANSMIT:
        return (False, False, False, True)
    elif ecm_state in (ECM_UNPRESSED_ALL_LIT, ECM_PRESSED_ALL_LIT):
        return (True, True, True, True)
    else:
        return (False, False, False, False)


def compute_ecm_sr_data(shm2):
    """FlightData2의 ecmBits[5]로부터 ECM SR 32비트 데이터 생성.
    SR layout: [ECM1_S,A,F,T, ECM2_S,A,F,T, ..., ECM5_S,A,F,T, ECM6_S,A,F,T, FRM_S,A,F,T, SPL_S,A,F,T]
    ECM programs 1-5 map to ecmBits[0-4]. ECM6/FRM/SPL are not in shared memory (always off).
    """
    sr_bits = 0
    for pgm in range(MAX_ECM_PROGRAMS):
        shm2.seek(OFF_FD2_ECMBITS + pgm * 4)
        ecm_val = struct.unpack('<I', shm2.read(4))[0]
        s, a, f, t = ecm_bits_to_saft(ecm_val)
        base = pgm * 4
        if s: sr_bits |= (1 << (base + 0))
        if a: sr_bits |= (1 << (base + 1))
        if f: sr_bits |= (1 << (base + 2))
        if t: sr_bits |= (1 << (base + 3))
    # ECM6(20-23), FRM(24-27), SPL(28-31) — no shared memory source, stay 0
    return struct.pack('<I', sr_bits)

# ================================================================
#  Device Class
# ================================================================

class Device:
    def __init__(self, port, dev_type, ser):
        self.port = port
        self.dev_type = dev_type  # 'AUX' or 'CONSOLE'
        self.ser = ser
        self.prev_frame = None

    def build_and_send(self, lbits, shm2):
        if self.dev_type == 'AUX':
            led_bits = compute_led_bits(AUX_LED_MAP, lbits)
            # Backlight: instrLight from FlightData2
            if shm2 is not None:
                instr = read_byte(shm2, OFF_FD2_INSTRLIGHT)
                if instr > 0:
                    led_bits |= (1 << 16)
            frame = build_aux_frame(led_bits)

        elif self.dev_type == 'CONSOLE':
            led_bits = compute_led_bits(CONSOLE_LED_MAP, lbits)
            sr_data = compute_ecm_sr_data(shm2) if shm2 else b'\x00\x00\x00\x00'
            frame = build_console_frame(led_bits, sr_data)

        else:
            return

        if frame != self.prev_frame:
            try:
                self.ser.write(frame)
                self.prev_frame = frame
            except Exception:
                pass

    def heartbeat(self):
        """Send current frame as heartbeat even if unchanged."""
        if self.prev_frame:
            try:
                self.ser.write(self.prev_frame)
            except Exception:
                pass

# ================================================================
#  Port Argument Parser
# ================================================================

def parse_port_arg(arg):
    """Parse 'COM3:AUX' or 'COM3' format. Auto-detect type if not specified."""
    if ':' in arg:
        port, dtype = arg.split(':', 1)
        dtype = dtype.upper()
        if dtype not in ('AUX', 'CONSOLE'):
            print(f"알 수 없는 디바이스 타입: {dtype} (AUX 또는 CONSOLE)")
            sys.exit(1)
        return port, dtype
    return arg, None


def detect_device_type(port):
    """VID/PID 기반 디바이스 타입 추정"""
    import serial.tools.list_ports
    for p in serial.tools.list_ports.comports():
        if p.device == port:
            if p.vid == TEENSY_VID:
                if p.pid == PID_AUX:
                    return 'AUX'
                elif p.pid == PID_CONSOLE:
                    return 'CONSOLE'
            # PID 매칭 실패 시 description fallback
            desc = (p.description or "").lower()
            if "left console" in desc:
                return 'CONSOLE'
            elif "left aux" in desc or "panels" in desc:
                return 'AUX'
    return None


TEENSY_VID = 0x16C0
PID_AUX     = 0x0489   # Left Aux Misc
PID_CONSOLE = 0x048E   # Left Console

PID_NAMES = {
    PID_AUX:     "REDKITE F16 Left Aux Misc",
    PID_CONSOLE: "REDKITE F16 Left Console",
}


def find_teensy_ports():
    """VID/PID 기반 Teensy COM 포트 자동 감지 + 디바이스 타입 판별.
    Returns (port_args, descriptions): port_args is list of 'COMx:TYPE', descriptions for display."""
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()
    port_args = []
    descriptions = []
    for p in ports:
        if p.vid == TEENSY_VID:
            name = PID_NAMES.get(p.pid, f"Unknown (PID:0x{p.pid:04X})")
            if p.pid == PID_AUX:
                port_args.append(f"{p.device}:AUX")
                descriptions.append(f"  {p.device}: {name} [AUX]")
            elif p.pid == PID_CONSOLE:
                port_args.append(f"{p.device}:CONSOLE")
                descriptions.append(f"  {p.device}: {name} [CONSOLE]")
            else:
                port_args.append(p.device)
                descriptions.append(f"  {p.device}: {name}")
    return port_args, descriptions

# ================================================================
#  Main
# ================================================================

def main():
    parser = argparse.ArgumentParser(description='BMS-BIOS Bridge (통합)')
    parser.add_argument('ports', nargs='*',
                        help='COM ports: COM3:AUX COM4:CONSOLE (or just COM3 COM4 for auto-detect)')
    parser.add_argument('--baud', type=int, default=1000000)
    parser.add_argument('--hz', type=int, default=20)
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    import serial as pyserial

    # 포트 결정
    port_args = args.ports
    if not port_args:
        auto, descs = find_teensy_ports()
        if auto:
            port_args = auto
            print("[Auto] Teensy 감지:")
            for d in descs:
                print(d)
        else:
            import serial.tools.list_ports
            all_ports = serial.tools.list_ports.comports()
            print("Teensy를 자동 감지하지 못했습니다.")
            if all_ports:
                print("사용 가능한 COM 포트:")
                for p in all_ports:
                    vid_str = f"VID:0x{p.vid:04X}" if p.vid else "VID:N/A"
                    pid_str = f"PID:0x{p.pid:04X}" if p.pid else "PID:N/A"
                    print(f"  {p.device}: {p.description} [{vid_str} {pid_str}]")
            print("포트를 인자로 지정하세요. 예: python bmsbios_bridge.py COM3:AUX COM4:CONSOLE")
            sys.exit(1)

    # 디바이스 생성
    devices = []
    failed = False
    for pa in port_args:
        port, dtype = parse_port_arg(pa)
        if dtype is None:
            dtype = detect_device_type(port)
            if dtype is None:
                print(f"  {port}: 디바이스 타입 자동 감지 실패. COM:TYPE 형식으로 지정하세요 (예: {port}:AUX)")
                continue
        try:
            s = pyserial.Serial(port, args.baud, timeout=0.1)
            dev = Device(port, dtype, s)
            devices.append(dev)
            print(f"  {port}: {dtype} 연결됨")
        except pyserial.SerialException as e:
            print(f"  {port}: 열기 실패 — {e}")
            failed = True

    if failed:
        import serial.tools.list_ports
        all_ports = serial.tools.list_ports.comports()
        if all_ports:
            print("현재 검색되는 COM 포트:")
            for p in all_ports:
                print(f"  {p.device}: {p.description}")
        else:
            print("시스템에 COM 포트가 없습니다.")

    if not devices:
        sys.exit(1)

    print(f"\n[BMS-BIOS] Update rate: {args.hz} Hz")
    print(f"[BMS-BIOS] Waiting for Falcon BMS shared memory...")

    interval = 1.0 / args.hz
    shm = None
    shm2 = None

    try:
        while True:
            if shm is None:
                shm = open_shm(SHM_NAME, SHM_SIZE)
                if shm is not None:
                    print("[BMS-BIOS] BMS shared memory connected!")
            if shm2 is None:
                shm2 = open_shm(SHM2_NAME, SHM2_SIZE)
                if shm2 is not None:
                    print("[BMS-BIOS] FlightData2 connected")

            if shm is not None:
                try:
                    lb  = read_int32(shm, OFF_LIGHTBITS)
                    lb2 = read_int32(shm, OFF_LIGHTBITS2)
                    lb3 = read_int32(shm, OFF_LIGHTBITS3)
                    lbits = {OFF_LIGHTBITS: lb, OFF_LIGHTBITS2: lb2, OFF_LIGHTBITS3: lb3}

                    if args.debug:
                        print(f"  LB=0x{lb:08X}  LB2=0x{lb2:08X}  LB3=0x{lb3:08X}", end="\r")

                    for dev in devices:
                        dev.build_and_send(lbits, shm2)

                    # Periodic heartbeat
                    if int(time.time() * args.hz) % args.hz == 0:
                        for dev in devices:
                            dev.heartbeat()

                except Exception as e:
                    print(f"\n[BMS-BIOS] SHM read error: {e}, reconnecting...")
                    try: shm.close()
                    except: pass
                    try:
                        if shm2: shm2.close()
                    except: pass
                    shm = None
                    shm2 = None
                    for dev in devices:
                        dev.prev_frame = None

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n[BMS-BIOS] Stopped.")
    finally:
        for dev in devices:
            dev.ser.close()
        if shm: shm.close()
        if shm2: shm2.close()


if __name__ == '__main__':
    main()
