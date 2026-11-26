"""暴力破解字元集與候選產生器（壓縮檔、Office 共用）。"""
from __future__ import annotations

import itertools
from typing import Iterator, List

CHARSETS = {
    "digits": "0123456789",
    "lower": "abcdefghijklmnopqrstuvwxyz",
    "upper": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "symbols": "!@#$%^&*()-_=+",
}


def build_charset(keys: List[str], custom: str = "") -> str:
    s = ""
    for k in keys or []:
        s += CHARSETS.get(k, "")
    s += custom or ""
    # 去重保序
    seen = set()
    out = []
    for c in s:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return "".join(out)


def brute_iter(charset: str, min_len: int, max_len: int) -> Iterator[str]:
    """依長度遞增產生所有組合。"""
    if not charset:
        return
    for length in range(max(1, min_len), max(1, max_len) + 1):
        for combo in itertools.product(charset, repeat=length):
            yield "".join(combo)


def brute_count(charset_size: int, min_len: int, max_len: int) -> int:
    total = 0
    for length in range(max(1, min_len), max(1, max_len) + 1):
        total += charset_size ** length
    return total


# 內建常用密碼小字典（補充使用者字典與學習庫之外的保底）
COMMON_PASSWORDS: List[str] = [
    "123456", "123456789", "12345678", "1234567890", "password", "qwerty",
    "111111", "000000", "888888", "123123", "abc123", "a123456", "1qaz2wsx",
    "iloveyou", "admin", "root", "123321", "520520", "5201314", "7758521",
    "woaini", "woaini1314", "aaaaaa", "qwerty123", "666666", "zxcvbnm",
    "1q2w3e4r", "password1", "P@ssw0rd", "Passw0rd", "test123", "abcd1234",
]
