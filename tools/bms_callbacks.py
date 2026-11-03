# -*- coding: utf-8 -*-
"""Redkite 컨트롤 이름 → Falcon BMS 콜백 매핑.

DX 번호가 아니라 **컨트롤 이름**을 키로 씁니다. dxOrder[] 를 재배열해도
이 표는 그대로이고, 하드웨어를 추가할 때만 늘어납니다.

값은 그 컨트롤이 차지하는 DX 하나당 한 항목인 리스트입니다:

    None                  일부러 비워 둠 (BMS 쪽에 바인딩할 대상 자체가 없음)
    UNMODELED('검색어',…)  BMS 가 아직 모델링하지 않아 비어 있음
    'SimFoo'              모멘터리  — 누를 때 1회
    ('SimOn', 'SimOff')   유지형    — 누를 때 SimOn, 뗄 때 SimOff
    ('SimOn', None)       유지형이지만 되돌릴 콜백이 없음 (누를 때만)

`None` 과 `UNMODELED` 의 차이가 중요합니다. `None` 은 영구적입니다 — 예를 들어
커버 DX 는 DCS 개념이라 BMS 가 버전업해도 생길 리가 없습니다. `UNMODELED` 은
"지금은 없다"는 뜻이고, 괄호 안은 **그때 찾아본 검색어**입니다. 생성기가 실행할
때마다 현재 BMS 의 콜백 목록을 이 검색어로 다시 뒤져, 버전업으로 생긴 게 있으면
알려줍니다. 그러니 새 BMS 를 깔고 한 번 돌려보기만 하면 됩니다.

3단 토글은 DX 2개로 들어오고 중립이 '뗀 상태'이므로, 각 DX 를
(해당 위치, 중립 위치) 로 두면 세 위치가 모두 표현됩니다.

TODO 로 표시한 항목은 아직 확정하지 못한 것입니다 — 생성기가 따로 보고합니다.
모든 콜백은 'BMS - Full.key' 에 실재하는지 생성 시점에 검증됩니다.
"""

TODO = '!TODO'


class Unmodeled(object):
    """BMS 가 아직 모델링하지 않아 비워 둔 자리.

    patterns 는 이 자리를 비우기로 할 때 콜백 이름과 설명에서 찾아봤던
    정규식입니다. 생성기가 매번 현재 BMS 의 콜백 목록을 같은 검색어로
    다시 뒤져, 하나라도 걸리면 보고합니다 — BMS 버전업으로 지원이
    생겼는지 사람이 기억하고 있을 필요가 없습니다.
    """

    __slots__ = ('patterns',)

    def __init__(self, *patterns):
        self.patterns = patterns

    def __repr__(self):
        return 'UNMODELED(%s)' % ', '.join(repr(p) for p in self.patterns)


UNMODELED = Unmodeled

