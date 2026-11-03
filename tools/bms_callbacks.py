# -*- coding: utf-8 -*-
"""Redkite 컨트롤 이름 → Falcon BMS 콜백 매핑.

DX 번호가 아니라 **컨트롤 이름**을 키로 씁니다. dxOrder[] 를 재배열해도
이 표는 그대로이고, 하드웨어를 추가할 때만 늘어납니다.

값은 그 컨트롤이 차지하는 DX 하나당 한 항목인 리스트입니다:

    None                  바인딩 없음 (BMS 가 모델링하지 않는 스위치)
    'SimFoo'              모멘터리  — 누를 때 1회
    ('SimOn', 'SimOff')   유지형    — 누를 때 SimOn, 뗄 때 SimOff
    ('SimOn', None)       유지형이지만 되돌릴 콜백이 없음 (누를 때만)

3단 토글은 DX 2개로 들어오고 중립이 '뗀 상태'이므로, 각 DX 를
(해당 위치, 중립 위치) 로 두면 세 위치가 모두 표현됩니다.

TODO 로 표시한 항목은 아직 확정하지 못한 것입니다 — 생성기가 따로 보고합니다.
모든 콜백은 'BMS - Full.key' 에 실재하는지 생성 시점에 검증됩니다.
"""

TODO = '!TODO'

CONSOLE = {
    # ---- MPO ----
    'MPO':               [TODO],          # SimMPO(Hold) / SimMPOToggle 중 택일
    # ---- UHF ----
    'UHF PRESET':        ['SimCycleRadioChannel', 'SimDecRadioChannel'],
    'UHF TEST':          [None],          # BMS 미모델링
    'UHF STATUS':        [None],          # BMS 미모델링
    'UHF 100MHz':        ['SimBupUhfFreq1Inc', 'SimBupUhfFreq1Dec'],
    'UHF 10MHz':         ['SimBupUhfFreq2Inc', 'SimBupUhfFreq2Dec'],
    'UHF 1MHz':          ['SimBupUhfFreq3Inc', 'SimBupUhfFreq3Dec'],
    'UHF 0.1MHz':        ['SimBupUhfFreq4Inc', 'SimBupUhfFreq4Dec'],
    'UHF 0.025MHz':      ['SimBupUhfFreq5Inc', 'SimBupUhfFreq5Dec'],
    'UHF FUNC OFF':      ['SimBupUhfOff'],
    'UHF FUNC MAIN':     ['SimBupUhfMain'],
    'UHF FUNC BOTH':     ['SimBupUhfBoth'],
    'UHF FUNC ADF':      [None],          # BMS 에 ADF 위치 없음
    'UHF MODE MNL':      ['SimBupUhfManual'],
    'UHF MODE PRE':      ['SimBupUhfPreset'],
    'UHF MODE GRD':      ['SimBupUhfGuard'],
    'UHF T-TONE':        [None],          # BMS 미모델링
    'UHF SQUELCH':       [None],          # BMS 미모델링
    # ---- ENG & JET START ----
    'JFS':               [('SimJfsStartUp', 'SimJfsStartMid'),
                          ('SimJfsStartDown', 'SimJfsStartMid')],
    'ENG CONT COVER':    [None],          # 커버는 DCS 전용 개념
    'ENG CONT':          [('SimEngContSec', 'SimEngContPri')],  # 접점 방향 확인 필요
    'AB RESET/ENG DATA': [None, None],    # BMS 미모델링
    'MAX POWER':         [None],          # BMS 미모델링
    # ---- AUDIO 1 ----
    'COMM1 PWR':         [('SimComm1PowerOn', 'SimComm1PowerOff')],
    'COMM2 PWR':         [('SimComm2PowerOn', 'SimComm2PowerOff')],
    'COMM1 OFF':         [None],          # BMS 에 COMM MODE OFF 콜백 없음
    'COMM1 SQL':         ['SimAud1Com1Sql'],
    'COMM1 GD':          ['SimAud1Com1Gd'],
    'COMM2 OFF':         [None],
    'COMM2 SQL':         ['SimAud1Com2Sql'],
    'COMM2 GD':          ['SimAud1Com2Gd'],
    # ---- AUDIO 2 ----
    'HOT MIC/CIPHER':    [TODO, TODO],    # 이름이 일치하는 콜백 없음
    # ---- ECM ----
    'ECM OPR/STBY':      [('SimEcmPowerOn', None), ('SimEcmPowerOff', None)],
    'ECM XMIT':          [('SimXMit1', 'SimXMit2'), ('SimXMit3', 'SimXMit2')],
    'ECM Buttons':       ['SimEcmMode1Toggle', 'SimEcmMode2Toggle', 'SimEcmMode3Toggle',
                          'SimEcmMode4Toggle', 'SimEcmMode5Toggle',
                          None, None, None],   # ECM 6 / FRM / SPL — 콜백 없음
    'ECM RESET':         [None],          # BMS 미모델링
    'ECM BIT':           ['SimECMBit'],
    # ---- EPU ----
    'EPU OFF COVER':     [None],
    'EPU ON COVER':      [None],
    'EPU':               [('SimEpuOff', 'SimEpuAuto'), ('SimEpuOn', 'SimEpuAuto')],
    # ---- ELEC ----
    'ELEC MAIN PWR':     [('SimMainPowerMain', 'SimMainPowerBatt'),
                          ('SimMainPowerOff', 'SimMainPowerBatt')],
    'ELEC CAUTION RST':  ['SimElecReset'],
    # ---- AVTR ----
    'AVTR':              [('SimAVTRSwitchOff', 'SimAVTRSwitchAuto'),
                          ('SimAVTRSwitchOn', 'SimAVTRSwitchAuto')],
}

