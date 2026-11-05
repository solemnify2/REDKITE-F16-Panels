#!/usr/bin/env python3
"""
Unified Bridge -- Falcon BMS / DCS World -> Teensy Serial

대기 모드에서 BMS 공유 메모리 또는 DCS-BIOS UDP를 감지하면
해당 모드로 전환하여 동작합니다. 심이 종료되면 다시 대기 모드로 복귀합니다.

사용법:
  python bridge.py                              (자동 감지)
  python bridge.py COM3:AUX COM4:CONSOLE        (수동 지정)
  python bridge.py --hz 20 --debug
"""

import sys
import time
import struct
import socket
import argparse
import ctypes

import serial
import serial.tools.list_ports

# ================================================================
#  Constants — Common
# ================================================================

TEENSY_VID = 0x16C0
SERIAL_BAUD = 1000000

PID_DEVICES = {
    0x0487: ("F16 LEFT AUX MISC", "AUX"),
    0x0489: ("F16 LEFT AUX MISC", "AUX"),
    0x048E: ("F16 LEFT CONSOLE",  "CONSOLE"),
}

# ================================================================
#  Constants — BMS
# ================================================================

SHM_NAME  = "FalconSharedMemoryArea"
SHM_SIZE  = 1024
SHM2_NAME = "FalconSharedMemoryArea2"
SHM2_SIZE = 1200
IV_NAME   = "FalconIntellivibeSharedMemoryArea"
IV_SIZE   = 52

OFF_LIGHTBITS  = 108
OFF_LIGHTBITS2 = 124
OFF_LIGHTBITS3 = 128
OFF_FD2_INSTRLIGHT = 1104
OFF_FD2_ECMBITS    = 1180
OFF_FD2_UHF_PRESET = 48
OFF_FD2_UHF_FREQ   = 52
OFF_IV_IS_EXIT_GAME = 20   # bool — BMS sets this true on exit

FILE_MAP_READ = 0x0004

LB_ADV_STANDBY      = 0x80000000
LB2_EWS_GO          = 0x00000040
LB2_EWS_NOGO        = 0x00000080
LB2_EWS_RDY         = 0x00000200
LB2_AUX_SRCH        = 0x00001000
LB2_AUX_ACT         = 0x00002000
LB2_AUX_LOW         = 0x00004000
LB2_AUX_PWR         = 0x00008000
LB2_ECM_PWR         = 0x00010000
LB2_EPU_ON          = 0x00100000
LB2_JFS_ON          = 0x00200000
LB2_ADV_ACTIVE      = 0x20000000
LB_GEARHANDLE       = 0x40000000

LB3_FLCS_PMG   = 0x00000001
LB3_MAIN_GEN   = 0x00000002
LB3_STBY_GEN   = 0x00000004
LB3_EPU_GEN    = 0x00000008
LB3_EPU_PMG    = 0x00000010
LB3_TO_FLCS    = 0x00000020
LB3_FLCS_RLY   = 0x00000040
LB3_BAT_FAIL   = 0x00000080
LB3_HYDRAZINE  = 0x00000100
LB3_AIR        = 0x00000200
LB3_NOSE_GEAR_DN  = 0x00010000
LB3_LEFT_GEAR_DN  = 0x00020000
LB3_RIGHT_GEAR_DN = 0x00040000

AUX_LED_MAP = [
    (0, OFF_LIGHTBITS2, LB2_ECM_PWR),
    (1, OFF_LIGHTBITS2, LB2_ADV_ACTIVE),
    (2, OFF_LIGHTBITS,  LB_ADV_STANDBY),
    (3, OFF_LIGHTBITS3, LB3_NOSE_GEAR_DN),
    (4, OFF_LIGHTBITS3, LB3_LEFT_GEAR_DN),
    (5, OFF_LIGHTBITS3, LB3_RIGHT_GEAR_DN),
    (6, OFF_LIGHTBITS2, LB_GEARHANDLE),
    (7, OFF_LIGHTBITS2, LB2_AUX_SRCH),
    (8, OFF_LIGHTBITS2, LB2_AUX_ACT),
    (9, OFF_LIGHTBITS2, LB2_AUX_LOW),
    (10, OFF_LIGHTBITS2, LB2_AUX_PWR),
    (11, OFF_LIGHTBITS2, LB2_EWS_RDY),
    (12, OFF_LIGHTBITS2, LB2_EWS_RDY),
    (13, OFF_LIGHTBITS2, LB2_EWS_RDY),
    (14, OFF_LIGHTBITS2, LB2_EWS_NOGO),
    (15, OFF_LIGHTBITS2, LB2_EWS_GO),
]

