# -*- coding: utf-8 -*-
"""Redkite 컨트롤 이름 -> DCS F-16C 입력 명령 ID.

bms_callbacks.py 와 같은 모양입니다 — 컨트롤이 차지하는 DX 하나당 한 항목:

    None                 바인딩 없음
    TODO                 아직 정하지 않음 (생성기가 보고합니다)
    'd3001...'           누를 때만
    ('d3001...', 'd3002...')   누를 때 / 뗄 때

3단 스위치의 가운데는 양쪽 DX 의 **뗄 때** 자리에 같은 명령을 넣으면 됩니다 —
생성기가 그 둘을 JOY_BTN<a>_OFF + JOY_BTN<b>_OFF 한 항목으로 합칩니다.

사용자의 DCS/InputUserProfiles 프로파일에서 자동 추출했습니다. 명령 ID 의 이름은
tools/dcs_catalog.txt 에 있습니다.
"""

TODO = '!TODO'

CONSOLE = {
    'MPO':                 ['d3010pnilu3010cd2vd1vpnilvu0'],   # MANUAL PITCH Override Switch
    'UHF PRESET':          ['d1200pnilunilcdnilvdnilvpnilvunil',
                             'd1199pnilunilcdnilvdnilvpnilvunil',
                            ],   # UHF CHAN Knob
    'UHF TEST':            ['d1213pnilu1213cdnilvd1vpnilvu0'],   # UHF TEST DISPLAY Button
    'UHF STATUS':          ['d1214pnilu1214cdnilvd1vpnilvu0'],   # UHF STATUS Button
    'UHF 100MHz':          ['d3027pnilunilcd37vd-1vpnilvunil',
                             'd3027pnilunilcd37vd1vpnilvunil',
                            ],   # UHF A-3-2 Knob
    'UHF 10MHz':           ['d1206pnilunilcdnilvdnilvpnilvunil',
                             'd1205pnilunilcdnilvdnilvpnilvunil',
                            ],   # UHF 10Mhz Manual Frequency Knob
    'UHF 1MHz':            ['d1208pnilunilcdnilvdnilvpnilvunil',
                             'd1207pnilunilcdnilvdnilvpnilvunil',
                            ],   # UHF 1Mhz Manual Frequency Knob
    'UHF 0.1MHz':          ['d1210pnilunilcdnilvdnilvpnilvunil',
                             'd1209pnilunilcdnilvdnilvpnilvunil',
                            ],   # UHF 0.1Mhz Manual Frequency Knob
    'UHF 0.025MHz':        ['d1212pnilunilcdnilvdnilvpnilvunil',
                             'd1211pnilunilcdnilvdnilvpnilvunil',
                            ],   # UHF 0.025Mhz Manual Frequency Knob
    'UHF FUNCTION':        ['d1221pnilunilcdnilvdnilvpnilvunil',
                             'd1220pnilunilcdnilvdnilvpnilvunil',
                             'd1219pnilunilcdnilvdnilvpnilvunil',
                             'd1218pnilunilcdnilvdnilvpnilvunil',
                            ],   # UHF Function Knob
    'UHF MODE':            ['d1224pnilunilcdnilvdnilvpnilvunil',
                             'd1223pnilunilcdnilvdnilvpnilvunil',
                             'd1222pnilunilcdnilvdnilvpnilvunil',
                            ],   # UHF Mode Knob
    'UHF T-TONE':          [TODO],
    'UHF SQUELCH':         [('d3010pnilunilcd37vd0vpnilvunil', 'd3010pnilunilcd37vd1vpnilvunil'),
                            ],   # UHF SQUELCH Switch
    'JFS':                 ['d3005pnilu3005cd6vd1vpnilvu0', 'd3006pnilu3006cd6vd-1vpnilvu0'],   # JFS Switch
    'ENG CONT COVER':      [('d3007pnilunilcd6vd1vpnilvunil', 'd3007pnilunilcd6vd0vpnilvunil')],   # ENG CONT Switch Cover
    'ENG CONT':            [('d3008pnilunilcd6vd1vpnilvunil', 'd3008pnilunilcd6vd0vpnilvunil')],   # ENG CONT Switch
    'AB RESET/ENG DATA':   ['d3010pnilu3010cd6vd1vpnilvu0', 'd3011pnilu3011cd6vd-1vpnilvu0'],   # AB RESET Switch
    'MAX POWER':           [('d3009pnilunilcd6vd1vpnilvunil', 'd3009pnilunilcd6vd0vpnilvunil')],   # MAX POWER Switch
    'COMM1 PWR':           [None],
    'COMM2 PWR':           [None],
    'COMM1 MODE':          ['d3002pnilunilcd39vd0vpnilvunil',
                             'd3002pnilunilcd39vd0.5vpnilvunil',
                             'd3002pnilunilcd39vd1vpnilvunil',
                            ],   # COMM 1 (UHF) Mode Knob
    'COMM2 MODE':          ['d3004pnilunilcd39vd0vpnilvunil',
                             'd3004pnilunilcd39vd0.5vpnilvunil',
                             'd3004pnilunilcd39vd1vpnilvunil',
                            ],   # COMM 2 (VHF) Mode Knob
    'HOT MIC/CIPHER':      [('d3012pnilunilcd39vd1vpnilvunil', 'd3012pnilunilcd39vd0vpnilvunil'),
                             ('d3012pnilunilcd39vd-1vpnilvunil', 'd3012pnilunilcd39vd0vpnilvunil'),
                            ],   # HOT MIC CIPHER Switch
    'ECM OPR/STBY':        [('d3001pnilunilcd66vd1vpnilvunil', 'd3001pnilunilcd66vd0vpnilvunil'),
                             ('d3001pnilunilcd66vd-1vpnilvunil', 'd3001pnilunilcd66vd0vpnilvunil'),
                            ],   # ECM Power Switch
    'ECM XMIT':            [('d3002pnilunilcd66vd1vpnilvunil', 'd3002pnilunilcd66vd0vpnilvunil'),
                             ('d3002pnilunilcd66vd-1vpnilvunil', 'd3002pnilunilcd66vd0vpnilvunil'),
                            ],   # ECM XMIT Switch
    'ECM Buttons':         ['d3018pnilunilcd66vd1vpnilvunil',
                             'd3019pnilunilcd66vd1vpnilvunil',
                             'd3020pnilunilcd66vd1vpnilvunil',
                             'd3021pnilunilcd66vd1vpnilvunil',
                             'd3022pnilunilcd66vd1vpnilvunil',
                             'd3023pnilunilcd66vd1vpnilvunil',
                             'd3024pnilunilcd66vd1vpnilvunil',
                             'd3025pnilunilcd66vd1vpnilvunil',
                            ],   # ECM 1 Button
    'ECM RESET':           ['d3004pnilu3004cd66vd1vpnilvu0'],   # ECM RESET Button
    'ECM BIT':             ['d3005pnilu3005cd66vd1vpnilvu0'],   # ECM BIT Button
    'EPU OFF COVER':       [TODO],
    'EPU ON COVER':        [TODO],
    'EPU':                 [('d3003pnilunilcd6vd1vpnilvunil', 'd3003pnilunilcd6vd0vpnilvunil'),
                             ('d3003pnilunilcd6vd-1vpnilvunil', 'd3003pnilunilcd6vd0vpnilvunil'),
                            ],   # EPU Switch
    'ELEC MAIN PWR':       [('d3001pnilunilcd3vd1vpnilvunil', 'd3001pnilunilcd3vd0vpnilvunil'),
                             ('d3001pnilunilcd3vd-1vpnilvunil', 'd3001pnilunilcd3vd0vpnilvunil'),
                            ],   # MAIN PWR Switch
    'ELEC CAUTION RST':    ['d3002pnilu3002cd3vd1vpnilvu0'],   # ELEC CAUTION RESET Button
    'AVTR':                [TODO, TODO],
}

