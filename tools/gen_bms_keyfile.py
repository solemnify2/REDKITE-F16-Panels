#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Redkite 펌웨어의 DX 맵에서 Falcon BMS .key 바인딩을 생성합니다.

    python tools/gen_bms_keyfile.py -o redkite.key

**기본은 보드에 직접 물어봅니다.** Teensy 를 VID/PID 로 찾아 "?DX" 를 보내고,
펌웨어가 돌려주는 현재 DX 맵을 읽습니다. 그래서 소스나 개발환경이 없는
PC(심 PC)에서도 이 폴더만 있으면 동작합니다. 필요한 것은 pyserial 과
BMS 설치본뿐입니다.

업로드된 펌웨어가 곧 BMS 가 보는 장치이므로, 보드가 유일하게 믿을 만한
근거입니다. 소스를 읽는 --from-source 는 보드가 없을 때를 위한 보조 수단이고,
--verify 로 둘을 대조하면 업로드를 깜빡했는지 바로 드러납니다.

콜백은 tools/bms_callbacks.py 의 이름 기반 표에서 오고, 모든 콜백이
'BMS - Full.key' 에 실재하는지 생성 시점에 검증합니다 — 없는 이름은 에러입니다.

브리지를 끄고 실행하십시오. Windows 는 COM 포트를 한 프로세스만 열 수 있고,
펌웨어도 프로토콜 미검출 상태에서만 "?DX" 에 응답합니다.

출력은 DX 바인딩 줄만 모은 **조각**입니다. 기존 .key 파일 끝에 붙이거나,
--merge 로 원본을 읽어 같은 DX·같은 콜백 줄을 걷어내고 합치십시오.

BMS DX 바인딩 줄 형식 (7필드, 설명 문자열 없음):

    <Callback> <BMS DX#> <-1|-2> -2 <0|0x42> 0x0 <soundID|-1>

      DX#     0-base. Windows 의 DX1 이 BMS 의 0
      3번째   -1 = 모멘터리, -2 = 유지형(누름/뗌 2줄 한 쌍)
      5번째   0 = 누를 때, 0x42 = 뗄 때
      7번째   사운드 ID. 같은 콜백의 키보드 줄에서 가져옵니다
