#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Redkite 보드의 DX 맵에서 Falcon BMS 의 **장치별 Setup XML** 을 생성합니다.

    python tools/gen_bms_setup_xml.py --config-dir "...\\Falcon4\\Config" -o out

BMS 는 버튼 바인딩을 두 곳에 둡니다 — 게임 전체가 공유하는 `.key` 와,
장치마다 하나씩인 `Setup.v100.<장치명> {GUID}.xml` 입니다. 이 도구는 후자를
만듭니다. `.key` 쪽은 gen_bms_keyfile.py 입니다.

장치별 파일이라 `.key` 보다 다루기 쉽습니다:

  - **장치 대역 오프셋이 없습니다.** `DxAssgn[i]` 가 그 장치의 DX 버튼 i+1 입니다
  - `DeviceSorting.txt` 도, 장치 순번도 필요 없습니다
  - 다른 장치 파일을 건드리지 않으니 병합도 필요 없습니다
  - 장치 순서가 바뀌어도 파일명의 GUID 로 찾으므로 안 깨집니다

**기존 파일을 템플릿으로 씁니다.** 축 보정(Invert/Saturation/Deadzone),
`<detentPosition>`, `<pov>` 는 그대로 두고 `<DxAssgn>` 만 갈아끼웁니다.
그래서 `--config-dir` 에 **지금 쓰고 있는 XML 이 있어야** 합니다.

구조 (한 버튼당 `<Assgn>` 4개):

    <DxAssgn><assign>
      <Assgn><Callback>SimXMit1</Callback><Invoke>Default</Invoke>...  슬롯0 = 누를 때
      <Assgn><Callback>SimDoNothing</Callback>...                      슬롯1 = 미사용
      <Assgn><Callback>SimXMit2</Callback><Invoke>Down</Invoke>...     슬롯2 = 뗄 때
      <Assgn><Callback>SimDoNothing</Callback>...                      슬롯3 = 미사용
    </assign></DxAssgn>

`<dx>` 섹션이 셋인데 앞의 둘은 내용이 같고 셋째는 비어 있습니다. 관측된 그대로
재현합니다 — 앞 두 블록에 같은 내용을, 셋째에는 빈 항목을 씁니다.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bms_callbacks  # noqa: E402
import gen_bms_keyfile as K  # noqa: E402

# 장치 -> USB 제품명 (name.c). 파일명이 이걸로 시작합니다.
PRODUCT = {'CONSOLE': 'F16 LEFT CONSOLE', 'AUX': 'F16 LEFT AUX MISC'}

EMPTY = ('SimDoNothing', 'Default', 0)

DXASSGN = re.compile(r'(<DxAssgn>\s*<assign>)(.*?)(</assign>\s*</DxAssgn>)', re.S)
ASSGN = re.compile(r'<Assgn>\s*<Callback>([^<]*)</Callback>\s*'
                   r'<Invoke>([^<]*)</Invoke>\s*<SoundID>([^<]*)</SoundID>\s*</Assgn>', re.S)


def find_template(config_dir, device):
    """그 장치의 Setup.v100.*.xml 경로. GUID 는 파일명에서 그대로 가져옵니다."""
    pat = 'Setup.v100.' + PRODUCT[device]
    hits = [f for f in os.listdir(config_dir)
            if f.startswith(pat) and f.endswith('.xml')]
    if not hits:
        raise SystemExit('%s 의 Setup XML 을 찾지 못했습니다: %s\n'
                         '  BMS 입력 설정에서 이 장치를 한 번 건드리면 생깁니다.'
                         % (device, os.path.join(config_dir, pat + ' {GUID}.xml')))
    if len(hits) > 1:
        raise SystemExit('%s 의 Setup XML 이 여러 개입니다: %s' % (device, hits))
    return os.path.join(config_dir, hits[0])


def slots_for(bind, catalog):
    """매핑 한 칸 -> (슬롯0, 슬롯1, 슬롯2, 슬롯3). 각 슬롯은 (콜백, Invoke, 사운드)."""
    if bind is None or isinstance(bind, bms_callbacks.Unmodeled) \
            or bind == bms_callbacks.TODO:
        return [EMPTY] * 4
    if isinstance(bind, str):
        return [(bind, 'Default', catalog[bind][0]), EMPTY, EMPTY, EMPTY]
    on, off = bind
    s0 = (on, 'Default', catalog[on][0])
    s2 = (off, 'Down', catalog[off][0]) if off else EMPTY
    return [s0, EMPTY, s2, EMPTY]


