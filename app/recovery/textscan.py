"""文字抓密碼 — 從自由格式文字中擷取密碼。

動機：一封郵件的加密附件，密碼卻以明文寫在另一封郵件或同一封信的內文裡，
例如「附件的密碼是 Q3Report2026z」。本模組把這些密碼抽出來。

概念參考 district-5/password-finder（自行以中英情境重寫），純標準庫。
"""
from __future__ import annotations

import re
from typing import List, Dict

# 中英文常見「密碼是 X」標籤
_LABELS = [
    r"密\s*碼", r"通\s*關\s*密\s*語", r"解\s*壓\s*密\s*碼", r"開\s*啟\s*密\s*碼",
    r"口\s*令", r"pass\s*word", r"pass\s*code", r"pass\s*phrase", r"pwd", r"pass",
    r"pin\s*碼?", r"解\s*鎖\s*碼",
]
_LABEL_RE = "(?:%s)" % "|".join(_LABELS)
# 連接詞：是 / ： / : / = / -> / 為 / 乃 / is / = 之類
_SEP = r"(?:\s*(?:是|為|乃|:|：|=|＝|->|→|為是)\s*|\s+is\s+|\s+)"

# 候選密碼字元：可見 ASCII（排除空白與常見句末標點），長度 4~64
_TOKEN = r"[!-~]{4,64}"

_PATTERN = re.compile(_LABEL_RE + _SEP + r"['\"「『<\[(（【]?(" + _TOKEN + r")", re.IGNORECASE)

# 結尾若黏到常見標點或括號，去掉
_TRIM_TAIL = re.compile(r"[\s。，、；！？」』>\])）】'\"”’.,:;!?]+$")
# 明顯不是密碼的 token（純網址、純檔名、純 email）過濾
_URL_RE = re.compile(r"^(https?://|www\.)", re.IGNORECASE)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean(tok: str) -> str:
    tok = _TRIM_TAIL.sub("", tok)
    return tok


def _looks_like_password(tok: str) -> bool:
    if len(tok) < 4:
        return False
    if _URL_RE.match(tok):
        return False
    if _EMAIL_RE.match(tok):
        return False
    # 純中文字詞通常不是密碼
    if re.fullmatch(r"[一-鿿]+", tok):
        return False
    return True


def extract(text: str) -> List[Dict[str, str]]:
    """從文字中擷取候選密碼，回傳 [{password, context}] 依出現順序、去重。"""
    if not text:
        return []
    results: List[Dict[str, str]] = []
    seen = set()
    for m in _PATTERN.finditer(text):
        tok = _clean(m.group(1))
        if not _looks_like_password(tok):
            continue
        if tok in seen:
            continue
        seen.add(tok)
        start = max(0, m.start() - 20)
        end = min(len(text), m.end() + 10)
        context = text[start:end].replace("\n", " ").strip()
        results.append({"password": tok, "context": context})
    return results
