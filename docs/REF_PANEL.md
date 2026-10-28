# 패널

콕핏 빌더 전문 업체에서 **구매**하거나, 3D 프린터와 아크릴 레이저 커팅으로 **직접 제작**할 수 있습니다.
본 프로젝트는 **MISC · Gear · CMDS 세 장만 구매품**이고, 나머지 패널은 전부 직접 만들었습니다.

---

## 1. 구매처

- [PC Flights](https://pcflights.com/flight-simulator-cockpit-panels/f-16c-viper-home-cockpit-panels/) — F-16C 패널 전문 **(본 프로젝트: MISC · Gear · CMDS)**
- [HispaPanel](https://hispapanels.com/tienda/en/20-f-16-fighting-falcon) — 레이저 커팅/각인 패널 키트
- [TEK Creations](https://tekcreations.space/shop/) — LED 백라이트 패널, DCS-BIOS 레디

| MISC | Gear | CMDS |
|:----:|:----:|:----:|
| [![MISC](https://pcflights.com/image/cache/catalog/panels/f-16c_viper_misc_panel-600x400.jpg)](https://pcflights.com/f-16c-viper-miscellaneous-misc-panel-flight-sim-part/) | [![Gear](https://pcflights.com/image/cache/catalog/panels/f-16c_viper_landing_gear_panel-600x400.jpg)](https://pcflights.com/f-16c-viper-landing-gear-panel-flight-simulator-module/) | [![CMDS](https://pcflights.com/image/cache/catalog/panels/f-16c_viper_cmds_control_panel-600x400.jpg)](https://pcflights.com/f-16c-viper-cmds-control-panel-module/) |

## 2. 3D 모델 출처

- [Greenisland](https://cults3d.com/en/users/Greenisland/3d-models) — F-16 콕핏 거의 전체 파트.
  STL 과 함께 **아크릴 재단용 DXF (`Lasercutting template`)** 를 동봉해서 배포합니다
  **(본 프로젝트: 위 3종을 뺀 나머지 전 패널)**
- [Legarsdusofa](https://cults3d.com/en/design-collections/Legarsdusofa/f-16-cockpit-simulator) — F-16 콕핏 거의 전체 파트
- [The_Viper_Project](https://cults3d.com/en/users/The_Viper_Project/3d-models) — 버튼 노브, 스위치 캡 등 무료

---

## 3. 레이어 구조

Greenisland 패널은 **3 레이어** 구조이고, 여기에 백라이트 플레이트가 더해집니다.
패널 한 장을 만들려면 **아크릴 재단 2종 + 3D 프린트 2종**이 필요합니다.

| 레이어 | 재료 | 제작 방법 | 역할 |
|--------|------|-----------|------|
| Top | 아크릴 **2 mm** — 흰색 또는 투명 (도색 방법에 따라) | **아크릴 재단** → 도색 → 문자 · 눈금 각인 | 전면 |
| Diffuser | **투명** 아크릴 **2~3 mm** | **아크릴 재단** | 빛 확산 |
| LED layer | 투명 PLA | **3D 프린트** | 스위치가 체결되는 층 |
| 백라이트 플레이트 | PLA · 레진 | **3D 프린트** | 패널 뒤 몇 cm — 본 프로젝트에서 추가 ([README 1-2](../README.md#1-2-3d-프린트-구조물)) |

```
   Top        아크릴 2 mm — 도색 + 각인        ← 전면
   Diffuser   투명 아크릴 2~3 mm                빛 확산
   LED layer  투명 PLA                         ← 스위치가 여기에 체결됨
   ┊
   ┊ 몇 cm 띄움
   ┊
   백라이트 플레이트   PLA · 레진              ← LED 를 여기에 장착
```

PC Flights 패널(MISC · Gear · CMDS)은 2 층(전면 도색 + 후면 투명)입니다.

---

## 4. 두께

Top **2 mm**, Diffuser **투명 2~3 mm** 로 주문했습니다. Top 의 색은 도색 방법에 따라 갈립니다(→ [6](#6-top-도색--각인--두-가지-방법)).
Diffuser 는 2 mm 와 3 mm 중 고르면 되는데, **토글 스위치 나사가 두꺼우면 3 mm** 를 권합니다.

---

## 5. 무엇을 재단하고 무엇을 출력하는가

Top · Diffuser 는 동봉된 **아크릴 재단용 DXF** 로 바로 발주할 수 있습니다
(패널에 따라 컷 도면과 각인 도면이 따로 들어 있습니다).
**LED layer 는 DXF 가 없어** 아크릴 재단이 불가능하므로 투명 PLA 로 출력했습니다.
백라이트 플레이트는 자작 모델이라 처음부터 3D 프린트 전용입니다.

> ⚠ **LED layer 는 투명 아크릴이 낫습니다** — 투명 PLA 는 이름만큼 투명하지 않아,
> 백라이트가 이 층을 지나면서 눈에 띄게 어두워집니다. 다시 만든다면 투명 아크릴로
> 재단하겠습니다. 다만 DXF 가 없으므로 STL 에서 도면을 직접 떠야 합니다.

국내는 [아크릴마켓](https://smartstore.naver.com/acrylicmarket) 등 레이저 가공 업체에 DXF 를 보내 주문하며,
**DXF R2000 형식**을 요구하는 곳이 많습니다.

---

## 6. Top 도색 · 각인 — 두 가지 방법

글자는 인쇄하는 게 아닙니다. 아크릴을 통째로 도색한 뒤 **글자 모양만 레이저로 걷어내고**,
그 자리로 뒤에서 온 빛이 새어 나오게 만듭니다. 걷어낸 바닥이 무엇이냐에 따라 두 갈래입니다.

| | 아크릴 | 도색 | 레이저가 걷어내는 것 | 글자 바닥 |
|---|--------|------|---------------------|-----------|
| **A** | **흰색** 2 mm | 검정 락카 **1 회** | 검정 락카 | 흰색 아크릴 |
| **B** | **투명** 2 mm | 흰색 락카 → 검정 락카 **2 중** | 검정 락카 층만 | 흰색 락카 |

A 는 도색이 한 번이라 간단합니다. B 는 두 번 칠해야 하고, 레이저가 **검정 층만 벗기고
흰색 층은 남겨야** 하므로 출력 · 속도를 더 정확히 맞춰야 합니다.

---

## 7. 백라이트 플레이트가 따로 있는 이유

원래 설계는 백라이트 LED 도 `LED layer` 에 함께 장착하도록 되어 있습니다. 그런데 LED layer 는
Top 과 너무 가까워, 고르게 밝히려면 LED 가 아주 많이 필요합니다. 그래서 패널 **뒤쪽 몇 cm 뒤에
별도 플레이트**를 두어 LED 수량을 줄였습니다.

자세한 내용은 [REF_BACKLIGHT.md](REF_BACKLIGHT.md) 참조.
