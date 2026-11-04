# 키맵 자동 생성

Teensy에 업로드된 펌웨어에서 현재 DX 번호와 컨트롤 이름을 읽어, 장치별 키맵을 생성합니다.
`dxOrder[]`를 변경한 뒤에는 펌웨어를 업로드하고 키맵을 다시 생성하십시오.

| 대상 | 실행 파일 | 출력 파일 예시 |
|---|---|---|
| Falcon BMS | `tools/gen_bms_setup_xml.py` | `left_console_new1.xml` |
| DCS F-16C | `tools/gen_dcs_profile.py` | `left_console_new1.diff.lua` |

연결된 보드마다 파일이 하나씩 생성됩니다. 생성기는 기존 게임 설정을 변경하지 않습니다.
출력 파일은 현재 작업 폴더에 저장하며, 기존 파일과 겹치지 않는 번호를 붙입니다.

## 1. 실행 준비

1. Teensy를 연결합니다. 펌웨어는 `?DX` 질의를 지원해야 합니다.
2. BMS/DCS 브리지를 종료하고 **6초 이상** 기다립니다. 브리지가 COM 포트를 사용 중이거나 펌웨어가 BIOS 수신 상태이면 질의에 응답하지 못합니다.
3. 프로젝트 루트에서 필요한 생성기를 실행합니다.

Python과 `pyserial`이 필요합니다.

```powershell
python -m pip install pyserial
```

실행에는 `tools/` 폴더가 필요하며, Arduino 소스나 개발환경은 필요하지 않습니다.
BMS 생성기는 설치된 `BMS - Full.key`를 읽습니다. DCS 생성기는 저장소의 명령 카탈로그를 사용합니다.

| 옵션 | 용도 |
|---|---|
| 생략 | VID/PID로 보드 자동 탐지 |
| `--port COM7` | 질의할 포트 지정. 여러 보드는 옵션을 반복 지정 |
| `--bms-root "D:\Falcon BMS 4.38"` | BMS 설치 경로 지정. BMS 생성기 전용 |
| `--dcs-profiles "D:\...\InputUserProfiles"` | 덮어쓸 프로파일을 고를 폴더. DCS 생성기 전용 |

생성기는 항상 현재 폴더에 새 파일을 만든 다음, 심이 쓰는 파일을 **덮어쓸지 물어봅니다.**
고른 파일은 먼저 `.bak1`, `.bak2`로 복사해 두므로 이전 설정이 남습니다.
Enter를 누르면 아무것도 건드리지 않습니다. 터미널이 아닌 환경에서는 묻지 않습니다.

## 2. BMS: 생성 및 적용

```powershell
python tools/gen_bms_setup_xml.py
```

기본 BMS 경로는 `C:\Falcon BMS 4.38`입니다. 연결된 보드에 따라 다음 파일이 생성됩니다.

| 보드 | 생성 파일 예시 | 적용할 파일 (`User\Config` 안) |
|---|---|---|
| CONSOLE | `left_console_new1.xml` | `Setup.v100.F16 LEFT CONSOLE {GUID}.xml` |
| AUX | `left_aux_misc_new1.xml` | `Setup.v100.F16 LEFT AUX MISC {GUID}.xml` |

적용 순서:

1. BMS의 **SETUP → CONTROLLERS**에서 각 장치에 버튼을 하나 할당하고 저장합니다. 장치별 XML이 이미 있으면 생략합니다.
2. BMS와 Launcher를 종료합니다.
3. 생성기를 실행하고, 덮어쓸 XML을 번호로 고릅니다.
4. BMS를 다시 실행해 F-16 버튼 매핑과 축 설정을 확인합니다.

```text
CONSOLE — 덮어쓸 Setup XML (Enter = 건너뛰기)
  1) Setup.v100.F16 LEFT CONSOLE {6AE05230-5FA3-11F1-8002-444553540000}.xml   2026-11-04 14:16
  2) Setup.v100.F16 LEFT CONSOLE {024BB000-C258-11EF-8002-444553540000}.xml   2024-12-21 08:02
  > 1
```

