#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""BMS 공유 메모리와 프로세스를 같이 들여다보는 진단 도구.

    python tools/bms_shm_probe.py

0.5초마다 한 줄씩 찍습니다. BMS 를 켜고 비행에 들어갔다가 **정상 종료**시키면서
무엇이 언제 바뀌는지 보려는 것입니다. 보려는 것은 세 가지입니다:

  1. BMS 가 종료할 때 `IsExitGame` 이 실제로 true 가 되는가
  2. 종료하면 섹션이 사라지는가 (= OpenFileMapping 이 실패하는가)
  3. `currentTime` 이 메뉴/일시정지에서 어떻게 움직이는가

**이 도구는 섹션을 쥐지 않습니다.** 매번 `OpenFileMapping` 으로 열고, 읽고, 바로
닫습니다. `CreateFileMapping` 을 쓰지 않으므로 없는 섹션을 새로 만들 일도 없습니다.
`mmap.mmap(-1, size, tagname=...)` 은 "있으면 열고 없으면 만든다" 라서, 그걸 쓰면
도구 자신이 섹션을 살려두게 되어 2번을 영원히 관측할 수 없습니다.

    --hold    일부러 매핑을 붙들고 있습니다 (tools/bridge.py 의 현재 동작).
              BMS 를 꺼도 섹션이 안 사라지는 것을 눈으로 확인하는 용도입니다.

오프셋은 C:\Falcon BMS 4.38\Tools\SharedMem\FlightData.h / IVibeData.h 에서
구조체를 복원해 계산했고, 브리지가 이미 쓰는 네 오프셋(48/52/1104/1180)이
그대로 재현되는 것으로 검증했습니다. VERSION 열로 실행 중인 BMS 와도 맞는지
확인하십시오 — 헤더의 FLIGHTDATA2_VERSION 은 22 입니다.
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import sys
import time

FD2_NAME = 'FalconSharedMemoryArea2'
FD2_SIZE = 1276
OFF_CURRENT_TIME = 68          # int32  — 심 시계(초)
OFF_VERSION_NUM = 76           # int32  — FlightData2 버전

IV_NAME = 'FalconIntellivibeSharedMemoryArea'
IV_SIZE = 52
OFF_IS_END_FLIGHT = 13         # bool
OFF_IN_3D = 15                 # bool
OFF_IS_PAUSED = 16             # bool
OFF_IS_EXIT_GAME = 20          # bool

FILE_MAP_READ = 0x0004
TH32CS_SNAPPROCESS = 0x0002

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
k32.OpenFileMappingW.restype = wt.HANDLE
k32.OpenFileMappingW.argtypes = (wt.DWORD, wt.BOOL, wt.LPCWSTR)
k32.MapViewOfFile.restype = wt.LPVOID
k32.MapViewOfFile.argtypes = (wt.HANDLE, wt.DWORD, wt.DWORD, wt.DWORD, ctypes.c_size_t)
k32.UnmapViewOfFile.argtypes = (wt.LPVOID,)
k32.CloseHandle.argtypes = (wt.HANDLE,)
k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
k32.CreateToolhelp32Snapshot.argtypes = (wt.DWORD, wt.DWORD)
INVALID_HANDLE = ctypes.c_void_p(-1).value


class Section(object):
    """이름 붙은 공유 메모리 한 벌. 열기만 하고, 만들지는 않습니다."""

    def __init__(self, name, size):
        self.name, self.size = name, size
        self.handle = self.view = None

    def open(self):
        self.handle = k32.OpenFileMappingW(FILE_MAP_READ, False, self.name)
        if not self.handle:
            return False
        self.view = k32.MapViewOfFile(self.handle, FILE_MAP_READ, 0, 0, self.size)
        if not self.view:
            k32.CloseHandle(self.handle)
            self.handle = None
            return False
        return True

    def close(self):
        # 핸들만 닫는 것으로는 부족합니다. 매핑된 뷰가 남아 있으면 그것만으로
        # 커널 섹션이 계속 살아 있어, 종료를 관측할 수 없게 됩니다.
        if self.view:
            k32.UnmapViewOfFile(self.view)
            self.view = None
        if self.handle:
            k32.CloseHandle(self.handle)
            self.handle = None

    def read(self, offset, length):
        return ctypes.string_at(self.view + offset, length)

    def i32(self, offset):
        return int.from_bytes(self.read(offset, 4), 'little', signed=True)

    def flag(self, offset):
        return self.read(offset, 1)[0] != 0


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('cntUsage', wt.DWORD),
                ('th32ProcessID', wt.DWORD),
                ('th32DefaultHeapID', ctypes.POINTER(ctypes.c_ulong)),
                ('th32ModuleID', wt.DWORD), ('cntThreads', wt.DWORD),
                ('th32ParentProcessID', wt.DWORD), ('pcPriClassBase', wt.LONG),
                ('dwFlags', wt.DWORD), ('szExeFile', wt.WCHAR * 260)]


