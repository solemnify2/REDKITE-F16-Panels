# Teensyduino / Arduino IDE 업그레이드 가이드

Arduino IDE 또는 Teensyduino 업데이트 시 코어 파일이 덮어씌워집니다.
업데이트 후 아래 두 파일을 반드시 다시 수정해야 합니다.

코어 파일 경로:
```
%LOCALAPPDATA%\Arduino15\packages\teensy\hardware\avr\<version>\cores\teensy4\
```

---

## 1. usb_desc.h

`#elif defined(USB_SERIAL_HID)` 섹션을 찾아 아래 항목을 수정합니다.

### JOYSTICK_SIZE (두 곳)

`USB_SERIAL` 섹션과 `USB_SERIAL_HID` 섹션에 각각 하나씩 있습니다.

```c
// USB_SERIAL 섹션 (~line 272)
#define JOYSTICK_SIZE         64    //  12 = normal, 64 = extreme joystick

// USB_SERIAL_HID 섹션 (~line 321-322)
//  #define JOYSTICK_SIZE         12    //  12 = normal, 64 = extreme joystick
  #define JOYSTICK_SIZE         64    //  12 = normal, 64 = extreme joystick
```

### PRODUCT_ID

`USB_SERIAL_HID` 섹션에서 변경:

```c
  // #define PRODUCT_ID        0x0487    // Original USB_SERIAL_HID
  // #define PRODUCT_ID        0x048D    // LEFT AUX MISC
  #define PRODUCT_ID           0x048e    // LEFT CONSOLE
  #define BCD_DEVICE 0x0212     // added by kimhy
```

> LEFT_AUX_MISC 빌드 시에는 `0x048D` 를 활성화하고 `0x048e` 를 주석 처리합니다.
> 현재 양쪽 스케치 모두 `JOYSTICK_SIZE 64` 를 사용하므로 전환 시 PID만 바꾸면 됩니다.

---

## 2. usb_desc.c

`#elif JOYSTICK_SIZE == 64` 블록 (extreme joystick) 안의 HID descriptor 를 수정합니다.

### 변경 내용: 슬라이더 Report Count 23 → 8 + padding 15

Teensyduino 원본은 슬라이더 17개를 전부 `Usage 0x36`(Slider)으로 선언합니다.
이 중복으로 인해 Windows DirectInput이 슬라이더를 전혀 인식하지 못합니다.
Report Count 를 8로 줄이고 나머지를 constant padding으로 처리하면 해결됩니다.

**원본 (변경 전):**
```c
        0x75, 0x10,                     // Report Size (16)
        0x95, 23,                       // Report Count (23)
        0x09, 0x30,                     // Usage (X)
        0x09, 0x31,                     // Usage (Y)
        0x09, 0x32,                     // Usage (Z)
        0x09, 0x33,                     // Usage (Rx)
        0x09, 0x34,                     // Usage (Ry)
        0x09, 0x35,                     // Usage (Rz)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x81, 0x02,                     // Input (variable,absolute)
```

**수정 후:**
```c
        0x75, 0x10,                     // Report Size (16)
        0x95, 8,                        // Report Count (8)
        0x09, 0x30,                     // Usage (X)
        0x09, 0x31,                     // Usage (Y)
        0x09, 0x32,                     // Usage (Z)
        0x09, 0x33,                     // Usage (Rx)
        0x09, 0x34,                     // Usage (Ry)
        0x09, 0x35,                     // Usage (Rz)
        0x09, 0x36,                     // Usage (Slider)
        0x09, 0x36,                     // Usage (Slider)
        0x81, 0x02,                     // Input (variable,absolute)
        0x95, 15,                       // Report Count (15)
        0x81, 0x01,                     // Input (constant) — padding
```

USB report 크기(64바이트)는 변하지 않습니다.

---

## 검증 체크리스트

1. `usb_desc.h` — `JOYSTICK_SIZE 64` 두 곳 확인
2. `usb_desc.h` — `PRODUCT_ID 0x048E` (LEFT CONSOLE) 확인
3. `usb_desc.c` — Report Count `8` + padding `15` 확인
4. Arduino IDE에서 빌드 → 업로드
5. joy.cpl에서 X/Y/Z/Rx/Ry/Rz + Slider 0/1 = 8축 동작 확인
