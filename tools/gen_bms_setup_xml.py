#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Redkite 보드의 DX 맵에서 Falcon BMS 의 **장치별 Setup XML** 을 만듭니다.

    python tools/gen_bms_setup_xml.py -o out

**파일을 처음부터 전부 만듭니다.** 기존 XML 이 없어도 되고, 참고하지도 않습니다 —
축 설정·GUID 처럼 유도할 수 없는 값은 `tools/sim_axes.py` 에 데이터로 적혀 있습니다.
축의 invert/deadzone 을 바꾸고 싶으면 그 파일을 고치십시오.

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
sys.path.insert(0, HERE)
import bms_callbacks  # noqa: E402
import sim_axes as AX  # noqa: E402
import gen_bms_keyfile as K  # noqa: E402

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
    """[(dx, 이름, 폭)] -> ({dx: 슬롯 4개}, 미매핑 목록)"""
    out, missing = {}, []
    for dx, name, w in entries:
        binds = mapping.get(name)
        if binds is None:
            missing.append((dx, name, w))
            continue
        if len(binds) != w:
            raise SystemExit('%s: %r 는 DX %d 개인데 매핑은 %d 개입니다'
                             % (device, name, w, len(binds)))
        for k, b in enumerate(binds):
            for cb in ([b] if isinstance(b, str)
                       else list(b) if isinstance(b, tuple) else []):
                if cb and cb not in catalog:
                    raise SystemExit('%s: 콜백 %r 가 BMS - Full.key 에 없습니다 (%s)'
                                     % (device, cb, name))
            out[dx + k] = slots_for(b, catalog)
    return out, missing


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
    ap.add_argument('-o', '--out-dir', required=True, help='생성한 XML 을 쓸 폴더')
    ap.add_argument('--bms-root', default=K.DEFAULT_BMS, help='BMS 설치 경로')
    ap.add_argument('--from-source', action='store_true',
                    help='보드 대신 스케치의 dxOrder[] 를 읽습니다 (오프라인용)')
    ap.add_argument('--port', action='append', metavar='COMx', help='포트 직접 지정')
    ap.add_argument('--guid', action='append', nargs=2, metavar=('DEVICE', 'GUID'),
                    help='장치 GUID 지정 (기본은 sim_axes.py 의 값)')
    args = ap.parse_args()

    for dev, g in (args.guid or []):
        AX.BMS_GUID[dev.upper()] = g.strip('{}')

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
            if dev not in AX.PRODUCT:
                raise SystemExit('%s: 알 수 없는 device=%r' % (port, dev))
            sys.stderr.write('%s 에서 %s DX 맵 %d 항목 수신\n' % (port, dev, len(entries)))
            maps[dev] = entries

    catalog = K.load_catalog(args.bms_root)
    if not os.path.isdir(args.out_dir):
        os.makedirs(args.out_dir)

    for dev in sorted(maps):
        dxmap, missing = build_map(maps[dev], bms_callbacks.MAPS[dev], catalog, dev)
        fn = 'Setup.v100.%s {%s}.xml' % (AX.PRODUCT[dev], AX.BMS_GUID[dev])
        dest = os.path.join(args.out_dir, fn)
        open(dest, 'w', encoding='utf-8', newline='\n').write(render(dev, dxmap))
        bound = sum(1 for v in dxmap.values() if v[0] is not EMPTY)
        total = maps[dev][-1][0] + maps[dev][-1][2] - 1
        sys.stderr.write('%-8s %s\n' % (dev, fn))
        sys.stderr.write('         바인딩 %d개 / DX %d, 축 %d칸\n'
                         % (bound, total, len(AX.BMS_AXES[dev])))
        for dx, name, w in missing:
            sys.stderr.write('         매핑 없음: DX %d %s (x%d)\n' % (dx, name, w))
    sys.stderr.write('\n%s 에 기록했습니다. BMS 의 User\\Config 로 복사하십시오.\n'
                     '축 설정(invert/deadzone)과 GUID 는 tools/sim_axes.py 에 있습니다.\n'
                     % args.out_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