def falcon_processes():
    """이름에 'falcon' 이 든 프로세스. 실행 파일 이름을 확인하는 용도이기도 합니다."""
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if not snap or snap == INVALID_HANDLE:
        return []
    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(entry)
    found = []
    try:
        if not k32.Process32FirstW(snap, ctypes.byref(entry)):
            return []
        while True:
            if 'falcon' in entry.szExeFile.lower():
                found.append(entry.szExeFile)
            if not k32.Process32NextW(snap, ctypes.byref(entry)):
                break
    finally:
        k32.CloseHandle(snap)
    return found


def sample(fd2, iv, hold):
    """한 줄 분량의 상태. hold 면 열어둔 채로, 아니면 매번 열고 닫습니다."""
    row = {}
    for key, sec in (('fd2', fd2), ('iv', iv)):
        if hold and sec.view is not None:
            row[key] = True          # 한 번 연 뒤로는 계속 들고 있습니다
        else:
            row[key] = sec.open()
    row['time'] = fd2.i32(OFF_CURRENT_TIME) if row['fd2'] else None
    row['ver'] = fd2.i32(OFF_VERSION_NUM) if row['fd2'] else None
    if row['iv']:
        row['in3d'] = iv.flag(OFF_IN_3D)
        row['paused'] = iv.flag(OFF_IS_PAUSED)
        row['exit'] = iv.flag(OFF_IS_EXIT_GAME)
        row['endflt'] = iv.flag(OFF_IS_END_FLIGHT)
    if not hold:
        fd2.close()
        iv.close()
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--hold', action='store_true',
                    help='매핑을 붙들고 있습니다 — bridge.py 의 현재 동작 재현')
    ap.add_argument('--interval', type=float, default=0.5, metavar='초')
    args = ap.parse_args()

    if not sys.platform.startswith('win'):
        raise SystemExit('Windows 전용입니다.')

    fd2 = Section(FD2_NAME, FD2_SIZE)
    iv = Section(IV_NAME, IV_SIZE)

    print('섹션을 %s' % ('붙들고 봅니다 (bridge.py 동작)' if args.hold
                         else '매번 열고 닫습니다'))
    print('BMS 를 켜고 3D 에 들어갔다가 정상 종료해 보십시오. Ctrl+C 로 끝냅니다.\n')
    print('시각      FD2  시계      VER  IVIBE  In3D   Paused  EndFlt  ExitGame  프로세스')

    prev = None
    try:
        while True:
            row = sample(fd2, iv, args.hold)
            procs = falcon_processes()
            line = '%s  %-3s  %-8s  %-3s  %-5s  %-5s  %-6s  %-6s  %-8s  %s' % (
                time.strftime('%H:%M:%S'),
                'O' if row['fd2'] else '-',
                row['time'] if row['fd2'] else '-',
                row['ver'] if row['fd2'] else '-',
                'O' if row['iv'] else '-',
                row.get('in3d', '-'), row.get('paused', '-'),
                row.get('endflt', '-'), row.get('exit', '-'),
                ', '.join(procs) or '-')
            # 바뀐 순간이 눈에 띄도록, 같은 상태는 시계만 흐르고 줄은 덮어씁니다.
            key = (tuple(procs), row['fd2'], row['iv'], row.get('in3d'),
                   row.get('paused'), row.get('endflt'), row.get('exit'))
            end = '\n' if key != prev else '\r'
            sys.stdout.write(line + end)
            sys.stdout.flush()
            prev = key
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('\n\n마지막으로 보인 falcon 프로세스: %s' % (falcon_processes() or '없음'))
    finally:
        fd2.close()
        iv.close()


if __name__ == '__main__':
    sys.exit(main())
