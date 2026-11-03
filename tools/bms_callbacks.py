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
    # 실기 MPO 는 OVRD 로 눌러 쥐고 있는 스위치입니다. DX 를 -1 로 걸면
    # BMS 가 누름/뗌을 모두 받아 쥐고 있는 동안 유효합니다 — 스톡 키 파일의
    # SimTriggerFirstDetent / SimHotasPinkyShift 와 같은 모양.
    'MPO':               ['SimMPO'],
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
    # HOT MIC 도 CIPHER 도 BMS 에 콜백이 없습니다 (Mic/Cipher/Secure 전부 0건).
    # BMS 가 모델링하지 않는 스위치입니다.
    'HOT MIC/CIPHER':    [None, None],
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
    # BMS 의 'TWA:' 버튼은 SEARCH / LOW / POWER 셋뿐입니다. 실기 4개 중
    # ACT/PWR 은 활성·전원 표시등 쪽이라 대응 콜백이 없습니다.
    # POWER 는 실제로 계통을 켜는 SYSTEM POWER 에 걸었습니다 — 패널에서
    # 반대로 동작하면 아래 두 항목을 맞바꾸십시오.
    'TWA Buttons':       [None,                      # ACT/PWR — 콜백 없음
                          'SimRWRSetSearch',         # SEARCH
                          'SimRWRSetGroundPriority',  # LOW ALTITUDE
                          'SimRwrPower'],            # SYSTEM POWER
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
    # MODE 래더 7 — 실기 MODE 노브는 6 위치(OFF·STBY·MAN·SEMI·AUTO·BYP)이고
    # 여기 쓴 로터리는 7 단이라 한 자리가 남습니다. 아래는 래더 위치 1 이
    # 노브의 반시계 끝(OFF)이라고 본 배치입니다.
    #
    # ※ 방향 확인: joy.cpl 에서 노브를 반시계 끝까지 돌려 DX 44 가 켜지면 그대로,
    #   DX 49 가 켜지면 이 여섯 줄을 뒤집고 None 을 맨 앞으로 옮기십시오.
    'CMDS MODE':         ['SimEWSModeOff', 'SimEWSModeStby', 'SimEWSModeMan',
                          'SimEWSModeSemi', 'SimEWSModeAuto', 'SimEWSModeByp',
                          None],           # 7번째 — 실기에 없는 여분 자리
    # ---- ALT GEAR ----
    'ALT GEAR Handle':   ['AFAlternateGear'],
}

MAPS = {'CONSOLE': CONSOLE, 'AUX': AUX}
