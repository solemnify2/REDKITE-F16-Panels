#!/usr/bin/env python3
"""
Unified Bridge -- Falcon BMS / DCS World -> Teensy Serial

대기 모드에서 BMS 공유 메모리 또는 DCS-BIOS UDP를 감지하면
해당 모드로 전환하여 동작합니다. 심이 종료되면 다시 대기 모드로 복귀합니다.

기본은 트레이 상주입니다. 콘솔 창은 숨고 알림 영역에 아이콘만 남습니다
(아이콘 더블클릭하면 콘솔이 다시 보이고, 우클릭하면 메뉴가 나옵니다).
창으로 띄우려면 --foreground 를 주십시오.

사용법:
  python bridge.py                              (트레이 상주, 자동 감지)
  python bridge.py --foreground                 (콘솔 창으로)
  python bridge.py COM3:AUX COM4:CONSOLE        (수동 지정)
  python bridge.py --hz 20 --debug
"""

import os
import sys
import time
import struct
import socket
import argparse
import ctypes
import ctypes.wintypes as wt
import threading

def _alert(text, title='Redkite Bridge'):
    """치명적 오류를 알립니다. 콘솔이 없으면(=pythonw) 대화상자로 띄웁니다.

    없으면 창도 메시지도 없이 그냥 사라져 버려서, 무엇이 없어서 못 떴는지 알 길이
    없습니다.
    """
    try:
        print(text)
    except Exception:
        pass
    if sys.platform != 'win32':
        return
    k32 = ctypes.WinDLL('kernel32')
    u32 = ctypes.WinDLL('user32')
    hwnd = k32.GetConsoleWindow()

    # 이 콘솔에 우리만 붙어 있으면, 창은 우리가 끝나는 순간 같이 닫힙니다.
    # .py 를 더블클릭했을 때가 그렇습니다 — 글자는 찍히지만 읽을 틈이 없습니다.
    buf = (ctypes.c_uint32 * 8)()
    owned = k32.GetConsoleProcessList(buf, 8) == 1

    # 읽을 사람이 없을 때만 띄웁니다. 터미널에서 돌리는 중이면 출력으로 충분합니다.
    unseen = (not k32.GetConsoleCP()                       # pythonw — 콘솔 자체가 없음
              or (hwnd and not u32.IsWindowVisible(hwnd))  # 트레이가 숨겨 둔 콘솔
              or owned)                                    # 더블클릭 — 곧 닫힘
    if unseen:
        u32.MessageBoxW(None, text, title, 0x10)      # MB_ICONERROR


def _die(text, title='Redkite Bridge'):
    _alert(text, title)
    sys.exit(1)


def _ask(text, title='Redkite Bridge'):
    """예/아니오를 묻습니다. 물어볼 창을 띄울 수 없으면 콘솔로 묻습니다."""
    if sys.platform == 'win32':
        u32 = ctypes.WinDLL('user32')
        # MB_YESNO | MB_ICONQUESTION, IDYES == 6
        return u32.MessageBoxW(None, text, title, 0x04 | 0x20) == 6
    try:
        return input(text + ' [y/N] ').strip().lower().startswith('y')
    except EOFError:
        return False


def _need(module, package):
    """모듈을 가져오되, 없으면 설치할지 묻고 직접 깔아 줍니다.

    실행할 PC 마다 무엇을 깔아야 하는지 미리 알 수는 없습니다. 없으면 없다고만
    하고 끝내는 대신, 그 자리에서 받을 기회를 줍니다.
    """
    import importlib
    try:
        return importlib.import_module(module)
    except ImportError:
        pass
    if not _ask('%s 패키지가 필요합니다.\n\n지금 설치할까요?\n\n    pip install %s'
                % (package, package)):
        _die('%s 없이는 실행할 수 없습니다.\n\n설치:\n    pip install %s'
             % (package, package))

    import subprocess
    cmd = [sys.executable, '-m', 'pip', 'install', package]
    flags = 0x08000000 if sys.platform == 'win32' else 0   # CREATE_NO_WINDOW
    try:
        done = subprocess.run(cmd, capture_output=True, text=True,
                              creationflags=flags)
    except Exception as exc:                 # pip 자체를 못 부른 경우
        _die('설치를 실행하지 못했습니다: %s\n\n직접 설치하십시오:\n    pip install %s'
             % (exc, package))
    try:
        importlib.invalidate_caches()
        return importlib.import_module(module)
    except ImportError:
        tail = ((done.stderr or done.stdout or '').strip().splitlines() or [''])[-5:]
        _die('%s 설치에 실패했습니다.\n\n%s\n\n직접 설치하십시오:\n    pip install %s'
             % (package, '\n'.join(tail), package))


