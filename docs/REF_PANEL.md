# 패널

MISC·Gear·CMDS는 PC Flights 제품을 사용합니다. 나머지 패널은 Greenisland 모델을 바탕으로 아크릴 가공과 3D 출력으로 제작했습니다.

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
| 백라이트 플레이트 | PLA · 레진 | **3D 프린트** | 패널 뒤 몇 cm — 본 프로젝트에서 추가 ([REF_ENCLOSURE.md](REF_ENCLOSURE.md)) |

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

Top은 2 mm, Diffuser는 투명 아크릴 2~3 mm를 사용했습니다. Top 색상은 도색 방법에 따라 선택합니다(→ [6](#6-top-도색--각인--두-가지-방법)).
Diffuser 는 2 mm 와 3 mm 중 고르면 되는데, **토글 스위치 나사가 두꺼우면 3 mm** 를 권합니다.

---

## 5. 무엇을 재단하고 무엇을 출력하는가

Top · Diffuser 는 동봉된 **아크릴 재단용 DXF** 로 바로 발주할 수 있습니다
(패널에 따라 컷 도면과 각인 도면이 따로 들어 있습니다).
LED layer용 DXF가 제공되지 않아 이 프로젝트에서는 투명 PLA로 출력했습니다. 아크릴로 제작하려면 별도 재단 도면이 필요합니다.
백라이트 플레이트는 자작 모델이라 처음부터 3D 프린트 전용입니다.

> 투명 PLA 출력물은 빛을 산란시켜 백라이트를 어둡게 만들 수 있습니다. 투명 아크릴을 사용하려면 제공 모델을 바탕으로 재단 도면과 체결 치수를 확인하십시오.

국내는 [아크릴마켓](https://smartstore.naver.com/acrylicmarket) 등 레이저 가공 업체에 DXF 를 보내 주문하며,
**DXF R2000 형식**을 요구하는 곳이 많습니다.

---

## 6. Top 도색 · 각인 — 두 가지 방법

아크릴을 도색한 뒤 문자·눈금 부분의 검정 도막을 레이저로 제거합니다. 남은 흰색층이 뒤쪽 조명을 확산합니다. 제작 방식은 다음 두 가지입니다.

| | 아크릴 | 도색 | 레이저가 걷어내는 것 | 글자 바닥 |
|---|--------|------|---------------------|-----------|
| **A** | **흰색** 2 mm | 검정 락카 **1 회** | 검정 락카 | 흰색 아크릴 |
| **B** | **투명** 2 mm | 흰색 락카 → 검정 락카 **2 중** | 검정 락카 층만 | 흰색 락카 |

A 는 도색이 한 번이라 간단합니다. B 는 두 번 칠해야 하고, 레이저가 **검정 층만 벗기고
흰색 층은 남겨야** 하므로 출력 · 속도를 더 정확히 맞춰야 합니다.

---

## 7. 백라이트 플레이트가 따로 있는 이유

원본은 LED를 스위치 체결층인 `LED layer`에 장착합니다. 이 프로젝트는 빛이 퍼질 거리를 확보하고 LED 수를 줄이기 위해 패널 뒤에 별도 플레이트를 배치했습니다.

자세한 내용은 [REF_BACKLIGHT.md](REF_BACKLIGHT.md) 참조.