CONSOLE_LED_MAP = [
    (0, OFF_LIGHTBITS2, LB2_JFS_ON),
    (1, OFF_LIGHTBITS3, LB3_HYDRAZINE),
    (2, OFF_LIGHTBITS3, LB3_AIR),
    (3, OFF_LIGHTBITS2, LB2_EPU_ON),
    (4, OFF_LIGHTBITS3, LB3_FLCS_PMG),
    (5, OFF_LIGHTBITS3, LB3_MAIN_GEN),
    (6, OFF_LIGHTBITS3, LB3_STBY_GEN),
    (7, OFF_LIGHTBITS3, LB3_EPU_GEN),
    (8, OFF_LIGHTBITS3, LB3_EPU_PMG),
    (9, OFF_LIGHTBITS3, LB3_TO_FLCS),
    (10, OFF_LIGHTBITS3, LB3_FLCS_RLY),
    (11, OFF_LIGHTBITS3, LB3_BAT_FAIL),
]

ECM_PRESSED_STANDBY  = 0x08
ECM_PRESSED_ACTIVE   = 0x10
ECM_PRESSED_TRANSMIT = 0x20
ECM_PRESSED_FAIL     = 0x40
ECM_UNPRESSED_ALL_LIT = 0x02
ECM_PRESSED_ALL_LIT   = 0x80
MAX_ECM_PROGRAMS = 5

BMS_SYNC = b'\xAA\xBB'
DIM_PWM_DEFAULT = 255
DIM_PWM_LOWERED = 50
BRT_PWM = 255

DEVICE_PROFILES = {
    'AUX':     {'led_map': AUX_LED_MAP,     'has_backlight': True, 'has_ecm': False},
    'CONSOLE': {'led_map': CONSOLE_LED_MAP,  'has_backlight': True, 'has_ecm': True},
}

# ================================================================
#  Constants — DCS
# ================================================================

DCS_MULTICAST_GROUP = "239.255.50.10"
DCS_MULTICAST_PORT  = 5010
DCS_LIGHT_INST_PNL  = 0x4484
DCS_OFFLINE_TIMEOUT = 10   # seconds without UDP data -> standby

# ================================================================
#  Cougar MFD Backlight (HID) — shared
# ================================================================

MFD_VID  = 0x044F
MFD_PIDS = [0xB351, 0xB352]


class MfdBacklight:
    def __init__(self):
        self.devices = []
        self.prev_brightness = -1
        self.brt_seen = False

    def open(self):
        try:
            import hid
        except ImportError:
            print("[MFD] Cougar MFD 백라이트 동기화를 사용하려면: pip install hidapi")
            return
        for pid in MFD_PIDS:
            for info in hid.enumerate(MFD_VID, pid):
                try:
                    dev = hid.device()
                    dev.open_path(info['path'])
                    name = info.get('product_string', f'PID:0x{pid:04X}')
                    self.devices.append((dev, name))
                    print(f"  [MFD] {name} connected")
                except Exception as e:
                    print(f"  [MFD] PID:0x{pid:04X} open failed: {e}")

    def set_brightness(self, brightness):
        if brightness == self.prev_brightness:
            return
        self.prev_brightness = brightness
        for dev, _ in self.devices:
            try:
                dev.send_feature_report(bytes([0x00, 0x01, brightness]))
            except Exception:
                pass

    def reset(self):
        self.set_brightness(0)
        self.prev_brightness = -1
        self.brt_seen = False

    def close(self):
        self.set_brightness(0)
        for dev, _ in self.devices:
            try:
                dev.close()
            except Exception:
                pass

# ================================================================
#  Common Utilities
# ================================================================

def find_teensy_ports():
    ports = serial.tools.list_ports.comports()
    found = []
    descs = []
    for p in ports:
        if p.vid == TEENSY_VID:
            entry = PID_DEVICES.get(p.pid)
            if entry:
                name, dtype = entry
                found.append((p.device, dtype))
                descs.append(f"  {p.device}: {name} [{dtype}]")
            else:
                found.append((p.device, None))
                descs.append(f"  {p.device}: Unknown (PID:0x{p.pid:04X})")
    return found, descs


