#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""보드에서 DX 맵을 읽고, BMS 콜백 목록을 다루는 부분.

직접 실행하는 파일이 아니라 **생성기가 import 하는 라이브러리**입니다:

    find_boards()      VID/PID 로 Teensy 찾기
    query_board(port)  "?DX" 를 보내 현재 DX 맵을 받기
    dx_map(ino)        스케치 소스의 dxOrder[] 읽기 (--verify 용)
    load_catalog()     BMS - Full.key 에서 콜백 목록 읽기
    check_unmodeled()  UNMODELED 검색어를 현재 목록에 다시 걸어 보기
    next_out(base,ext) 비어 있는 번호를 붙인 출력 파일명

업로드된 펜웨어가 곰 심이 보는 장치이므로, 소스가 아니라 보드가 기준입니다.
그래서 생성기는 항상 보드에 물어보고, `--verify` 가 둘을 대조합니다.

브리지를 끄고 실행하십시오. Windows 는 COM 포트를 한 프로세스만 열 수 있고,
펜웨어도 프로토콜 미검출 상태에서만 "?DX" 에 응답합니다.
"""
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))   # 리포 루트

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

SKETCHES = {
    'CONSOLE': 'F16_LEFT_CONSOLE/F16_LEFT_CONSOLE.ino',
    'AUX':     'F16_LEFT_AUX_MISC/F16_LEFT_AUX_MISC.ino',
}

COVER_NAMES = ['ENG CONT COVER', 'EPU OFF COVER', 'EPU ON COVER']
COMMPWR_NAMES = ['COMM1 PWR', 'COMM2 PWR']


# ----------------------------------------------------------------- 소스 파싱
def _strip(src):
    src = re.sub(r'/\*.*?\*/', '', src, flags=re.S)
    return '\n'.join(re.sub(r'//.*$', '', ln) for ln in src.split('\n'))


def _array(src, name):
    m = re.search(r'\b' + name + r'\[\]\s*=\s*\{', src)
    if not m:
        return []
    i, depth = m.end(), 1
    while depth:
        if src[i] == '{':
            depth += 1
        elif src[i] == '}':
            depth -= 1
        i += 1
    body = src[m.end():i - 1]
    return [[f.strip() for f in e.split(',')] for e in re.findall(r'\{([^{}]*)\}', body)]


def dx_map(path):
    """dxOrder[] 를 assignButtons() 와 같은 규칙으로 펼쳐 [(dx, 이름, 폭)] 반환."""
    src = _strip(open(path, encoding='utf-8').read())
    sw = _array(src, 'switches')
    enc = _array(src, 'encoders')
    ana = _array(src, 'analogBtnArrays')
    order = _array(src, 'dxOrder')
    if not order:
        raise SystemExit('%s: dxOrder[] 를 찾지 못했습니다' % path)
    width = {'SW_ON_OFF': 1, 'SW_ON_OFF_ON': 2, 'SW_ON_OFF_NC': 1}
    nm = lambda f: f.strip().strip('"')  # noqa: E731

    out, dx = [], 1
    for kind, idx in [(e[0], int(e[1])) for e in order]:
        if kind == 'DX_SW':
            e = sw[idx]
            name = nm(e[0])
            w = int(e[6]) if e[2] == 'SW_ROTARY' else width[e[2]]
        elif kind == 'DX_LADDER':
            name, w = nm(ana[idx][0]), int(ana[idx][3])
        elif kind == 'DX_ENC':
            name, w = nm(enc[idx][0]), 2
        elif kind == 'DX_COVER':
            name, w = COVER_NAMES[idx], 1
        elif kind == 'DX_COMMPWR':
            name, w = COMMPWR_NAMES[idx], 1
        else:
            raise SystemExit('알 수 없는 DxKind: %s' % kind)
        out.append((dx, name, w))
        dx += w
    return out


# --------------------------------------------------------------- 보드 질의
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


# ----------------------------------------------------------------- 줄 생성
CATALOG_BASELINE = os.path.join(HERE, 'bms_catalog.txt')

# DX 바인딩 줄: <Callback> <DX#> <-1|-2> -2 ...
#  4번째 필드가 리터럴 -2 인 것이 DX 바인딩의 표식입니다. 키보드 줄은
#  그 자리에 스캔코드(0x3B 등)가 오므로 섞일 일이 없습니다.
def check_unmodeled(unmodeled_all, catalog):
    """UNMODELED 자리의 검색어를 현재 콜백 목록에 다시 걸어 본다.

    BMS 버전업으로 지원이 생기면 여기서 걸립니다. 사람이 기억할 필요 없이
    키 파일을 다시 뽑을 때마다 자동으로 확인됩니다.
    """
    hits = []
    for dev, dx, label, bind in unmodeled_all:
        found = []
        for pat in bind.patterns:
            try:
                rx = re.compile(pat, re.I)
            except re.error:
                continue
            for cb, (snd, desc) in catalog.items():
                if rx.search(cb) or rx.search(desc):
                    found.append((cb, desc))
        if found:
            hits.append((dev, dx, label, sorted(set(found))))
    return hits


def catalog_diff(catalog):
    """콜백 목록을 커밋된 기준선과 비교. (추가, 삭제) 반환."""
    if not os.path.isfile(CATALOG_BASELINE):
        return None, None
    old = set()
    for line in open(CATALOG_BASELINE, encoding='utf-8'):
        line = line.strip()
        if line and not line.startswith('#'):
            old.add(line.split(None, 1)[0])
    new = set(catalog)
    return sorted(new - old), sorted(old - new)


def write_catalog_baseline(catalog):
    with open(CATALOG_BASELINE, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# Falcon BMS 콜백 목록 기준선 — BMS - Full.key 에서 생성.\n'
                '# 생성기가 매번 이 파일과 현재 BMS 를 비교해,\n'
                '# 버전업으로 추가/삭제된 콜백을 알려줍니다.\n'
                '# BMS 를 올린 뒤 내용을 확인했으면 --update-catalog 로 갱신하십시오.\n'
                '# git diff 가 그대로 "이번 BMS 가 뭘 추가했나" 목록이 됩니다.\n')
        for cb in sorted(catalog):
            f.write('%s\t%s\n' % (cb, catalog[cb][1]))
    return len(catalog)
