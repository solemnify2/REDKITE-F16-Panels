# 3D 프린트 구조물

`3d stl/` 폴더에 STL 파일이 있습니다. 썸네일을 클릭하면 STL 을 내려받습니다.
치수는 바운딩 박스 기준입니다.

## 출력 재료

| 대상 | 재료 |
|------|------|
| 인클로저 · 스탠드 · 콘솔 · MFD 홀더 | **PLA** 또는 **PETG** |
| 패널 `LED layer` (스위치 체결층) | **투명 PLA** |
| 백라이트 플레이트 | **PLA** 또는 **레진(SLA)** |

PETG 는 JLC3DP 에서 지원하지 않아 PCBWay 등에 별도 주문해야 합니다.

## 인클로저 & 스탠드

Stand 는 Center 인클로저 뒷면에 에폭시로 부착합니다 (조립은 [README 2-1](../README.md#2-1-조립-순서)).

| Center Left Enclosure | Center Right Enclosure (new) | Left Stand (new) | Right Stand (new) |
|:----:|:----:|:----:|:----:|
| <img src="../3d%20stl/Center%20Left%20Enclosure.png" width="160"><br>278.4 × 142.8 × 193.5 mm | <img src="../3d%20stl/Center%20Right%20Enclosure%20-%20new.png" width="160"><br>278.4 × 144.0 × 179.9 mm | <a href="../3d%20stl/Left%20Stand%20-%20new.stl"><img src="../3d%20stl/Left%20Stand%20-%20new.png" width="160"></a><br>137.1 × 132.3 × 161.2 mm | <a href="../3d%20stl/Right%20Stand-%20new.stl"><img src="../3d%20stl/Right%20Stand-%20new.png" width="160"></a><br>137.1 × 129.2 × 162.0 mm |

> Center Left/Right Enclosure 는 **Greenisland 와 Legarsdusofa 의 Cults3D 구매 모델에서
> 각각 쓸 만한 부분을 잘라 합친 것**입니다. 두 원본 모두 구매품이라 재배포하지 않고,
> 형상 참고용 이미지만 싣습니다.

## Left Aux 인클로저

| LeftAuxEnclosure | LeftAuxFrontPanel | LeftAuxBackPanel |
|:----:|:----:|:----:|
| <a href="../3d%20stl/LeftAuxEnclosure.stl"><img src="../3d%20stl/LeftAuxEnclosure.png" width="160"></a><br>265.8 × 245.0 × 242.0 mm | <a href="../3d%20stl/LeftAuxFrontPanel.stl"><img src="../3d%20stl/LeftAuxFrontPanel.png" width="160"></a><br>266.2 × 244.8 × 242.0 mm | <a href="../3d%20stl/LeftAuxBackPanel.stl"><img src="../3d%20stl/LeftAuxBackPanel.png" width="160"></a><br>265.8 × 12.0 × 242.0 mm |

## Left Console

Upper / Lower 를 맞물려 조립하고, Bottom 2 종이 바닥판입니다.

| LeftConsoleUpper | LeftConsoleLower | LeftConsoleBottomUpper | LeftConsoleBottomLower |
|:----:|:----:|:----:|:----:|
| <a href="../3d%20stl/LeftConsoleUpper.stl"><img src="../3d%20stl/LeftConsoleUpper.png" width="160"></a><br>220.2 × 270.5 × 51.4 mm | <a href="../3d%20stl/LeftConsoleLower.stl"><img src="../3d%20stl/LeftConsoleLower.png" width="160"></a><br>273.6 × 125.2 × 56.1 mm | <a href="../3d%20stl/LeftConsoleBottomUpper.stl"><img src="../3d%20stl/LeftConsoleBottomUpper.png" width="160"></a><br>124.2 × 239.0 × 19.0 mm | <a href="../3d%20stl/LeftConsoleBottomLower.stl"><img src="../3d%20stl/LeftConsoleBottomLower.png" width="160"></a><br>273.6 × 125.2 × 13.0 mm |

## MFD 홀더

**Thrustmaster(TM) MFD** 를 Center 인클로저에 고정하는 브래킷입니다.
MFD 와 **Alibaba 에서 구한 7.6인치 정사각 LCD** 를 겹쳐 놓고 홀더가 둘을 함께 잡습니다.
접착하지 않아 수리 시 분리가 쉽습니다. 조립은 [README 2-1](../README.md#2-1-조립-순서) 참조.

| LeftMFDHolder | LeftMFDHolderUpper | RightMFDHolder | RightMFDHolderUpper |
|:----:|:----:|:----:|:----:|
| <a href="../3d%20stl/LeftMFDHolder.stl"><img src="../3d%20stl/LeftMFDHolder.png" width="160"></a><br>146.1 × 10.6 × 35.2 mm | <a href="../3d%20stl/LeftMFDHolderUpper.stl"><img src="../3d%20stl/LeftMFDHolderUpper.png" width="160"></a><br>145.6 × 7.2 × 5.0 mm | <a href="../3d%20stl/RightMFDHolder.stl"><img src="../3d%20stl/RightMFDHolder.png" width="160"></a><br>146.1 × 11.0 × 35.2 mm | <a href="../3d%20stl/RightMFDHolderUpper.stl"><img src="../3d%20stl/RightMFDHolderUpper.png" width="160"></a><br>145.6 × 7.2 × 5.0 mm |

## 백라이트 플레이트

패널 **뒤쪽 몇 cm 뒤**에 띄워 배치하는 백라이트 LED 거치판입니다.
Greenisland 패널의 `LED layer`(스위치가 체결되는 층, [REF_PANEL.md](REF_PANEL.md) 참조)**와는 다른 부품**으로,
LED 수량을 줄이려고 본 프로젝트에서 추가한 것입니다. 거리를 띄운 만큼 빛이 퍼져 적은 LED 로도 고르게 밝습니다.

PLA 나 레진 출력으로 충분합니다 — MJF 등 고급 공정은 필요 없고 비용만 올라갑니다.

> 파일명이 `LED Plate …` 이지만 `LED layer` 가 아니라 **백라이트 플레이트**입니다. 자작 모델입니다.

**Left Aux** — 패널별로 한 장씩

| LED Plate - Gear | LED Plate - CMDS | LED Plate - TWA | LED Plate - HMCS |
|:----:|:----:|:----:|:----:|
| <a href="../3d%20stl/LED%20Plate%20-%20Gear.stl"><img src="../3d%20stl/LED%20Plate%20-%20Gear.png" width="160"></a><br>190.1 × 140.4 × 112.1 mm | <a href="../3d%20stl/LED%20Plate%20-%20CMDS.stl"><img src="../3d%20stl/LED%20Plate%20-%20CMDS.png" width="160"></a><br>144.2 × 81.8 × 81.8 mm | <a href="../3d%20stl/LED%20Plate%20-%20TWA.stl"><img src="../3d%20stl/LED%20Plate%20-%20TWA.png" width="160"></a><br>47.9 × 68.5 × 68.5 mm | <a href="../3d%20stl/LED%20Plate%20-%20HMCS.stl"><img src="../3d%20stl/LED%20Plate%20-%20HMCS.png" width="160"></a><br>144.2 × 40.8 × 40.8 mm |

**Left Console** — `LED Plate1` ~ `4`

| LED Plate1 | LED Plate2 | LED Plate3 | LED Plate4 |
|:----:|:----:|:----:|:----:|
| <a href="../3d%20stl/LED%20Plate1.stl"><img src="../3d%20stl/LED%20Plate1.png" width="160"></a><br>92.8 × 265.2 × 10.7 mm | <a href="../3d%20stl/LED%20Plate2.stl"><img src="../3d%20stl/LED%20Plate2.png" width="160"></a><br>117.6 × 230.1 × 13.1 mm | <a href="../3d%20stl/LED%20Plate3.stl"><img src="../3d%20stl/LED%20Plate3.png" width="160"></a><br>124.0 × 86.5 × 13.8 mm | <a href="../3d%20stl/LED%20Plate4.stl"><img src="../3d%20stl/LED%20Plate4.png" width="160"></a><br>136.5 × 119.0 × 14.6 mm |
