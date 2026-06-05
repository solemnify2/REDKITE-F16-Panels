# Windows 조이스틱 이름 캐시 변경

Windows는 조이스틱을 처음 인식할 때 USB Product Name을 레지스트리에 캐시합니다.
이후 펌웨어에서 이름을 변경해도 캐시된 이름이 계속 표시됩니다 (joy.cpl 등).

## 캐시 위치

```
HKCU\System\CurrentControlSet\Control\MediaProperties\PrivateProperties\Joystick\OEM\VID_xxxx&PID_xxxx
```

| 장치 | VID | PID | 레지스트리 키 |
|------|-----|-----|--------------|
| Left Aux Misc | 0x16C0 | 0x0487 | `VID_16C0&PID_0487` |
| Left Console | 0x16C0 | 0x048E | `VID_16C0&PID_048E` |

## 캐시 갱신

펌웨어 업로드 후 이름이 반영되지 않으면 `tools/update_joystick_name.bat`을 더블클릭하세요.

`joy.cpl` (조이스틱 제어판)을 다시 열면 변경된 이름이 표시됩니다.

## 참고

- 레지스트리 삭제(`Remove-ItemProperty`)는 Windows가 다시 드라이버 이름("Serial/Keyboard/Mouse/Joystick")으로 재생성하므로, 삭제 대신 **덮어쓰기**를 사용합니다.
- 새 PID를 가진 장치를 처음 연결하면 캐시가 없으므로 펌웨어의 USB Product Name이 바로 반영됩니다.
- `name.c`에서 USB Product Name을 변경한 경우 반드시 펌웨어 업로드 후 캐시를 갱신하세요.