def read_serial_output(port, ser, rx_bufs):
    n = ser.in_waiting
    if n <= 0:
        return
    rx_bufs[port] = rx_bufs.get(port, b'') + ser.read(n)
    while b'\n' in rx_bufs[port]:
        line, rx_bufs[port] = rx_bufs[port].split(b'\n', 1)
        print(f"[{port}] {line.decode('utf-8', errors='replace').rstrip()}")


# ================================================================
#  BMS — SHM, Frame Builder, Device
# ================================================================

_kernel32 = ctypes.windll.kernel32
_kernel32.OpenFileMappingW.restype  = ctypes.c_void_p
_kernel32.OpenFileMappingW.argtypes = (ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p)
_kernel32.MapViewOfFile.restype     = ctypes.c_void_p
_kernel32.MapViewOfFile.argtypes    = (ctypes.c_void_p, ctypes.c_uint32,
                                       ctypes.c_uint32, ctypes.c_uint32, ctypes.c_size_t)
_kernel32.UnmapViewOfFile.restype   = ctypes.c_int
_kernel32.UnmapViewOfFile.argtypes  = (ctypes.c_void_p,)
_kernel32.CloseHandle.restype       = ctypes.c_int
_kernel32.CloseHandle.argtypes      = (ctypes.c_void_p,)


def shm_exists(name):
    """SHM이 존재하는지만 확인합니다. 섹션을 만들거나 붙들지 않습니다."""
    handle = _kernel32.OpenFileMappingW(FILE_MAP_READ, False, name)
    if not handle:
        return False
    _kernel32.CloseHandle(handle)
    return True


class ShmView:
    """ctypes 로 공유 메모리를 열고 읽는 래퍼.

    mmap.mmap(-1, tagname=...) 은 CreateFileMappingW 를 써서 섹션이 없으면
    새로 만들고, 있으면 레퍼런스를 붙듭니다. BMS 가 종료해도 bridge 가
    매핑을 쥐고 있으면 커널 섹션이 사라지지 않아 종료를 감지할 수 없습니다.

    이 클래스는 OpenFileMappingW 만 사용하므로 섹션을 만들지 않고,
    close() 하면 레퍼런스를 완전히 놓습니다.
    """

    def __init__(self, name, size):
        self.name, self.size = name, size
        self._handle = None
        self._view = None

    def open(self):
        h = _kernel32.OpenFileMappingW(FILE_MAP_READ, False, self.name)
        if not h:
            return False
        v = _kernel32.MapViewOfFile(h, FILE_MAP_READ, 0, 0, self.size)
        if not v:
            _kernel32.CloseHandle(h)
            return False
        self._handle, self._view = h, v
        return True

    @property
    def ok(self):
        return self._view is not None

    def read(self, offset, length):
        return ctypes.string_at(self._view + offset, length)

    def i32(self, offset):
        return int.from_bytes(self.read(offset, 4), 'little', signed=True)

    def u32(self, offset):
        return int.from_bytes(self.read(offset, 4), 'little', signed=False)

    def u8(self, offset):
        return self.read(offset, 1)[0]

    def flag(self, offset):
        return self.read(offset, 1)[0] != 0

    def close(self):
        if self._view:
            _kernel32.UnmapViewOfFile(self._view)
            self._view = None
        if self._handle:
            _kernel32.CloseHandle(self._handle)
            self._handle = None


def read_int32(shm, offset):
    return shm.i32(offset)


def read_byte(shm, offset):
    return shm.u8(offset)


def compute_led_bits(led_map, lbits):
    bits = 0
    for idx, offset, mask in led_map:
        if lbits[offset] & mask:
            bits |= (1 << idx)
    return bits


def ecm_bits_to_saft(ecm_state):
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
    return (False, False, False, False)


def compute_ecm_sr_data(shm2):
    sr_bits = 0
    for pgm in range(MAX_ECM_PROGRAMS):
        ecm_val = shm2.u32(OFF_FD2_ECMBITS + pgm * 4)
        s, a, f, t = ecm_bits_to_saft(ecm_val)
        base = pgm * 4
        if s: sr_bits |= (1 << (base + 0))
        if a: sr_bits |= (1 << (base + 1))
        if f: sr_bits |= (1 << (base + 2))
        if t: sr_bits |= (1 << (base + 3))
    return struct.pack('<I', sr_bits)


ZERO4 = bytes(4)


def build_bms_frame(led_bits, sr_data=ZERO4, uhf=(0, 0)):
    khz, preset = uhf
    payload = (struct.pack('<I', led_bits) + sr_data
               + struct.pack('<IB', khz & 0xFFFFFFFF, preset & 0xFF))
    checksum = 0
    for b in payload:
        checksum ^= b
    return BMS_SYNC + payload + bytes([checksum])


