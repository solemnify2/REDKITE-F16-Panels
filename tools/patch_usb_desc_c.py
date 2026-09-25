#!/usr/bin/env python3
"""
usb_desc.c 자동 패치 — Redkite F16 Panels

Teensyduino 업데이트 후 실행:
    python tools/patch_usb_desc_c.py            # 패치 적용
    python tools/patch_usb_desc_c.py --check    # 상태 확인만
    python tools/patch_usb_desc_c.py --revert   # 백업에서 복원

수정 내용:
  JOYSTICK_SIZE 64 (extreme joystick) HID descriptor 에서
  Report Count 23 → 8 (6 named + 2 Slider) + 15 constant padding.

  Teensyduino 원본은 슬라이더 17개를 전부 Usage 0x36 으로 선언하는데,
  이 중복이 Windows DirectInput 을 혼란시켜 슬라이더가 전혀 인식되지 않습니다.
  8개만 variable 로 선언하면 DirectInput 이 정상 매핑합니다.
"""

import os, sys, shutil, argparse

# ================================================================
#  패턴 정의
# ================================================================

SLIDER_LINE = '        0x09, 0x36,                     // Usage (Slider)\n'

ORIGINAL_BLOCK = (
    '        0x95, 23,                       // Report Count (23)\n'
    '        0x09, 0x30,                     // Usage (X)\n'
    '        0x09, 0x31,                     // Usage (Y)\n'
    '        0x09, 0x32,                     // Usage (Z)\n'
    '        0x09, 0x33,                     // Usage (Rx)\n'
    '        0x09, 0x34,                     // Usage (Ry)\n'
    '        0x09, 0x35,                     // Usage (Rz)\n'
    + SLIDER_LINE * 17
    + '        0x81, 0x02,                     // Input (variable,absolute)'
)

PATCHED_BLOCK = (
    '        0x95, 8,                        // Report Count (8)\n'
    '        0x09, 0x30,                     // Usage (X)\n'
    '        0x09, 0x31,                     // Usage (Y)\n'
    '        0x09, 0x32,                     // Usage (Z)\n'
    '        0x09, 0x33,                     // Usage (Rx)\n'
    '        0x09, 0x34,                     // Usage (Ry)\n'
    '        0x09, 0x35,                     // Usage (Rz)\n'
    '        0x09, 0x36,                     // Usage (Slider)\n'
    '        0x09, 0x36,                     // Usage (Slider)\n'
    '        0x81, 0x02,                     // Input (variable,absolute)\n'
    '        0x95, 15,                       // Report Count (15)\n'
    '        0x81, 0x01,                     // Input (constant) — padding'
)

# ================================================================
#  경로 탐지
# ================================================================

def find_core_path():
    base = os.path.join(os.environ.get('LOCALAPPDATA', ''),
                        'Arduino15', 'packages', 'teensy', 'hardware', 'avr')
    if not os.path.isdir(base):
        return None
    for v in sorted(os.listdir(base), reverse=True):
        p = os.path.join(base, v, 'cores', 'teensy4')
        if os.path.isdir(p):
            return p
    return None

# ================================================================
#  메인
# ================================================================

def main():
    ap = argparse.ArgumentParser(description='usb_desc.c 슬라이더 HID 패치')
    ap.add_argument('--check', action='store_true', help='상태 확인만')
    ap.add_argument('--revert', action='store_true', help='백업에서 복원')
    ap.add_argument('--path', type=str, help='코어 경로 직접 지정')
    args = ap.parse_args()

    core = args.path or find_core_path()
    if not core:
        print('[ERROR] Teensyduino 코어 경로를 찾을 수 없습니다. --path 로 지정하세요.')
        sys.exit(1)

    fpath = os.path.join(core, 'usb_desc.c')
    if not os.path.isfile(fpath):
        print(f'[ERROR] {fpath} 를 찾을 수 없습니다.')
        sys.exit(1)

    print(f'파일: {fpath}\n')

    if args.revert:
        bak = fpath + '.redkite.bak'
        if os.path.exists(bak):
            shutil.copy2(bak, fpath)
            print(f'복원 완료: {os.path.basename(bak)} → usb_desc.c')
        else:
            print('백업 파일 없음')
        return

    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # 이미 패치됨
    if PATCHED_BLOCK in content:
        print('이미 패치됨 (변경 없음)')
        return

    # 원본 패턴 검색
    if ORIGINAL_BLOCK not in content:
        if '0x95, 23,' in content and 'JOYSTICK_SIZE == 64' in content:
            print('[WARN] Report Count 23 발견했으나 패턴 불일치. 수동 확인 필요.')
        else:
            print('[WARN] extreme joystick 블록을 찾을 수 없습니다.')
        return

    if args.check:
        print('  [예정] Report Count 23 → 8 + padding 15')
        print('\n--check 없이 실행하면 적용됩니다.')
        return

    # 백업
    bak = fpath + '.redkite.bak'
    if not os.path.exists(bak):
        shutil.copy2(fpath, bak)
        print(f'백업: {os.path.basename(bak)}')

    content = content.replace(ORIGINAL_BLOCK, PATCHED_BLOCK)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

    print('  [적용] Report Count 23 → 8 + padding 15')
    print('\n완료. 펌웨어를 빌드하세요.')


if __name__ == '__main__':
    main()
