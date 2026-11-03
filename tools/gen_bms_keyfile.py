#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Redkite 펌웨어의 DX 맵에서 Falcon BMS .key 바인딩을 생성합니다.

    python tools/gen_bms_keyfile.py --device-index 2 -o redkite.key

DX 번호는 스케치의 `dxOrder[]` 표에서 직접 읽습니다. dxOrder[] 가 DX 순서의
유일한 근거이므로, 재배열한 뒤 다시 돌리기만 하면 바인딩이 따라옵니다.
콜백은 tools/bms_callbacks.py 의 이름 기반 표에서 오고, 모든 콜백이
'BMS - Full.key' 에 실재하는지 생성 시점에 검증합니다 — 없는 이름은 에러입니다.

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
    """[(dx, 이름, 폭)] + 매핑 → (줄 리스트, 미매핑 리스트, TODO 리스트)"""
    lines, unmapped, todo, missing = [], [], [], []
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
    return lines, unmapped, todo


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
    ap.add_argument('-o', '--out', help='출력 파일 (기본: 표준출력)')
    ap.add_argument('--comments', action='store_true',
                    help='각 줄 뒤에 컨트롤 이름을 주석으로 (BMS 는 무시하지만 '
                         'BMS UI 에서 저장하면 사라집니다)')
    args = ap.parse_args()

    if not args.device_index:
        ap.error('--device-index 가 필요합니다. 예: --device-index CONSOLE 2 '
                 '--device-index AUX 3\n'
                 'DeviceSorting.txt 에서 각 Teensy 가 몇 번째인지 확인하십시오.')

    catalog = load_catalog(args.bms_root)
    out, todos, unmapped_all = [], [], []
    for dev, n in args.device_index:
        dev = dev.upper()
        if dev not in SKETCHES:
            ap.error('알 수 없는 장치 %r (CONSOLE 또는 AUX)' % dev)
        base = (int(n) - 1) * args.buttons_per_device
        entries = dx_map(os.path.join(ROOT, SKETCHES[dev]))
        lines, unmapped, todo = emit(entries, bms_callbacks.MAPS[dev], catalog, base, dev)
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
    return 0


if __name__ == '__main__':
    sys.exit(main())
