"""星號密碼顯示 — 還原本機視窗中以 ●/* 遮住的密碼框文字。

合法用途：顯示自己電腦上、自己輸入在傳統 Win32 密碼框裡的密碼
（例如某些舊軟體的登入框）。只讀取游標所指的那個控制項文字。
參考 syhyz1990/starpassword 概念，改以 Windows API 實作。

限制：只對傳統 Win32 Edit 密碼框有效；瀏覽器、UWP、Electron、
Qt 等自繪控制項讀不到（這是系統限制，非程式錯誤）。
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Dict, Optional

try:
    import win32gui
    import win32con
    import win32api
    _HAS_WIN32 = True
except Exception:  # noqa
    _HAS_WIN32 = False

user32 = ctypes.windll.user32 if hasattr(ctypes, "windll") else None

WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E
EM_SETPASSWORDCHAR = 0x00CC
WM_SETREDRAW = 0x000B


def _get_window_text(hwnd: int) -> str:
    length = user32.SendMessageW(hwnd, WM_GETTEXTLENGTH, 0, 0)
    if length <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.SendMessageW(hwnd, WM_GETTEXT, length + 1, ctypes.byref(buf))
    return buf.value


def _class_name(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def _is_password_edit(hwnd: int) -> bool:
    cls = _class_name(hwnd).lower()
    if "edit" not in cls:
        return False
    style = user32.GetWindowLongW(hwnd, win32con.GWL_STYLE if _HAS_WIN32 else -16)
    ES_PASSWORD = 0x0020
    return bool(style & ES_PASSWORD)


def reveal_at_cursor() -> Dict[str, Optional[str]]:
    """讀取目前游標所在位置的密碼框文字。"""
    if user32 is None:
        return {"ok": False, "error": "此功能僅支援 Windows"}
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    hwnd = user32.WindowFromPoint(pt)
    if not hwnd:
        return {"ok": False, "error": "游標下沒有視窗"}
    cls = _class_name(hwnd)
    is_pw = _is_password_edit(hwnd)
    # 先嘗試取消密碼遮罩字元，再讀文字（對傳統 Edit 有效）
    try:
        user32.SendMessageW(hwnd, EM_SETPASSWORDCHAR, 0, 0)
        user32.InvalidateRect(hwnd, None, True)
    except Exception:  # noqa
        pass
    text = _get_window_text(hwnd)
    if text:
        return {"ok": True, "password": text, "class": cls, "is_password_box": is_pw}
    return {
        "ok": False,
        "class": cls,
        "is_password_box": is_pw,
        "error": "讀不到文字。可能是瀏覽器／UWP／Electron 等自繪控制項，"
                 "系統層級無法讀取，請改用對應軟體自身的『顯示密碼』功能。",
    }
