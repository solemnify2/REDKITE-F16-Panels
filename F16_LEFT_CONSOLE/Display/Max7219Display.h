#pragma once
// ================================================================
//  UHF 패널 7세그먼트 디스플레이 (MAX7219 + 8 x 0.36" 공통캐소드)
// ================================================================
//
//  보드: f-16-cockpit-uhf-radio-panel/display/pcb  (rev A)
//    MAX7219 + 74AHCT125 레벨 시프터(3.3V -> 5V), J1 5핀
//    J1.1 +5V(VIN)  J1.2 GND  J1.3 DIN  J1.4 CLK  J1.5 CS
//
//  자릿수 배치 (MAX7219 DIGn -> 레지스터 0x01+n):
//    DIG0~DIG5 = 주파수 6자리 (왼쪽->오른쪽), DIG2 에 소수점
//    DIG6      = 프리셋 채널 10의 자리
//    DIG7      = 프리셋 채널 1의 자리
//
//  ※ 하드웨어 SPI2 를 씁니다. SPI0(MOSI 11 / SCK 13)은 엔코더·백라이트가
//    점유했지만, Teensy 4.1 하단 SD 카드 인터페이스의 SPI2 가 비어 있습니다
//    (SD 확장 케이블로 빼내 사용). 엣지 핀은 하나도 쓰지 않습니다.
//      MOSI2 = 43  ->  J1.3 DIN
//      CS2   = 44  ->  J1.5 CS   (소프트웨어 토글)
//      SCK2  = 45  ->  J1.4 CLK
//    MISO 는 MAX7219 가 단방향이라 사용하지 않습니다.
//
//  핀(PIN_DISP_*)은 메인 스케치의 핀 배정 블록에서 정의합니다.

#include <SPI.h>

// ---- MAX7219 레지스터 ----
#define MAXR_DIGIT0       0x01      // .. 0x08 = DIG7
#define MAXR_DECODEMODE   0x09
#define MAXR_INTENSITY    0x0A
#define MAXR_SCANLIMIT    0x0B
#define MAXR_SHUTDOWN     0x0C
#define MAXR_DISPLAYTEST  0x0F

// Code-B 디코드 값
#define CB_BLANK          0x0F
#define CB_DASH           0x0A
#define CB_DP             0x80      // 소수점 비트

#define DISP_NUM_DIGITS   8
#define DISP_DEFAULT_INTENSITY  0x08   // 0x0F 는 Rset 20k 에서 ~208mA

// MAX7219 최대 10MHz. 8MHz 로 두면 2바이트 전송이 2us 남짓입니다.
static SPISettings dispSpiCfg(8000000, MSBFIRST, SPI_MODE0);

static uint8_t dispCache[DISP_NUM_DIGITS];
static bool    dispCacheValid = false;
static bool    dispPowered    = false;

static void maxWrite(uint8_t reg, uint8_t data) {
  SPI2.beginTransaction(dispSpiCfg);
  digitalWriteFast(PIN_DISP_CS, LOW);
  SPI2.transfer(reg);
  SPI2.transfer(data);
  digitalWriteFast(PIN_DISP_CS, HIGH);     // 상승 엣지에서 래치
  SPI2.endTransaction();
}

// 값이 바뀐 자리만 전송 — 100Hz 루프에서 I/O 를 최소화합니다.
static void maxDigit(uint8_t d, uint8_t v) {
  if (dispCacheValid && dispCache[d] == v) return;
  dispCache[d] = v;
  maxWrite(MAXR_DIGIT0 + d, v);
}

void displayBlank() {
  for (uint8_t d = 0; d < DISP_NUM_DIGITS; d++) maxDigit(d, CB_BLANK);
}

// 브릿지 오프라인 표시 — 전 자리 대시 ("------  --")
void displayDashes() {
  for (uint8_t d = 0; d < DISP_NUM_DIGITS; d++) maxDigit(d, CB_DASH);
}

void displayBegin() {
  pinMode(PIN_DISP_CS, OUTPUT);            // CS 는 소프트웨어로 토글
  digitalWriteFast(PIN_DISP_CS, HIGH);
  SPI2.setMOSI(PIN_DISP_DIN);
  SPI2.setSCK(PIN_DISP_CLK);
  SPI2.begin();

  maxWrite(MAXR_DISPLAYTEST, 0x00);        // 정상 동작
  maxWrite(MAXR_SCANLIMIT,   0x07);        // 8자리 전부 스캔
  maxWrite(MAXR_DECODEMODE,  0xFF);        // 8자리 모두 Code B
  maxWrite(MAXR_INTENSITY,   DISP_DEFAULT_INTENSITY);
  dispCacheValid = false;
  displayBlank();
  dispCacheValid = true;
  maxWrite(MAXR_SHUTDOWN,    0x01);        // 깨우기
  dispPowered = true;
}

void displayBrightness(uint8_t level) {    // 0..15
  maxWrite(MAXR_INTENSITY, level & 0x0F);
}

void displayOn(bool on) {
  if (dispPowered == on) return;
  dispPowered = on;
  maxWrite(MAXR_SHUTDOWN, on ? 0x01 : 0x00);
}

// 램프 테스트 — 전 세그먼트 점등 (세리머니용)
void displayLampTest(bool on) {
  maxWrite(MAXR_DISPLAYTEST, on ? 0x01 : 0x00);
}

/* 주파수 kHz (225000~399975) -> "305.750" */
void displayFrequency(uint32_t khz) {
  if (khz < 100000UL || khz > 999999UL) {  // 범위 밖 -> 대시
    for (uint8_t d = 0; d < 6; d++) maxDigit(d, CB_DASH);
    return;
  }
  uint32_t v = khz;
  for (int8_t d = 5; d >= 0; d--) {        // DIG5 = 주파수 맨 오른쪽
    uint8_t digit = v % 10;
    v /= 10;
    if (d == 2) digit |= CB_DP;            // MHz 뒤 소수점
    maxDigit(d, digit);
  }
}

/* 프리셋 채널 1~20 (0 또는 99 초과면 공백) */
void displayChannel(uint8_t ch) {
  if (ch == 0 || ch > 99) {
    maxDigit(6, CB_BLANK);
    maxDigit(7, CB_BLANK);
    return;
  }
  uint8_t tens = ch / 10;
  maxDigit(6, (tens == 0) ? CB_BLANK : tens);
  maxDigit(7, ch % 10);
}
