#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Redkite 보드의 DX 맵에서 DCS F-16C 입력 프로파일(.diff.lua)을 생성합니다.

    python tools/gen_dcs_profile.py -o out

BMS 와 달리 DCS 는 **장치마다 파일 하나**이고 버튼 번호에 오프셋이 없습니다 —
`JOY_BTN<n>` 의 n 이 그 장치의 DX 번호 그대로입니다. 그래서 장치 순번도,
DeviceSorting 도, 다른 장치와의 병합도 필요 없습니다.

`InputUserProfiles` 에 넣는 프로파일은 GUID 가 아니라 **이름**으로 식별되므로
파일명을 그냥 정하면 됩니다. DCS 입력 설정에서 장치에 이 프로파일을 지정하십시오.

명령 ID 와 이름은 tools/dcs_catalog.txt, 컨트롤 대응은 tools/dcs_commands.py.

**축은 기존 프로파일에서 원문 그대로 베껴 옵니다** (`--profiles-dir`). 이 패널의
포트는 전부 `invert = true` 이고 `curvature`·`filter` 도 들어 있어, 다시 만들면
노브가 전부 반대로 돕니다. 버튼 재배열은 축을 건드리지 않으므로 기존 블록이
그대로 유효합니다.

그 안의 `removed` 항목이 특히 중요합니다 — 오늘까지의 작업에서 `pots[]` 의 `axis` 열은
건드리지 않았으므로 기존 축 바인딩이 그대로 유효합니다. 특히 `removed` 항목 —
DCS 가 새 조이스틱에 자동으로 거는 Pitch←JOY_Y, Roll←JOY_X, Thrust←JOY_Z
(콘솔은 Rudder←JOY_RZ 까지) 를 떼어내는 줄 — 을 빠뜨리면 HMCS 노브나
오디오 포트가 기체를 조종하게 됩니다.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dcs_commands  # noqa: E402
import gen_bms_keyfile as K  # noqa: E402

CATALOG = os.path.join(HERE, 'dcs_catalog.txt')

# 파일명. DCS 는 GUID 가 아니라 이름으로 찾으므로 바꿔도 됩니다.
PROFILE_NAME = {'CONSOLE': 'F16 Left Console panel',
                'AUX':     'F16 Left AUX MISCpanel'}


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


def axis_block(profiles_dir, device):
    """기존 프로파일의 axisDiffs 안쪽을 **원문 그대로** 돌려줍니다.

    invert / curvature / filter / deadzone 같은 축 설정은 생성기가 알 수 없어서,
    다시 만드는 대신 베껴 옵니다. BMS 쪽 Setup XML 생성기와 같은 방식입니다.
    """
    if not profiles_dir:
        return None, None
    path = os.path.join(profiles_dir, PROFILE_NAME[device] + '.diff.lua')
    if not os.path.isfile(path):
        return None, path
    text = open(path, encoding='utf-8', errors='replace').read()
    m = re.search(r'\["axisDiffs"\]\s*=\s*\{\n(.*?)\n\t\},\n', text, re.S)
    return (m.group(1) if m else None), path


