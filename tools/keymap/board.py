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

브리지를 끄고 실행하십시오. Windows 는 COM 포트를 한 프로세스만 열 수 있어, 브리지가
떠 있으면 포트를 열지도 못합니다. 끈 뒤 몇 초 지나야 펌웨어가 프로토콜 미검출로
돌아와 "?DX" 에 답합니다 (콘솔 3초, AUX 6초).
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

    #DX BEGIN device=CONSOLE pid=0x048E entries=34 total=64
    #DX <첫 DX 번호> <차지하는 개수> <스위치 이름>
    #DX END
    """

    def __init__(self):
        self.device, self.entries, self.done = None, [], False
        self.expected_entries = self.total = None
        self.next_dx = 1
        self.names = set()

    def feed(self, line):
        line = line.strip()
        if not line.startswith('#DX '):
            return
        body = line[4:]
        if body.startswith('BEGIN'):
            m = re.fullmatch(r'BEGIN device=(\w+) pid=0x[0-9A-Fa-f]+ '
                             r'entries=(\d+) total=(\d+)', body)
            if not m or self.expected_entries is not None:
                raise ValueError('DX BEGIN 헤더가 잘못되었거나 중복되었습니다')
            self.device = m.group(1)
            self.expected_entries, self.total = int(m.group(2)), int(m.group(3))
            if not 1 <= self.expected_entries <= self.total <= 128:
                raise ValueError('DX 항목 수와 총 버튼 수는 1~128 범위여야 합니다')
        elif body == 'END':
            if self.expected_entries is None:
                raise ValueError('DX BEGIN 없이 END를 받았습니다')
            if len(self.entries) != self.expected_entries or self.next_dx != self.total + 1:
                raise ValueError('DX 응답의 항목 수 또는 총 버튼 수가 헤더와 다릅니다')
            self.done = True
        else:
            if self.expected_entries is None or self.done:
                raise ValueError('DX 항목이 BEGIN/END 범위 밖에 있습니다')
            parts = body.split(None, 2)
            if len(parts) != 3 or not parts[0].isdigit() or not parts[1].isdigit():
                raise ValueError('DX 항목 형식이 잘못되었습니다')
            dx, width, name = int(parts[0]), int(parts[1]), parts[2]
            if width < 1 or dx < 1 or dx + width - 1 > self.total:
                raise ValueError('DX 번호 또는 개수가 버튼 범위를 벗어났습니다')
            if dx != self.next_dx:
                raise ValueError('DX 번호가 중복되었거나 연속적이지 않습니다')
            if name in self.names or len(self.entries) >= self.expected_entries:
                raise ValueError('DX 컨트롤 이름이 중복되었거나 항목 수를 초과했습니다')
            self.entries.append((dx, name, width))
            self.names.add(name)
            self.next_dx = dx + width


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
            try:
                p.feed(raw.decode('ascii', 'replace'))
            except ValueError as exc:
                raise SystemExit('%s: 잘못된 DX 응답: %s' % (port, exc)) from exc
            if p.done:
                return p.device, p.entries
    raise SystemExit('%s: 보드가 "?DX" 에 응답하지 않았습니다.\n'
                     '  - 브리지가 돌고 있으면 끄십시오 (포트를 선점합니다)\n'
                     '  - 막 껐다면 몇 초 기다리십시오 — 프레임이 끊겨야 펌웨어가\n'
                     '    프로토콜 미검출로 돌아갑니다 (콘솔 3초, AUX 6초)\n'
                     '  - 펌웨어가 이 기능이 들어간 빌드인지 확인하십시오' % port)


def load_catalog(bms_root):
    """BMS - Full.key 에서 콜백 → 사운드 ID. 콜백 실재 여부 검증에도 씁니다."""
    path = os.path.join(bms_root, 'User', 'Config', 'BMS - Full.key')
    if not os.path.isfile(path):
        raise SystemExit('BMS - Full.key 를 찾을 수 없습니다: %s\n'
                         '--bms-root 로 BMS 설치 경로를 지정하십시오.' % path)
    cat = {}
    pat = re.compile(r'^(\w+)\s+(-?\d+)\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+-?\d+\s+"(.*)"$')
    with open(path, encoding='utf-8', errors='replace') as src:
        for line in src:
            m = pat.match(line.strip())
            if m and m.group(1) != 'SimDoNothing':
                cat.setdefault(m.group(1), (int(m.group(2)), m.group(3)))
    return cat
