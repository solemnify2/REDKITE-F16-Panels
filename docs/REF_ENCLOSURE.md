# 3D 프린트 구조물

`3d stl/` 폴더에 STL 파일이 쓰임새별로 나뉘어 있습니다 — `LeftAuxMiscCenter/` ·
`LeftConsole/` · `ToggleCover/`. STL 링크가 있는 썸네일을 클릭하면 파일을 내려받을 수
있습니다. 치수는 바운딩 박스 기준입니다.

## 출력 재료

| 대상 | 재료 |
|------|------|
| 인클로저 · 스탠드 · 콘솔 · MFD 홀더 | **PLA** 또는 **PETG** |
| 패널 `LED layer` (스위치 체결층) | **투명 PLA** |
| 백라이트 플레이트 | **PLA** 또는 **레진(SLA)** |

출력 업체의 지원 재료와 견적은 발주할 때 확인하십시오.

## 출력 수량

패널 `LED layer` 까지 포함한, 이 프로젝트를 한 벌 만드는 데 필요한 출력물 전체입니다.

| 구분 | 수량 | 재료 | STL 위치 |
|------|----:|------|----------|
| 패널 `LED layer` | 11 | 투명 PLA | Greenisland 모델 동봉 |
| 백라이트 플레이트 | 8 | PLA · 레진 | `LeftAuxMiscCenter/` · `LeftConsole/` |
| Left Aux 인클로저 | 3 | PLA · PETG | `LeftAuxMiscCenter/` |
| Left Console | 4 | PLA · PETG | `LeftConsole/` |
| MFD 홀더 | 4 | PLA · PETG | `LeftAuxMiscCenter/` |
| 스탠드 | 2 | PLA · PETG | `LeftAuxMiscCenter/` |
| 토글 스위치 커버 | 7 | PLA · 판금 | `ToggleCover/` |
| 인클로저 | 2 | PLA · PETG | Cults3D 구매 모델 |
| **합계** | **41** | | |

스위치 캡 · 노브는 별도이며, 수량은 스위치 구성에 따라 달라집니다 (본 프로젝트 기준 64개).

## 인클로저 & 스탠드