def read_uhf(shm2):
    if not shm2.ok:
        return (0, 0)
    try:
        preset = read_int32(shm2, OFF_FD2_UHF_PRESET)
        freq   = read_int32(shm2, OFF_FD2_UHF_FREQ)
    except Exception:
        return (0, 0)
    if not (100000 <= freq <= 999999):
        freq = 0
    if not (0 <= preset <= 99):
        preset = 0
    return (freq, preset)


class BmsDevice:
    def __init__(self, port, dev_type, ser):
        self.port = port
        self.dev_type = dev_type
        self.ser = ser
        self.prev_frame = None
        self.profile = DEVICE_PROFILES[dev_type]
        self.brt_seen = False

    def reset(self):
        self.prev_frame = None
        self.brt_seen = False

    def build_and_send(self, lbits, shm2):
        led_bits = compute_led_bits(self.profile['led_map'], lbits)

        if self.profile['has_backlight'] and shm2.ok:
            instr = read_byte(shm2, OFF_FD2_INSTRLIGHT)
            if instr >= 2 and not self.brt_seen:
                self.brt_seen = True
                print(f"[{self.port}] instrLight=2(BRT) -- DIM {DIM_PWM_LOWERED}")
            if instr == 0:
                brightness = 0
            elif instr >= 2:
                brightness = BRT_PWM
            else:
                brightness = DIM_PWM_LOWERED if self.brt_seen else DIM_PWM_DEFAULT
            led_bits |= (brightness << 16) | (brightness << 24)

        sr_data = compute_ecm_sr_data(shm2) if self.profile['has_ecm'] and shm2.ok else ZERO4
        uhf = read_uhf(shm2)
        frame = build_bms_frame(led_bits, sr_data, uhf)

        if frame != self.prev_frame:
            try:
                self.ser.write(frame)
                self.prev_frame = frame
            except Exception:
                pass

    def heartbeat(self):
        if self.prev_frame:
            try:
                self.ser.write(self.prev_frame)
            except Exception:
                pass


def run_bms(devices, mfd, hz=20, debug=False):
    """BMS 모드 루프. IsExitGame 또는 SHM 소실 시 return."""
    interval = 1.0 / hz
    shm  = ShmView(SHM_NAME, SHM_SIZE)
    shm2 = ShmView(SHM2_NAME, SHM2_SIZE)
    iv   = ShmView(IV_NAME, IV_SIZE)
    rx_bufs = {}
    print(f"[BMS] Update rate: {hz} Hz")

    try:
        while True:
            if not shm.ok:
                if not shm.open():
                    return
                print("[BMS] shared memory connected")
            if not shm2.ok:
                if shm2.open():
                    print("[BMS] FlightData2 connected")
            if not iv.ok:
                if iv.open():
                    print("[BMS] IntelliVibe connected")

            try:
                # IntelliVibe: BMS 가 종료 플래그를 세우면 즉시 복귀
                if iv.ok and iv.flag(OFF_IV_IS_EXIT_GAME):
                    print("[BMS] IsExitGame detected")
                    return

                lb  = read_int32(shm, OFF_LIGHTBITS)
                lb2 = read_int32(shm, OFF_LIGHTBITS2)
                lb3 = read_int32(shm, OFF_LIGHTBITS3)
                lbits = {OFF_LIGHTBITS: lb, OFF_LIGHTBITS2: lb2, OFF_LIGHTBITS3: lb3}

                if debug:
                    instr_dbg = read_byte(shm2, OFF_FD2_INSTRLIGHT) if shm2.ok else -1
                    print(f"  LB=0x{lb:08X} LB2=0x{lb2:08X} LB3=0x{lb3:08X} instr={instr_dbg}")

                for dev in devices:
                    dev.build_and_send(lbits, shm2)

                mfd.update_bms(shm2)

                if int(time.time() * hz) % hz == 0:
                    for dev in devices:
                        dev.heartbeat()

                for dev in devices:
                    read_serial_output(dev.port, dev.ser, rx_bufs)

            except Exception:
                # SHM read error -> BMS offline
                print("[BMS] SHM read error")
                return

            time.sleep(interval)

    except KeyboardInterrupt:
        raise
    finally:
        for dev in devices:
            dev.reset()
        mfd.reset()
        shm.close()
        shm2.close()
        iv.close()


# ================================================================
#  DCS — UDP, Frame Parser
# ================================================================

