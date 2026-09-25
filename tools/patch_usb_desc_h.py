#!/usr/bin/env python3
"""
usb_desc.h 자동 패치 — Redkite F16 Panels

Teensyduino 업데이트 후 실행:
    python tools/patch_usb_desc_h.py                   # LEFT CONSOLE (PID 0x048E)
    python tools/patch_usb_desc_h.py --device aux      # LEFT AUX MISC (PID 0x0487)
    python tools/patch_usb_desc_h.py --check            # 상태 확인만
    python tools/patch_usb_desc_h.py --revert           # 백업에서 복원

수정 내용:
  1. JOYSTICK_SIZE 64 (USB_SERIAL, USB_SERIAL_HID 두 섹션)
  2. PRODUCT_ID (디바이스에 따라 0x048E 또는 0x0487)
  3. BCD_DEVICE 0x0212 추가 (LEFT CONSOLE)
"""

import os, sys, re, shutil, argparse

DEVICE_PIDS = {
    'console': ('0x048e', 'LEFT CONSOLE'),
    'aux':     ('0x0487', 'LEFT AUX MISC'),
}


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


def patch(content, device):
    changes = []
    pid, label = DEVICE_PIDS[device]

    # --- JOYSTICK_SIZE: USB_SERIAL 섹션 (USB_SERIAL_HID 이전) ---
    hid_pos = content.find('#elif defined(USB_SERIAL_HID)')
    if hid_pos == -1:
        print('  [ERROR] USB_SERIAL_HID 섹션을 찾을 수 없습니다')
        return content, changes

    before = content[:hid_pos]
    after = content[hid_pos:]

    pat = r'(#define JOYSTICK_SIZE\s+)12(\s+//\s*12 = normal)'
    if re.search(pat, before):
        before = re.sub(pat, r'\g<1>64\2', before)
        changes.append('USB_SERIAL: JOYSTICK_SIZE 12 → 64')

    # --- JOYSTICK_SIZE: USB_SERIAL_HID 섹션 ---
    pat12 = r'^(\s*)(#define JOYSTICK_SIZE\s+12\s+//.*12 = normal.*)$'
    pat64_off = r'^(\s*)//\s*(#define JOYSTICK_SIZE\s+64\s+//.*12 = normal.*)$'
    if re.search(pat12, after, re.MULTILINE):
        after = re.sub(pat12, r'\1//  \2', after, flags=re.MULTILINE)
        changes.append('USB_SERIAL_HID: JOYSTICK_SIZE 12 주석 처리')
    if re.search(pat64_off, after, re.MULTILINE):
        after = re.sub(pat64_off, r'\1  \2', after, flags=re.MULTILINE)
        changes.append('USB_SERIAL_HID: JOYSTICK_SIZE 64 활성화')

    content = before + after

    # --- PRODUCT_ID ---
    # 원본: #define PRODUCT_ID 0x0487 (주석 없이)
    # 패치 후: 선택한 PID만 활성화
    pid_original = r'^\s*#define PRODUCT_ID\s+0x0487\s*$'
    if re.search(pid_original, content, re.MULTILINE):
        if device == 'console':
            block = (
                '  // #define PRODUCT_ID\t\t0x0487    // Original USB_SERIAL_HID\n'
                '  #define PRODUCT_ID\t\t 0x048e      // LEFT CONSOLE\n'
                '  #define BCD_DEVICE 0x0212     // added by kimhy'
            )
        else:
            block = '  #define PRODUCT_ID\t\t0x0487    // LEFT AUX MISC (original)'
        content = re.sub(pid_original, block, content, count=1, flags=re.MULTILINE)
        changes.append(f'PRODUCT_ID → {pid} ({label})')

    # 이미 패치된 상태에서 디바이스 전환
    if device == 'console':
        # 0x0487 활성 → 주석, 0x048e 주석 → 활성
        pat_0487_active = r'^(\s*)#define PRODUCT_ID\s+0x0487\s+//.*$'
        pat_048e_comment = r'^(\s*)//\s*(#define PRODUCT_ID\s+0x048e\b.*)$'
        if re.search(pat_0487_active, content, re.MULTILINE) and \
           re.search(pat_048e_comment, content, re.MULTILINE):
            content = re.sub(pat_0487_active,
                             r'\1// #define PRODUCT_ID\t\t0x0487    // Original USB_SERIAL_HID',
                             content, flags=re.MULTILINE)
            content = re.sub(pat_048e_comment, r'\1  \2', content, flags=re.MULTILINE)
            changes.append(f'PRODUCT_ID 전환 → {pid} ({label})')
    elif device == 'aux':
        # 0x048e 활성 → 주석, 0x0487 주석 → 활성
        pat_048e_active = r'^(\s*)#define PRODUCT_ID\s+0x048e\b.*$'
        pat_0487_comment = r'^(\s*)//\s*(#define PRODUCT_ID\s+0x0487\b.*)$'
        if re.search(pat_048e_active, content, re.MULTILINE) and \
           re.search(pat_0487_comment, content, re.MULTILINE):
            content = re.sub(pat_048e_active,
                             r'\1// #define PRODUCT_ID\t\t 0x048e      // LEFT CONSOLE',
                             content, flags=re.MULTILINE)
            content = re.sub(pat_0487_comment, r'\1  \2', content, flags=re.MULTILINE)
            changes.append(f'PRODUCT_ID 전환 → {pid} ({label})')

    return content, changes


def main():
    ap = argparse.ArgumentParser(description='usb_desc.h 패치')
    ap.add_argument('--device', choices=['console', 'aux'], default='console',
                    help='대상 디바이스 (기본: console)')
    ap.add_argument('--check', action='store_true', help='상태 확인만')
    ap.add_argument('--revert', action='store_true', help='백업에서 복원')
    ap.add_argument('--path', type=str, help='코어 경로 직접 지정')
    args = ap.parse_args()

    core = args.path or find_core_path()
    if not core:
        print('[ERROR] Teensyduino 코어 경로를 찾을 수 없습니다. --path 로 지정하세요.')
        sys.exit(1)

    fpath = os.path.join(core, 'usb_desc.h')
    if not os.path.isfile(fpath):
        print(f'[ERROR] {fpath} 를 찾을 수 없습니다.')
        sys.exit(1)

    print(f'파일: {fpath}')
    print(f'디바이스: {args.device.upper()}\n')

    if args.revert:
        bak = fpath + '.redkite.bak'
        if os.path.exists(bak):
            shutil.copy2(bak, fpath)
            print(f'복원 완료: {os.path.basename(bak)} → usb_desc.h')
        else:
            print('백업 파일 없음')
        return

    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        original = f.read()

    result, changes = patch(original, args.device)

    if result == original:
        print('이미 패치됨 (변경 없음)')
        return

    if args.check:
        for c in changes:
            print(f'  [예정] {c}')
        print('\n--check 없이 실행하면 적용됩니다.')
        return

    # 백업
    bak = fpath + '.redkite.bak'
    if not os.path.exists(bak):
        shutil.copy2(fpath, bak)
        print(f'백업: {os.path.basename(bak)}')

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(result)
    for c in changes:
        print(f'  [적용] {c}')
    print('\n완료. 펌웨어를 빌드하세요.')


if __name__ == '__main__':
    main()