**제품명이 같은 파일이 여러 개일 수 있습니다.** 같은 보드라도 다른 USB 포트에 꽂으면
BMS가 새 GUID로 파일을 하나 더 만들고, 쓰지 않는 파일도 그대로 남기 때문입니다.
BMS는 현재 장치의 GUID와 맞는 파일만 읽으므로, 죽은 파일에 써넣으면 **오류 없이 매핑만 빠집니다.**
어느 쪽인지는 수정 시각으로 가늠합니다 — 보통 BMS가 마지막으로 저장한 파일이 사용 중인 파일입니다.

후보가 하나도 없으면 1단계에서 장치 설정을 저장했는지 확인하십시오.
Enter로 건너뛰면 직접 실행할 복사 명령이 출력됩니다.

```powershell
Copy-Item "left_console_new1.xml" "C:\Falcon BMS 4.38\User\Config\Setup.v100.F16 LEFT CONSOLE {6AE05230-5FA3-11F1-8002-444553540000}.xml"
```

이 방식은 장치별 XML을 사용하므로 DX 번호에 장치 오프셋을 더하지 않습니다.
`.key`와 `DeviceSorting.txt`를 수정하거나 다른 장치의 설정을 병합할 필요도 없습니다.
**덮어쓴 장치의 기존 버튼·축 설정은 생성된 내용으로 바뀝니다.**

### XML 구조

각 장치는 DX 1부터 번호를 사용합니다. `DxAssgn[0]`이 DX 1입니다.
버튼 하나의 `<Assgn>` 4칸 중 슬롯 0은 누름(`Default`), 슬롯 2는 해제(`Down`)에 사용합니다.
나머지 슬롯은 `SimDoNothing`으로 둡니다.

```xml
<JoyAssgn>
  <detentPosition>...</detentPosition>
  <axis>...</axis>
  <pov>...</pov>
  <dx>...</dx>
  <profileDefaultF16>
    <pov>...</pov>
    <dx>...</dx>
  </profileDefaultF16>
  <profileF15ABCD>
    <pov>...</pov>
    <dx>...</dx>
  </profileF15ABCD>
</JoyAssgn>
```

루트와 F-16 프로파일에 같은 버튼 매핑을 넣고, F-15 프로파일은 비웁니다.
각 `<dx>`에는 버튼 128개가 들어갑니다.
`profileDefaultF16`을 생략하고 루트에 `<dx>`만 반복하면 F-16 매핑이 표시되지 않을 수 있습니다.

## 3. DCS: 생성 및 적용

```powershell
python tools/gen_dcs_profile.py
```

연결된 보드에 따라 `left_console_new1.diff.lua`, `left_aux_misc_new1.diff.lua`가 생성됩니다.

1. DCS의 **Options → Controls**에서 F-16C를 선택합니다.
2. 적용할 Teensy 장치 열을 선택하고 **Save Profile As...**로 기존 설정을 백업합니다.
3. 같은 장치 열에서 **Load Profile...**을 눌러 생성된 `.diff.lua`를 불러옵니다.
4. 다른 보드에도 반복하고, 버튼·축 설정을 확인한 뒤 저장합니다.

`.diff.lua`에는 장치 GUID가 없습니다. **불러올 때 선택한 장치 열**에 적용되므로 CONSOLE과 AUX 파일을 구분하십시오.

생성기는 `InputUserProfiles`의 `.diff.lua` 목록을 보여주고 덮어쓸 파일을 고르게 합니다.
프로파일 이름은 사람이 정하는 것이라 장치명으로 짐작할 수 없기 때문입니다.
폴더는 `--dcs-profiles`로 지정하며, 생략하면 아래 표준 위치를 찾습니다.

```text
C:\Users\<계정>\Saved Games\DCS\InputUserProfiles\
C:\Users\<계정>\Saved Games\DCS.openbeta\InputUserProfiles\
```

**덮어써도 적용은 되지 않습니다.** 위 3번의 Load Profile을 해야 현재 장치에 들어갑니다.
덮어쓰기가 줄여주는 것은 파일을 옮기고 이름을 맞추는 수고뿐입니다.

생성기는 각 장치 열에서 불러올 파일을 안내합니다. 파일명은 변경해도 되지만,
CONSOLE과 AUX 중 어느 장치용인지 구분할 수 있도록 보관하십시오.

## 4. 매핑 기준과 수정 방법

### 펌웨어에서 읽는 정보

생성기는 시리얼로 `?DX`를 보내 다음 형식의 응답을 받습니다.
Arduino 소스의 배열을 읽지 않으므로 **업로드된 펌웨어의 DX 배치**가 기준입니다.

