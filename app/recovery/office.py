"""Office 文件密碼回復 — Word / Excel / PowerPoint。

合法用途：找回自己忘記的 .docx/.xlsx/.pptx（及舊版 .doc/.xls/.ppt）開啟密碼。
以 msoffcrypto-tool 驗證密碼，整合「成功密碼學習庫」。
"""
from __future__ import annotations

import os
import time
from typing import Callable, Dict, List, Optional

from . import charset as cs

try:
    import msoffcrypto
except Exception:  # noqa
    msoffcrypto = None


def detect_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".docx", ".docm", ".doc"):
        return "word"
    if ext in (".xlsx", ".xlsm", ".xls"):
        return "excel"
    if ext in (".pptx", ".pptm", ".ppt"):
        return "ppt"
    return "office"


def is_encrypted(path: str) -> bool:
    if msoffcrypto is None:
        return False
    try:
        with open(path, "rb") as f:
            of = msoffcrypto.OfficeFile(f)
            return of.is_encrypted()
    except Exception:  # noqa
        return False


def make_tester(path: str) -> Callable[[str], bool]:
    if msoffcrypto is None:
        raise RuntimeError("未安裝 msoffcrypto-tool，無法處理 Office 檔")
    # 先把檔案讀進記憶體，避免每次開檔
    with open(path, "rb") as f:
        data = f.read()
    import io

    def test(pwd: str) -> bool:
        try:
            of = msoffcrypto.OfficeFile(io.BytesIO(data))
            of.load_key(password=pwd)
            of.decrypt(io.BytesIO())  # 僅驗證，不寫出
            return True
        except Exception:  # noqa
            return False

    return test


def _candidate_stream(options: Dict, learned: List[str]):
    seen = set()

    def emit(seq):
        for p in seq:
            if not p or p in seen:
                continue
            seen.add(p)
            yield p

    mode = options.get("mode", "smart")
    if mode in ("smart", "dictionary"):
        yield from emit(learned or [])
    wordlist = options.get("wordlist") or []
    if isinstance(wordlist, str):
        wordlist = [w.strip() for w in wordlist.splitlines()]
    if mode in ("smart", "dictionary"):
        yield from emit(wordlist)
    if mode == "smart":
        yield from emit(cs.COMMON_PASSWORDS)
    if mode in ("smart", "brute"):
        charset = cs.build_charset(options.get("charsets", []), options.get("custom_chars", ""))
        if charset:
            yield from emit(cs.brute_iter(
                charset, int(options.get("min_len", 1)), int(options.get("max_len", 4))))


def crack(
    path: str,
    options: Dict,
    learned: Optional[List[str]] = None,
    progress_cb: Optional[Callable[[Dict], None]] = None,
    should_stop: Optional[Callable[[], bool]] = None,
) -> Dict:
    kind = detect_type(path)
    if not is_encrypted(path):
        return {"found": True, "password": "", "kind": kind, "tried": 0,
                "elapsed": 0, "stopped": False, "note": "此檔未加密，可直接開啟"}
    tester = make_tester(path)
    learned = learned or []
    start = time.time()
    tried = 0
    for pwd in _candidate_stream(options, learned):
        if should_stop and should_stop():
            return {"found": False, "password": None, "kind": kind,
                    "tried": tried, "elapsed": time.time() - start, "stopped": True}
        tried += 1
        if tester(pwd):
            return {"found": True, "password": pwd, "kind": kind,
                    "tried": tried, "elapsed": time.time() - start, "stopped": False}
        if progress_cb and tried % 100 == 0:
            progress_cb({"tried": tried, "current": pwd, "elapsed": time.time() - start})
    return {"found": False, "password": None, "kind": kind,
            "tried": tried, "elapsed": time.time() - start, "stopped": False}