def update_mfd_from_dcsbios(data, mfd):
    i = 0
    while i + 3 < len(data) and data[i] == 0x55 and data[i+1] == 0x55 and data[i+2] == 0x55 and data[i+3] == 0x55:
        i += 4
    while i + 3 < len(data):
        addr = data[i] | (data[i+1] << 8)
        count = data[i+2] | (data[i+3] << 8)
        i += 4
        if addr == 0x5555 and count == 0x5555:
            break
        if i + count > len(data):
            break
        if addr <= DCS_LIGHT_INST_PNL < addr + count:
            off = DCS_LIGHT_INST_PNL - addr
            if i + off + 1 < len(data):
                val = data[i + off] | (data[i + off + 1] << 8)
                mfd.set_brightness(val >> 8)
        i += count


def parse_dcsbios_frame(data, watch_addrs):
    i = 0
    while i + 3 < len(data) and data[i] == 0x55 and data[i+1] == 0x55 and data[i+2] == 0x55 and data[i+3] == 0x55:
        i += 4
    while i + 3 < len(data):
        addr = data[i] | (data[i+1] << 8)
        count = data[i+2] | (data[i+3] << 8)
        i += 4
        if addr == 0x5555 and count == 0x5555:
            break
        if i + count > len(data):
            break
        for offset in range(0, count, 2):
            if i + offset + 1 < len(data):
                word_addr = addr + offset
                if word_addr in watch_addrs:
                    val = data[i + offset] | (data[i + offset + 1] << 8)
                    print(f"  [WATCH] 0x{word_addr:04X} = 0x{val:04X}")
        i += count


def create_dcs_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", DCS_MULTICAST_PORT))
    mreq = struct.pack("4s4s", socket.inet_aton(DCS_MULTICAST_GROUP),
                        socket.inet_aton("0.0.0.0"))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    return sock


def run_dcs(serials, mfd, udp_sock, watch_addrs=None, debug=False):
    """DCS 모드 루프. UDP 타임아웃이 지속되면 return."""
    rx_bufs = {}
    total_bytes = 0
    packet_count = 0
    last_status = time.time()
    last_data_time = time.time()
    receiving = False

    if watch_addrs is None:
        watch_addrs = set()

    port_names = ', '.join(p for p, _ in serials)
    udp_sock.settimeout(1.0)

    try:
        while True:
            try:
                data, addr = udp_sock.recvfrom(4096)
                if data:
                    for port, s in serials:
                        try:
                            s.write(data)
                        except serial.SerialException:
                            pass

                    if mfd.devices:
                        update_mfd_from_dcsbios(data, mfd)

                    if watch_addrs:
                        parse_dcsbios_frame(data, watch_addrs)

                    total_bytes += len(data)
                    packet_count += 1
                    last_data_time = time.time()

                    if not receiving:
                        receiving = True
                        print(f"[DCS] 데이터 수신 시작 (from {addr[0]})")

                    now = time.time()
                    if now - last_status >= 1.0:
                        print(f"  packets: {packet_count}, bytes: {total_bytes} -> {port_names}", end="\r")
                        last_status = now

            except socket.timeout:
                pass

            for port, s in serials:
                read_serial_output(port, s, rx_bufs)

            # Offline detection
            if receiving and time.time() - last_data_time > DCS_OFFLINE_TIMEOUT:
                print(f"\n[DCS] {DCS_OFFLINE_TIMEOUT}s 수신 없음")
                return
            if not receiving and time.time() - last_data_time > DCS_OFFLINE_TIMEOUT:
                return

    except KeyboardInterrupt:
        raise
    finally:
        if packet_count:
            print(f"\n[DCS] 총 {packet_count} packets, {total_bytes} bytes")
        mfd.reset()


# ================================================================
#  MFD BMS helper (instrLight adaptive logic)
# ================================================================

def _mfd_update_bms(self, shm2):
    if not self.devices or not shm2.ok:
        return
    instr = read_byte(shm2, OFF_FD2_INSTRLIGHT)
    if instr >= 2 and not self.brt_seen:
        self.brt_seen = True
    if instr == 0:
        brightness = 0
    elif instr >= 2:
        brightness = BRT_PWM
    else:
        brightness = DIM_PWM_LOWERED if self.brt_seen else DIM_PWM_DEFAULT
    self.set_brightness(brightness)

MfdBacklight.update_bms = _mfd_update_bms

# ================================================================
#  Main
# ================================================================

