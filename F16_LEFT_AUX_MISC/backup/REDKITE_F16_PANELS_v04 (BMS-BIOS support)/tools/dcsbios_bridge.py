"""
DCS-BIOS UDP -> Serial Bridge
DCS-BIOS UDP 멀티캐스트 데이터를 Teensy COM 포트로 전달합니다.

사용법:
  python dcsbios_bridge.py          (COM 포트 자동 감지)
  python dcsbios_bridge.py COM5     (COM 포트 지정)

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


def main():
    # COM 포트 결정
    if len(sys.argv) > 1:
        com_port = sys.argv[1]
    else:
        com_port = find_teensy_port()
        if not com_port:
            print("COM 포트를 찾을 수 없습니다. 포트를 인자로 지정하세요.")
            print("예: python dcsbios_bridge.py COM5")
            sys.exit(1)

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

    try:
        while True:
            try:
                data, addr = sock.recvfrom(4096)
                if data:
                    ser.write(data)
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