```text
#DX BEGIN device=CONSOLE pid=0x048E entries=34 total=64
#DX 1 1 MPO
#DX 2 2 UHF PRESET
...
#DX END
```

각 행은 `#DX <첫 DX 번호> <DX 개수> <컨트롤 이름>`입니다.
응답의 `device=` 값으로 CONSOLE/AUX 매핑 표를 선택합니다.
헤더의 항목 수·총 버튼 수와 실제 응답을 비교하고, DX 범위(1~128)·연속성·중복을 검사합니다.
검증에 실패하면 파일을 생성하지 않고 중단합니다.

### 컨트롤 이름으로 기능 연결

| 파일 | 내용 |
|---|---|
| `tools/keymap/bms_callbacks.py` | 컨트롤 이름 → BMS 콜백 |
| `tools/keymap/dcs_commands.py` | 컨트롤 이름 → DCS 명령 ID |
| `tools/keymap/dcs_catalog.txt` | DCS 명령 ID → 표시 이름 |
| `tools/keymap/sim_axes.py` | 축 설정, 제품명, 출력 파일명 |
| `tools/keymap/board.py` | 보드 탐지, DX 질의, BMS 콜백 목록 읽기 |

매핑 표의 키는 `?DX` 응답에 들어 있는 컨트롤 이름입니다.
DX 순서만 바꾸면 표를 수정할 필요가 없습니다. 컨트롤을 추가하거나 이름을 바꾸면 두 시뮬레이터의 표도 수정해야 합니다.
표에 없는 이름은 생성 시 보고되며, 해당 DX는 빈칸으로 남습니다.

컨트롤이 사용하는 DX 하나당 목록 항목 하나를 지정합니다.

| 값 | 동작 |
|---|---|
| `'X'` | 누를 때 X에 할당. 별도의 해제 명령은 지정하지 않음 |
| `('X', 'Y')` | 누를 때 X, 뗄 때 Y |
| `('X', None)` | 누를 때 X, 해제 시 추가 명령 없음 |
| `None` | 의도적으로 비워 둔 자리 |
| `UNMODELED(...)` | 현재 BMS에서 대응 기능을 찾지 못한 자리 |
| `TODO` | 명령 확인이 필요한 자리 |

3단 토글은 양 끝 위치에 DX를 하나씩 사용합니다. 중립 명령은 양쪽 DX의 해제에 지정합니다.

```python
'EPU': [('SimEpuOff', 'SimEpuAuto'),
        ('SimEpuOn',  'SimEpuAuto')],
```

JFS는 예외로, 시동 도중 OFF 명령이 나가지 않도록 해제 명령을 지정하지 않습니다.

```python
'JFS': [('SimJfsStartUp',   None),
        ('SimJfsStartDown', None)],
```

로터리(`SW_ROTARY`)는 펌웨어 `switches[]`의 `pins[]` 순서대로 위치별 명령을 지정합니다.
DCS의 누름 키는 `JOY_BTN<n>`, 해제 키는 `JOY_BTN<n>_OFF`입니다.
EPU 중립처럼 여러 DX의 해제가 같은 명령이면 하나의 명령 항목으로 합칩니다.

### 축 설정

두 생성기는 기존 설정 파일을 읽거나 병합하지 않습니다.
축 할당과 반전·데드존·포화 값은 `sim_axes.py`의 `BMS_AXES`, `DCS_AXES`에서 가져옵니다.
축을 바꾸려면 이 값을 수정한 뒤 다시 생성하십시오.

DCS의 `removed` 항목은 패널 축에 자동 할당된 Pitch·Roll·Thrust 등을 해제합니다.
이 항목이 빠지면 노브가 비행 조종축으로 동작할 수 있습니다.

펌웨어의 `slider(1)`인 ILS 노브는 BMS의 `<AxAssgn>` 슬롯 7(0부터 계산), DCS의 `JOY_SLIDER2`에 대응합니다.

## 5. 미매핑 항목과 버전 변경

### BMS

생성할 때 설치된 `User\Config\BMS - Full.key`에서 콜백 존재 여부와 사운드 ID를 읽습니다.
매핑 표에 지정한 콜백이 없으면 생성을 중단합니다. `TODO`는 빈칸으로 생성하고 해당 DX를 로그에 표시합니다.

