"""
DCS-BIOS UDP -> Serial Bridge (통합)
DCS-BIOS UDP 멀티캐스트 데이터를 여러 Teensy COM 포트로 동시 전달합니다.

각 Teensy는 자신이 관심 있는 DCS-BIOS 주소만 파싱하므로,
동일한 데이터를 모든 포트에 전송합니다.

사용법:
  python dcsbios_bridge.py                     (자동 감지)
  python dcsbios_bridge.py COM3 COM4           (수동 지정)
  python dcsbios_bridge.py --debug

필요 패키지:
  pip install pyserial
"""

import socket
import struct
import sys
import time
import serial
import serial.tools.list_ports

MULTICAST_GROUP = "239.255.50.10"
MULTICAST_PORT = 5010
SERIAL_BAUD = 1000000


TEENSY_VID  = 0x16C0

# 새 Teensy 추가 시 여기에 한 줄 추가
PID_NAMES = {
    0x0487: "REDKITE F16 Left Aux Misc",
    0x0489: "REDKITE F16 Left Aux Misc",
    0x048E: "REDKITE F16 ELEC ECM AVTR",
}


def read_serial_output(port, s, rx_bufs):
    """Read and print any serial output from Teensy (non-blocking)."""
    n = s.in_waiting
    if n <= 0:
        return
    rx_bufs[port] = rx_bufs.get(port, b'') + s.read(n)
    while b'\n' in rx_bufs[port]:
        line, rx_bufs[port] = rx_bufs[port].split(b'\n', 1)
        print(f"[{port}] {line.decode('utf-8', errors='replace').rstrip()}")


def find_teensy_ports():
    """VID 기반 Teensy COM 포트 자동 감지 (복수).
    Returns (ports, descriptions)."""
    ports = serial.tools.list_ports.comports()
    found = []
    descriptions = []
    for p in ports:
        if p.vid == TEENSY_VID:
            found.append(p.device)
            name = PID_NAMES.get(p.pid, f"Unknown (PID:0x{p.pid:04X})")
            descriptions.append(f"  {p.device}: {name}")
    return found, descriptions



def parse_dcsbios_frame(data, watch_addrs):
    """Parse DCS-BIOS frame and print watched addresses."""
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
                if word_addr in watch_addrs:
                    val = data[i + offset] | (data[i + offset + 1] << 8)
                    print(f"  [WATCH] 0x{word_addr:04X} = 0x{val:04X}")
        i += count


def main():
    import argparse
    parser = argparse.ArgumentParser(description='DCS-BIOS UDP -> Serial Bridge (통합)')
    parser.add_argument('ports', nargs='*', help='COM ports (default: auto-detect Teensy)')
    parser.add_argument('--debug', action='store_true', help='Print debug info')
    parser.add_argument('--watch', type=str, default='', help='Hex addresses to watch, comma separated (e.g. 0x4480,0x448A)')
    args = parser.parse_args()

    # COM 포트 결정
    com_ports = args.ports
    if not com_ports:
        com_ports, descs = find_teensy_ports()
        if not com_ports:
            all_ports = serial.tools.list_ports.comports()
            print("Teensy를 자동 감지하지 못했습니다.")
            if all_ports:
                print("사용 가능한 COM 포트:")
                for p in all_ports:
                    vid_str = f"VID:0x{p.vid:04X}" if p.vid else "VID:N/A"
                    pid_str = f"PID:0x{p.pid:04X}" if p.pid else "PID:N/A"
                    print(f"  {p.device}: {p.description} [{vid_str} {pid_str}]")
            print("포트를 인자로 지정하세요. 예: python dcsbios_bridge.py COM3 COM4")
            sys.exit(1)

    rx_bufs = {}

    # 시리얼 포트 열기
    serials = []
    failed = False
    # PID→이름 역매핑 (연결 메시지용)
    port_pid_names = {}
    for p in serial.tools.list_ports.comports():
        if p.vid == TEENSY_VID:
            port_pid_names[p.device] = PID_NAMES.get(p.pid, f"Unknown (PID:0x{p.pid:04X})")

    for port in com_ports:
        try:
            s = serial.Serial(port, SERIAL_BAUD, timeout=0)
            serials.append((port, s))
            rx_bufs[port] = b''
            name = port_pid_names.get(port, port)
            print(f"  {port}: {name}")
        except serial.SerialException as e:
            print(f"[Serial] {port} 열기 실패: {e}")
            failed = True

    if failed:
        all_ports = serial.tools.list_ports.comports()
        if all_ports:
            print("현재 검색되는 COM 포트:")
            for p in all_ports:
                print(f"  {p.device}: {p.description}")
        else:
            print("시스템에 COM 포트가 없습니다.")

    if not serials:
        sys.exit(1)

    # UDP 멀티캐스트 소켓
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", MULTICAST_PORT))
    mreq = struct.pack("4s4s", socket.inet_aton(MULTICAST_GROUP), socket.inet_aton("0.0.0.0"))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.settimeout(1.0)

    port_names = ', '.join(p for p, _ in serials)
    print(f"[UDP] {MULTICAST_GROUP}:{MULTICAST_PORT} 수신 대기 중...")
    print(f"[Target] {port_names}")
    print("DCS World를 실행하고 비행을 시작하세요. (Ctrl+C로 종료)\n")

    total_bytes = 0
    packet_count = 0
    last_status = time.time()
    receiving = False
    watch_addrs = set()
    if args.watch:
        for a in args.watch.split(','):
            watch_addrs.add(int(a.strip(), 0))

    try:
        while True:
            try:
                data, addr = sock.recvfrom(4096)
                if data:
                    for port, s in serials:
                        try:
                            s.write(data)
                        except serial.SerialException:
                            pass

                    if watch_addrs:
                        parse_dcsbios_frame(data, watch_addrs)

                    total_bytes += len(data)
                    packet_count += 1

                    if not receiving:
                        receiving = True
                        print(f"[OK] DCS-BIOS 데이터 수신 시작! (from {addr[0]})")

                    # Read serial output from Teensy
                    for port, s in serials:
                        read_serial_output(port, s, rx_bufs)

                    now = time.time()
                    if now - last_status >= 1.0:
                        print(f"  패킷: {packet_count}, 전송: {total_bytes} bytes → {port_names}", end="\r")
                        last_status = now

            except socket.timeout:
                if receiving:
                    print(f"\n[!] UDP 데이터 수신 중단됨. 대기 중...")
                    receiving = False

            # Read serial output from Teensy (always, even without UDP data)
            for port, s in serials:
                read_serial_output(port, s, rx_bufs)

    except KeyboardInterrupt:
        print(f"\n종료. 총 {packet_count} 패킷, {total_bytes} bytes 전송됨.")
    finally:
        for _, s in serials:
            s.close()
        sock.close()


if __name__ == "__main__":
    main()
