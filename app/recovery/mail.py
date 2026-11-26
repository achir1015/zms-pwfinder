"""郵件密碼回復 — 還原本機郵件軟體「已儲存」的帳號密碼。

合法用途：找回自己電腦上 Thunderbird / Outlook 等軟體已經替你記住的
郵件帳號密碼。全程在本機，只讀自己的設定檔，不連線、不猜測他人信箱。

重要：本模組「不會」也「不能」去線上破解或噴灑任何郵件伺服器——那是攻擊
他人帳號，不在本工具範圍內。
"""
from __future__ import annotations

import base64
import ctypes
import glob
import json
import os
from ctypes import c_void_p, c_char_p, c_int, Structure, POINTER, byref
from typing import Dict, List, Optional


# ---------------- Thunderbird（NSS 解密） ----------------

class _SECItem(Structure):
    _fields_ = [("type", c_int), ("data", c_void_p), ("len", c_int)]


def _find_thunderbird_profiles() -> List[str]:
    base = os.path.join(os.environ.get("APPDATA", ""), "Thunderbird", "Profiles")
    if not os.path.isdir(base):
        return []
    profiles = []
    for d in glob.glob(os.path.join(base, "*")):
        if os.path.isfile(os.path.join(d, "logins.json")):
            profiles.append(d)
    return profiles


def _find_nss_dll() -> Optional[str]:
    candidates = []
    for root in (
        r"C:\Program Files\Mozilla Thunderbird",
        r"C:\Program Files (x86)\Mozilla Thunderbird",
        r"C:\Program Files\Mozilla Firefox",
        r"C:\Program Files (x86)\Mozilla Firefox",
    ):
        candidates.append(os.path.join(root, "nss3.dll"))
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def _decrypt_thunderbird(profile_dir: str, nss_path: str) -> List[Dict[str, str]]:
    """以 NSS 解密某個設定檔的 logins.json。需 profile 無主密碼或空主密碼。"""
    dll_dir = os.path.dirname(nss_path)
    old_cwd = os.getcwd()
    results: List[Dict[str, str]] = []
    try:
        os.chdir(dll_dir)  # 讓相依 dll 可被載入
        nss = ctypes.CDLL(nss_path)
        if nss.NSS_Init(profile_dir.encode("utf-8")) != 0:
            return [{"error": f"NSS_Init 失敗：{profile_dir}"}]
        try:
            with open(os.path.join(profile_dir, "logins.json"), "r", encoding="utf-8") as f:
                data = json.load(f)
            for entry in data.get("logins", []):
                host = entry.get("hostname", "")
                user = _pk11_decrypt(nss, entry.get("encryptedUsername", ""))
                pwd = _pk11_decrypt(nss, entry.get("encryptedPassword", ""))
                results.append({"source": "Thunderbird", "host": host,
                                "username": user, "password": pwd})
        finally:
            nss.NSS_Shutdown()
    except Exception as e:  # noqa
        results.append({"error": f"Thunderbird 解密例外：{e}"})
    finally:
        os.chdir(old_cwd)
    return results


def _pk11_decrypt(nss, b64: str) -> str:
    if not b64:
        return ""
    try:
        raw = base64.b64decode(b64)
        inp = _SECItem(0, ctypes.cast(ctypes.create_string_buffer(raw, len(raw)), c_void_p), len(raw))
        out = _SECItem(0, None, 0)
        nss.PK11SDR_Decrypt.argtypes = [POINTER(_SECItem), POINTER(_SECItem), c_void_p]
        if nss.PK11SDR_Decrypt(byref(inp), byref(out), None) != 0:
            return "(需主密碼或解密失敗)"
        if out.len == 0 or not out.data:
            return ""
        return ctypes.string_at(out.data, out.len).decode("utf-8", "ignore")
    except Exception:  # noqa
        return "(解密失敗)"


def thunderbird_passwords() -> List[Dict[str, str]]:
    profiles = _find_thunderbird_profiles()
    if not profiles:
        return []
    nss = _find_nss_dll()
    if not nss:
        return [{"error": "找到 Thunderbird 設定檔，但找不到 nss3.dll；"
                          "請確認已安裝 Thunderbird 或 Firefox。"}]
    out = []
    for p in profiles:
        out.extend(_decrypt_thunderbird(p, nss))
    return out


# ---------------- Outlook（DPAPI） ----------------

def _dpapi_unprotect(blob: bytes) -> Optional[bytes]:
    class DATA_BLOB(Structure):
        _fields_ = [("cbData", ctypes.c_ulong), ("pbData", POINTER(ctypes.c_char))]

    buf_in = DATA_BLOB(len(blob), ctypes.cast(ctypes.create_string_buffer(blob, len(blob)),
                                              POINTER(ctypes.c_char)))
    buf_out = DATA_BLOB()
    if ctypes.windll.crypt32.CryptUnprotectData(
        byref(buf_in), None, None, None, None, 0, byref(buf_out)
    ):
        data = ctypes.string_at(buf_out.pbData, buf_out.cbData)
        ctypes.windll.kernel32.LocalFree(buf_out.pbData)
        return data
    return None


def outlook_accounts() -> List[Dict[str, str]]:
    """列出 Outlook 帳號；新版 Outlook 多半不再以可還原形式存密碼，
    僅能列出帳號與（若有）可 DPAPI 還原的舊式密碼。"""
    results: List[Dict[str, str]] = []
    try:
        import winreg
    except Exception:  # noqa
        return results
    roots = [
        r"Software\Microsoft\Office\16.0\Outlook\Profiles",
        r"Software\Microsoft\Office\15.0\Outlook\Profiles",
        r"Software\Microsoft\Windows NT\CurrentVersion\Windows Messaging Subsystem\Profiles",
    ]
    for root in roots:
        try:
            _walk_outlook(winreg, winreg.HKEY_CURRENT_USER, root, results)
        except Exception:  # noqa
            continue
    return results


def _walk_outlook(winreg, hive, path, results):
    try:
        key = winreg.OpenKey(hive, path)
    except Exception:  # noqa
        return
    try:
        i = 0
        while True:
            try:
                sub = winreg.EnumKey(key, i)
            except OSError:
                break
            i += 1
            subpath = path + "\\" + sub
            # 讀取可能的帳號/密碼欄位
            try:
                sk = winreg.OpenKey(hive, subpath)
                acct = _read_val(winreg, sk, "Email") or _read_val(winreg, sk, "Account Name")
                pw_blob = _read_blob(winreg, sk, "Password")
                if acct or pw_blob:
                    pwd = ""
                    if pw_blob:
                        dec = _dpapi_unprotect(pw_blob)
                        if dec:
                            pwd = dec.replace(b"\x00", b"").decode("utf-8", "ignore")
                    results.append({"source": "Outlook", "account": acct or sub, "password": pwd})
                winreg.CloseKey(sk)
            except Exception:  # noqa
                pass
            _walk_outlook(winreg, hive, subpath, results)
    finally:
        winreg.CloseKey(key)


def _read_val(winreg, key, name):
    try:
        v, _ = winreg.QueryValueEx(key, name)
        if isinstance(v, bytes):
            return v.replace(b"\x00", b"").decode("utf-8", "ignore")
        return str(v)
    except Exception:  # noqa
        return ""


def _read_blob(winreg, key, name):
    try:
        v, t = winreg.QueryValueEx(key, name)
        if isinstance(v, bytes):
            return v
    except Exception:  # noqa
        pass
    return None


def all_mail_passwords() -> Dict[str, List[Dict[str, str]]]:
    return {
        "thunderbird": thunderbird_passwords(),
        "outlook": outlook_accounts(),
    }
