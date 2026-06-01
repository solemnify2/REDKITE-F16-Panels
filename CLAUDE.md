# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Teensy 4.0 기반 F-16 Left Console (ECM + ELEC 패널) USB 조이스틱 컨트롤러.
Falcon BMS 시뮬레이터용 커스텀 콕핏 하드웨어 프로젝트 (Redkite Project).

## Build & Upload

Arduino IDE 또는 PlatformIO에서 Teensy 4.0 타겟으로 빌드.
- Board: Teensy 4.0
- USB Type: Serial + Keyboard + Mouse + Joystick
- 의존성: Joystick 라이브러리 (Teensyduino 내장)

## Architecture

단일 `.ino` 파일 구조 (REDKITE_F16_LEFT_CONSOLE.ino):

1. **Hardware Config** (상단): `SwitchDef`, `LedDef`, `AnalogBtnArrayDef` 배열로 핀/스위치/LED 선언
2. **74HC595 Driver**: 4개 데이지체인 시프트 레지스터로 ECM 패널 32개 LED 제어 (`srWrite`, `srFlush`)
3. **Input Processing**: 디지털 스위치 (`processSwitches`) + 아날로그 저항래더 (`processAnalogButtons`)
4. **Output**: USB Joystick 버튼으로 매핑 (순차 할당, 버튼 1번부터)

`name.c`: USB 디바이스 이름을 "REDKITE F16 Left Console"로 커스터마이즈.

## Key Conventions

- 스위치는 INPUT_PULLUP, active-low
- 새 스위치/버튼 추가 시 `switches[]` 또는 `analogBtnArrays[]` 배열에 항목 추가하면 조이스틱 버튼 번호 자동 할당
- LED 추가: GPIO 직결은 `leds[]` 배열, 시프트 레지스터는 `ecmSrLedNames[]`
- 디버그: `ALLOW_DEBUG`를 true로 변경하면 시리얼 모니터에 입력 상태 출력
- 핀 배치 문서: `doc/PIN_ASSIGNMENT.md`
