#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Redkite 보드의 DX 맵에서 Falcon BMS 의 **장치별 Setup XML** 을 만듭니다.

    python tools/gen_bms_setup_xml.py

보이는 보드마다 `left_console_new1.xml` 같은 파일을 현재 폴더에 남깁니다.
번호는 비어 있는 것으로 골라서, 전에 뽑은 걸 덮어쓰지 않습니다.

**생성기는 BMS 폴더를 건드리지 않습니다.** 나온 파일을 BMS 가 만들어 둔
`Setup.v100.<제품명> {GUID}.xml` 이름으로 바꿔 `User\Config` 에 넣는 것은
사람의 일입니다. 그래서 생성기는 GUID 를 몰라도 됩니다 — GUID 는 파일 이름에만
있고 내용에는 없습니다. BMS 설치 경로는 콜백 목록을 읽는 데만 씁니다.

**파일을 처음부터 전부 만듭니다.** 기존 XML 을 참고하지 않습니다 — 축 설정처럼
유도할 수 없는 값은 `tools/keymap/sim_axes.py` 에 데이터로 적혀 있습니다.

BMS 는 버튼 바인딩을 장치마다 하나씩인 `Setup.v100.<장치명> {GUID}.xml` 에 둡니다.
장치별이라 대역 오프셋도, `DeviceSorting.txt` 도, 다른 장치와의 병합도 필요 없습니다.

문서 구조:

    <JoyAssgn>
      <detentPosition>  AB / IDLE
      <axis>            AxAssgn x8 — HID 축 순서 X Y Z Rx Ry Rz S1 S2
      <pov>   x3        각 PovAssgn x4, 각 direction 1 + DirAssgn x8 (전부 빈값)
      <dx>    x3        각 DxAssgn x128

`DxAssgn[i]` 가 그 장치의 DX 버튼 i+1 입니다 — 오프셋 없음. 버튼 하나는 `<Assgn>`
4칸이고 슬롯 0 이 누를 때(`Default`), 슬롯 2 가 뗄 때(`Down`), 1 과 3 은 안 씁니다.
`<dx>` 세 벌 중 앞 두 벌에 같은 내용이 들어가고 셋째는 빕니다.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'keymap'))
import bms_callbacks  # noqa: E402
import sim_axes as AX  # noqa: E402
import board as K  # noqa: E402

EMPTY = ('SimDoNothing', 'Default', 0)


I = '  '          # BMS 가 쓰는 들여쓰기


def slots_for(bind, catalog):
    """매핑 한 칸 -> <Assgn> 4칸. 각 칸은 (콜백, Invoke, 사운드)."""
    if bind is None or isinstance(bind, bms_callbacks.Unmodeled) \
            or bind == bms_callbacks.TODO:
        return [EMPTY] * 4
    if isinstance(bind, str):
        return [(bind, 'Default', catalog[bind][0]), EMPTY, EMPTY, EMPTY]
    on, off = bind
    return [(on, 'Default', catalog[on][0]), EMPTY,
            (off, 'Down', catalog[off][0]) if off else EMPTY, EMPTY]


def build_map(entries, mapping, catalog, device):
    """[(dx, 이름, 폭)] -> ({dx: 슬롯 4개}, 미매핑, 미모델링)"""
    out, missing, unmodeled = {}, [], []
    for dx, name, w in entries:
        binds = mapping.get(name)
        if binds is None:
            missing.append((dx, name, w))
            continue
        if len(binds) != w:
            raise SystemExit('%s: %r 는 DX %d 개인데 매핑은 %d 개입니다'
                             % (device, name, w, len(binds)))
        for k, b in enumerate(binds):
            if isinstance(b, bms_callbacks.Unmodeled):
                label = name if w == 1 else '%s [%d]' % (name, k + 1)
                unmodeled.append((device, dx + k, label, b))
            for cb in ([b] if isinstance(b, str)
                       else list(b) if isinstance(b, tuple) else []):
                if cb and cb not in catalog:
                    raise SystemExit('%s: 콜백 %r 가 BMS - Full.key 에 없습니다 (%s)'
                                     % (device, cb, name))
            out[dx + k] = slots_for(b, catalog)
    return out, missing, unmodeled