"""
import argparse
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import bms_callbacks  # noqa: E402

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
            w = int(e[5]) if e[2] == 'SW_ROTARY' else width[e[2]]
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
        raise SystemExit('pyserial 이 필요합니다:  pip install pyserial\n'
                         '(보드 없이 소스로 만들려면 --from-source)')
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


def read_device_sorting(bms_root):
    """DeviceSorting.txt 를 읽어 [(순번, 원문)] 반환. 비어 있으면 []."""
    path = os.path.join(bms_root, 'User', 'Config', 'DeviceSorting.txt')
    if not os.path.isfile(path):
        return []
    out = []
    for line in open(path, encoding='utf-8', errors='replace'):
        line = line.strip()
        if line and not line.startswith('#'):
            out.append((len(out) + 1, line))
    return out


# ------------------------------------------------------------- BMS 콜백 카탈로그
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
def emit(entries, mapping, catalog, base, device_label):
    """[(dx, 이름, 폭)] + 매핑 → (줄, 미매핑, TODO, 미모델링)"""
    lines, unmapped, todo, unmodeled, missing = [], [], [], [], []
    for dx, name, w in entries:
        binds = mapping.get(name)
        if binds is None:
            unmapped.append((dx, name, w))
            continue
        if len(binds) != w:
            raise SystemExit('%s: %r 는 DX %d 개인데 매핑은 %d 개입니다'
                             % (device_label, name, w, len(binds)))
        for k, bind in enumerate(binds):
            bms_dx = base + (dx - 1) + k          # Windows DX n → BMS n-1
            label = name if w == 1 else '%s [%d]' % (name, k + 1)
            if bind is None:
                continue
            if isinstance(bind, bms_callbacks.Unmodeled):
                unmodeled.append((dx + k, label, bind))
                continue
            if bind == bms_callbacks.TODO:
                todo.append((dx + k, label))
                continue
            if isinstance(bind, str):
                cbs, held = [(bind, '0')], '-1'
            else:
                on, off = bind
                cbs, held = [(on, '0')], '-2'
                if off:
                    cbs.append((off, '0x42'))
            for cb, edge in cbs:
                if cb not in catalog:
                    missing.append((label, cb))
                    continue
                sound = catalog[cb][0]
                lines.append(('%s %d %s -2 %s 0x0 %d'
                              % (cb, bms_dx, held, edge, sound),
                              dx + k, label, catalog[cb][1]))
    if missing:
        msg = '\n'.join('  %-26s 콜백 %r 가 BMS - Full.key 에 없습니다' % m for m in missing)
        raise SystemExit('%s: 존재하지 않는 콜백\n%s' % (device_label, msg))
    return lines, unmapped, todo, unmodeled


CATALOG_BASELINE = os.path.join(HERE, 'bms_catalog.txt')


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
                '# gen_bms_keyfile.py 가 매번 이 파일과 현재 BMS 를 비교해,\n'
                '# 버전업으로 추가/삭제된 콜백을 알려줍니다.\n'
                '# BMS 를 올린 뒤 내용을 확인했으면 --update-catalog 로 갱신하십시오.\n'
                '# git diff 가 그대로 "이번 BMS 가 뭘 추가했나" 목록이 됩니다.\n')
        for cb in sorted(catalog):
            f.write('%s\t%s\n' % (cb, catalog[cb][1]))
    return len(catalog)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--bms-root', default=DEFAULT_BMS, help='BMS 설치 경로')
    ap.add_argument('--device-index', action='append', nargs=2,
                    metavar=('DEVICE', 'N'),
                    help='DeviceSorting.txt 기준 장치 순번(1-base). '
                         'DEVICE 는 CONSOLE 또는 AUX. 여러 번 지정 가능')
    ap.add_argument('--buttons-per-device', type=int, default=128,
                    help='Falcon BMS User.cfg 의 g_nButtonsPerDevice (기본 128)')
    ap.add_argument('--from-source', action='store_true',
                    help='보드 대신 스케치 소스의 dxOrder[] 를 읽습니다 (오프라인용)')
    ap.add_argument('--verify', action='store_true',
                    help='보드와 소스를 모두 읽어 DX 맵이 같은지 대조만 합니다')
    ap.add_argument('--port', action='append', metavar='COMx',
                    help='자동 탐지 대신 쓸 포트. 여러 번 지정 가능')
    ap.add_argument('-o', '--out', help='출력 파일 (기본: 표준출력)')
    ap.add_argument('--comments', action='store_true',
                    help='각 줄 뒤에 컨트롤 이름을 주석으로 (BMS 는 무시하지만 '
                         'BMS UI 에서 저장하면 사라집니다)')
    ap.add_argument('--update-catalog', action='store_true',
                    help='현재 BMS 의 콜백 목록을 tools/bms_catalog.txt 에 기준선으로 '
                         '기록하고 끝냅니다. BMS 를 올린 뒤 변경을 확인하고 쓰십시오')
    args = ap.parse_args()

    if args.update_catalog:
        catalog = load_catalog(args.bms_root)
        added, removed = catalog_diff(catalog)
        n = write_catalog_baseline(catalog)
        sys.stderr.write('%s 에 콜백 %d 개 기록\n' % (CATALOG_BASELINE, n))
        if added:
            sys.stderr.write('추가 %d: %s\n' % (len(added), ', '.join(added[:20])))
        if removed:
            sys.stderr.write('삭제 %d: %s\n' % (len(removed), ', '.join(removed[:20])))
        return 0

    # --- DX 맵 확보: 보드 질의가 기본, --from-source 는 보조 ---
    maps = {}            # device -> [(dx, name, width)]
    if args.verify or not args.from_source:
        boards = [(p, None) for p in args.port] if args.port else find_boards()
        if not boards:
            raise SystemExit('Teensy 보드를 찾지 못했습니다 (VID 0x16C0).\n'
                             '  - USB 가 꽂혀 있는지, 브리지가 꺼져 있는지 확인하십시오\n'
                             '  - 포트를 직접 주려면 --port COM7\n'
                             '  - 보드 없이 소스로 만들려면 --from-source')
        for port, _ in boards:
            dev, entries = query_board(port)
            if dev not in SKETCHES:
                raise SystemExit('%s: 알 수 없는 device=%r' % (port, dev))
            sys.stderr.write('%s 에서 %s DX 맵 %d 항목 수신\n' % (port, dev, len(entries)))
            maps[dev] = entries
    if args.verify or args.from_source:
        for dev, rel in SKETCHES.items():
            path = os.path.join(ROOT, rel)
            if not os.path.isfile(path):
                continue
            src_entries = dx_map(path)
            if args.verify and dev in maps:
                if src_entries != maps[dev]:
                    sys.stderr.write('\n%s: 보드와 소스의 DX 맵이 다릅니다\n' % dev)
                    for a, b in zip(src_entries, maps[dev]):
                        if a != b:
                            sys.stderr.write('  소스 %-28s  보드 %s\n' % (a, b))
                    return 1
                sys.stderr.write('%s: 보드 = 소스 (%d 항목)\n' % (dev, len(src_entries)))
            elif args.from_source:
                maps[dev] = src_entries
    if args.verify:
        sys.stderr.write('\n대조 완료 — 업로드된 펌웨어가 소스와 일치합니다.\n')
        return 0

    # --- BMS 블록 오프셋 ---
    sorting = read_device_sorting(args.bms_root)
    idx = {d.upper(): int(n) for d, n in (args.device_index or [])}
    if sorting and not idx:
        sys.stderr.write('\nDeviceSorting.txt:\n')
        for n, text in sorting:
            sys.stderr.write('  %d: %s\n' % (n, text))
    for dev in maps:
        if dev in idx:
            continue
        hit = [n for n, text in sorting if 'CONSOLE' in text.upper()] if dev == 'CONSOLE' \
            else [n for n, text in sorting if 'AUX' in text.upper()]
        if len(hit) == 1:
            idx[dev] = hit[0]
            sys.stderr.write('%s: DeviceSorting.txt 에서 순번 %d 로 판단\n' % (dev, hit[0]))
        else:
            raise SystemExit('%s 의 장치 순번을 정할 수 없습니다.\n'
                             '  --device-index %s N 으로 직접 주십시오 '
                             '(DeviceSorting.txt 에서 몇 번째인지, 1-base).' % (dev, dev))

    catalog = load_catalog(args.bms_root)
    out, todos, unmapped_all, unmodeled_all = [], [], [], []
    for dev in sorted(maps):
        n = idx[dev]
        base = (n - 1) * args.buttons_per_device
        entries = maps[dev]
        lines, unmapped, todo, unmod = emit(entries, bms_callbacks.MAPS[dev],
                                           catalog, base, dev)
        out.append('')
        out.append('# ---- %s : 장치 %s, BMS DX %d~%d (Windows DX %d~%d) ----'
                   % (dev, n, base, base + entries[-1][0] + entries[-1][2] - 2,
                      1, entries[-1][0] + entries[-1][2] - 1))
        w = max([len(t[0]) for t in lines] or [0])
        for text, dx, label, desc in lines:
            out.append('%-*s  # DX %-3d %s' % (w, text, dx, label)
                       if args.comments else text)
        todos += [(dev,) + t for t in todo]
        unmapped_all += [(dev,) + u for u in unmapped]
        unmodeled_all += [(dev,) + u for u in unmod]

    body = '\n'.join(out).lstrip('\n') + '\n'
    if args.out:
        open(args.out, 'w', encoding='utf-8', newline='\n').write(body)
        print('%s 에 %d 줄 기록' % (args.out, body.count('\n')))
    else:
        sys.stdout.write(body)

    n_lines = sum(1 for ln in out if ln and not ln.startswith('#'))
    sys.stderr.write('\n바인딩 %d 줄 생성\n' % n_lines)
    if todos:
        sys.stderr.write('\n확정 필요 (%d):\n' % len(todos))
        for dev, dx, label in todos:
            sys.stderr.write('  %-8s DX %-3d %s\n' % (dev, dx, label))
    if unmapped_all:
        sys.stderr.write('\n매핑 표에 없는 컨트롤 (%d) — bms_callbacks.py 에 추가하십시오:\n'
                         % len(unmapped_all))
        for dev, dx, name, w in unmapped_all:
            sys.stderr.write('  %-8s DX %-3d %s (x%d)\n' % (dev, dx, name, w))

    # --- BMS 가 새로 모델링한 게 있는지 ---
    hits = check_unmodeled(unmodeled_all, catalog)
    if hits:
        sys.stderr.write('\n*** BMS 에 콜백이 새로 생겼습니다 (%d) ***\n'
                         '비워 둔 자리의 검색어가 이제 걸립니다. 확인 후 '
                         'bms_callbacks.py 에서 UNMODELED 를 콜백 이름으로 바꾸십시오:\n'
                         % len(hits))
        for dev, dx, label, found in hits:
            sys.stderr.write('  %-8s DX %-3d %s\n' % (dev, dx, label))
            for cb, desc in found:
                sys.stderr.write('      %-26s %s\n' % (cb, desc))
    else:
        sys.stderr.write('\n비워 둔 자리 %d 개 — 현재 BMS 에도 대응 콜백 없음\n'
                         % len(unmodeled_all))

    added, removed = catalog_diff(catalog)
    if added is None:
        sys.stderr.write('콜백 기준선이 없습니다 — --update-catalog 로 만들어 두면 '
                         '다음 BMS 버전에서 바뀐 것을 알 수 있습니다.\n')
    elif added or removed:
        sys.stderr.write('\nBMS 콜백 목록이 기준선과 다릅니다 '
                         '(추가 %d, 삭제 %d):\n' % (len(added), len(removed)))
        for cb in added:
            sys.stderr.write('  + %-26s %s\n' % (cb, catalog[cb][1]))
        for cb in removed:
            sys.stderr.write('  - %s\n' % cb)
        sys.stderr.write('확인했으면 --update-catalog 로 기준선을 갱신하십시오.\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
