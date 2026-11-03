# 키맵 자동 생성

시뮬레이터 바인딩 파일을 **손으로 쓰지 않고 생성**합니다. DX 번호는 보드에 물어보고,
컨트롤 이름은 콜백/명령 이름에 표로 대응시킵니다.

왜 생성해야 하느냐 — `dxOrder[]` 에서 줄 하나만 옮기면 그 뒤 DX 가 전부 밀립니다
([REF_LEFT_CONSOLE_WIRING.md](REF_LEFT_CONSOLE_WIRING.md#dx-버튼-맵-64--128) 참조).
손으로 유지하는 바인딩 파일은 그 순간 조용히 틀어집니다. 생성기를 다시 돌리면 그만입니다.

| 시뮬 | 상태 | 생성기 | 출력 |
|---|---|---|---|
| **Falcon BMS** | 동작함 (바인딩 128줄) | `tools/gen_bms_keyfile.py` | `.key` 조각 **1개** |
| **DCS World** | **미착수** — 아래 「DCS 계획」 | — | `.diff.lua` **장치당 1개** |

## 장치를 구분하는 방식이 두 시뮬에서 다릅니다

보드가 둘이라 먼저 짚고 갑니다. **BMS 는 파일 하나, DCS 는 장치마다 하나**입니다.

| | BMS | DCS |
|---|---|---|
| 파일 수 | **1개** — 게임 전체가 키 파일 하나 | **장치당 1개** |
| 파일 안에 장치 구분이 | **없습니다** | 파일명에 장치명 + GUID |
| 그럼 어떻게 구분하나 | **DX 번호 대역으로.** N번째 장치는 `(N-1) × g_nButtonsPerDevice` 부터 | 파일이 나뉘어 있으니 구분 불필요 |
| 버튼 번호 | 대역이 더해진 **전역 번호** | 그 장치 안에서 **1부터** — 오프셋 없음 |

그래서 BMS 쪽 생성기는 두 보드를 **한 파일에** 쓰고, 각 보드 앞에 어느 대역인지
주석을 답니다:

```
# ---- CONSOLE : 장치 2, BMS DX 128~191 (Windows DX 1~64) ----
# ---- AUX : 장치 3, BMS DX 256~306 (Windows DX 1~51) ----
```

`--device-index` 와 `DeviceSorting.txt` 가 필요한 이유가 이것뿐입니다 — 대역 시작점을
알아야 하니까요. **DCS 에는 이 개념이 없습니다.** 장치마다 파일이 따로라
`JOY_BTN1` 이 그 장치의 1번 버튼이고, 오프셋을 더하면 오히려 틀립니다.

---

## 1. 쓰는 법 (BMS)

브리지를 **끄고** 실행하십시오. Windows 는 COM 포트를 한 프로세스만 열 수 있고,
펌웨어도 프로토콜 미검출 상태에서만 요청에 응답합니다.

```
python tools/gen_bms_keyfile.py --comments -o redkite.key
```

보드를 VID/PID 로 찾아 각각에 물어보고, 응답의 `device=` 로 어느 매핑 표를 쓸지
스스로 정합니다. **소스나 개발환경이 필요 없습니다** — `tools/` 폴더와 pyserial,
BMS 설치본이면 됩니다. 심 PC 에 그대로 들고 가도 동작합니다.

| 옵션 | |
|---|---|
| (없음) | 보드에 질의 — 기본 |
| `--from-source` | 보드 대신 스케치의 `dxOrder[]` 를 읽음 (오프라인용) |
| `--verify` | 보드와 소스를 모두 읽어 **대조만** 함. 업로드를 깜빡했는지 잡힙니다 |
| `--port COMx` | 자동 탐지 대신 포트 지정 |
| `--device-index CONSOLE 2` | `DeviceSorting.txt` 기준 장치 순번 (1-base) |
| `--comments` | 줄마다 `# DX 28  ENG CONT` 주석 — 현장 확인용 |
| `--update-catalog` | BMS 콜백 기준선 갱신 (아래 4절) |
| `--bms-root` | BMS 설치 경로 (기본 `C:\Falcon BMS 4.38`) |

> ⚠ **`--comments` 로 만든 파일을 BMS 설정 UI 에서 저장하면 주석이 사라집니다.**
> 키 파일 맨 위의 경고와 같은 이유입니다. 확인용으로만 쓰고 배포본은 주석 없이 뽑으십시오.

### 장치 순번

BMS 는 장치마다 `g_nButtonsPerDevice` 만큼의 블록을 줍니다 — N번째 장치는
`(N-1) × 128` 부터 시작합니다. 순서는 `User\Config\DeviceSorting.txt` 가 정합니다.
그 파일이 채워져 있으면 생성기가 읽고, 비어 있으면 `--device-index` 로 직접 줘야 합니다.

심 PC 의 `User\Config\Falcon BMS User.cfg` 에 다음이 필요합니다:

```
set g_nButtonsPerDevice 128
set g_nHotasPinkyShiftMagnitude 0
```

---

## 2. 보드가 DX 맵을 알려주는 방법

펌웨어가 `?DX` 한 줄에 응답합니다. **업로드된 펌웨어가 BMS 가 실제로 보는 장치**이므로,
소스가 아니라 보드가 기준입니다.

```
#DX BEGIN device=CONSOLE pid=0x048E entries=34 total=64
#DX 1 1 MPO
#DX 2 2 UHF PRESET
#DX 4 1 UHF TEST
...
#DX END
```

`#DX <첫 DX 번호> <차지하는 개수> <컨트롤 이름>`.

- **`PROTO_UNKNOWN` 에서만 응답합니다.** BIOS 프레임이 흐르는 중에 ASCII 가 섞이면
  프레임 해석이 깨집니다. 그 상태에서 ASCII 바이트는 원래 동기 카운터만 리셋하고
  버려지던 자리라, 훅을 걸어도 프로토콜 검출에 영향이 없습니다.
- **기동 시가 아니라 요청 시에** 찍습니다. Teensy USB CDC 는 읽는 호스트가 없으면
  출력을 버려서, 부팅 배너는 대개 아무도 못 받습니다.

기동 시리얼 요약도 같은 정보를 같은 순서로 찍으므로, 눈으로 대조할 때 쓸 수 있습니다.

---

## 3. 이름 → 콜백 표

`tools/bms_callbacks.py`. **DX 번호가 아니라 컨트롤 이름이 키**입니다. 그래서
`dxOrder[]` 를 재배열해도 이 표는 그대로고, 하드웨어를 추가할 때만 늘어납니다.

컨트롤이 차지하는 DX 하나당 한 항목:

| 값 | 뜻 | 생성되는 줄 |
|---|---|---|
| `'SimFoo'` | 모멘터리 | 1줄, 3번째 필드 `-1` |
| `('SimOn', 'SimOff')` | 유지형 | 2줄 — 누를 때 `0`, 뗄 때 `0x42` |
| `('SimOn', None)` | 유지형, 되돌릴 콜백 없음 | 1줄 |
| `UNMODELED('검색어', …)` | BMS 가 **아직** 모델링 안 함 | 없음 — 4절 참조 |
| `None` | **영구적으로** 대상 없음 | 없음 |

3단 토글은 DX 2개로 들어오고 중립이 '뗀 상태'이므로, 각 DX 를 `(해당 위치, 중립)` 으로
두면 세 위치가 모두 표현됩니다:

```python
'JFS': [('SimJfsStartUp',   'SimJfsStartMid'),
        ('SimJfsStartDown', 'SimJfsStartMid')],
```

로터리(`SW_ROTARY`)는 위치 순서대로 나열하며, `switches[]` 의 `pins[]` 와 같은 순서입니다.

> **모든 콜백은 생성 시점에 `BMS - Full.key` 에 실재하는지 검증합니다.**
> 없는 이름은 죽은 바인딩을 뱉는 대신 에러로 중단합니다. 사운드 ID 도 같은 파일에서
> 읽어 오므로 하드코딩이 없습니다.

### BMS DX 바인딩 줄 형식

```
<Callback> <BMS DX#> <-1|-2> -2 <0|0x42> 0x0 <soundID|-1>
```

| 필드 | |
|---|---|
| 2 | BMS DX 번호. **0-base** — Windows 의 DX1 이 BMS 의 0 |
| 3 | `-1` 모멘터리, `-2` 유지형(누름/뗌 2줄 한 쌍) |
| 4 | 항상 `-2` — 키보드가 아니라 DX 바인딩이라는 표시 |
| 5 | `0` 누를 때, `0x42` 뗄 때 |
| 7 | 사운드 ID. 같은 콜백의 키보드 줄에서 가져옴 |

스톡 파일(`Hotas\Archive\BMS - BasicDX *.key`)의 실제 예:

```
SimCATI   56 -2 -2 0    0x0 115
SimCATIII 56 -2 -2 0x42 0x0 115
```

2단 스위치가 **같은 DX 두 줄**인 것이 핵심입니다 — COMM 전원을 펄스가 아니라
유지형 DX 로 만든 근거입니다.

`-1` 모멘터리는 BMS 가 누름·뗌 양쪽 엣지를 받으므로 "- Hold" 계열 콜백이 쥐고 있는
동안 유효합니다 (`SimTriggerFirstDetent`, `SimHotasPinkyShift` 가 같은 모양).

---

## 4. BMS 버전업 추적

25개 DX 가 비어 있습니다. 그중 **21개는 BMS 가 아직 모델링하지 않아서**고, 4개만
영구적으로 대상이 없습니다. 나중에 BMS 가 지원을 추가해도 아무도 안 알려주면
영영 모르게 되므로, 두 겹으로 자동 확인합니다.

### 비워 둔 자리가 스스로 다시 확인

`UNMODELED` 항목은 **그때 찾아본 검색어**를 들고 있습니다. 생성기가 돌 때마다 현재
콜백 목록에 다시 걸어 봅니다.

```python
'UHF SQUELCH': [UNMODELED('SQUELCH')],
```

걸리면 이렇게 나옵니다:

```
*** BMS 에 콜백이 새로 생겼습니다 (1) ***
  CONSOLE  DX 24  UHF SQUELCH
      SimBupUhfSquelch       UHF: SQUELCH Switch - Toggle
```

**BMS 를 올린 뒤 키 파일을 다시 뽑는 것, 그게 절차 전부입니다.**

### 콜백 목록 전체 기준선

위 방식은 우리가 검색해 본 것만 잡습니다. `tools/bms_catalog.txt` 가 콜백 1207개
전부를 커밋된 기준선으로 들고 있고, 차이가 생기면 보고합니다. 정렬된 상태로 git 에
있으므로 **`git diff` 자체가 "이번 BMS 가 뭘 바꿨나" 목록**이 됩니다.
확인 후 `--update-catalog` 로 갱신하십시오.

### 현재 비어 있는 자리

| 보드 | 컨트롤 | 분류 |
|---|---|---|
| CONSOLE | UHF TEST, UHF STATUS, UHF T-TONE, UHF SQUELCH | 미모델링 |
| CONSOLE | UHF FUNCTION 의 ADF 위치 | 미모델링 |
| CONSOLE | AB RESET, ENG DATA, MAX POWER | 미모델링 |
| CONSOLE | ECM RESET, ECM 버튼 6 · FRM · SPL | 미모델링 |
| CONSOLE | COMM1 · COMM2 MODE 의 OFF 위치 | 미모델링 |
| CONSOLE | HOT MIC, CIPHER | 미모델링 |
| CONSOLE | ENG CONT · EPU OFF · EPU ON 커버 | **영구** — 커버는 DCS 개념 |
| AUX | ALT REL | 미모델링 |
| AUX | TWA ACT/PWR | 미모델링 |
| AUX | CMDS PRGM 의 BIT · 5 · 6 | 미모델링 |
| AUX | CMDS MODE 7번째 자리 | **영구** — 7단 로터리인데 실기는 6위치 |

---

## 5. 현장에서 확인할 것

소스로는 알 수 없어 추정으로 둔 것들입니다. `joy.cpl` 에 DX 번호가 그대로 보입니다.

| 확인 | 방법 | 틀렸을 때 |
|---|---|---|
| UHF FUNCTION / MODE 핀 방향 | 노브를 OFF 에 두고 켜지는 DX — 16 이면 정상, 19 면 역매핑 | `switches[]` 의 `uhfFuncPins[]` 를 뒤집기 |
| CMDS MODE 노브 방향 | 래더는 DX 44~50. 반시계 끝(OFF)에서 **DX 44** 면 정상 | `'CMDS MODE'` 6줄 뒤집고 `None` 을 앞으로 |
| TWA ACT/PWR vs SYS PWR | 어느 버튼이 계통을 켜는지 | 두 항목 맞바꾸기 |
| 3단 토글 13개의 접점 방향 | 위로 올렸을 때 나가는 DX 가 `--comments` 의 위치와 맞는지 | 튜플 순서 뒤집기 |

전부 `bms_callbacks.py` 또는 `switches[]` 의 **한 줄 수정**으로 끝나고, DX 번호는
움직이지 않으므로 키 파일을 다시 뽑을 필요도 없습니다 (핀 순서 변경의 경우).

---

## 6. DCS 계획

**미착수.** 구조는 BMS 와 같게 가되, 데이터 두 가지가 DCS 설치본에만 있습니다.

### 대응 관계

| | BMS (완료) | DCS (예정) |
|---|---|---|
| 카탈로그 원천 | `User\Config\BMS - Full.key` | 모듈의 `Input\F-16C_50\joystick\default.lua` |
| 커밋된 기준선 | `tools/bms_catalog.txt` | `tools/dcs_catalog.txt` |
| 이름→명령 표 | `tools/bms_callbacks.py` | `tools/dcs_commands.py` |
| 출력 | `.key` 조각 1개 | `.diff.lua` **장치당 1개** |
| 출력 위치 | BMS 키 파일에 병합 | `Saved Games\DCS\Config\Input\F-16C_50\joystick\<장치명> {GUID}.diff.lua` |
| 버튼 번호 | 장치 대역이 더해진 전역 번호 | **그 장치 안에서 1부터** |

DX 맵을 보드에서 읽는 부분(`?DX`, 포트 탐지, 파서)은 **그대로 재사용**합니다. 보드가
`device=CONSOLE` 을 알려주므로 어느 파일에 쓸지도 자동으로 갈립니다.

**BMS 쪽 코드를 그대로 가져오면 안 되는 지점이 둘 있습니다.**

1. **장치 대역 오프셋을 적용하면 안 됩니다.** `(N-1) × 128` 은 BMS 가 파일 하나에
   모든 장치를 담기 때문에 필요한 것이고, DCS 는 파일이 나뉘어 있어 그 장치의
   1번 버튼이 그냥 `JOY_BTN1` 입니다. `--device-index` 와 `DeviceSorting.txt` 도
   DCS 에서는 쓰지 않습니다.
2. **출력이 조각이 아니라 완결된 파일입니다.** BMS 는 기존 키 파일에 붙이는
   텍스트 조각이지만, `.diff.lua` 는 `local diff = { ... } return diff` 로 닫히는
   온전한 Lua 파일이고 장치마다 하나씩 덮어씁니다.

### 막히는 지점

**`.diff.lua` 의 명령 ID 형식이 확인되지 않았습니다.** `d3001pnt3` 같은 문자열이
`cockpit_device_id` 와 `device_commands.Button_N` 에서 어떤 순서로 조합되는지 —
추측으로 쓰면 **파일은 정상 로드되는데 버튼이 안 먹는** 식으로 조용히 실패합니다.

파일명의 GUID 도 Windows 가 장치마다 정하는 값이라 만들어낼 수 없습니다.

### 가져와야 할 파일

DCS 설치 폴더(보통 `C:\Program Files\Eagle Dynamics\DCS World`)에서:

```
Mods\aircraft\F-16C\Input\F-16C_50\joystick\default.lua
Mods\aircraft\F-16C\Cockpit\Scripts\devices.lua
Mods\aircraft\F-16C\Cockpit\Scripts\command_defs.lua
```

| 파일 | 왜 |
|---|---|
| `default.lua` | 바인딩 가능한 전체 명령 목록 (이름·카테고리 포함) |
| `devices.lua` | `devices.ELEC_INTERFACE` 같은 심볼을 숫자로 |
| `command_defs.lua` | `device_commands.Button_1` 을 숫자로 |

`default.lua` 는 명령을 심볼 이름으로만 적어 놓아서, 뒤의 둘이 없으면 숫자 ID 를
만들 수 없습니다.

그리고 **DCS 에서 직접 만든 샘플** — 입력 설정에서 아무 컨트롤 2~3개를 Teensy 버튼에
바인딩하고 저장하면 생기는 파일을, **양쪽 보드 모두**:

```
%USERPROFILE%\Saved Games\DCS\Config\Input\F-16C_50\joystick\
    F16 LEFT CONSOLE {GUID}.diff.lua
    F16 LEFT AUX MISC {GUID}.diff.lua
```

바인딩 종류를 섞으면(모멘터리 버튼 · 2단 스위치 · 3단 스위치의 한 위치) ID 형식과
파일명 규칙, GUID, 그리고 2단/3단을 어떻게 표현하는지를 한 번에 확인할 수 있습니다.

> `Saved Games\DCS` 가 `DCS.openbeta` 일 수 있습니다. 있는 쪽으로.

### 예상되는 차이

- **커버 DX 3개가 DCS 에서는 살아납니다.** BMS 에선 비웠지만 DCS 는 커버를 따로
  여닫습니다 — 애초에 이 DX 를 만든 이유가 DCS 쪽입니다.
- **BMS 가 안 모델링한 것 상당수가 DCS 엔 있을 것**입니다 — HOT MIC, CIPHER,
  UHF SQUELCH · T-TONE, ADF 위치 등. DCS 가 더 세밀한 편입니다.
- **축 10개**는 버튼이 아니라 `.diff.lua` 의 `axisDiffs` 쪽이라 형식이 다릅니다.
  필요하면 같이 생성합니다.

---

## 7. 관련 문서

| | |
|---|---|
| DX 맵 (콘솔) | [REF_LEFT_CONSOLE_WIRING.md](REF_LEFT_CONSOLE_WIRING.md#dx-버튼-맵-64--128) |
| DX 맵 (AUX) | [REF_LEFT_AUX_WIRING.md](REF_LEFT_AUX_WIRING.md#dx-버튼-맵-51--128) |
| 장치 개요 | [REF_DEVICES.md](REF_DEVICES.md) |
| BIOS 프로토콜 · LED 주소 | [REF_PROTOCOL.md](REF_PROTOCOL.md) |