serial = _need('serial', 'pyserial')
import serial.tools.list_ports          # noqa: E402  (위에서 받아 온 뒤라야 됩니다)


# ================================================================
#  Constants — Common
# ================================================================

TEENSY_VID = 0x16C0
SERIAL_BAUD = 1000000

HERE = os.path.dirname(os.path.abspath(__file__))
TRAY_ICON = os.path.join(HERE, 'bridge-plain.ico')

# 트레이에서 종료를 고르면 올라갑니다. 심 모드 루프도 이걸 보고 빠져나옵니다.
STOP = threading.Event()

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
BMS_EXIT_WAIT = 15.0       # 종료한 세션의 SHM 정리를 기다리는 상한(초)

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

_kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
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
    """SHM이 존재하는지만 확인합니다. 섹션을 만들거나 붙들지 않습니다.

    "이름이 조회되는가"일 뿐 "BMS가 살아 있는가"가 아닙니다. 이름은 마지막
    핸들이 닫혀야 사라지므로, 죽어가는 세션도 새로 뜬 세션도 똑같이 True입니다.
    """
    handle = _kernel32.OpenFileMappingW(FILE_MAP_READ, False, name)
    if not handle:
        return False
    _kernel32.CloseHandle(handle)
    return True


def exit_flag_set():
    """IntelliVibe의 IsExitGame. 읽고 바로 놓습니다 — 섹션을 붙들지 않습니다."""
    iv = ShmView(IV_NAME, IV_SIZE)
    if not iv.open():
        return False
    try:
        return iv.flag(OFF_IV_IS_EXIT_GAME)
    except Exception:
        return False
    finally:
        iv.close()