CONSOLE = {
    # ---- MPO ----
    # 실기 MPO 는 OVRD 로 눌러 쥐고 있는 스위치입니다. DX 를 -1 로 걸면
    # BMS 가 누름/뗌을 모두 받아 쥐고 있는 동안 유효합니다 — 스톡 키 파일의
    # SimTriggerFirstDetent / SimHotasPinkyShift 와 같은 모양.
    'MPO':               ['SimMPO'],
    # ---- UHF ----
    # 엔코더는 **CCW 가 먼저**입니다 — processEncoders() 가
    # encoderBtnStart[i] 를 btnCCW 로, +1 을 btnCW 로 씁니다.
    # 그래서 감소(Dec)가 앞, 증가(Inc)가 뒤입니다. 심 PC 의 기존
    # 바인딩도 전부 이 순서였습니다.
    'UHF PRESET':        ['SimDecRadioChannel', 'SimCycleRadioChannel'],
    'UHF TEST':          [UNMODELED('UHF.*TEST', 'TEST DISPLAY')],
    'UHF STATUS':        [UNMODELED('UHF.*STATUS')],
    'UHF 100MHz':        ['SimBupUhfFreq1Dec', 'SimBupUhfFreq1Inc'],
    'UHF 10MHz':         ['SimBupUhfFreq2Dec', 'SimBupUhfFreq2Inc'],
    'UHF 1MHz':          ['SimBupUhfFreq3Dec', 'SimBupUhfFreq3Inc'],
    'UHF 0.1MHz':        ['SimBupUhfFreq4Dec', 'SimBupUhfFreq4Inc'],
    'UHF 0.025MHz':      ['SimBupUhfFreq5Dec', 'SimBupUhfFreq5Inc'],
    # 로터리는 위치 순서대로 — switches[] 의 pins[] 와 같은 순서입니다
    'UHF FUNCTION':      ['SimBupUhfOff', 'SimBupUhfMain', 'SimBupUhfBoth',
                          UNMODELED('ADF')],           # BMS 에 ADF 위치 없음
    'UHF MODE':          ['SimBupUhfManual', 'SimBupUhfPreset', 'SimBupUhfGuard'],
    'UHF T-TONE':        [UNMODELED('T-TONE', 'Tone')],
    'UHF SQUELCH':       [UNMODELED('SQUELCH')],
    # ---- ENG & JET START ----
    # 뗄 때는 아무것도 보내지 않습니다. 실기 JFS 는 OFF 로 돌아오는 스프링
    # 스위치라 BMS 도 시동 명령만 받으면 되고, 놓는 순간 SimJfsStartMid 를
    # 보내면 막 시작한 시동에 OFF 를 던지는 꼴이 됩니다.
    'JFS':               [('SimJfsStartUp', None),
                          ('SimJfsStartDown', None)],
    # 커버 DX 는 DCS 전용 개념입니다. BMS 는 스위치를 올리면 커버가 알아서
    # 열리므로 버전업으로 생길 대상이 아닙니다 — UNMODELED 가 아니라 None.
    'ENG CONT COVER':    [None],
    'ENG CONT':          [('SimEngContSec', 'SimEngContPri')],  # 접점 방향 확인 필요
    'AB RESET/ENG DATA': [UNMODELED('AB RESET', 'Afterburner Reset'),
                          UNMODELED('ENG DATA', 'Engine Data')],
    'MAX POWER':         [UNMODELED('MAX POWER', 'Max Pwr')],
    # ---- AUDIO 1 ----
    'COMM1 PWR':         [('SimComm1PowerOn', 'SimComm1PowerOff')],
    'COMM2 PWR':         [('SimComm2PowerOn', 'SimComm2PowerOff')],
    'COMM1 MODE':        [UNMODELED('COMM 1 Mode.*OFF', 'Aud1Com1Off'),
                          'SimAud1Com1Sql', 'SimAud1Com1Gd'],
    'COMM2 MODE':        [UNMODELED('COMM 2 Mode.*OFF', 'Aud1Com2Off'),
                          'SimAud1Com2Sql', 'SimAud1Com2Gd'],
    # ---- AUDIO 2 ----
    # HOT MIC 도 CIPHER 도 BMS 에 콜백이 없습니다 (Mic/Cipher/Secure 전부 0건).
    # BMS 가 모델링하지 않는 스위치입니다.
    'HOT MIC/CIPHER':    [UNMODELED('HOT ?MIC'), UNMODELED('CIPHER', 'Secure Voice')],
    # ---- ECM ----
    'ECM OPR/STBY':      [('SimEcmPowerOn', None), ('SimEcmPowerOff', None)],
    'ECM XMIT':          [('SimXMit1', 'SimXMit2'), ('SimXMit3', 'SimXMit2')],
    'ECM Buttons':       ['SimEcmMode1Toggle', 'SimEcmMode2Toggle', 'SimEcmMode3Toggle',
                          'SimEcmMode4Toggle', 'SimEcmMode5Toggle',
                          UNMODELED('Ecm.*Mode ?6'), UNMODELED('ECM.*FRM'),
                          UNMODELED('ECM.*SPL')],
    'ECM RESET':         [UNMODELED('ECM.*RESET')],
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
    # 이 패널의 AVTR 토글은 OFF - ON - AUTO 순서입니다. 가운데가 ON 이라
    # 양쪽 위치를 놓으면 ON 으로 돌아옵니다 (AUTO 가 아님).
    'AVTR':              [('SimAVTRSwitchOff', 'SimAVTRSwitchOn'),
                          ('SimAVTRSwitchAuto', 'SimAVTRSwitchOn')],
}

