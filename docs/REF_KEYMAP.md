# 키맵 자동 생성

시뮬레이터 바인딩 파일을 **손으로 쓰지 않고 생성**합니다. DX 번호는 보드에 물어보고,
컨트롤 이름은 콜백/명령 이름에 표로 대응시킵니다.

왜 생성해야 하느냐 — `dxOrder[]` 에서 줄 하나만 옮기면 그 뒤 DX 가 전부 밀립니다
([REF_LEFT_CONSOLE_WIRING.md](REF_LEFT_CONSOLE_WIRING.md#dx-버튼-맵-64--128) 참조).
손으로 유지하는 바인딩 파일은 그 순간 조용히 틀어집니다. 생성기를 다시 돌리면 그만입니다.

| 시뮬 | 상태 | 생성기 | 출력 |
|---|---|---|---|
| **Falcon BMS** | 동작함 | `tools/gen_bms_setup_xml.py` | `Setup.v100.*.xml` **장치당 1개** |
| **DCS World** | 동작함 | `tools/gen_dcs_profile.py` | `.diff.lua` **장치당 1개** |

> **BMS 는 바인딩을 장치마다 하나씩인 `Setup.v100.<장치명> {GUID}.xml` 에 둡니다.**
> 게임 전체가 공유하는 `.key` 로도 DX 를 바인딩할 수는 있지만, 이 프로젝트는
> **`.key` 를 건드리지 않습니다** — 장치별 파일이면 오프셋도 `DeviceSorting.txt` 도
> 병합도 필요 없고, 장치 순서가 바뀌어도 파일명의 GUID 로 찾으므로 안 깨집니다.

## 장치 구분 — 두 시뮬 모두 장치별 파일입니다

보드가 둘이라 먼저 짚고 갑니다. **BMS 도 DCS 도 장치마다 파일이 따로** 있고,
버튼 번호에 오프셋이 없습니다 — `JOY_BTN1` / `DxAssgn[0]` 이 그 보드의 DX 1 입니다.

| | BMS 장치별 | DCS |
|---|---|---|
| 파일 | `Setup.v100.<장치명> {GUID}.xml` | `<프로파일명>.diff.lua` |
| 어디에 | `User\Config\` | `Saved Games\...\InputUserProfiles\` |
| 장치 식별 | 파일명의 **GUID** | 파일명 — **GUID 없음**, 이름으로 지정 |
| 버튼 번호 | `DxAssgn[i]` = DX **i+1** | `JOY_BTN<n>` = DX **n** |
| 오프셋 | **없음** | **없음** |

심 PC 의 실제 설정을 보면 BMS 바인딩은 **이 XML 쪽에** 들어 있습니다. 그래서
`gen_bms_setup_xml.py` 를 권합니다.

## 1. 쓰는 법

브리지를 **끄고** 실행하십시오. Windows 는 COM 포트를 한 프로세스만 열 수 있고,
펌웨어도 프로토콜 미검출 상태에서만 요청에 응답합니다.

두 생성기 모두 보드를 VID/PID 로 찾아 각각에 물어보고, 응답의 `device=` 로 어느
매핑 표를 쓸지 스스로 정합니다. **소스나 개발환경이 필요 없습니다** — `tools/` 폴더와
pyserial, 그리고 해당 심 설치본이면 됩니다. 심 PC 에 그대로 들고 가도 동작합니다.

공통 옵션:

| 옵션 | |
|---|---|
| (없음) | 보드에 질의 — 기본 |
| `--from-source` | 보드 대신 스케치의 `dxOrder[]` 를 읽음 (오프라인용) |
| `--port COMx` | 자동 탐지 대신 포트 지정 |
| `-o` | 출력 폴더. **원본을 덮어쓰지 않습니다** |

> 보드와 소스가 어긋나지 않았는지(업로드를 깜빡했는지) 보려면
> `python tools/gen_bms_keyfile.py --verify` 를 쓰십시오 — 아무 파일도 쓰지 않고
> 대조만 합니다. `gen_bms_keyfile.py` 는 보드 질의·DX 맵 파싱 코드를 담고 있어
> 다른 두 생성기가 이 파일을 import 합니다. 지우지 마십시오.

### 1-1. BMS — 장치별 Setup XML

```
python tools/gen_bms_setup_xml.py --config-dir "<BMS User\Config>" -o out
```

| 옵션 | |
|---|---|
| `--config-dir` | 기존 Setup XML 이 있는 폴더 (템플릿·GUID 출처) |
| `--bms-root` | BMS 설치 경로 (기본 `C:\Falcon BMS 4.38`) |

**기존 XML 을 템플릿으로 씁니다.** 축 보정(Invert/Saturation/Deadzone),
`<detentPosition>`, `<pov>` 는 바이트 단위로 그대로 두고 `<DxAssgn>` 만 갈아끼웁니다.
그래서 `--config-dir` 에 지금 쓰고 있는 XML 이 있어야 하고, GUID 도 거기서 가져옵니다.
`-o` 로 받아 확인한 뒤 `User\Config` 로 복사하십시오.

버튼 하나가 `<Assgn>` 4칸입니다:

| 슬롯 | `<Invoke>` | 뜻 |
|---|---|---|
| 0 | `Default` | 누를 때 |
| 1 | — | 미사용 (`SimDoNothing`) |
| 2 | `Down` | 뗄 때 |
| 3 | — | 미사용 |

`DxAssgn[i]` 가 그 장치의 **DX 버튼 i+1** 입니다 — 오프셋 없음. `<dx>` 섹션이 셋인데
앞 둘은 내용이 같고 셋째는 비어 있어, 관측된 그대로 재현합니다.

### 1-2. DCS — 입력 프로파일

```
python tools/gen_dcs_profile.py --profiles-dir "<InputUserProfiles>" -o out
```

| 옵션 | |
|---|---|
| `--profiles-dir` | 기존 `.diff.lua` 가 있는 폴더 (**축 블록 출처**) |
| `--name CONSOLE "이름"` | 파일명 지정 |

장치마다 `.diff.lua` 하나를 만들고, `Saved Games\DCS\Config\Input\...\InputUserProfiles\`
에 넣은 뒤 DCS 입력 설정에서 장치에 지정합니다. GUID 가 없어 파일명은 자유입니다.

#### 축은 다시 만들지 않고 베껴 옵니다

> ⚠ **`--profiles-dir` 없이 돌리지 마십시오.** 이 패널의 포트는 전부
> `invert = true` 이고 `curvature`·`filter` 도 붙어 있습니다. 생성기는 이걸 알 수
> 없으므로, 다시 만들면 **볼륨 노브 일곱 개와 HMCS 가 전부 반대로 돕니다.**

그래서 기존 프로파일의 `axisDiffs` 블록을 **원문 그대로** 복사합니다. 버튼 재배열은
축을 건드리지 않으므로 기존 블록이 그대로 유효합니다.

그 안에 **`removed` 항목**도 들어 있습니다 — DCS 가 새 조이스틱에 자동으로 거는
`Pitch←JOY_Y` · `Roll←JOY_X` · `Thrust←JOY_Z` (콘솔은 `Rudder←JOY_RZ` 까지) 를
떼어내는 줄입니다. 없으면 **HMCS 노브가 스로틀을 움직이고** 빈 축이 기수를 밉니다.

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

## 3. 이름 → 콜백 표 (BMS)

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

### 누름 / 뗌 쌍이라는 모양

2단 스위치를 **누를 때와 뗄 때 두 콜백**으로 표현하는 것이 BMS 의 기본 모양입니다.
Setup XML 에서는 한 버튼의 `<Assgn>` 슬롯 0(`Default`)과 2(`Down`) 가 그 둘이고,
BMS 가 배포하는 스톡 HOTAS 파일도 같은 쌍으로 적습니다:

```
SimCATI   56 -2 -2 0    0x0 115     <- 누를 때
SimCATIII 56 -2 -2 0x42 0x0 115     <- 뗄 때
```

COMM 전원을 모멘터리 펄스가 아니라 **유지형 DX** 로 만든 근거가 이것입니다 —
펄스는 전환 순간에만 나가서, 심을 나중에 띄우면 이미 올라가 있는 노브를 알 방법이
없습니다.

모멘터리 바인딩은 BMS 가 누름·뗌 양쪽 엣지를 받으므로 "- Hold" 계열 콜백이 쥐고
있는 동안 유효합니다 — MPO 를 `SimMPO` 하나로 거는 근거입니다.

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

**BMS 를 올린 뒤 생성기를 다시 돌리는 것, 그게 절차 전부입니다.**

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
움직이지 않으므로 바인딩 파일을 다시 뽑을 필요도 없습니다 (핀 순서 변경의 경우).

---

## 6. DCS 쪽 참고

| 파일 | 역할 |
|---|---|
| `tools/dcs_catalog.txt` | 명령 ID ↔ 이름. BMS 의 `bms_catalog.txt` 에 해당 |
| `tools/dcs_commands.py` | 컨트롤 이름 → 명령 ID |
| `tools/gen_dcs_profile.py` | 생성기 |

### 명령 ID 는 구조체입니다

```
d<down>p<pressed>u<up>cd<cockpit_device>vd<value_down>vp<value_pressed>vu<value_up>
```

`nil` 은 그 필드 없음. `d3001pnilunilcd32vd0vpnilvunil` = 명령 3001, 콕핏 장치 32,
value_down 0. 축은 `a<command>cd<device>` 입니다.

버튼은 `JOY_BTN<n>`, **뗄 때는 `JOY_BTN<n>_OFF`**. 3단 스위치의 가운데는 양쪽
릴리스를 한 항목에 묶습니다 — `bms_callbacks.py` 의 `(위치, 중립)` 모델 그대로라
표가 거의 그대로 옮겨갑니다:

```lua
["name"] = "EPU Switch - NORM",
  [1] = { ["key"] = "JOY_BTN58_OFF" },
  [2] = { ["key"] = "JOY_BTN59_OFF" },
```

모멘터리 버튼은 릴리스 키가 필요 없습니다 — 명령 자체가 `vd=1 vu=0` 을 품습니다.

### DCS 가 BMS 보다 많이 가진 것

BMS 에서 비워 둔 자리 상당수가 DCS 엔 있습니다 — UHF SQUELCH · TEST DISPLAY ·
STATUS, FUNCTION 의 ADF, MAX POWER, MPO, AB RESET 과 ENG DATA 각각,
HOT MIC/CIPHER 3단, ECM RESET, ECM 1~6 · FRM · SPL 전부, ALT REL, RWR ACT/PWR.

**`ENG CONT Switch Cover - OPEN / CLOSE`** 도 있습니다. 커버 DX 를 만든 이유가
원래 이쪽입니다.

### 남은 자리 5개

매번 실행할 때마다 보고됩니다.

| | |
|---|---|
| UHF T-TONE | 프로파일에 안 묶여 있음 |
| AVTR ×2 | 안 묶여 있음 |
| EPU 커버 ×2 | DCS 가 ENG CONT 에만 커버 명령을 주는 것으로 보임 |

앞의 셋은 DCS 에서 한 번 묶어 저장한 뒤 카탈로그를 다시 뽑으면 채워집니다.
EPU 커버는 모듈의 `Input/F-16C_50/joystick/default.lua` 를 봐야 확실합니다.

### 카탈로그를 다시 뽑으려면

`tools/dcs_catalog.txt` 는 사용자의 프로파일에서 추출한 것입니다. DCS 에서 새로
바인딩한 뒤 다시 뽑으면 그 명령이 카탈로그에 들어오고, `dcs_commands.py` 의
`TODO` 를 채울 수 있습니다.

---

---

## 7. 관련 문서

| | |
|---|---|
| DX 맵 (콘솔) | [REF_LEFT_CONSOLE_WIRING.md](REF_LEFT_CONSOLE_WIRING.md#dx-버튼-맵-64--128) |
| DX 맵 (AUX) | [REF_LEFT_AUX_WIRING.md](REF_LEFT_AUX_WIRING.md#dx-버튼-맵-51--128) |
| 장치 개요 | [REF_DEVICES.md](REF_DEVICES.md) |
| BIOS 프로토콜 · LED 주소 | [REF_PROTOCOL.md](REF_PROTOCOL.md) |