Stand 는 Center 인클로저 뒷면에 에폭시로 부착합니다 (조립은 [README 2-1](../README.md#2-1-조립-순서)).

| Center Left Enclosure | Center Right Enclosure (new) | Left Stand (new) | Right Stand (new) |
|:----:|:----:|:----:|:----:|
| <img src="../3d%20stl/LeftAuxMiscCenter/Center%20Left%20Enclosure.png" width="160"><br>278.4 × 142.8 × 193.5 mm | <img src="../3d%20stl/LeftAuxMiscCenter/Center%20Right%20Enclosure%20-%20new.png" width="160"><br>278.4 × 144.0 × 179.9 mm | <a href="../3d%20stl/LeftAuxMiscCenter/Left%20Stand%20-%20new.stl"><img src="../3d%20stl/LeftAuxMiscCenter/Left%20Stand%20-%20new.png" width="160"></a><br>137.1 × 132.3 × 161.2 mm | <a href="../3d%20stl/LeftAuxMiscCenter/Right%20Stand-%20new.stl"><img src="../3d%20stl/LeftAuxMiscCenter/Right%20Stand-%20new.png" width="160"></a><br>137.1 × 129.2 × 162.0 mm |

> Center Left/Right Enclosure 는 **Greenisland 와 Legarsdusofa 의 Cults3D 구매 모델에서
> 각각 쓸 만한 부분을 잘라 합친 것**입니다. 두 원본 모두 구매품이라 재배포하지 않고,
> 형상 참고용 이미지만 싣습니다.

## Left Aux 인클로저

| LeftAuxEnclosure | LeftAuxFrontPanel | LeftAuxBackPanel |
|:----:|:----:|:----:|
| <a href="../3d%20stl/LeftAuxMiscCenter/LeftAuxEnclosure.stl"><img src="../3d%20stl/LeftAuxMiscCenter/LeftAuxEnclosure.png" width="160"></a><br>265.8 × 245.0 × 242.0 mm | <a href="../3d%20stl/LeftAuxMiscCenter/LeftAuxFrontPanel.stl"><img src="../3d%20stl/LeftAuxMiscCenter/LeftAuxFrontPanel.png" width="160"></a><br>266.2 × 244.8 × 242.0 mm | <a href="../3d%20stl/LeftAuxMiscCenter/LeftAuxBackPanel.stl"><img src="../3d%20stl/LeftAuxMiscCenter/LeftAuxBackPanel.png" width="160"></a><br>265.8 × 12.0 × 242.0 mm |

## Left Console

Upper와 Lower를 결합한 뒤, Bottom 2종을 바닥판으로 장착합니다.

이 인클로저는 **Thrustmaster Viper TQS** 와 맞물리도록 설계되어 있습니다.
결합 전에 TQS의 **Mission Pack 또는 더미 덮개를 분리**합니다.

| LeftConsoleUpper | LeftConsoleLower | LeftConsoleBottomUpper | LeftConsoleBottomLower |
|:----:|:----:|:----:|:----:|
| <a href="../3d%20stl/LeftConsole/LeftConsoleUpper.stl"><img src="../3d%20stl/LeftConsole/LeftConsoleUpper.png" width="160"></a><br>220.2 × 270.5 × 51.4 mm | <a href="../3d%20stl/LeftConsole/LeftConsoleLower.stl"><img src="../3d%20stl/LeftConsole/LeftConsoleLower.png" width="160"></a><br>273.6 × 125.2 × 56.1 mm | <a href="../3d%20stl/LeftConsole/LeftConsoleBottomUpper.stl"><img src="../3d%20stl/LeftConsole/LeftConsoleBottomUpper.png" width="160"></a><br>124.2 × 239.0 × 19.0 mm | <a href="../3d%20stl/LeftConsole/LeftConsoleBottomLower.stl"><img src="../3d%20stl/LeftConsole/LeftConsoleBottomLower.png" width="160"></a><br>273.6 × 125.2 × 13.0 mm |

## MFD 홀더

**Thrustmaster(TM) MFD** 를 Center 인클로저에 고정하는 브래킷입니다.
MFD 와 **Alibaba 에서 구한 7.6인치 정사각 LCD** 를 겹쳐 놓고 홀더가 둘을 함께 잡습니다.
접착하지 않아 수리 시 분리가 쉽습니다. 조립은 [README 2-1](../README.md#2-1-조립-순서) 참조.

| LeftMFDHolder | LeftMFDHolderUpper | RightMFDHolder | RightMFDHolderUpper |
|:----:|:----:|:----:|:----:|
| <a href="../3d%20stl/LeftAuxMiscCenter/LeftMFDHolder.stl"><img src="../3d%20stl/LeftAuxMiscCenter/LeftMFDHolder.png" width="160"></a><br>146.1 × 10.6 × 35.2 mm | <a href="../3d%20stl/LeftAuxMiscCenter/LeftMFDHolderUpper.stl"><img src="../3d%20stl/LeftAuxMiscCenter/LeftMFDHolderUpper.png" width="160"></a><br>145.6 × 7.2 × 5.0 mm | <a href="../3d%20stl/LeftAuxMiscCenter/RightMFDHolder.stl"><img src="../3d%20stl/LeftAuxMiscCenter/RightMFDHolder.png" width="160"></a><br>146.1 × 11.0 × 35.2 mm | <a href="../3d%20stl/LeftAuxMiscCenter/RightMFDHolderUpper.stl"><img src="../3d%20stl/LeftAuxMiscCenter/RightMFDHolderUpper.png" width="160"></a><br>145.6 × 7.2 × 5.0 mm |

## 백라이트 플레이트

패널 뒤에 간격을 두고 설치하는 LED 거치판입니다. 스위치를 체결하는 `LED layer`와 구분하십시오.
빛이 퍼질 거리를 확보해 LED 수를 줄이도록 추가했습니다. 설치 원리는 [REF_BACKLIGHT.md](REF_BACKLIGHT.md)를 참고하십시오.

이 프로젝트에서는 PLA 또는 레진 출력을 사용합니다.

> 파일명이 `LED Plate …` 이지만 `LED layer` 가 아니라 **백라이트 플레이트**입니다. 자작 모델입니다.

**Left Aux** — 패널별로 한 장씩

| LED Plate - Gear | LED Plate - CMDS | LED Plate - TWA | LED Plate - HMCS |
|:----:|:----:|:----:|:----:|
| <a href="../3d%20stl/LeftAuxMiscCenter/LED%20Plate%20-%20Gear.stl"><img src="../3d%20stl/LeftAuxMiscCenter/LED%20Plate%20-%20Gear.png" width="160"></a><br>190.1 × 140.4 × 112.1 mm | <a href="../3d%20stl/LeftAuxMiscCenter/LED%20Plate%20-%20CMDS.stl"><img src="../3d%20stl/LeftAuxMiscCenter/LED%20Plate%20-%20CMDS.png" width="160"></a><br>144.2 × 81.8 × 81.8 mm | <a href="../3d%20stl/LeftAuxMiscCenter/LED%20Plate%20-%20TWA.stl"><img src="../3d%20stl/LeftAuxMiscCenter/LED%20Plate%20-%20TWA.png" width="160"></a><br>47.9 × 68.5 × 68.5 mm | <a href="../3d%20stl/LeftAuxMiscCenter/LED%20Plate%20-%20HMCS.stl"><img src="../3d%20stl/LeftAuxMiscCenter/LED%20Plate%20-%20HMCS.png" width="160"></a><br>144.2 × 40.8 × 40.8 mm |

**Left Console** — `LED Plate1` ~ `4`

| LED Plate1 | LED Plate2 | LED Plate3 | LED Plate4 |
|:----:|:----:|:----:|:----:|
| <a href="../3d%20stl/LeftConsole/LED%20Plate1.stl"><img src="../3d%20stl/LeftConsole/LED%20Plate1.png" width="160"></a><br>92.8 × 265.2 × 10.7 mm | <a href="../3d%20stl/LeftConsole/LED%20Plate2.stl"><img src="../3d%20stl/LeftConsole/LED%20Plate2.png" width="160"></a><br>117.6 × 230.1 × 13.1 mm | <a href="../3d%20stl/LeftConsole/LED%20Plate3.stl"><img src="../3d%20stl/LeftConsole/LED%20Plate3.png" width="160"></a><br>124.0 × 86.5 × 13.8 mm | <a href="../3d%20stl/LeftConsole/LED%20Plate4.stl"><img src="../3d%20stl/LeftConsole/LED%20Plate4.png" width="160"></a><br>136.5 × 119.0 × 14.6 mm |

## 토글 스위치 커버

EPU · Engine Cont 처럼 실수로 건드리면 안 되는 토글에 씌우는 보호 커버입니다.
`3d stl/ToggleCover/` 에 있습니다. 썸네일이 없어 파일 이름을 바로 링크했습니다 —
이름을 누르면 STL, 오른쪽 칸을 누르면 STEP 을 내려받습니다.

파일 이름의 `(SM 1.0t)` 는 **1.0t 판금(sheet metal)** 기준으로 그린 모델이라는
뜻입니다. 일곱 개 모두 **STL 과 STEP 이 한 쌍**이라, 3D 출력도 판금 발주도
그대로 됩니다.

| 파일 | 크기 (mm) | 판금용 |
|------|----------:|:----:|
| [`EPU Switch Guard - Base (SM 1.0t)`](../3d%20stl/ToggleCover/EPU%20Switch%20Guard%20-%20Base%20%28SM%201.0t%29.stl) | 16.8 × 28.6 × 6.0 | [STEP](../3d%20stl/ToggleCover/EPU%20Switch%20Guard%20-%20Base%20%28SM%201.0t%29.step) |
| [`EPU Switch Guard - Top L (SM 1.0t)`](../3d%20stl/ToggleCover/EPU%20Switch%20Guard%20-%20Top%20L%20%28SM%201.0t%29.stl) | 8.3 × 24.0 × 12.3 | [STEP](../3d%20stl/ToggleCover/EPU%20Switch%20Guard%20-%20Top%20L%20%28SM%201.0t%29.step) |
| [`EPU Switch Guard - Top R (SM 1.0t)`](../3d%20stl/ToggleCover/EPU%20Switch%20Guard%20-%20Top%20R%20%28SM%201.0t%29.stl) | 8.4 × 24.0 × 12.3 | [STEP](../3d%20stl/ToggleCover/EPU%20Switch%20Guard%20-%20Top%20R%20%28SM%201.0t%29.step) |
| [`Trigger Guard - Base Body Long (SM 1.0t)`](../3d%20stl/ToggleCover/Trigger%20Guard%20-%20Base%20Body%20Long%20%28SM%201.0t%29.stl) | 16.8 × 34.7 × 6.0 | [STEP](../3d%20stl/ToggleCover/Trigger%20Guard%20-%20Base%20Body%20Long%20%28SM%201.0t%29.step) |
| [`Trigger Guard A - Top Body (SM 1.0t)`](../3d%20stl/ToggleCover/Trigger%20Guard%20A%20-%20Top%20Body%20%28SM%201.0t%29.stl) | 17.0 × 24.1 × 12.5 | [STEP](../3d%20stl/ToggleCover/Trigger%20Guard%20A%20-%20Top%20Body%20%28SM%201.0t%29.step) |
| [`Trigger Guard B - Top Body (SM 1.0t)`](../3d%20stl/ToggleCover/Trigger%20Guard%20B%20-%20Top%20Body%20%28SM%201.0t%29.stl) | 17.0 × 24.1 × 12.5 | [STEP](../3d%20stl/ToggleCover/Trigger%20Guard%20B%20-%20Top%20Body%20%28SM%201.0t%29.step) |
| [`Trigger Guard B - Top Body Long`](../3d%20stl/ToggleCover/Trigger%20Guard%20B%20-%20Top%20Body%20Long.stl) | 17.0 × 30.2 × 12.5 | [STEP](../3d%20stl/ToggleCover/Trigger%20Guard%20B%20-%20Top%20Body%20Long%20%28SM%201.0t%29.step) |

커버 하나는 **베이스 + 상부** 로 이루어집니다. EPU 는 상부가 좌우 한 쌍(`Top L` ·
`Top R`)이고, Trigger Guard 는 상부 A/B 와 길이 두 가지를 같은 베이스에 조합합니다.
