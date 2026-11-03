# -*- coding: utf-8 -*-
"""두 심의 **축 설정**. 생성기가 바인딩 파일을 처음부터 만들 때 쓰는 데이터입니다.

버튼은 `dxOrder[]` 와 콜백/명령 표에서 전부 유도되지만, 축에는 유도할 수 없는 값이
붙습니다 — `invert`, `deadzone`, `saturation` 같은 것들입니다. 그래서 기존 설정에서
한 번 뽑아 여기 적어 두고, 생성기는 이 파일만 보고 축 블록을 만듭니다. 템플릿 파일이
없어도 되고, 값을 바꾸고 싶으면 여기를 고치면 됩니다.

출처: 사용자의 `Setup.v100.*.xml` 과 `*.diff.lua` (2025-09 시점).

**슬라이더 번호 주의** — 펌웨어의 `slider(1)`(= `AXIS_S1`, ILS)이 두 심 모두에서
**두 번째** 슬라이더로 보입니다. BMS 는 `<AxAssgn>` 슬롯 7, DCS 는 `JOY_SLIDER2`.
HID 디스크립터 쪽 특성으로 보이며, 양쪽이 일치하므로 그대로 둡니다.
`slider(2)`(`AXIS_S2`, SECURE VOL)는 아직 어느 심에도 안 묶여 있습니다.
"""

# ---------------------------------------------------------------- Falcon BMS
#
# `<axis>` 는 HID 축 순서대로 8칸입니다: X, Y, Z, Rx, Ry, Rz, Slider1, Slider2.
# 빈 칸은 AxisName 을 비우면 됩니다.
#
#   (AxisName, Invert, Saturation, Deadzone)

BMS_DETENT = {'AB': 65536, 'IDLE': 0}

BMS_AXES = {
    'CONSOLE': [
        ('COMM_Channel_1',  True,  'None', 'None'),   # X   AUDIO COMM CH1
        ('COMM_Channel_2',  True,  'None', 'None'),   # Y   AUDIO COMM CH2
        ('MSL_Volume',      True,  'None', 'None'),   # Z   AUDIO MSL VOL
        ('Threat_Volume',   True,  'None', 'None'),   # Rx  AUDIO THREAT VOL
        ('Intercom',        True,  'None', 'None'),   # Ry  AUDIO INTERCOM
        ('AI_vs_IVC',       True,  'None', 'None'),   # Rz  UHF VOL
        ('',                False, 'None', 'None'),   # S1  (미사용)
        ('ILS_Volume_Knob', True,  'None', 'None'),   # S2  AUDIO ILS VOL
    ],
    'AUX': [
        ('',                False, 'None',  'None'),  # X   (미사용)
        ('',                False, 'None',  'None'),  # Y   (미사용)
        ('HMS_Brightness',  False, 'Large', 'None'),  # Z   HMCS Symbology
        ('Toe_Brake',       True,  'None',  'None'),  # Rx  Left Brake
        ('Toe_Brake_Right', True,  'None',  'None'),  # Ry  Right Brake
        ('Yaw',             False, 'None',  'None'),  # Rz  러더
        ('',                False, 'None',  'None'),  # S1  (미사용)
        ('',                False, 'None',  'None'),  # S2  (미사용)
    ],
}

# `<pov>` 는 3벌, 각 벌에 PovAssgn 4개, 각 PovAssgn 에 direction 1개와
# DirAssgn 8개. 전부 비어 있습니다 (SimDoNothing).
BMS_POV_SETS = 3
BMS_POV_ASSGN = 4
BMS_DIR_ASSGN = 8

# BMS 가 AssgnDate 에 쓰는 '비어 있음' 값. 설정 UI 를 건드리면 BMS 가 다시 씁니다.
BMS_ASSGN_DATE = '1998-12-12T12:00:00'

# USB 제품명 (name.c). Setup XML 파일명의 앞부분이라, 생성기가
# BMS 설정 폴더에서 GUID 를 찾을 때 이 이름으로 골라냅니다.
PRODUCT = {'CONSOLE': 'F16 LEFT CONSOLE', 'AUX': 'F16 LEFT AUX MISC'}

# DCS 프로파일 파일명. DCS 는 GUID 가 아니라 이름으로 찾습니다.
DCS_PROFILE = {'CONSOLE': 'F16 Left Console panel', 'AUX': 'F16 Left AUX MISCpanel'}

# `<dx>` 섹션 수와 섹션당 버튼 수. 앞 두 벌에 같은 내용이 들어가고 셋째는 빕니다.
BMS_DX_SETS = 3
BMS_DX_PER_SET = 128
BMS_DX_LIVE_SETS = 2


# ------------------------------------------------------------------ DCS World
#
# 노브에 붙는 표준 필터. 이 패널의 포트는 전부 반전입니다.
KNOB = {'curvature': [0], 'deadzone': 0, 'hardwareDetent': False,
        'hardwareDetentAB': 0, 'hardwareDetentMax': 0, 'invert': True,
        'saturationX': 1, 'saturationY': 1, 'slider': False}

# (명령 ID, 이름, 'added'|'removed', 키, 필터 또는 None)
#
# `removed` 는 DCS 가 새 조이스틱에 자동으로 거는 기본 축을 **떼어내는** 항목입니다.
# 두 보드 모두 X/Y/Z 를 보고하므로, 이게 없으면 노브가 기체를 조종합니다.
DCS_AXES = {
    'CONSOLE': [
        ('a2001cdnil', 'Pitch',                   'removed', 'JOY_Y',       None),
        ('a2002cdnil', 'Roll',                    'removed', 'JOY_X',       None),
        ('a2003cdnil', 'Rudder',                  'removed', 'JOY_RZ',      None),
        ('a2004cdnil', 'Thrust',                  'removed', 'JOY_Z',       None),
        ('a3020cd39',  'COMM 1 (UHF) Power Knob', 'added',   'JOY_X',       KNOB),
        ('a3023cd39',  'COMM 2 (VHF) Power Knob', 'added',   'JOY_Y',       KNOB),
        ('a3024cd37',  'UHF VOL Knob',            'added',   'JOY_RZ',      KNOB),
        ('a3028cd39',  'MSL Tone Knob',           'added',   'JOY_Z',       KNOB),
        ('a3032cd39',  'THREAT Tone Knob',        'added',   'JOY_RX',      KNOB),
        ('a3034cd39',  'ILS Power Knob',          'added',   'JOY_SLIDER2', KNOB),
        ('a3038cd39',  'INTERCOM Knob',           'added',   'JOY_RY',      KNOB),
    ],
    'AUX': [
        ('a2001cdnil', 'Pitch',                   'removed', 'JOY_Y',  None),
        ('a2002cdnil', 'Roll',                    'removed', 'JOY_X',  None),
        ('a2004cdnil', 'Thrust',                  'removed', 'JOY_Z',  None),
        ('a2112cdnil', 'Wheel Brake Left',        'added',   'JOY_RX', None),
        ('a2113cdnil', 'Wheel Brake Right',       'added',   'JOY_RY', None),
        ('a3003cd30',  'HMCS SYMBOLOGY INT Knob', 'added',   'JOY_Z',  KNOB),
    ],
}
