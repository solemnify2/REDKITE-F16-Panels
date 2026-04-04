"""
DCS-BIOS UDP -> Serial Bridge
DCS-BIOS UDP 멀티캐스트 데이터를 Teensy COM 포트로 전달합니다.

사용법:
  python dcsbios_bridge.py          (COM 포트 자동 감지)
  python dcsbios_bridge.py COM4     (COM 포트 지정)

필요 패키지:
  pip install pyserial
"""

import socket
import struct
import sys
import time
import serial
import serial.tools.list_ports

# DCS-BIOS UDP 설정 (BIOSConfig.lua 기본값)
MULTICAST_GROUP = "239.255.50.10"
MULTICAST_PORT = 5010
# Teensy는 USB CDC이므로 baud rate는 무관하지만 형식상 설정
SERIAL_BAUD = 1000000

# Tracked DCS-BIOS address for backlight resync
ADDR_LIGHT_INST_PNL   = 0x4484  # LIGHT_INST_PNL (output indicator, 0–65535)


def find_teensy_port():
    """Teensy COM 포트 자동 감지"""
    ports = serial.tools.list_ports.comports()
    for p in ports:
        desc = (p.description or "").lower()
        mfr = (p.manufacturer or "").lower()
        if "teensy" in desc or "teensy" in mfr:
            return p.device
    if ports:
        print("Teensy를 자동 감지하지 못했습니다. 사용 가능한 포트:")
        for p in ports:
            print(f"  {p.device} - {p.description}")
    return None


def filter_changed_only(data, state):
    """Parse DCS-BIOS frame, update state dict, return frame with only changed values.
    Returns None if nothing changed."""
    # Skip sync header (0x55 x4)
    i = 0
    while i + 3 < len(data) and data[i] == 0x55 and data[i+1] == 0x55 and data[i+2] == 0x55 and data[i+3] == 0x55:
        i += 4
    changed_chunks = []
    while i + 3 < len(data):
        addr = data[i] | (data[i+1] << 8)
        count = data[i+2] | (data[i+3] << 8)
        i += 4
        if addr == 0x5555 and count == 0x5555:
            break
        if i + count > len(data):
            break
        # Check each word in this chunk for changes
        for offset in range(0, count, 2):
            if i + offset + 1 < len(data):
                word_addr = addr + offset
                new_val = data[i + offset] | (data[i + offset + 1] << 8)
                old_val = state.get(word_addr)
                if old_val != new_val:
                    state[word_addr] = new_val
                    changed_chunks.append((word_addr, new_val))
        i += count

    if not changed_chunks:
        return None

    # Build a filtered DCS-BIOS frame with only changed words
    frame = b'\x55\x55\x55\x55'
    for word_addr, value in changed_chunks:
        frame += struct.pack('<HHH', word_addr, 2, value)
    frame += struct.pack('<HH', 0x5555, 0x5555)
    return frame


def extract_tracked_values(data, tracked, debug=False):
    """Parse DCS-BIOS frame and update tracked address values dict."""
    # Skip sync header (0x55 x4)
    i = 0
    while i + 3 < len(data) and data[i] == 0x55 and data[i+1] == 0x55 and data[i+2] == 0x55 and data[i+3] == 0x55:
        i += 4
    while i + 3 < len(data):
        addr = data[i] | (data[i+1] << 8)
        count = data[i+2] | (data[i+3] << 8)
        i += 4
        if addr == 0x5555 and count == 0x5555:
            break
        if i + count > len(data):
            break
        for offset in range(0, count, 2):
            if i + offset + 1 < len(data):
                word_addr = addr + offset
                if word_addr in tracked:
                    new_val = data[i + offset] | (data[i + offset + 1] << 8)
                    if debug and tracked[word_addr] != new_val:
                        print(f"\n  [LIGHT] 0x{word_addr:04X}: {tracked[word_addr]} → {new_val}")
                    tracked[word_addr] = new_val
        i += count



_debug_prev = {}