AUX = {
    # ---- MISC ----
    # pin1(GPA4)=SILENT, pin2(GPA5)=NORM, 가운데 QUIET
    'RF':                [('SimRFSilent', 'SimRFQuiet'), ('SimRFNorm', 'SimRFQuiet')],
    'Laser ARM':         [('SimLaserArmOn', 'SimLaserArmOff')],
    'ALT REL':           [UNMODELED('ALT REL', 'Alternate Release')],
    # pin1(GPA0)=SIM, pin2(GPA1)=ARM, 가운데 OFF
    'Master ARM':        [('SimSimMasterArm', 'SimSafeMasterArm'),
                          ('SimArmMasterArm', 'SimSafeMasterArm')],
    'ADV MODE':          ['SimToggleTFR'],
    'Roll AP':           [('SimLeftAPUp', 'SimLeftAPMid'),
                          ('SimLeftAPDown', 'SimLeftAPMid')],
    'Pitch AP':          [('SimRightAPUp', 'SimRightAPMid'),
                          ('SimRightAPDown', 'SimRightAPMid')],
    # ---- GEAR ----
    'EMER Jettison':     ['SimEmergencyJettison'],
    'Hook':              [('SimHookUp', 'SimHookDown')],
    'GND JETT ENABLE':   [('SimGndJettOn', 'SimGndJettOff')],
    'BRAKES Channel':    [('SimBrakeChannelUp', 'SimBrakeChannelDown')],
    'ANTI SKID':         [('SimParkingBrakeUp', 'SimParkingBrakeMid'),
                          ('SimParkingBrakeDown', 'SimParkingBrakeMid')],
    'DN LOCK REL':       ['AFEmergencyGearHandleUnlock'],
    # 핸들에 중립이 없어 두 위치가 각각 그대로 명령입니다 — 모멘터리로 겁니다
    'Landing Gear':      ['AFGearUp', 'AFGearDown'],
    'Store CAT':         [('SimCATI', 'SimCATIII')],
    'Horn Silencer':     ['SimSilenceHorn'],
    # pin1(3)=TAXI, pin2(4)=LANDING, 가운데 OFF. pin2=UP 은 페달 브레이크
    # 모드의 PEDAL_BRAKE_SW_VALUE 1 (= pin2 활성 = landing light UP) 과도 일치합니다.
    'Landing Light':     [('SimLandingLightDown', 'SimLandingLightMid'),
                          ('SimLandingLightUp', 'SimLandingLightMid')],
    # ---- TWA (래더 4: ACT/PWR, SEARCH, ALT, SYS PWR) ----
    # BMS 의 'TWA:' 버튼은 SEARCH / LOW / POWER 셋뿐입니다. 실기 4개 중
    # ACT/PWR 은 활성·전원 표시등 쪽이라 대응 콜백이 없습니다.
    # POWER 는 실제로 계통을 켜는 SYSTEM POWER 에 걸었습니다 — 패널에서
    # 반대로 동작하면 아래 두 항목을 맞바꾸십시오.
    'TWA Buttons':       [UNMODELED('ACT/PWR', 'ACTIVITY'),   # ACT/PWR
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
    'CMDS PRGM':         [UNMODELED('PRGM.*BIT'), 'SimEWSProgOne', 'SimEWSProgTwo',
                          'SimEWSProgThree', 'SimEWSProgFour',
                          UNMODELED('ProgFive', 'PRGM Knob - 5'),
                          UNMODELED('ProgSix', 'PRGM Knob - 6')],
    # MODE 래더 7 — 실기 MODE 노브는 6 위치(OFF·STBY·MAN·SEMI·AUTO·BYP)이고
    # 여기 쓴 로터리는 7 단이라 한 자리가 남습니다. 아래는 래더 위치 1 이
    # 노브의 반시계 끝(OFF)이라고 본 배치입니다.
    #
    # ※ 방향 확인: joy.cpl 에서 노브를 반시계 끝(OFF)까지 돌려 보십시오.
    #   래더는 DX 44~50 을 씁니다. DX 44 가 켜지면 이대로 맞습니다.
    #   44 가 아니면(끝쪽 번호면) 순서가 거꾸로이니 여섯 줄을 뒤집고
    #   None 을 맨 앞으로 옮기십시오. 남는 자리가 어느 쪽 끝인지도
    #   그때 같이 드러납니다 — 어느 detent 에서 아무 DX 도 안 켜지는지 보면 됩니다.
    'CMDS MODE':         ['SimEWSModeOff', 'SimEWSModeStby', 'SimEWSModeMan',
                          'SimEWSModeSemi', 'SimEWSModeAuto', 'SimEWSModeByp',
                          None],           # 7번째 — 실기에 없는 여분 자리
    # ---- ALT GEAR ----
    'ALT GEAR Handle':   ['AFAlternateGear'],
}

MAPS = {'CONSOLE': CONSOLE, 'AUX': AUX}
