#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Redkite 보드의 DX 맵에서 DCS F-16C 입력 프로파일(.diff.lua)을 생성합니다.

    python tools/gen_dcs_profile.py

보이는 보드마다 `left_console_new1.diff.lua` 같은 파일을 현재 폴더에 남깁니다.
번호는 비어 있는 것으로 골라서, 전에 뽑은 걸 덮어쓰지 않습니다.

**생성기는 DCS 폴더를 건드리지 않습니다.** 나온 파일을 `InputUserProfiles` 의
쓰던 프로파일 이름으로 바꿔 넣는 것은 사람의 일입니다. 그 이름은 DCS 의
Save Profile As... 에서 사람이 타이핑한 것이라, 생성기가 알 방법은 없습니다 —
`sim_axes.py` 의 `DCS_PROFILE` 은 마지막에 보여주는 복사 명령에만 씁니다.

BMS 와 달리 DCS 는 버튼 번호에 오프셋이 없습니다 — `JOY_BTN<n>` 의 n 이
그 장치의 DX 번호 그대로입니다.

명령 ID 와 이름은 tools/keymap/dcs_catalog.txt, 컨트롤 대응은 tools/keymap/dcs_commands.py.

**파일을 처음부터 전부 만듭니다.** 기존 프로파일을 참고하지 않습니다 — 축 설정처럼
유도할 수 없는 값은 `tools/keymap/sim_axes.py` 에 데이터로 적혀 있습니다. 이 패널의 포트는
전부 `invert = true` 라, 그 값이 빠지면 노브가 반대로 돕니다.

축의 `removed` 항목이 특히 중요합니다 — DCS 가 새 조이스틱에 자동으로 거는
`Pitch←JOY_Y` · `Roll←JOY_X` · `Thrust←JOY_Z` (콘솔은 `Rudder←JOY_RZ` 까지) 를
떼어내는 줄이라, 없으면 HMCS 노브가 스로틀을 움직입니다.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'keymap'))
import dcs_commands  # noqa: E402
import sim_axes as AX  # noqa: E402
import board as K  # noqa: E402

CATALOG = os.path.join(HERE, 'keymap', 'dcs_catalog.txt')

def load_catalog():
    """(이름 사전, 장치별 축 목록) 반환."""
    names, axes, sect = {}, {}, None
    for line in open(CATALOG, encoding='utf-8'):
        line = line.rstrip('\n')
        if line.startswith('## '):
            sect = line.split()[1]
            continue
        if not line or line.startswith('#'):
            continue
        f = line.split('\t')
        if sect == 'BUTTONS' and len(f) >= 3:
            names[f[1]] = f[2]
        elif sect == 'AXES' and len(f) >= 5:
            dev, aid, nm = f[0], f[1], f[2]
            add = [x for x in f[3][1:].split(',') if x]
            rem = [x for x in f[4][1:].split(',') if x]
            axes.setdefault(dev, []).append((aid, nm, add, rem))
    return names, axes


def collect(entries, mapping, device):
    """[(dx, 이름, 폭)] -> ({명령 ID: [키…]}, TODO 목록, 미매핑 목록)

    같은 명령이 여러 DX 의 '뗄 때' 자리에 오면 키가 한 항목에 모입니다 —
    3단 스위치의 가운데가 JOY_BTN<a>_OFF + JOY_BTN<b>_OFF 가 되는 그 모양입니다.
    """
    out, todo, unmapped = {}, [], []
    for dx, name, w in entries:
        binds = mapping.get(name)
        if binds is None:
            unmapped.append((dx, name, w))
            continue
        if len(binds) != w:
            raise SystemExit('%s: %r 는 DX %d 개인데 매핑은 %d 개입니다'
                             % (device, name, w, len(binds)))
        for k, b in enumerate(binds):
            label = name if w == 1 else '%s [%d]' % (name, k + 1)
            if b is None:
                continue
            if b == dcs_commands.TODO:
                todo.append((dx + k, label))
                continue
            press, release = (b, None) if isinstance(b, str) else b
            if press:
                out.setdefault(press, []).append('JOY_BTN%d' % (dx + k))
            if release:
                out.setdefault(release, []).append('JOY_BTN%d_OFF' % (dx + k))
    return out, todo, unmapped


def filt(f, ind):
    """DCS 가 쓰는 모양의 ["filter"] 블록."""
    L = [ind + '["filter"] = {',
         ind + '	["curvature"] = {']
    for i, v in enumerate(f['curvature'], 1):
        L.append(ind + '		[%d] = %s,' % (i, v))
    L.append(ind + '	},')
    for k in ('deadzone', 'hardwareDetent', 'hardwareDetentAB', 'hardwareDetentMax',
              'invert', 'saturationX', 'saturationY', 'slider'):
        v = f[k]
        L.append(ind + '	["%s"] = %s,' % (k, 'true' if v is True else
                                            'false' if v is False else v))
    L.append(ind + '},')
    return L