def main():
    parser = argparse.ArgumentParser(description='Unified Bridge -- BMS / DCS auto-detect')
    parser.add_argument('ports', nargs='*',
                        help='COM3:AUX COM4:CONSOLE (or just COM3 COM4)')
    parser.add_argument('--baud', type=int, default=SERIAL_BAUD)
    parser.add_argument('--hz', type=int, default=20, help='BMS poll rate')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--watch', type=str, default='',
                        help='DCS: hex addresses to watch (e.g. 0x4480,0x448A)')
    args = parser.parse_args()

    # --- Teensy port detection ---
    port_specs = []   # [(port, dev_type), ...]
    if args.ports:
        for pa in args.ports:
            if ':' in pa:
                port, dtype = pa.split(':', 1)
                dtype = dtype.upper()
                if dtype not in DEVICE_PROFILES:
                    print(f"알 수 없는 디바이스 타입: {dtype}")
                    sys.exit(1)
                port_specs.append((port, dtype))
            else:
                # PID로 타입 추정
                dtype = None
                for p in serial.tools.list_ports.comports():
                    if p.device == pa and p.vid == TEENSY_VID:
                        entry = PID_DEVICES.get(p.pid)
                        if entry:
                            dtype = entry[1]
                        break
                port_specs.append((pa, dtype))
    else:
        auto, descs = find_teensy_ports()
        if not auto:
            all_ports = serial.tools.list_ports.comports()
            print("Teensy를 자동 감지하지 못했습니다.")
            if all_ports:
                print("사용 가능한 COM 포트:")
                for p in all_ports:
                    vid = f"VID:0x{p.vid:04X}" if p.vid else "VID:N/A"
                    pid = f"PID:0x{p.pid:04X}" if p.pid else "PID:N/A"
                    print(f"  {p.device}: {p.description} [{vid} {pid}]")
            sys.exit(1)
        port_specs = auto

    # --- Open serial ports ---
    serials = []    # [(port, ser), ...]
    devices = []    # [BmsDevice, ...]  (for BMS mode)
    print("Teensy 연결:")
    for port, dtype in port_specs:
        try:
            s = serial.Serial(port, args.baud, timeout=0)
            serials.append((port, s))
            if dtype and dtype in DEVICE_PROFILES:
                devices.append(BmsDevice(port, dtype, s))
                name = next((n for _, (n, t) in PID_DEVICES.items() if t == dtype), dtype)
                print(f"  {port}: {name} [{dtype}]")
            else:
                print(f"  {port}: Unknown type (DCS only)")
        except serial.SerialException as e:
            print(f"  {port}: 열기 실패 -- {e}")

    if not serials:
        sys.exit(1)

    # --- MFD ---
    mfd = MfdBacklight()
    mfd.open()

    if sys.platform == 'win32':
        _HT = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong)
        def _handler(event):
            mfd.set_brightness(0)
            return False
        _href = _HT(_handler)
        ctypes.windll.kernel32.SetConsoleCtrlHandler(_href, True)

    # --- DCS UDP socket (bind once) ---
    udp_sock = create_dcs_socket()

    # --- Watch addresses ---
    watch_addrs = set()
    if args.watch:
        for a in args.watch.split(','):
            watch_addrs.add(int(a.strip(), 0))

    print("\n[Bridge] 대기 모드 -- BMS 또는 DCS 감지 중...\n")

    try:
        while True:
            # 1) BMS check (instant)
            if shm_exists(SHM_NAME):
                print("[Bridge] Falcon BMS 감지됨")
                run_bms(devices, mfd, hz=args.hz, debug=args.debug)
                print("[Bridge] BMS 오프라인 -- 대기 모드로 복귀\n")
                continue

            # 2) DCS check (1s timeout)
            udp_sock.settimeout(1.0)
            try:
                data, addr = udp_sock.recvfrom(4096)
                if data:
                    # First packet received -> enter DCS mode
                    # Forward this first packet immediately
                    for port, s in serials:
                        try:
                            s.write(data)
                        except serial.SerialException:
                            pass
                    print("[Bridge] DCS World 감지됨")
                    run_dcs(serials, mfd, udp_sock,
                            watch_addrs=watch_addrs, debug=args.debug)
                    print("[Bridge] DCS 오프라인 -- 대기 모드로 복귀\n")
            except socket.timeout:
                pass

    except KeyboardInterrupt:
        print("\n[Bridge] 종료.")
    finally:
        mfd.close()
        for _, s in serials:
            s.close()
        udp_sock.close()


if __name__ == '__main__':
    main()