def wait_for_bms_gone(timeout=BMS_EXIT_WAIT):
    """종료한 세션의 SHM이 정리되길 기다립니다.

    이름만 보고 기다리면 BMS를 곧바로 다시 켰을 때 새 세션의 섹션을 이전 세션으로
    착각해 영영 빠져나오지 못합니다. IsExitGame을 같이 봅니다 — 새 세션이 만든
    섹션에서는 내려가 있으므로, 그때는 기다리지 않고 바로 다시 붙습니다.

    상한을 두는 것은 다른 BMS 도구가 핸들을 쥐고 있거나 BMS가 종료 도중 멈춰서
    이름이 영영 남는 경우에 갇히지 않기 위해서입니다.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not shm_exists(SHM_NAME):
            return
        if not exit_flag_set():
            print("[Bridge] 새 BMS 세션 감지")
            return
        time.sleep(0.5)
    print("[Bridge] SHM이 %.0f초 동안 남아 있습니다 -- 그대로 진행합니다" % timeout)


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
        while not STOP.is_set():
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
#  Tray — Windows 알림 영역 아이콘 + 콘솔 관리
# ================================================================

_user32  = ctypes.WinDLL('user32',  use_last_error=True)
_shell32 = ctypes.WinDLL('shell32', use_last_error=True)
_ole32   = ctypes.OleDLL('ole32')

WM_DESTROY       = 0x0002
WM_COMMAND       = 0x0111
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP     = 0x0205
WM_TRAY          = 0x0401       # WM_APP+1
NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
NIF_MESSAGE, NIF_ICON, NIF_TIP = 0x01, 0x02, 0x04
IMAGE_ICON          = 1
LR_LOADFROMFILE     = 0x0010
LR_DEFAULTSIZE      = 0x0040
MF_STRING, MF_SEPARATOR, MF_GRAYED = 0x0000, 0x0800, 0x0001
TPM_RIGHTBUTTON     = 0x0002
SW_HIDE, SW_SHOW, SW_RESTORE = 0, 5, 9
CW_USEDEFAULT       = -0x80000000

_LRESULT = ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long
_WNDPROC = ctypes.WINFUNCTYPE(_LRESULT, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)


class _WNDCLASSW(ctypes.Structure):
    _fields_ = [('style', wt.UINT), ('lpfnWndProc', _WNDPROC),
                ('cbClsExtra', ctypes.c_int), ('cbWndExtra', ctypes.c_int),
                ('hInstance', wt.HINSTANCE), ('hIcon', wt.HICON),
                ('hCursor', wt.HANDLE), ('hbrBackground', wt.HBRUSH),
                ('lpszMenuName', wt.LPCWSTR), ('lpszClassName', wt.LPCWSTR)]


class _NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [('cbSize', wt.DWORD), ('hWnd', wt.HWND), ('uID', wt.UINT),
                ('uFlags', wt.UINT), ('uCallbackMessage', wt.UINT),
                ('hIcon', wt.HICON), ('szTip', wt.WCHAR * 128),
                ('dwState', wt.DWORD), ('dwStateMask', wt.DWORD),
                ('szInfo', wt.WCHAR * 256), ('uVersion', wt.UINT),
                ('szInfoTitle', wt.WCHAR * 64), ('dwInfoFlags', wt.DWORD)]


class _GUID(ctypes.Structure):
    _fields_ = [('Data1', wt.DWORD), ('Data2', wt.WORD), ('Data3', wt.WORD),
                ('Data4', ctypes.c_ubyte * 8)]


# --- user32 argtypes ---
_user32.DefWindowProcW.restype  = _LRESULT
_user32.DefWindowProcW.argtypes = (wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
_user32.CreateWindowExW.restype  = wt.HWND
_user32.CreateWindowExW.argtypes = (
    wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID)
_user32.LoadImageW.restype  = wt.HANDLE
_user32.LoadImageW.argtypes = (wt.HINSTANCE, wt.LPCWSTR, wt.UINT,
                               ctypes.c_int, ctypes.c_int, wt.UINT)
_user32.LoadIconW.restype  = wt.HICON
_user32.LoadIconW.argtypes = (wt.HINSTANCE, wt.LPCWSTR)
_user32.CreatePopupMenu.restype = wt.HMENU
_user32.AppendMenuW.argtypes    = (wt.HMENU, wt.UINT, ctypes.c_void_p, wt.LPCWSTR)
_user32.TrackPopupMenu.argtypes = (wt.HMENU, wt.UINT, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, wt.HWND, wt.LPVOID)
_user32.PostMessageW.argtypes       = (wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
_user32.ShowWindow.argtypes         = (wt.HWND, ctypes.c_int)
_user32.IsWindowVisible.argtypes    = (wt.HWND,)
_user32.IsIconic.argtypes           = (wt.HWND,)
_user32.IsIconic.restype            = wt.BOOL
_user32.SetForegroundWindow.argtypes = (wt.HWND,)
_user32.DestroyMenu.argtypes        = (wt.HMENU,)
_shell32.Shell_NotifyIconW.argtypes  = (wt.DWORD, ctypes.c_void_p)
_kernel32.GetConsoleWindow.restype   = wt.HWND
_kernel32.GetConsoleCP.restype       = wt.UINT
_kernel32.SetConsoleTitleW.argtypes  = (wt.LPCWSTR,)
_kernel32.GetModuleHandleW.restype   = wt.HMODULE
_kernel32.GetModuleHandleW.argtypes  = (wt.LPCWSTR,)

# --- ITaskbarList COM (작업표시줄 항목 삭제용) ---
_CLSID_TaskbarList = _GUID(0x56FDF344, 0xFD6D, 0x11D0,
                           (ctypes.c_ubyte * 8)(0x95, 0x8A, 0x00, 0x60, 0x97, 0xC9, 0xA0, 0x90))
_IID_ITaskbarList  = _GUID(0x56FDF342, 0xFD6D, 0x11D0,
                           (ctypes.c_ubyte * 8)(0x95, 0x8A, 0x00, 0x60, 0x97, 0xC9, 0xA0, 0x90))


def _taskbar_delete_tab(hwnd):
    """ITaskbarList::DeleteTab — 작업표시줄에서 창을 직접 제거합니다."""
    _ole32.CoInitialize(None)
    p = ctypes.c_void_p()
    hr = _ole32.CoCreateInstance(ctypes.byref(_CLSID_TaskbarList), None, 1,
                                ctypes.byref(_IID_ITaskbarList), ctypes.byref(p))
    if hr != 0 or not p:
        return
    vtbl = ctypes.cast(ctypes.cast(p, ctypes.POINTER(ctypes.c_void_p))[0],
                       ctypes.POINTER(ctypes.c_void_p * 6))[0]
    _FT = ctypes.WINFUNCTYPE
    _FT(ctypes.HRESULT, ctypes.c_void_p)(vtbl[3])(p)                   # HrInit
    _FT(ctypes.HRESULT, ctypes.c_void_p, wt.HWND)(vtbl[5])(p, hwnd)    # DeleteTab
    _FT(ctypes.c_ulong, ctypes.c_void_p)(vtbl[2])(p)                   # Release


def _reopen_stdio():
    """stdout/stderr 를 현재 콘솔(CONOUT$)에 묶습니다."""
    try:
        sys.stdout = open('CONOUT$', 'w', encoding='utf-8',
                          errors='backslashreplace', buffering=1)
        sys.stderr = sys.stdout
    except OSError:
        sys.stdout = sys.stderr = open(os.devnull, 'w')


def _console_window():
    hwnd = _kernel32.GetConsoleWindow()
    return hwnd or None


def ensure_console(title=None, show=True):
    """콘솔을 마련하고 print 가 거기로 가게 합니다. 콘솔 창 핸들을 돌려줍니다."""
    if sys.platform != 'win32':
        return None
    if not _kernel32.GetConsoleCP():
        _kernel32.AllocConsole()
        _reopen_stdio()
    elif sys.stdout is None:
        _reopen_stdio()
    if title:
        _kernel32.SetConsoleTitleW(title)
    hwnd = _kernel32.GetConsoleWindow()
    if hwnd:
        _user32.ShowWindow(hwnd, SW_SHOW if show else SW_HIDE)
    return hwnd or None


class Tray:
    """Windows 알림 영역(트레이) 아이콘."""

    FIRST_ID = 0x1000

    def __init__(self, icon_path, tooltip='', on_quit=None, title='Bridge'):
        self.icon_path = icon_path
        self.tooltip = tooltip
        self.on_quit = on_quit
        self.title = title
        self.items = []
        self.hwnd = None
        self._nid = None
        self._proc = _WNDPROC(self._wndproc)
        self._console = _console_window()

    def item(self, label, action=None):
        self.items.append((label, action))

    def separator(self):
        self.items.append((None, None))

    def toggle_console(self):
        if self._console:
            if _user32.IsWindowVisible(self._console) and not _user32.IsIconic(self._console):
                _user32.ShowWindow(self._console, SW_HIDE)
            else:
                _user32.ShowWindow(self._console, SW_RESTORE)
                _user32.SetForegroundWindow(self._console)
                _taskbar_delete_tab(self._console)

    def hide_console(self):
        if self._console:
            _user32.ShowWindow(self._console, SW_HIDE)

    def show_console(self):
        if self._console:
            _user32.ShowWindow(self._console, SW_RESTORE)
            _user32.SetForegroundWindow(self._console)
            _taskbar_delete_tab(self._console)

    def set_tooltip(self, text):
        self.tooltip = text
        if self._nid is not None:
            self._nid.szTip = text[:127]
            _shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self._nid))

    def stop(self):
        if self.hwnd:
            _user32.PostMessageW(self.hwnd, WM_DESTROY, 0, 0)

    def _wndproc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAY:
            if lparam in (WM_RBUTTONUP, 0x0007):
                self._popup()
            elif lparam == WM_LBUTTONDBLCLK:
                self.toggle_console()
            return 0
        if msg == WM_COMMAND:
            index = (wparam & 0xFFFF) - self.FIRST_ID
            if 0 <= index < len(self.items):
                action = self.items[index][1]
                if action:
                    action()
            return 0
        if msg == WM_DESTROY:
            self._remove()
            _user32.PostQuitMessage(0)
            return 0
        return _user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _popup(self):
        menu = _user32.CreatePopupMenu()
        for i, (label, action) in enumerate(self.items):
            if label is None:
                _user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
            else:
                flags = MF_STRING | (0 if action else MF_GRAYED)
                _user32.AppendMenuW(menu, flags, self.FIRST_ID + i, label)
        pos = wt.POINT()
        _user32.GetCursorPos(ctypes.byref(pos))
        _user32.SetForegroundWindow(self.hwnd)
        _user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON, pos.x, pos.y, 0, self.hwnd, None)
        _user32.PostMessageW(self.hwnd, 0, 0, 0)
        _user32.DestroyMenu(menu)

    def _remove(self):
        if self._nid is not None:
            _shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self._nid))
            self._nid = None

    def _create(self):
        hinst = _kernel32.GetModuleHandleW(None)
        cls = _WNDCLASSW()
        cls.lpfnWndProc = self._proc
        cls.hInstance = hinst
        cls.lpszClassName = 'RedkiteBridgeTray'
        if not _user32.RegisterClassW(ctypes.byref(cls)):
            err = ctypes.get_last_error()
            if err != 1410:
                raise ctypes.WinError(err)
        self.hwnd = _user32.CreateWindowExW(
            0, cls.lpszClassName, self.title, 0,
            CW_USEDEFAULT, CW_USEDEFAULT, 0, 0, None, None, hinst, None)
        if not self.hwnd:
            raise ctypes.WinError(ctypes.get_last_error())

        hicon = None
        if self.icon_path and os.path.isfile(self.icon_path):
            hicon = _user32.LoadImageW(None, self.icon_path, IMAGE_ICON, 0, 0,
                                       LR_LOADFROMFILE | LR_DEFAULTSIZE)
        if not hicon:
            hicon = _user32.LoadIconW(None, ctypes.c_wchar_p(32512))

        nid = _NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(_NOTIFYICONDATAW)
        nid.hWnd = self.hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAY
        nid.hIcon = hicon
        nid.szTip = self.tooltip[:127]
        if not _shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid)):
            raise ctypes.WinError(ctypes.get_last_error())
        self._nid = nid

    def run(self):
        self._create()
        if self._console:
            _taskbar_delete_tab(self._console)
        msg = wt.MSG()
        try:
            while _user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                _user32.TranslateMessage(ctypes.byref(msg))
                _user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            self._remove()
            if self.on_quit:
                self.on_quit()


# ================================================================
#  Main
# ================================================================

def run_tray(work, title='Redkite Bridge'):
    """일은 뒤 스레드에 맡기고, 이 스레드는 트레이 메시지를 돕니다."""
    icon = Tray(TRAY_ICON, title, title=title)
    icon.item(title)
    icon.separator()
    icon.item('콘솔 보기/숨기기', icon.toggle_console)
    icon.item('종료', icon.stop)

    def status(text):
        icon.items[0] = (text, None)
        icon.set_tooltip('%s — %s' % (title, text))

    worker = threading.Thread(target=work, kwargs={'status': status}, daemon=True)
    worker.start()
    try:
        icon.run()
    finally:
        STOP.set()
        worker.join(timeout=5.0)


def main():
    parser = argparse.ArgumentParser(description='Unified Bridge -- BMS / DCS auto-detect')
    parser.add_argument('ports', nargs='*',
                        help='COM3:AUX COM4:CONSOLE (or just COM3 COM4)')
    parser.add_argument('--baud', type=int, default=SERIAL_BAUD)
    parser.add_argument('--hz', type=int, default=20, help='BMS poll rate')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--watch', type=str, default='',
                        help='DCS: hex addresses to watch (e.g. 0x4480,0x448A)')
    parser.add_argument('--foreground', action='store_true',
                        help='트레이에 넣지 않고 콘솔 창으로 돌립니다')
    args = parser.parse_args()

    # 트레이 모드에서 python.exe 로 실행됐으면 pythonw.exe 로 재실행합니다.
    # python.exe 는 부모 터미널(Windows Terminal 등)을 물고 들어오므로
    # 작업표시줄에서 뺄 수 없습니다. pythonw.exe 는 터미널 없이 시작되어
    # AllocConsole 으로 자체 콘솔을 만들면 완전히 제어할 수 있습니다.
    if (sys.platform == 'win32' and not args.foreground
            and os.path.basename(sys.executable).lower().startswith('python')
            and not os.path.basename(sys.executable).lower().startswith('pythonw')):
        import subprocess
        pythonw = os.path.join(os.path.dirname(sys.executable),
                               os.path.basename(sys.executable).replace('python', 'pythonw', 1))
        if os.path.exists(pythonw):
            subprocess.Popen([pythonw, os.path.abspath(__file__)] + sys.argv[1:],
                             creationflags=subprocess.DETACHED_PROCESS)
            sys.exit(0)

    if sys.platform == 'win32':
        ensure_console('Redkite Bridge', show=args.foreground)
    elif sys.stdout is None:
        sys.stdout = sys.stderr = open(os.devnull, 'w')

    # --- Teensy port detection ---
    port_specs = []   # [(port, dev_type), ...]
    if args.ports:
        for pa in args.ports:
            if ':' in pa:
                port, dtype = pa.split(':', 1)
                dtype = dtype.upper()
                if dtype not in DEVICE_PROFILES:
                    _die(f"알 수 없는 디바이스 타입: {dtype}")
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
            lines = ["Teensy를 자동 감지하지 못했습니다.",
                     "USB 연결과 펌웨어 업로드 상태를 확인하십시오."]
            if all_ports:
                lines.append("")
                lines.append("보이는 COM 포트:")
                for p in all_ports:
                    vid = f"VID:0x{p.vid:04X}" if p.vid else "VID:N/A"
                    pid = f"PID:0x{p.pid:04X}" if p.pid else "PID:N/A"
                    lines.append(f"  {p.device}: {p.description} [{vid} {pid}]")
            _die(chr(10).join(lines))
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
        _die('열 수 있는 포트가 없습니다.' + '\n' + '\n' +
             '다른 프로그램이 같은 COM 포트를 쓰고 있는지 확인하십시오 — '
             'Windows 는 포트 하나를 한 프로세스만 엽니다.')

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

    WAITING = "대기 모드 -- BMS 또는 DCS 감지 중"

    def work(status=None):
        """대기 ↔ 심 모드를 오가는 본체. 트레이 모드에서는 뒤 스레드에서 돕니다."""
        def say(text):
            print("[Bridge] " + text)
            if status:
                status(text)

        say(WAITING)
        try:
            while not STOP.is_set():
                # 1) BMS check (instant)
                if shm_exists(SHM_NAME):
                    say("Falcon BMS")
                    run_bms(devices, mfd, hz=args.hz, debug=args.debug)
                    if STOP.is_set():
                        break
                    wait_for_bms_gone()
                    say(WAITING)
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
                        say("DCS World")
                        run_dcs(serials, mfd, udp_sock,
                                watch_addrs=watch_addrs, debug=args.debug)
                        if STOP.is_set():
                            break
                        say(WAITING)
                except socket.timeout:
                    pass
        except KeyboardInterrupt:
            print("\n[Bridge] 종료.")

    try:
        if args.foreground:
            work()
        else:
            run_tray(work)
    finally:
        mfd.close()
        for _, s in serials:
            s.close()
        udp_sock.close()


if __name__ == '__main__':
    main()
