#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows 알림 영역(트레이) 아이콘. ctypes 로만 만들어 의존성이 없습니다.

    tray = Tray(icon_path, '대기 중', on_quit=stop_everything)
    tray.item('콘솔 보기', tray.toggle_console)
    tray.run()                      # 메시지 루프 — 종료할 때까지 돌아옵니다

`set_tooltip()` 은 다른 스레드에서 불러도 됩니다. 나머지는 `run()` 을 부른
스레드에서만 쓰십시오 — Win32 창은 만든 스레드에 묶입니다.
"""
import ctypes
import ctypes.wintypes as wt
import os
import sys

user32 = ctypes.WinDLL('user32', use_last_error=True)
shell32 = ctypes.WinDLL('shell32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

WM_DESTROY = 0x0002
WM_COMMAND = 0x0111
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP = 0x0205
WM_TRAY = 0x0400 + 1            # WM_APP+1 — 아이콘이 보내오는 알림
NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
NIF_MESSAGE, NIF_ICON, NIF_TIP = 0x01, 0x02, 0x04
IMAGE_ICON = 1
LR_LOADFROMFILE, LR_DEFAULTSIZE, LR_SHARED = 0x0010, 0x0040, 0x8000
MF_STRING, MF_SEPARATOR, MF_GRAYED = 0x0000, 0x0800, 0x0001
TPM_RIGHTBUTTON = 0x0002
SW_HIDE, SW_SHOW = 0, 5
CW_USEDEFAULT = -0x80000000

LRESULT = ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [('style', wt.UINT), ('lpfnWndProc', WNDPROC),
                ('cbClsExtra', ctypes.c_int), ('cbWndExtra', ctypes.c_int),
                ('hInstance', wt.HINSTANCE), ('hIcon', wt.HICON),
                ('hCursor', wt.HANDLE), ('hbrBackground', wt.HBRUSH),
                ('lpszMenuName', wt.LPCWSTR), ('lpszClassName', wt.LPCWSTR)]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [('cbSize', wt.DWORD), ('hWnd', wt.HWND), ('uID', wt.UINT),
                ('uFlags', wt.UINT), ('uCallbackMessage', wt.UINT),
                ('hIcon', wt.HICON), ('szTip', wt.WCHAR * 128),
                ('dwState', wt.DWORD), ('dwStateMask', wt.DWORD),
                ('szInfo', wt.WCHAR * 256), ('uVersion', wt.UINT),
                ('szInfoTitle', wt.WCHAR * 64), ('dwInfoFlags', wt.DWORD)]


user32.DefWindowProcW.restype = LRESULT
user32.DefWindowProcW.argtypes = (wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
user32.CreateWindowExW.restype = wt.HWND
# argtypes 를 적어 두지 않으면 ctypes 가 HINSTANCE 핸들을 int 로 보고 넘기다
# 64비트에서 넘칩니다.
user32.CreateWindowExW.argtypes = (
    wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID)
user32.LoadImageW.restype = wt.HANDLE
user32.LoadImageW.argtypes = (wt.HINSTANCE, wt.LPCWSTR, wt.UINT,
                              ctypes.c_int, ctypes.c_int, wt.UINT)
user32.LoadIconW.restype = wt.HICON
user32.LoadIconW.argtypes = (wt.HINSTANCE, wt.LPCWSTR)
user32.CreatePopupMenu.restype = wt.HMENU
user32.AppendMenuW.argtypes = (wt.HMENU, wt.UINT, ctypes.c_void_p, wt.LPCWSTR)
user32.TrackPopupMenu.argtypes = (wt.HMENU, wt.UINT, ctypes.c_int, ctypes.c_int,
                                  ctypes.c_int, wt.HWND, wt.LPVOID)
user32.PostMessageW.argtypes = (wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
user32.ShowWindow.argtypes = (wt.HWND, ctypes.c_int)
user32.IsWindowVisible.argtypes = (wt.HWND,)
user32.SetForegroundWindow.argtypes = (wt.HWND,)
user32.DestroyMenu.argtypes = (wt.HMENU,)
shell32.Shell_NotifyIconW.argtypes = (wt.DWORD, ctypes.c_void_p)
user32.GetSystemMetrics.argtypes = (ctypes.c_int,)
kernel32.GetConsoleWindow.restype = wt.HWND
kernel32.GetConsoleCP.restype = wt.UINT
kernel32.SetConsoleTitleW.argtypes = (wt.LPCWSTR,)
kernel32.GetModuleHandleW.restype = wt.HMODULE
kernel32.GetModuleHandleW.argtypes = (wt.LPCWSTR,)


def console_window():
    """이 프로세스에 붙은 콘솔 창. pythonw 로 띄웠으면 None."""
    hwnd = kernel32.GetConsoleWindow()
    return hwnd or None


def ensure_console(title=None, show=True):
    """콘솔을 마련하고 `print` 가 거기로 가게 합니다. 콘솔 창 핸들을 돌려줍니다.

    바로가기나 pythonw 로 띄우면 콘솔이 아예 없어 출력이 갈 데가 없습니다. 그때만
    새로 만들고 stdout/stderr 를 묶습니다. 이미 콘솔이 있으면 (터미널에서 실행했거나
    파이프로 묶였거나) 손대지 않습니다 — 묶어 버리면 파이프로 보내던 출력이
    콘솔로 새 버립니다.
    """
    if sys.platform != 'win32':
        return None
    # 창이 있느냐로 따지면 안 됩니다. 요즘 터미널(ConPTY)은 콘솔이 붙어 있어도
    # GetConsoleWindow() 가 0 이라, 그걸 보고 새로 만들면 이미 붙은 콘솔을 다시
    # 잡아 파이프로 가던 출력이 사라집니다. 붙어 있는지는 코드페이지로 봅니다.
    if not kernel32.GetConsoleCP():
        kernel32.AllocConsole()
        try:
            sys.stdout = open('CONOUT$', 'w', encoding='utf-8',
                              errors='backslashreplace', buffering=1)
            sys.stderr = sys.stdout
        except OSError:
            pass
    elif sys.stdout is None:                 # 콘솔은 붙었는데 핸들이 없을 때
        try:
            sys.stdout = sys.stderr = open('CONOUT$', 'w', encoding='utf-8',
                                           errors='backslashreplace', buffering=1)
        except OSError:
            sys.stdout = sys.stderr = open(os.devnull, 'w')
    if title:
        kernel32.SetConsoleTitleW(title)
    hwnd = kernel32.GetConsoleWindow()       # ConPTY 에서는 창이 없어 0 입니다
    if hwnd:
        user32.ShowWindow(hwnd, SW_SHOW if show else SW_HIDE)
    return hwnd or None


class Tray(object):
    """트레이 아이콘 하나와 그 오른쪽 클릭 메뉴."""

    FIRST_ID = 0x1000

    def __init__(self, icon_path, tooltip='', on_quit=None, title='Bridge'):
        self.icon_path = icon_path
        self.tooltip = tooltip
        self.on_quit = on_quit
        self.title = title
        self.items = []             # [(라벨, 콜백 또는 None)]
        self.hwnd = None
        self._nid = None
        self._proc = WNDPROC(self._wndproc)   # GC 되면 안 되므로 들고 있습니다
        self._console = console_window()

    # ---------------------------------------------------------- 메뉴
    def item(self, label, action=None):
        """메뉴 줄 추가. `action` 이 없으면 눌리지 않는 항목(상태 표시용)."""
        self.items.append((label, action))

    def separator(self):
        self.items.append((None, None))

    # ------------------------------------------------------ 콘솔 토글
    def toggle_console(self):
        if self._console:
            visible = user32.IsWindowVisible(self._console)
            user32.ShowWindow(self._console, SW_HIDE if visible else SW_SHOW)

    def hide_console(self):
        if self._console:
            user32.ShowWindow(self._console, SW_HIDE)

    def show_console(self):
        if self._console:
            user32.ShowWindow(self._console, SW_SHOW)

    # ---------------------------------------------------------- 표시
    def set_tooltip(self, text):
        """다른 스레드에서 불러도 됩니다 — Shell_NotifyIcon 은 스레드 안전합니다."""
        self.tooltip = text
        if self._nid is not None:
            self._nid.szTip = text[:127]
            shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self._nid))

    def stop(self):
        """메시지 루프를 끝냅니다."""
        if self.hwnd:
            user32.PostMessageW(self.hwnd, WM_DESTROY, 0, 0)

    # ---------------------------------------------------------- 내부
    def _wndproc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAY:
            if lparam in (WM_RBUTTONUP, 0x0007):      # 우클릭 / 컨텍스트 키
                self._popup()
            elif lparam == WM_LBUTTONDBLCLK:
                self.toggle_console()
            return 0
        if msg == WM_COMMAND:
            index = (wparam & 0xFFFF) - self.FIRST_ID
            if 0 <= index < len(self.items):
                action = self.items[index][1]
                if action:
                    action()
            return 0
        if msg == WM_DESTROY:
            self._remove()
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _popup(self):
        menu = user32.CreatePopupMenu()
        for i, (label, action) in enumerate(self.items):
            if label is None:
                user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
            else:
                flags = MF_STRING | (0 if action else MF_GRAYED)
                user32.AppendMenuW(menu, flags, self.FIRST_ID + i, label)
        pos = wt.POINT()
        user32.GetCursorPos(ctypes.byref(pos))
        # 메뉴 밖을 눌렀을 때 바로 닫히도록 — Win32 트레이 메뉴의 오랜 규칙입니다.
        user32.SetForegroundWindow(self.hwnd)
        user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON, pos.x, pos.y, 0, self.hwnd, None)
        user32.PostMessageW(self.hwnd, 0, 0, 0)
        user32.DestroyMenu(menu)

    def _remove(self):
        if self._nid is not None:
            shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self._nid))
            self._nid = None

    def _create(self):
        hinst = kernel32.GetModuleHandleW(None)
        cls = WNDCLASSW()
        cls.lpfnWndProc = self._proc
        cls.hInstance = hinst
        cls.lpszClassName = 'RedkiteBridgeTray'
        if not user32.RegisterClassW(ctypes.byref(cls)):
            err = ctypes.get_last_error()
            if err != 1410:                     # ERROR_CLASS_ALREADY_EXISTS
                raise ctypes.WinError(err)
        self.hwnd = user32.CreateWindowExW(
            0, cls.lpszClassName, self.title, 0,
            CW_USEDEFAULT, CW_USEDEFAULT, 0, 0, None, None, hinst, None)
        if not self.hwnd:
            raise ctypes.WinError(ctypes.get_last_error())

        hicon = None
        if self.icon_path and os.path.isfile(self.icon_path):
            hicon = user32.LoadImageW(None, self.icon_path, IMAGE_ICON, 0, 0,
                                      LR_LOADFROMFILE | LR_DEFAULTSIZE)
        if not hicon:                            # 아이콘이 없으면 기본 아이콘으로
            hicon = user32.LoadIconW(None, ctypes.c_wchar_p(32512))   # IDI_APPLICATION

        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAY
        nid.hIcon = hicon
        nid.szTip = self.tooltip[:127]
        if not shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid)):
            raise ctypes.WinError(ctypes.get_last_error())
        self._nid = nid

    def run(self):
        """아이콘을 올리고 메시지를 돌립니다. 종료될 때까지 돌아오지 않습니다."""
        if sys.platform != 'win32':
            raise SystemExit('트레이 모드는 Windows 전용입니다.')
        self._create()
        msg = wt.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            self._remove()
            if self.on_quit:
                self.on_quit()


if __name__ == '__main__':
    # 단독 실행하면 아이콘만 띄워 봅니다 (동작 확인용).
    here = os.path.dirname(os.path.abspath(__file__))
    t = Tray(os.path.join(here, 'bridge.ico'), 'Redkite Bridge — 확인용')
    t.item('상태: 확인용')
    t.separator()
    t.item('콘솔 보기/숨기기', t.toggle_console)
    t.item('종료', t.stop)
    t.run()