def lua(keydiffs, axes, names):
    """DCS 가 쓰는 것과 같은 모양 — 탭 들여쓰기, [n] 인덱스 테이블."""
    L = ['local diff = {', '	["axisDiffs"] = {']
    for aid, nm, tag, key, f in axes:
        block = ['			["%s"] = {' % tag, '				[1] = {']
        if f:
            block += filt(f, '					')
        block += ['					["key"] = "%s",' % key, '				},', '			},']
        name = ['			["name"] = "%s",' % nm]
        # DCS 는 테이블 키를 알파벳순으로 씁니다: added < name < removed
        L.append('		["%s"] = {' % aid)
        L += (block + name) if tag == 'added' else (name + block)
        L.append('		},')
    L += ['	},', '	["keyDiffs"] = {']
    for cid in sorted(keydiffs):
        L.append('		["%s"] = {' % cid)
        L.append('			["added"] = {')
        for i, k in enumerate(keydiffs[cid], 1):
            L += ['				[%d] = {' % i, '					["key"] = "%s",' % k, '				},']
        L.append('			},')
        L.append('			["name"] = "%s",' % names.get(cid, cid))
        L.append('		},')
    L += ['	},', '}', 'return diff']
    return '\n'.join(L) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--port', action='append', metavar='COMx', help='포트 직접 지정')
    args = ap.parse_args()

    maps = {}
    boards = [(p, None) for p in args.port] if args.port else K.find_boards()
    if not boards:
        raise SystemExit('Teensy 보드를 찾지 못했습니다. USB 와 브리지 종료를 '
                         '확인하거나 --port COM7 로 지정하십시오.')
    for port, _ in boards:
        dev, entries = K.query_board(port)
        if dev not in AX.DCS_AXES:
            raise SystemExit('%s: 알 수 없는 device=%r' % (port, dev))
        sys.stderr.write('%s 에서 %s DX 맵 %d 항목 수신\n' % (port, dev, len(entries)))
        maps[dev] = entries

    names, _ = load_catalog()
    todos, unmapped_all, made = [], [], []
    for dev in sorted(maps):
        kd, todo, unmapped = collect(maps[dev], dcs_commands.MAPS[dev], dev)
        ax = AX.DCS_AXES[dev]
        dest = K.next_out(AX.OUT_BASE[dev], '.diff.lua')
        open(dest, 'w', encoding='utf-8', newline='\n').write(lua(kd, ax, names))
        made.append((dev, dest))
        keys = sum(len(v) for v in kd.values())
        rem = sum(1 for a in ax if a[2] == 'removed')
        sys.stderr.write('%-8s %s\n' % (dev, dest))
        sys.stderr.write('         명령 %d개 / 버튼 키 %d개\n' % (len(kd), keys))
        sys.stderr.write('         축 %d개 (기본 할당 해제 %d개) — sim_axes.py\n'
                         % (len(ax), rem))
        todos += [(dev,) + t for t in todo]
        unmapped_all += [(dev,) + u for u in unmapped]

    if todos:
        sys.stderr.write('\n아직 명령을 못 정한 자리 (%d):\n' % len(todos))
        for dev, dx, label in todos:
            sys.stderr.write('  %-8s DX %-3d %s\n' % (dev, dx, label))
    if unmapped_all:
        sys.stderr.write('\n표에 없는 컨트롤 (%d) — dcs_commands.py 에 추가하십시오:\n'
                         % len(unmapped_all))
        for dev, dx, name, w in unmapped_all:
            sys.stderr.write('  %-8s DX %-3d %s (x%d)\n' % (dev, dx, name, w))

    sys.stderr.write('\n덮어쓰려면 (PowerShell):\n'
                     '  $p = Resolve-Path "$env:USERPROFILE%sSaved Games%sDCS*%sInputUserProfiles"\n' % (
                         chr(92), chr(92), chr(92)))
    for dev, dest in made:
        sys.stderr.write('  Copy-Item "%s" "$p%s%s.diff.lua"\n'
                         % (dest, chr(92), AX.DCS_PROFILE[dev]))
    sys.stderr.write('\n마지막 이름은 DCS 에서 쓰던 프로파일 이름과 같아야 합니다.\n'
                     '다르면 그쪽 이름으로 바꿔 주십시오.\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
