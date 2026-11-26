"""壓縮檔密碼回復 — 對使用者自己的 zip / 7z / rar 做字典與暴力回復。

合法用途：找回自己忘記的壓縮檔密碼。
參考 ZongXR/Archive-password-cracker 概念，改寫並整合「成功密碼學習庫」。
"""
from __future__ import annotations

import os
import time
import zipfile
from typing import Callable, Dict, List, Optional

from . import charset as cs

try:
    import pyzipper
except Exception:  # noqa
    pyzipper = None
try:
    import py7zr
except Exception:  # noqa
    py7zr = None
try:
    import rarfile
except Exception:  # noqa
    rarfile = None


def detect_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".zip",):
        return "zip"
    if ext in (".7z",):
        return "7z"
    if ext in (".rar",):
        return "rar"
    # 以檔頭判斷
    try:
        with open(path, "rb") as f:
            head = f.read(8)
        if head[:4] == b"PK\x03\x04":
            return "zip"
        if head[:6] == b"7z\xbc\xaf\x27\x1c":
            return "7z"
        if head[:4] == b"Rar!":
            return "rar"
    except Exception:  # noqa
        pass
    return "unknown"


# ---- 各格式的「測試單一密碼」函式；成功回傳 True ----

def _make_zip_tester(path: str) -> Callable[[str], bool]:
    # 以 pyzipper 優先（支援 AES），退回標準庫 zipfile（ZipCrypto）
    opener = pyzipper.AESZipFile if pyzipper else zipfile.ZipFile
    zf = opener(path)
    names = [n for n in zf.namelist() if not n.endswith("/")]
    first = names[0] if names else None

    def test(pwd: str) -> bool:
        try:
            zf.setpassword(pwd.encode("utf-8", "ignore"))
            if first is None:
                return True
            with zf.open(first) as fp:
                fp.read(16)
            return True
        except (RuntimeError, Exception):  # noqa
            return False

    return test


def _make_7z_tester(path: str) -> Callable[[str], bool]:
    if py7zr is None:
        raise RuntimeError("未安裝 py7zr，無法處理 7z 檔")

    def test(pwd: str) -> bool:
        try:
            with py7zr.SevenZipFile(path, mode="r", password=pwd) as z:
                z.testzip()
            return True
        except Exception:  # noqa
            return False

    return test


def _make_rar_tester(path: str) -> Callable[[str], bool]:
    if rarfile is None:
        raise RuntimeError("未安裝 rarfile，無法處理 rar 檔")
    rf = rarfile.RarFile(path)
    names = [n for n in rf.namelist() if not n.endswith("/")]
    first = names[0] if names else None

    def test(pwd: str) -> bool:
        try:
            if first is None:
                return True
            with rf.open(first, pwd=pwd) as fp:
                fp.read(16)
            return True
        except Exception:  # noqa
            return False

    return test


def make_tester(path: str, kind: str) -> Callable[[str], bool]:
    if kind == "zip":
        return _make_zip_tester(path)
    if kind == "7z":
        return _make_7z_tester(path)
    if kind == "rar":
        return _make_rar_tester(path)
    raise RuntimeError(f"不支援的壓縮格式：{kind}")


def _candidate_stream(options: Dict, learned: List[str]):
    """產生候選密碼：學習庫 → 使用者字典 → 內建常用 → 暴力。"""
    seen = set()

    def emit(seq):
        for p in seq:
            if not p:
                continue
            if p in seen:
                continue
            seen.add(p)
            yield p

    mode = options.get("mode", "smart")
    # 1) 學習庫（成功密碼優先）
    if mode in ("smart", "dictionary"):
        yield from emit(learned or [])
    # 2) 使用者提供字典
    wordlist = options.get("wordlist") or []
    if isinstance(wordlist, str):
        wordlist = [w.strip() for w in wordlist.splitlines()]
    if mode in ("smart", "dictionary"):
        yield from emit(wordlist)
    # 3) 內建常用字典
    if mode == "smart":
        yield from emit(cs.COMMON_PASSWORDS)
    # 4) 暴力
    if mode in ("smart", "brute"):
        charset = cs.build_charset(options.get("charsets", []), options.get("custom_chars", ""))
        if charset:
            min_len = int(options.get("min_len", 1))
            max_len = int(options.get("max_len", 4))
            yield from emit(cs.brute_iter(charset, min_len, max_len))


def crack(
    path: str,
    options: Dict,
    learned: Optional[List[str]] = None,
    progress_cb: Optional[Callable[[Dict], None]] = None,
    should_stop: Optional[Callable[[], bool]] = None,
) -> Dict:
    """回復壓縮檔密碼。

    options: {mode, wordlist, charsets[], custom_chars, min_len, max_len}
    回傳: {found, password, kind, tried, elapsed, stopped}
    """
    kind = detect_type(path)
    tester = make_tester(path, kind)
    learned = learned or []
    start = time.time()
    tried = 0
    report_every = 200

    for pwd in _candidate_stream(options, learned):
        if should_stop and should_stop():
            return {"found": False, "password": None, "kind": kind,
                    "tried": tried, "elapsed": time.time() - start, "stopped": True}
        tried += 1
        if tester(pwd):
            return {"found": True, "password": pwd, "kind": kind,
                    "tried": tried, "elapsed": time.time() - start, "stopped": False}
        if progress_cb and tried % report_every == 0:
            progress_cb({"tried": tried, "current": pwd, "elapsed": time.time() - start})

    return {"found": False, "password": None, "kind": kind,
            "tried": tried, "elapsed": time.time() - start, "stopped": False}