AUX = {
    # ---- MISC ----
    'RF':                [('SimRFNorm', 'SimRFQuiet'), ('SimRFSilent', 'SimRFQuiet')],
    'Laser ARM':         [('SimLaserArmOn', 'SimLaserArmOff')],
    'ALT REL':           [None],          # BMS 미모델링 (NC — DX 반전)
    'Master ARM':        [('SimArmMasterArm', 'SimSafeMasterArm'),
                          ('SimSimMasterArm', 'SimSafeMasterArm')],
    'ADV MODE':          ['SimToggleTFR'],
    'Roll AP':           [('SimLeftAPUp', 'SimLeftAPMid'),
                          ('SimLeftAPDown', 'SimLeftAPMid')],
    'Pitch AP':          [('SimRightAPUp', 'SimRightAPMid'),
                          ('SimRightAPDown', 'SimRightAPMid')],
    # ---- GEAR ----
    'EMER Jettison':     ['SimEmergencyJettison'],
    'Hook':              [('SimHookDown', 'SimHookUp')],
    'GND JETT ENABLE':   [('SimGndJettOn', 'SimGndJettOff')],
    'BRAKES Channel':    [('SimBrakeChannelDown', 'SimBrakeChannelUp')],
    'ANTI SKID':         [('SimParkingBrakeUp', 'SimParkingBrakeMid'),
                          ('SimParkingBrakeDown', 'SimParkingBrakeMid')],
    'DN LOCK REL':       ['AFEmergencyGearHandleUnlock'],
    'Landing Gear':      [('AFGearUp', None), ('AFGearDown', None)],
    'Store CAT':         [('SimCATI', 'SimCATIII')],
    'Horn Silencer':     ['SimSilenceHorn'],
    'Landing Light':     [('SimLandingLightUp', 'SimLandingLightMid'),
                          ('SimLandingLightDown', 'SimLandingLightMid')],
    # ---- TWA (래더 4: ACT/PWR, SEARCH, ALT, SYS PWR) ----
    'TWA Buttons':       ['SimRwrPower', 'SimRWRSetSearch',
                          'SimRWRSetGroundPriority', TODO],   # SYS PWR 미확정
    # ---- CMDS ----
    'CMDS RWR':          [('SimEWSRWROn', 'SimEWSRWROff')],
    'CMDS JMR':          [('SimEWSJammerOn', 'SimEWSJammerOff')],
    'CMDS MWS':          [('SimEWSMwsOn', 'SimEWSMwsOff')],
    'CMDS O1':           [('SimEWSO1On', 'SimEWSO1Off')],
    'CMDS O2':           [('SimEWSO2On', 'SimEWSO2Off')],
    'CMDS CH':           [('SimEWSChaffOn', 'SimEWSChaffOff')],
    'CMDS FL':           [('SimEWSFlareOn', 'SimEWSFlareOff')],
    'CMDS JETT':         [('SimEwsJettOn', 'SimEwsJettOff')],
    # PRGM 래더 7 = BIT, 1~6 — BMS 는 1~4 만 있음
    'CMDS PRGM':         [None, 'SimEWSProgOne', 'SimEWSProgTwo', 'SimEWSProgThree',
                          'SimEWSProgFour', None, None],
    # MODE 래더 7 — BMS MODE 는 OFF/STBY/MAN/SEMI/AUTO/BYP 6 위치
    'CMDS MODE':         [TODO] * 7,
    # ---- ALT GEAR ----
    'ALT GEAR Handle':   ['AFAlternateGear'],
}

MAPS = {'CONSOLE': CONSOLE, 'AUX': AUX}