def render(device, dxmap):
    """Setup XML 전체를 문자열로."""
    L = ['<?xml version="1.0" encoding="utf-8"?>',
         '<JoyAssgn xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
         ' xmlns:xsd="http://www.w3.org/2001/XMLSchema">']

    L.append(I + '<detentPosition>')
    L.append(I * 2 + '<AB>%d</AB>' % AX.BMS_DETENT['AB'])
    L.append(I * 2 + '<IDLE>%d</IDLE>' % AX.BMS_DETENT['IDLE'])
    L.append(I + '</detentPosition>')

    L.append(I + '<axis>')
    for name, invert, sat, dz in AX.BMS_AXES[device]:
        L.append(I * 2 + '<AxAssgn>')
        # 빈 축은 BMS 가 <AxisName /> 로 씁니다
        L.append(I * 3 + ('<AxisName>%s</AxisName>' % name if name else '<AxisName />'))
        L.append(I * 3 + '<AssgnDate>%s</AssgnDate>' % AX.BMS_ASSGN_DATE)
        L.append(I * 3 + '<Invert>%s</Invert>' % ('true' if invert else 'false'))
        L.append(I * 3 + '<Saturation>%s</Saturation>' % sat)
        L.append(I * 3 + '<Deadzone>%s</Deadzone>' % dz)
        L.append(I * 2 + '</AxAssgn>')
    L.append(I + '</axis>')

    for _ in range(AX.BMS_POV_SETS):
        L.append(I + '<pov>')
        for _ in range(AX.BMS_POV_ASSGN):
            L += [I * 2 + '<PovAssgn>', I * 3 + '<direction>']
            for _ in range(AX.BMS_DIR_ASSGN):
                L += [I * 4 + '<DirAssgn>',
                      I * 5 + '<Callback>',
                      I * 6 + '<string>SimDoNothing</string>',
                      I * 6 + '<string>SimDoNothing</string>',
                      I * 5 + '</Callback>',
                      I * 5 + '<SoundID>',
                      I * 6 + '<int>0</int>',
                      I * 6 + '<int>0</int>',
                      I * 5 + '</SoundID>',
                      I * 4 + '</DirAssgn>']
            L += [I * 3 + '</direction>', I * 2 + '</PovAssgn>']
        L.append(I + '</pov>')

    for s in range(AX.BMS_DX_SETS):
        L.append(I + '<dx>')
        for i in range(AX.BMS_DX_PER_SET):
            slots = dxmap.get(i + 1, [EMPTY] * 4) if s < AX.BMS_DX_LIVE_SETS \
                else [EMPTY] * 4
            L += [I * 2 + '<DxAssgn>', I * 3 + '<assign>']
            for cb, inv, snd in slots:
                L += [I * 4 + '<Assgn>',
                      I * 5 + '<Callback>%s</Callback>' % cb,
                      I * 5 + '<Invoke>%s</Invoke>' % inv,
                      I * 5 + '<SoundID>%s</SoundID>' % snd,
                      I * 4 + '</Assgn>']
            L += [I * 3 + '</assign>', I * 2 + '</DxAssgn>']
        L.append(I + '</dx>')

    L.append('</JoyAssgn>')
    return '\n'.join(L) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--bms-root', default=K.DEFAULT_BMS,
                    help='BMS 설치 경로 — 콜백 목록을 읽습니다')
    ap.add_argument('--port', action='append', metavar='COMx', help='포트 직접 지정')
    ap.add_argument('--verify', action='store_true',
                    help='보드와 스케치 소스의 DX 맵이 같은지 대조만 합니다')
    ap.add_argument('--update-catalog', action='store_true',
                    help='현재 BMS 의 콜백 목록을 기준선에 기록하고 끝냅니다')
    args = ap.parse_args()

    if args.update_catalog:
        catalog = K.load_catalog(args.bms_root)
        added, removed = K.catalog_diff(catalog)
        n = K.write_catalog_baseline(catalog)
        sys.stderr.write('%s 에 콜백 %d 개 기록\n' % (K.CATALOG_BASELINE, n))
        if added:
            sys.stderr.write('추가 %d: %s\n' % (len(added), ', '.join(added[:20])))
        if removed:
            sys.stderr.write('삭제 %d: %s\n' % (len(removed), ', '.join(removed[:20])))
        return 0

    maps = {}
    boards = [(p, None) for p in args.port] if args.port else K.find_boards()
    if not boards:
        raise SystemExit('Teensy 보드를 찾지 못했습니다. USB 와 브리지 종료를 '
                         '확인하거나 --port COM7 로 지정하십시오.')
    for port, _ in boards:
        dev, entries = K.query_board(port)
        if dev not in AX.PRODUCT:
            raise SystemExit('%s: 알 수 없는 device=%r' % (port, dev))
        sys.stderr.write('%s 에서 %s DX 맵 %d 항목 수신\n' % (port, dev, len(entries)))
        maps[dev] = entries

    if args.verify:
        bad = 0
        for dev, rel in sorted(K.SKETCHES.items()):
            path = os.path.join(K.ROOT, rel)
            if dev not in maps or not os.path.isfile(path):
                continue
            src = K.dx_map(path)
            if src == maps[dev]:
                sys.stderr.write('%s: 보드 = 소스 (%d 항목)\n' % (dev, len(src)))
                continue
            bad = 1
            sys.stderr.write('\n%s: 보드와 소스의 DX 맵이 다릅니다\n' % dev)
            for a, b in zip(src, maps[dev]):
                if a != b:
                    sys.stderr.write('  소스 %-28s  보드 %s\n' % (a, b))
        if not bad:
            sys.stderr.write('\n대조 완료 — 업로드된 펜웨어가 소스와 일치합니다.\n')
        return bad

    catalog = K.load_catalog(args.bms_root)
    made, unmodeled_all = [], []
    for dev in sorted(maps):
        dxmap, missing, unmod = build_map(maps[dev], bms_callbacks.MAPS[dev], catalog, dev)
        dest = K.next_out(AX.OUT_BASE[dev], '.xml')
        open(dest, 'w', encoding='utf-8', newline='\n').write(render(dev, dxmap))
        made.append((dev, dest))
        unmodeled_all += unmod
        bound = sum(1 for v in dxmap.values() if v[0] is not EMPTY)
        total = maps[dev][-1][0] + maps[dev][-1][2] - 1
        sys.stderr.write('%-8s %s\n' % (dev, dest))
        sys.stderr.write('         바인딩 %d개 / DX %d, 축 %d칸\n'
                         % (bound, total, len(AX.BMS_AXES[dev])))
        for dx, name, w in missing:
            sys.stderr.write('         매핑 없음: DX %d %s (x%d)\n' % (dx, name, w))

    hits = K.check_unmodeled(unmodeled_all, catalog)
    if hits:
        sys.stderr.write('\nBMS 가 그사이 지원하게 된 것 같습니다 (%d) — '
                         'bms_callbacks.py 를 고쳐 보십시오:\n' % len(hits))
        for dev, dx, label, found in hits:
            sys.stderr.write('  %-8s DX %-3d %s\n' % (dev, dx, label))
            for cb, desc in found[:4]:
                sys.stderr.write('      %-28s %s\n' % (cb, desc))

    cfg = os.path.join(args.bms_root, 'User', 'Config')
    sys.stderr.write('\n덮어쓰려면 (PowerShell):\n')
    for dev, dest in made:
        sys.stderr.write('  Copy-Item "%s" (Get-ChildItem "%s")\n'
                         % (dest, os.path.join(cfg, 'Setup.v100.%s {*}.xml'
                                               % AX.PRODUCT[dev])))
    sys.stderr.write('\nGet-ChildItem 이 파일을 못 찾으면 BMS 가 아직 그 장치를 모르는 것입니다.\n'
                     'SETUP - CONTROLLERS 에서 아무 버튼이나 한 번 바인드하고 저장하십시오.\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
