"""WiFi 密碼 — 顯示本機「已儲存」的無線網路密碼。

只讀取這台電腦自己記住的 WiFi 設定檔（netsh wlan show profile key=clear），
等同 Windows 設定裡本來就看得到的資訊，屬於合法的本機密碼回復。
參考 sdushantha/wifi-password 的概念，改以 Windows netsh 實作。
"""
from __future__ import annotations

import re
import subprocess
from typing import List, Dict

# netsh 輸出會依系統語言不同，中英文欄位都比對
# 繁中 Windows：金鑰內容 / 所有使用者設定檔 / 驗證
_PROFILE_KEYS = ["所有使用者設定檔", "使用者設定檔", "All User Profile", "User Profile"]
_KEY_KEYS = ["金鑰內容", "關鍵內容", "Key Content"]
_AUTH_KEYS = ["驗證", "Authentication"]
_SECURITY_KEYS = ["安全金鑰", "Security key"]


def _run(args: List[str]) -> str:
    try:
        out = subprocess.run(
            args, capture_output=True, timeout=20,
            creationflags=0x08000000,  # CREATE_NO_WINDOW
        )
        # netsh 中文輸出為系統 OEM 編碼；繁中=cp950、簡中=cp936，再退 utf-8
        for enc in ("cp950", "cp936", "mbcs", "utf-8"):
            try:
                return out.stdout.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return out.stdout.decode("utf-8", "ignore")
    except Exception:  # noqa
        return ""


def _grab(block: str, keys: List[str]) -> str:
    for k in keys:
        m = re.search(re.escape(k) + r"\s*[:：]\s*(.+)", block)
        if m:
            return m.group(1).strip()
    return ""


def list_profiles() -> List[str]:
    out = _run(["netsh", "wlan", "show", "profiles"])
    names = []
    for line in out.splitlines():
        v = _grab(line, _PROFILE_KEYS)
        if v:
            names.append(v)
    return names


def get_password(profile: str) -> Dict[str, str]:
    out = _run(["netsh", "wlan", "show", "profile", f"name={profile}", "key=clear"])
    pwd = _grab(out, _KEY_KEYS)
    sec = _grab(out, _SECURITY_KEYS)  # 不存在=開放網路
    if not pwd and (sec in ("不存在", "Absent", "")):
        pwd_display = "（開放網路／無密碼）"
    else:
        pwd_display = pwd
    return {
        "ssid": profile,
        "password": pwd_display,
        "auth": _grab(out, _AUTH_KEYS),
    }


def all_passwords() -> List[Dict[str, str]]:
    """回傳所有已儲存 WiFi 的 SSID 與密碼。"""
    result = []
    for name in list_profiles():
        info = get_password(name)
        result.append(info)
    return result
