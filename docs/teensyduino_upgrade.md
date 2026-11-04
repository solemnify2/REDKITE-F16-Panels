# Teensyduino 업데이트 후 USB 설정

Teensyduino 코어가 업데이트되면 이 프로젝트에서 수정한 USB 디스크립터가 교체될 수 있습니다.
사용 중인 코어의 `usb_desc.h`와 `usb_desc.c`를 확인한 뒤 다시 빌드하십시오.

```text
%LOCALAPPDATA%\Arduino15\packages\teensy\hardware\avr\<version>\cores\teensy4\
```

## 1. usb_desc.h: 버튼 수와 장치 PID

Arduino IDE의 USB Type은 **Serial + Keyboard + Mouse + Joystick**입니다.
이에 해당하는 `USB_SERIAL_HID` 분기의 활성 정의를 확인합니다.

```c
#define JOYSTICK_SIZE 64  // Extreme: 128 buttons
#define PRODUCT_ID 0x0487 // AUX; Console build: 0x048E
```

| 빌드 대상 | PID | JOYSTICK_SIZE |
|---|---|---|
| Left Aux + MISC | `0x0487` | `64` |
| Left Console | `0x048E` | `64` |

두 스케치의 `JOYSTICK_SIZE`는 같습니다. 보드를 바꿔 빌드할 때는 PID를 맞춥니다.
선택한 분기에 동일 매크로가 중복 정의되지 않도록 확인하십시오.
`USB_SERIAL` 분기도 별도로 수정해 사용한다면 해당 분기의 값도 확인합니다.
콘솔의 기존 코어 설정에는 장치 버전 값 `BCD_DEVICE 0x0212`도 포함되어 있습니다.

이전 기록의 AUX PID `0x048D`는 현재 스케치와 다릅니다. 현재 값은 `0x0487`입니다.

## 2. usb_desc.c: DirectInput용 축 구성

`#elif JOYSTICK_SIZE == 64`의 HID 디스크립터에서 아날로그 입력 부분을 확인합니다.
원본은 명명 축 6개와 슬라이더 17개를 선언합니다. 이 프로젝트에서는 DirectInput에서 사용할 축을 8개로 제한하고,
나머지 15개를 constant padding으로 처리합니다.

해당 아날로그 블록의 구성은 다음과 같습니다. 기존 블록과 교체하며, 아래 내용을 추가로 중복 삽입하지 않습니다.

```c
0x75, 0x10,       // Report Size: 16 bits
0x95, 8,          // Report Count: 8 axes
0x09, 0x30,       // X
0x09, 0x31,       // Y
0x09, 0x32,       // Z
0x09, 0x33,       // Rx
0x09, 0x34,       // Ry
0x09, 0x35,       // Rz
0x09, 0x36,       // Slider
0x09, 0x36,       // Slider
0x81, 0x02,       // Input: variable, absolute
0x95, 15,         // Remaining 15 channels
0x81, 0x01,       // Input: constant padding
```

USB 보고서 크기는 64바이트로 유지합니다. 펌웨어의 `Joystick.slider()` API는 유지되지만,
padding 영역은 게임의 입력 축으로 사용하지 않습니다.
ILS 노브의 실제 게임 매핑은 [REF_KEYMAP.md](REF_KEYMAP.md#축-설정)를 참고하십시오.

## 3. 보조 도구

저장소에는 `tools/patch_usb_desc_h.py`와 `tools/patch_usb_desc_c.py`가 있습니다.
도구를 사용할 때도 변경 전 코어를 백업하고, 변경 후 위 매크로와 디스크립터 내용을 직접 대조하십시오.
코어 버전과 기존 수정 상태에 따라 자동 패치 결과가 달라질 수 있습니다.

## 4. 확인 순서

1. 실제 빌드에 사용되는 코어 버전과 파일 경로를 확인합니다.
2. `USB_SERIAL_HID`의 `JOYSTICK_SIZE 64`와 대상 보드의 PID를 확인합니다.
3. 아날로그 Report Count가 8, padding이 15인지 확인합니다.
4. 해당 스케치를 빌드해 업로드합니다.
5. Windows 입력 도구에서 장치명·버튼·축을 확인합니다. `joy.cpl`은 버튼 32개까지만 표시합니다.
6. DX 배치를 바꿨다면 [키맵을 다시 생성](REF_KEYMAP.md)하고 게임에서 확인합니다.