def lua(keydiffs, axes, names, axis_raw=None):
    """DCS 가 쓰는 것과 같은 모양으로 — 탭 들여쓰기, [n] 인덱스 테이블.

    axis_raw 가 있으면 축 블록은 원문을 그대로 씁니다.
    """
    L = ['local diff = {', '\t["axisDiffs"] = {']
    if axis_raw is not None:
        L.append(axis_raw)
        axes = []
    for aid, nm, add, rem in axes:
        L.append('\t\t["%s"] = {' % aid)
        for tag, keys in (('added', add), ('removed', rem)):
            if not keys:
                continue
            L.append('\t\t\t["%s"] = {' % tag)
            for i, k in enumerate(keys, 1):
                L += ['\t\t\t\t[%d] = {' % i, '\t\t\t\t\t["key"] = "%s",' % k, '\t\t\t\t},']
            L.append('\t\t\t},')
        L += ['\t\t\t["name"] = "%s",' % nm, '\t\t},']
    L += ['\t},', '\t["keyDiffs"] = {']
    for cid in sorted(keydiffs):
        L.append('\t\t["%s"] = {' % cid)
        L.append('\t\t\t["added"] = {')
        for i, k in enumerate(keydiffs[cid], 1):
            L += ['\t\t\t\t[%d] = {' % i, '\t\t\t\t\t["key"] = "%s",' % k, '\t\t\t\t},']
        L.append('\t\t\t},')
        L.append('\t\t\t["name"] = "%s",' % names.get(cid, cid))
        L.append('\t\t},')
    L += ['\t},', '}', 'return diff']
    return '\n'.join(L) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-o', '--out-dir', required=True, help='생성한 .diff.lua 를 쓸 폴더')
    ap.add_argument('--from-source', action='store_true',
                    help='보드 대신 스케치의 dxOrder[] 를 읽습니다 (오프라인용)')
    ap.add_argument('--port', action='append', metavar='COMx', help='포트 직접 지정')
    ap.add_argument('--profiles-dir',
                    help='기존 .diff.lua 가 있는 폴더. 축 블록을 여기서 원문 그대로 '
                         '베껴 옵니다 — invert/curvature 는 생성기가 만들 수 없습니다')
    ap.add_argument('--name', action='append', nargs=2, metavar=('DEVICE', 'NAME'),
                    help='프로파일 파일명 지정 (기본: %s)' % PROFILE_NAME)
    args = ap.parse_args()

    for dev, nm in (args.name or []):
        PROFILE_NAME[dev.upper()] = nm

    maps = {}
    if args.from_source:
        for dev, rel in K.SKETCHES.items():
            p = os.path.join(K.ROOT, rel)
            if os.path.isfile(p):
                maps[dev] = K.dx_map(p)
    else:
        boards = [(p, None) for p in args.port] if args.port else K.find_boards()
        if not boards:
            raise SystemExit('Teensy 보드를 찾지 못했습니다. 브리지를 껐는지 확인하거나 '
                             '--from-source 를 쓰십시오.')
        for port, _ in boards:
            dev, entries = K.query_board(port)
            sys.stderr.write('%s 에서 %s DX 맵 %d 항목 수신\n' % (port, dev, len(entries)))
            maps[dev] = entries

    names, axes = load_catalog()
    if not os.path.isdir(args.out_dir):
        os.makedirs(args.out_dir)

    todos, unmapped_all = [], []
    for dev in sorted(maps):
        kd, todo, unmapped = collect(maps[dev], dcs_commands.MAPS[dev], dev)
        ax = axes.get(dev, [])
        raw, tried = axis_block(args.profiles_dir, dev)
        dest = os.path.join(args.out_dir, PROFILE_NAME[dev] + '.diff.lua')
        open(dest, 'w', encoding='utf-8', newline='\n').write(lua(kd, ax, names, raw))
        keys = sum(len(v) for v in kd.values())
        sys.stderr.write('%-8s %s\n' % (dev, os.path.basename(dest)))
        sys.stderr.write('         명령 %d개 / 버튼 키 %d개 / 축 %d개\n'
                         % (len(kd), keys, len(ax)))
        if raw is not None:
            sys.stderr.write('         축: %s 에서 원문 복사 — invert/curvature 보존\n'
                             % os.path.basename(tried))
        else:
            rem = sum(1 for a in ax if a[3])
            sys.stderr.write('         축: 카탈로그에서 재구성 %d개 (해제 %d개)\n'
                             % (len(ax), rem))
            sys.stderr.write('         [!] invert/curvature 가 빠집니다 — '
                             '--profiles-dir 로 기존 프로파일을 지정하십시오\n')
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
    sys.stderr.write('\n%s 에 기록했습니다. DCS 의 Saved Games\\...\\InputUserProfiles 로 '
                     '복사한 뒤 입력 설정에서 장치에 지정하십시오.\n' % args.out_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