현재 비워 둔 항목은 다음과 같습니다.

| 보드 | 컨트롤 | 구분 |
|---|---|---|
| CONSOLE | UHF TEST, STATUS, T-TONE, SQUELCH, FUNCTION의 ADF | 대응 기능 미확인 |
| CONSOLE | AB RESET, ENG DATA, MAX POWER | 대응 기능 미확인 |
| CONSOLE | ECM RESET, ECM 버튼 6·FRM·SPL | 대응 기능 미확인 |
| CONSOLE | COMM1·COMM2 MODE의 OFF, HOT MIC/CIPHER | 대응 기능 미확인 |
| CONSOLE | ENG CONT·EPU OFF·EPU ON 커버 | 현재 매핑 대상에서 제외 |
| AUX | ALT REL, TWA ACT/PWR | 대응 기능 미확인 |
| AUX | CMDS PRGM의 BIT·5·6 | 대응 기능 미확인 |
| AUX | CMDS MODE의 7번째 위치 | 실기에 없는 여분 위치 |

`UNMODELED(...)`의 문자열은 기능을 조사할 때 사용한 검색어입니다.
**생성기는 새로 지원된 기능을 자동 탐지하지 않습니다.** BMS를 업데이트한 뒤에는 다음 순서로 확인하십시오.

1. 릴리스 노트와 `BMS - Full.key`에서 해당 기능의 추가 여부를 확인합니다.
2. 콜백의 동작과 스위치 위치를 확인해 `bms_callbacks.py`를 수정합니다.
3. 키맵을 다시 생성하고 게임에서 확인합니다.

### DCS

명령 카탈로그는 사용자의 기존 `.diff.lua` 두 개에서 추출했습니다.
모듈의 전체 입력 목록은 아니며, 명령 ID와 표시 이름을 제공합니다.

| 미확정 항목 | 상태 |
|---|---|
| UHF T-TONE | 기존 프로파일에 명령 없음 |
| AVTR의 양 끝 위치 | 기존 프로파일에 명령 없음 |
| EPU OFF·ON 커버 | 별도 커버 명령 지원 여부 확인 필요 |

위 5개 DX는 `TODO`이며 생성할 때 보고됩니다.
기능이 지원되지 않는 것인지, 기존 프로파일에만 없는 것인지는 추가 확인이 필요합니다.

DCS에서 해당 기능을 바인딩해 저장한 `.diff.lua` 또는 모듈의
`Input/F-16C_50/joystick/default.lua`를 확인해 카탈로그와 `dcs_commands.py`를 보완하십시오.
DCS 명령 ID에는 명령 번호·콕핏 장치 번호·누름/해제 값이 포함되므로, 표시 이름만 보고 ID를 추측하지 않습니다.

## 6. 문제 확인

| 증상 | 확인할 내용 |
|---|---|
| 보드를 찾지 못함 | USB 연결, `pyserial` 설치, `--port` 지정 |
| DX 응답 검증 실패 | 헤더·항목 수·버튼 범위 및 펌웨어 버전 확인 후 다시 생성 |
| `?DX` 응답 없음 | 브리지 종료 후 6초 대기, 질의 기능이 포함된 펌웨어인지 확인 |
| BMS 대상 XML이 없음 | CONTROLLERS에서 해당 장치 설정 저장 |
| BMS 매핑이 표시되지 않음 | 수정된 생성기로 재생성, 실제 장치의 XML에 적용했는지 및 F-16 프로파일 계층 확인 |
| DCS 매핑이 적용되지 않음 | F-16C의 해당 장치 열에서 Load Profile 실행 |
| 컨트롤 일부가 빈칸 | 생성 로그의 미매핑/TODO 및 위 미매핑 목록 확인 |
| DX 번호가 맞지 않음 | 변경한 펌웨어 업로드 후 키맵 재생성 |

## 7. 관련 문서

- [콘솔 DX 맵](REF_LEFT_CONSOLE_WIRING.md#dx-버튼-맵-64--128)
- [AUX DX 맵](REF_LEFT_AUX_WIRING.md#dx-버튼-맵-51--128)
- [장치 개요](REF_DEVICES.md)
- [BIOS 프로토콜·LED 주소](REF_PROTOCOL.md)