def build_map(entries, mapping, catalog, device):
    """[(dx, 이름, 폭)] -> {dx: [슬롯 4개]}"""
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
            for cb in ([b] if isinstance(b, str) else list(b) if isinstance(b, tuple) else []):
                if cb and cb not in catalog:
                    raise SystemExit('%s: 콜백 %r 가 BMS - Full.key 에 없습니다 (%s)'
                                     % (device, cb, name))
            out[dx + k] = slots_for(b, catalog)
    return out, missing


def render(template_text, dxmap, buttons_per_block=128):
    """템플릿의 <DxAssgn> 만 교체. 나머지 바이트는 그대로 둡니다."""
    n = [0]

    def repl(m):
        head, body, tail = m.group(1), m.group(2), m.group(3)
        k = n[0]
        n[0] += 1
        block, idx = divmod(k, buttons_per_block)
        # 앞 두 블록에만 바인딩을 쓰고, 셋째는 비웁니다 (관측된 구조 그대로)
        slots = dxmap.get(idx + 1, [EMPTY] * 4) if block < 2 else [EMPTY] * 4
        # 원본 <Assgn> 의 들여쓰기를 그대로 재사용합니다
        orig = ASSGN.findall(body)
        indent = re.search(r'\n(\s*)<Assgn>', body)
        pad = indent.group(1) if indent else '        '
        if len(orig) != 4:
            return m.group(0)      # 모양이 다르면 손대지 않습니다
        parts = []
        for cb, inv, snd in slots:
            parts.append('%s<Assgn>\n%s  <Callback>%s</Callback>\n'
                         '%s  <Invoke>%s</Invoke>\n%s  <SoundID>%s</SoundID>\n%s</Assgn>'
                         % (pad, pad, cb, pad, inv, pad, snd, pad))
        close = re.search(r'\n(\s*)</assign>', m.group(0))
        return head + '\n' + '\n'.join(parts) + '\n' + (close.group(1) if close else '      ') \
            + tail.lstrip()

    out = DXASSGN.sub(repl, template_text)
    return out, n[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--config-dir', required=True,
                    help='기존 Setup.v100.*.xml 이 있는 폴더 (템플릿으로 씁니다)')
    ap.add_argument('-o', '--out-dir', required=True,
                    help='생성한 XML 을 쓸 폴더. 원본을 덮어쓰지 않습니다')
    ap.add_argument('--bms-root', default=K.DEFAULT_BMS, help='BMS 설치 경로')
    ap.add_argument('--from-source', action='store_true',
                    help='보드 대신 스케치의 dxOrder[] 를 읽습니다 (오프라인용)')
    ap.add_argument('--port', action='append', metavar='COMx', help='포트 직접 지정')
    args = ap.parse_args()

    # --- DX 맵 ---
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
            if dev not in PRODUCT:
                raise SystemExit('%s: 알 수 없는 device=%r' % (port, dev))
            sys.stderr.write('%s 에서 %s DX 맵 %d 항목 수신\n' % (port, dev, len(entries)))
            maps[dev] = entries

    catalog = K.load_catalog(args.bms_root)
    if not os.path.isdir(args.out_dir):
        os.makedirs(args.out_dir)

    for dev in sorted(maps):
        tpl = find_template(args.config_dir, dev)
        dxmap, missing = build_map(maps[dev], bms_callbacks.MAPS[dev], catalog, dev)
        text = open(tpl, encoding='utf-8', errors='replace').read()
        out, touched = render(text, dxmap)
        dest = os.path.join(args.out_dir, os.path.basename(tpl))
        open(dest, 'w', encoding='utf-8', newline='\n').write(out)
        bound = sum(1 for v in dxmap.values() if v[0] is not EMPTY)
        sys.stderr.write('%-8s %s\n' % (dev, os.path.basename(tpl)))
        sys.stderr.write('         템플릿 %s\n' % tpl)
        sys.stderr.write('         DxAssgn %d개 갱신, 바인딩 %d개 / DX %d\n'
                         % (touched, bound, len(maps[dev]) and
                            maps[dev][-1][0] + maps[dev][-1][2] - 1))
        for dx, name, w in missing:
            sys.stderr.write('         매핑 없음: DX %d %s (x%d)\n' % (dx, name, w))
    sys.stderr.write('\n%s 에 기록했습니다. 확인 후 BMS 의 User\\Config 로 복사하십시오.\n'
                     % args.out_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
