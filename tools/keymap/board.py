#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""보드에서 DX 맵을 읽고, BMS 콜백 목록을 다루는 부분.

직접 실행하는 파일이 아니라 **생성기가 import 하는 라이브러리**입니다:

    find_boards()      VID/PID 로 Teensy 찾기
    query_board(port)  "?DX" 를 보내 현재 DX 맵을 받기
    load_catalog()     BMS - Full.key 에서 콜백 목록 읽기
    next_out(base,ext) 비어 있는 번호를 붙인 출력 파일명

업로드된 펌웨어가 곧 심이 보는 장치이므로, 소스가 아니라 보드가 기준입니다.
생성기는 스케치 소스를 아예 읽지 않습니다.

브리지를 끄고 실행하십시오. Windows 는 COM 포트를 한 프로세스만 열 수 있고,
펌웨어도 프로토콜 미검출 상태에서만 "?DX" 에 응답합니다.
"""
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# 한글 콘솔(cp949)에서 줄표(—) 하나에 --help 가 터지는 것을 막습니다.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors='backslashreplace')
    except (AttributeError, ValueError):  # 파이프로 묶였을 때
        pass

def next_out(base, ext):
    """`base` + 비어 있는 가장 작은 번호 + `ext`. 전에 뽑은 걸 덮어쓰지 않게."""
    n = 1
    while os.path.exists('%s%d%s' % (base, n, ext)):
        n += 1
    return '%s%d%s' % (base, n, ext)


DEFAULT_BMS = r'C:\Falcon BMS 4.38'


# ----------------------------------------------------------------- 보드 질의
TEENSY_VID = 0x16C0
PID_DEVICES = {0x0487: 'AUX', 0x0489: 'AUX', 0x048E: 'CONSOLE'}


def _require_serial():
    try:
        import serial              # noqa: F401
        import serial.tools.list_ports
    except ImportError:
        raise SystemExit('pyserial 이 필요합니다:  pip install pyserial')
    return serial


def find_boards():
    """VID/PID 로 Teensy 를 찾아 [(포트, 'CONSOLE'|'AUX')] 반환."""
    serial = _require_serial()
    found = []
    for p in serial.tools.list_ports.comports():
        if p.vid == TEENSY_VID and p.pid in PID_DEVICES:
            found.append((p.device, PID_DEVICES[p.pid]))
    return found


class DumpParser(object):
    """펌웨어의 '#DX ...' 덤프를 누적 파싱. 완성되면 done 이 True.

    #DX BEGIN device=CONSOLE pid=0x048E entries=43 total=64
    #DX <첫 DX 번호> <차지하는 개수> <컨트롤 이름>
    #DX END
    """

    def __init__(self):
        self.device, self.entries, self.done = None, [], False

    def feed(self, line):
        line = line.strip()
        if not line.startswith('#DX '):
            return
        body = line[4:]
        if body.startswith('BEGIN'):
            m = re.search(r'device=(\w+)', body)
            self.device, self.entries, self.done = (m.group(1) if m else None), [], False
        elif body == 'END':
            self.done = True
        else:
            parts = body.split(None, 2)
            if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
                self.entries.append((int(parts[0]), parts[2], int(parts[1])))


def query_board(port, timeout=3.0):
    """'?DX' 를 보내고 #DX 덤프를 받아 (device, [(dx, 이름, 폭)]) 반환."""
    serial = _require_serial()
    with serial.Serial(port, 1000000, timeout=0.2) as ser:
        ser.reset_input_buffer()
        ser.write(b'?DX\n')
        ser.flush()
        p, deadline = DumpParser(), time.time() + timeout
        while time.time() < deadline:
            raw = ser.readline()
            if not raw:
                continue
            p.feed(raw.decode('ascii', 'replace'))
            if p.done:
                return p.device, p.entries
    raise SystemExit('%s: 보드가 "?DX" 에 응답하지 않았습니다.\n'
                     '  - 브리지가 돌고 있으면 끄십시오 (포트를 선점합니다)\n'
                     '  - 펌웨어가 이 기능이 들어간 빌드인지 확인하십시오\n'
                     '  - 보드 없이 쓰려면 --from-source' % port)


def load_catalog(bms_root):
    """BMS - Full.key 에서 콜백 → 사운드 ID. 콜백 실재 여부 검증에도 씁니다."""
    path = os.path.join(bms_root, 'User', 'Config', 'BMS - Full.key')
    if not os.path.isfile(path):
        raise SystemExit('BMS - Full.key 를 찾을 수 없습니다: %s\n'
                         '--bms-root 로 BMS 설치 경로를 지정하십시오.' % path)
    cat = {}
    pat = re.compile(r'^(\w+)\s+(-?\d+)\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+-?\d+\s+"(.*)"$')
    for line in open(path, encoding='utf-8', errors='replace'):
        m = pat.match(line.strip())
        if m and m.group(1) != 'SimDoNothing':
            cat.setdefault(m.group(1), (int(m.group(2)), m.group(3)))
    return cat
