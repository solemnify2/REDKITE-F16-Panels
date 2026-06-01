# REDKITE F16 LEFT CONSOLE - Teensy 4.0 Pin Assignment

## ELEC Digital Switch Pins (INPUT_PULLUP)

| Pin     | Signal Name        | Switch Type  | Description              |
|---------|--------------------|--------------|--------------------------|
| 0       | ELEC MAIN PWR pin1 | SW_ON_OFF_ON | ELEC BATT position       |
| 1       | ELEC MAIN PWR pin2 | SW_ON_OFF_ON | ELEC MAIN position       |
| 2       | ELEC CAUTION RST   | SW_ON_OFF    | momentary pushbutton     |

## ELEC Panel LED Pins (OUTPUT, Direct GPIO)

| Pin     | LED Name     |
|---------|--------------|
| 3       | FLCS PMG     |
| 4       | MAIN GEN     |
| 5       | STBY GEN     |
| 6       | EPU GEN      |
| 7       | EPU PMG      |
| 8       | FLCS RLY     |
| 9       | BATT FAIL    |
| 10      | BATT TO FLCS |
| 11      | ELEC SYS     |

## ECM Digital Switch Pins (INPUT_PULLUP, descending)

| Pin     | Signal Name        | Switch Type  | Description              |
|---------|--------------------|--------------|--------------------------|
| 13      | ECM RESET          | SW_ON_OFF    | momentary pushbutton     |
| 14      | ECM BIT            | SW_ON_OFF    | momentary pushbutton     |
| 15      | ECM XMIT pin2      | SW_ON_OFF_ON | ECM XMIT 3 position     |
| 16      | ECM XMIT pin1      | SW_ON_OFF_ON | ECM XMIT 1 position     |
| 17      | ECM OPR/STBY pin2  | SW_ON_OFF_ON | ECM STBY position        |
| 18      | ECM OPR/STBY pin1  | SW_ON_OFF_ON | ECM OPR position         |

## ECM Panel PCB Pins (74HC595 Pins)

| Pin     | Signal Name | Description                                    |
|---------|-------------|------------------------------------------------|
| 20      | ST_CP       | Storage register clock (latch)                 |
| 21      | SH_CP       | Shift register clock                           |
| 22      | DS          | Serial data input                              |
| 23 (A9) | ECM Buttons | 8-button resistor ladder (1k + 4.7k pulldown)  |

## Joystick Button Mapping

| Button # | Panel | Name             |
|----------|-------|------------------|
| 1        | ECM   | ECM OPR          |
| 2        | ECM   | ECM STBY         |
| 3        | ECM   | ECM XMIT 1       |
| 4        | ECM   | ECM XMIT 3       |
| 5        | ECM   | ECM BIT          |
| 6        | ECM   | ECM RESET        |
| 7        | ECM   | ECM 1 (analog)   |
| 8        | ECM   | ECM 2 (analog)   |
| 9        | ECM   | ECM 3 (analog)   |
| 10       | ECM   | ECM 4 (analog)   |
| 11       | ECM   | ECM 5 (analog)   |
| 12       | ECM   | ECM 6 (analog)   |
| 13       | ECM   | ECM FRM (analog) |
| 14       | ECM   | ECM SPL (analog) |
| 15       | ELEC  | ELEC BATT        |
| 16       | ELEC  | ELEC MAIN        |
| 17       | ELEC  | ELEC CAUTION RST |

## 74HC595 Shift Register LED Mapping (32 outputs)

| SR Index | LED Name  | SR Index | LED Name  |
|----------|-----------|----------|-----------|
| 0        | ECM_1_S   | 16       | ECM_5_S   |
| 1        | ECM_1_A   | 17       | ECM_5_A   |
| 2        | ECM_1_F   | 18       | ECM_5_F   |
| 3        | ECM_1_T   | 19       | ECM_5_T   |
| 4        | ECM_2_S   | 20       | ECM_6_S   |
| 5        | ECM_2_A   | 21       | ECM_6_A   |
| 6        | ECM_2_F   | 22       | ECM_6_F   |
| 7        | ECM_2_T   | 23       | ECM_6_T   |
| 8        | ECM_3_S   | 24       | ECM_FRM_S |
| 9        | ECM_3_A   | 25       | ECM_FRM_A |
| 10       | ECM_3_F   | 26       | ECM_FRM_F |
| 11       | ECM_3_T   | 27       | ECM_FRM_T |
| 12       | ECM_4_S   | 28       | ECM_SPL_S |
| 13       | ECM_4_A   | 29       | ECM_SPL_A |
| 14       | ECM_4_F   | 30       | ECM_SPL_F |
| 15       | ECM_4_T   | 31       | ECM_SPL_T |

## Pin Usage Summary

| Pin Range | Usage              | Count |
|-----------|--------------------|-------|
| 0 - 2     | ELEC Switches      | 3     |
| 3 - 11    | ELEC LEDs (GPIO)   | 9     |
| 12        | (unused)           | 1     |
| 13 - 18   | ECM Switches       | 6     |
| 19        | (unused)           | 1     |
| 20 - 22   | 74HC595 SR Control | 3     |
| A9 (23)   | Analog Ladder      | 1     |

> Note: Teensy 4.0의 A9 핀은 디지털 핀 23번과 동일합니다.
> Pin 12, 19는 현재 미사용 상태입니다.