def parse_dcsbios_packet(data, debug_addrs):
    """Parse DCS-BIOS binary frame and print values at watched addresses (change only)."""
    # Skip sync header (0x55 x4)
    i = 0
    while i + 3 < len(data) and data[i] == 0x55 and data[i+1] == 0x55 and data[i+2] == 0x55 and data[i+3] == 0x55:
        i += 4
    while i + 3 < len(data):
        addr = data[i] | (data[i+1] << 8)
        count = data[i+2] | (data[i+3] << 8)
        i += 4
        if addr == 0x5555 and count == 0x5555:
            break  # frame end
        if i + count > len(data):
            break
        for offset in range(0, count, 2):
            if i + offset + 1 < len(data):
                word_addr = addr + offset
                if word_addr in debug_addrs:
                    value = data[i + offset] | (data[i + offset + 1] << 8)
                    if _debug_prev.get(word_addr) != value:
                        _debug_prev[word_addr] = value
                        act = 1 if (value & 0x0004) else 0
                        stb = 1 if (value & 0x0008) else 0
                        twa = f"{1 if (value & 0x0400) else 0}{1 if (value & 0x0800) else 0}{1 if (value & 0x1000) else 0}{1 if (value & 0x2000) else 0}"
                        print(f"\n  [DCS] 0x{word_addr:04X} = 0x{value:04X}  ACT={act} STB={stb} TWA={twa}")
        i += count


def main():
    import argparse
    parser = argparse.ArgumentParser(description='DCS-BIOS UDP -> Serial Bridge')
    parser.add_argument('port', nargs='?', default=None, help='COM port (default: auto-detect or COM4)')
    parser.add_argument('--debug', action='store_true', help='Print 0x447E values to console')
    parser.add_argument('--raw', action='store_true', help='Forward all DCS-BIOS data including carousel resync (default: changed values only)')
    args = parser.parse_args()

    # COM 포트 결정
    if args.port:
        com_port = args.port
    else:
        com_port = find_teensy_port()
        if not com_port:
            com_port = 'COM4'
            print(f"COM 포트 자동 감지 실패, 기본값 {com_port} 사용")

    debug_addrs = {0x447E} if args.debug else set()

    # 시리얼 포트 열기
    try:
        ser = serial.Serial(com_port, SERIAL_BAUD, timeout=0)
        print(f"[Serial] {com_port} 연결됨")
    except serial.SerialException as e:
        print(f"[Serial] {com_port} 열기 실패: {e}")
        sys.exit(1)

    # UDP 멀티캐스트 소켓 설정
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", MULTICAST_PORT))

    mreq = struct.pack("4s4s", socket.inet_aton(MULTICAST_GROUP), socket.inet_aton("0.0.0.0"))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.settimeout(1.0)

    print(f"[UDP] {MULTICAST_GROUP}:{MULTICAST_PORT} 수신 대기 중...")
    print("DCS World를 실행하고 비행을 시작하세요. (Ctrl+C로 종료)")
    print()

    total_bytes = 0
    packet_count = 0
    last_status = time.time()
    receiving = False

    # Tracked address for backlight debug
    tracked = {ADDR_LIGHT_INST_PNL: None}
    # State dict for change-only filtering (default: enabled, --raw disables)
    resync_state = None if args.raw else {}

    try:
        while True:
            try:
                data, addr = sock.recvfrom(4096)
                if data:
                    if resync_state is not None:
                        filtered = filter_changed_only(data, resync_state)
                        if filtered:
                            ser.write(filtered)
                            if debug_addrs:
                                parse_dcsbios_packet(filtered, debug_addrs)
                    else:
                        ser.write(data)
                        if debug_addrs:
                            parse_dcsbios_packet(data, debug_addrs)
                    extract_tracked_values(data, tracked, debug=args.debug)
                    total_bytes += len(data)
                    packet_count += 1

                    if not receiving:
                        receiving = True
                        print(f"[OK] DCS-BIOS 데이터 수신 시작! (from {addr[0]})")

                    # 1초마다 상태 출력
                    now = time.time()
                    if now - last_status >= 1.0:
                        print(f"  패킷: {packet_count}, 전송: {total_bytes} bytes", end="\r")
                        last_status = now

            except socket.timeout:
                if receiving:
                    print(f"\n[!] UDP 데이터 수신 중단됨. 대기 중...")
                    receiving = False
            except serial.SerialException:
                print(f"\n[Serial] {com_port} 연결 끊김. 재연결 시도...")
                ser.close()
                while True:
                    try:
                        time.sleep(2)
                        ser = serial.Serial(com_port, SERIAL_BAUD, timeout=0)
                        print(f"[Serial] {com_port} 재연결됨")
                        break
                    except serial.SerialException:
                        pass
    except KeyboardInterrupt:
        print(f"\n종료. 총 {packet_count} 패킷, {total_bytes} bytes 전송됨.")
    finally:
        ser.close()
        sock.close()


if __name__ == "__main__":
    main()