AUX = {
    'RF':                  [('d3038pnilunilcd17vd-1vpnilvunil', 'd3038pnilunilcd17vd0vpnilvunil'),
                             ('d3038pnilunilcd17vd1vpnilvunil', 'd3038pnilunilcd17vd0vpnilvunil'),
                            ],   # RF Switch
    'Laser ARM':           [('d3004pnilunilcd22vd1vpnilvunil', 'd3004pnilunilcd22vd0vpnilvunil'),
                            ],   # LASER ARM Switch
    'ALT REL':             ['d3005pnilu3005cd19vd1vpnilvu0'],   # ALT REL Button
    'Master ARM':          [('d3002pnilunilcd19vd-1vpnilvunil', 'd3002pnilunilcd19vd0vpnilvunil'),
                             ('d3002pnilunilcd19vd1vpnilvunil', 'd3002pnilunilcd19vd0vpnilvunil'),
                            ],   # MASTER ARM Switch
    'ADV MODE':            ['d3034pnilunilcd2vd1vpnilvunil'],   # ADV MODE Switch
    'Roll AP':             [('d3014pnilunilcd2vd1vpnilvunil', 'd3014pnilunilcd2vd0vpnilvunil'),
                             ('d3014pnilunilcd2vd-1vpnilvunil', 'd3014pnilunilcd2vd0vpnilvunil'),
                            ],   # Autopilot ROLL Switch
    'Pitch AP':            [('d3032pnilu3032cd2vd1vpnilvu0', 'd3032pnilunilcd2vd-1vpnilvunil'),
                             ('d3031pnilu3031cd2vd-1vpnilvu0', 'd3032pnilunilcd2vd-1vpnilvunil'),
                            ],   # Autopilot PITCH Switch
    'EMER Jettison':       ['d3003pnilu3003cd19vd1vpnilvu0'],   # EMER STORES JETTISON Button
    'Hook':                [('d3006pnilunilcd7vd1vpnilvunil', 'd3006pnilunilcd7vd0vpnilvunil')],   # HOOK Switch
    'GND JETT ENABLE':     [('d3004pnilunilcd19vd1vpnilvunil', 'd3004pnilunilcd19vd0vpnilvunil'),
                            ],   # GND JETT ENABLE Switch
    'BRAKES Channel':      [('d3005pnilunilcd7vd1vpnilvunil', 'd3005pnilunilcd7vd0vpnilvunil')],   # BRAKES Channel Switch
    'ANTI SKID':           [('d3014pnilu3014cd7vd1vpnilvu0', 'd3010pnilunilcd7vd0vpnilvunil'),
                             ('d3010pnilunilcd7vd-1vpnilvunil', 'd3010pnilunilcd7vd0vpnilvunil'),
                            ],   # ANTI-SKID Switch
    'DN LOCK REL':         ['d3002pnilu3002cd7vd1vpnilvu0'],   # DN LOCK REL Button
    'Landing Gear':        ['d430pnilunilcdnilvdnilvpnilvunil',
                             'd431pnilunilcdnilvdnilvpnilvunil',
                            ],   # LG Handle
    'Store CAT':           [('d3011pnilunilcd2vd1vpnilvunil', 'd3011pnilunilcd2vd0vpnilvunil')],   # STORES CONFIG Switch
    'Horn Silencer':       ['d3007pnilu3007cd7vd1vpnilvu0'],   # HORN SILENCER Button
    'Landing Light':       [('d3008pnilunilcd11vd-1vpnilvunil', 'd3008pnilunilcd11vd0vpnilvunil'),
                             ('d3008pnilunilcd11vd1vpnilvunil', 'd3008pnilunilcd11vd0vpnilvunil'),
                            ],   # LANDING TAXI LIGHTS Switch
    'TWA Buttons':         ['d3010pnilu3010cd33vd1vpnilvu0',
                             'd3009pnilu3009cd33vd1vpnilvu0',
                             'd3012pnilu3012cd33vd1vpnilvu0',
                             'd3017pnilunilcd33vd1vpnilvunil',
                            ],   # RWR Indicator Control ACT/PWR Button
    'CMDS RWR':            [('d3001pnilunilcd32vd1vpnilvunil', 'd3001pnilunilcd32vd0vpnilvunil'),
                            ],   # RWR Source Switch
    'CMDS JMR':            [('d3002pnilunilcd32vd1vpnilvunil', 'd3002pnilunilcd32vd0vpnilvunil'),
                            ],   # JMR Source Switch
    'CMDS MWS':            [('d3003pnilunilcd32vd1vpnilvunil', 'd3003pnilunilcd32vd0vpnilvunil'),
                            ],   # MWS Source Switch
    'CMDS O1':             [('d3008pnilunilcd32vd1vpnilvunil', 'd3008pnilunilcd32vd0vpnilvunil'),
                            ],   # FL Expendable Category Switch
    'CMDS O2':             [('d3007pnilunilcd32vd1vpnilvunil', 'd3007pnilunilcd32vd0vpnilvunil'),
                            ],   # CH Expendable Category Switch
    'CMDS CH':             [('d3006pnilunilcd32vd1vpnilvunil', 'd3006pnilunilcd32vd0vpnilvunil'),
                            ],   # O2 Expendable Category Switch
    'CMDS FL':             [('d3005pnilunilcd32vd1vpnilvunil', 'd3005pnilunilcd32vd0vpnilvunil'),
                            ],   # O1 Expendable Category Switch
    'CMDS JETT':           [('d3004pnilunilcd32vd1vpnilvunil', 'd3004pnilunilcd32vd0vpnilvunil'),
                            ],   # JETT Switch
    'CMDS PRGM':           ['d3009pnilunilcd32vd0vpnilvunil',
                             'd3009pnilunilcd32vd0.1vpnilvunil',
                             'd3009pnilunilcd32vd0.2vpnilvunil',
                             'd3009pnilunilcd32vd0.3vpnilvunil',
                             'd3009pnilunilcd32vd0.4vpnilvunil',
                             None,
                             None,
                            ],   # PROGRAM Knob
    'CMDS MODE':           ['d3010pnilunilcd32vd0vpnilvunil',
                             'd3010pnilunilcd32vd0.1vpnilvunil',
                             'd3010pnilunilcd32vd0.2vpnilvunil',
                             'd3010pnilunilcd32vd0.3vpnilvunil',
                             'd3010pnilunilcd32vd0.4vpnilvunil',
                             'd3010pnilunilcd32vd0.5vpnilvunil',
                             None,
                            ],   # MODE Knob
    'ALT GEAR Handle':     [('d3008pnilunilcd7vd1vpnilvunil', 'd3008pnilunilcd7vd0vpnilvunil')],   # ALT GEAR Handle, PULL
}

MAPS = {'CONSOLE': CONSOLE, 'AUX': AUX}
