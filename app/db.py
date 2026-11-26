"""資料庫層 — 成功密碼學習庫 + 使用者權限。

設計原則（符合「打開就能用、不要命令列」）：
- 預設用本機 JSON 檔當學習庫，零設定即可運作。
- 若在設定裡填了 MariaDB 連線（企業／多人共用、沿用資料助秘的帳號機制），
  就改用 MariaDB，並自動建表。學習庫資料表：learned_passwords。
- 使用者權限沿用資料助秘系列概念（users / 權限欄位），僅在接 MariaDB 時啟用。

「成功的方法要記錄在資料庫，增加成功機率」：每次破解成功就寫入一筆
（密碼、模組、檔案類型、長度、字元特徵），下次破解時依「命中次數」排序
把學過的密碼排在最前面優先嘗試。
"""
from __future__ import annotations

import json
import os
import threading
import time
from typing import Dict, List, Optional

APP_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                       "資料助秘密碼查找器")
os.makedirs(APP_DIR, exist_ok=True)
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
LEARNED_JSON = os.path.join(APP_DIR, "learned.json")

_lock = threading.Lock()

# MariaDB 預設連線（沿用資料助秘系列；DB 埠 3558，本工具專用資料庫）
DEFAULT_DB = {
    "enabled": False,
    "host": "127.0.0.1",
    "port": 3558,
    "user": "root",
    "password": "",
    "database": "zms_pwfinder",
}


def load_config() -> Dict:
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:  # noqa
            cfg = {}
    else:
        cfg = {}
    db = dict(DEFAULT_DB)
    db.update(cfg.get("db", {}))
    cfg["db"] = db
    return cfg


def save_config(cfg: Dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ---------------- MariaDB 後端 ----------------

def _db_conn():
    cfg = load_config()["db"]
    if not cfg.get("enabled"):
        return None
    try:
        import pymysql
        conn = pymysql.connect(
            host=cfg["host"], port=int(cfg["port"]), user=cfg["user"],
            password=cfg["password"], charset="utf8mb4", autocommit=True,
        )
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{cfg['database']}` "
                        "CHARACTER SET utf8mb4")
            cur.execute(f"USE `{cfg['database']}`")
            cur.execute(_SCHEMA_LEARNED)
            cur.execute(_SCHEMA_USERS)
        return conn
    except Exception as e:  # noqa
        print("[db] MariaDB 連線失敗，改用本機 JSON：", e)
        return None


_SCHEMA_LEARNED = """
CREATE TABLE IF NOT EXISTS learned_passwords (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    module VARCHAR(32) NOT NULL,
    file_kind VARCHAR(32) DEFAULT '',
    length INT DEFAULT 0,
    has_digit TINYINT DEFAULT 0,
    has_lower TINYINT DEFAULT 0,
    has_upper TINYINT DEFAULT 0,
    has_symbol TINYINT DEFAULT 0,
    hits INT DEFAULT 1,
    last_used DOUBLE DEFAULT 0,
    created DOUBLE DEFAULT 0,
    UNIQUE KEY uq_pw_mod (password, module)
) CHARACTER SET utf8mb4;
"""

_SCHEMA_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    display_name VARCHAR(64) DEFAULT '',
    role VARCHAR(16) DEFAULT 'user',
    can_wifi TINYINT DEFAULT 1,
    can_archive TINYINT DEFAULT 1,
    can_office TINYINT DEFAULT 1,
    can_mail TINYINT DEFAULT 1,
    can_star TINYINT DEFAULT 1,
    enabled TINYINT DEFAULT 1,
    created DOUBLE DEFAULT 0
) CHARACTER SET utf8mb4;
"""


# ---------------- 密碼特徵 ----------------

def _features(pw: str) -> Dict[str, int]:
    return {
        "length": len(pw),
        "has_digit": int(any(c.isdigit() for c in pw)),
        "has_lower": int(any(c.islower() for c in pw)),
        "has_upper": int(any(c.isupper() for c in pw)),
        "has_symbol": int(any(not c.isalnum() for c in pw)),
    }


# ---------------- 學習庫：寫入成功密碼 ----------------

def learn_success(password: str, module: str, file_kind: str = "") -> None:
    if not password:
        return
    now = time.time()
    feat = _features(password)
    conn = _db_conn()
    if conn is not None:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO learned_passwords "
                    "(password, module, file_kind, length, has_digit, has_lower, "
                    " has_upper, has_symbol, hits, last_used, created) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1,%s,%s) "
                    "ON DUPLICATE KEY UPDATE hits=hits+1, last_used=%s, "
                    " file_kind=VALUES(file_kind)",
                    (password, module, file_kind, feat["length"], feat["has_digit"],
                     feat["has_lower"], feat["has_upper"], feat["has_symbol"], now, now, now),
                )
            conn.close()
            return
        except Exception as e:  # noqa
            print("[db] 寫入學習庫失敗，改用 JSON：", e)
    # JSON 後端
    with _lock:
        store = _load_json()
        key = f"{module}::{password}"
        rec = store.get(key)
        if rec:
            rec["hits"] += 1
            rec["last_used"] = now
            rec["file_kind"] = file_kind or rec.get("file_kind", "")
        else:
            store[key] = {"password": password, "module": module, "file_kind": file_kind,
                          "hits": 1, "last_used": now, "created": now, **feat}
        _save_json(store)


# ---------------- 學習庫：取出優先嘗試清單 ----------------

def get_learned(module: Optional[str] = None, limit: int = 500) -> List[str]:
    """回傳依『命中次數、最近使用』排序的學過密碼，供下次破解優先嘗試。"""
    conn = _db_conn()
    if conn is not None:
        try:
            with conn.cursor() as cur:
                if module:
                    cur.execute(
                        "SELECT password FROM learned_passwords WHERE module=%s "
                        "ORDER BY hits DESC, last_used DESC LIMIT %s", (module, limit))
                else:
                    cur.execute(
                        "SELECT password FROM learned_passwords "
                        "ORDER BY hits DESC, last_used DESC LIMIT %s", (limit,))
                rows = [r[0] for r in cur.fetchall()]
            conn.close()
            return rows
        except Exception as e:  # noqa
            print("[db] 讀學習庫失敗，改用 JSON：", e)
    with _lock:
        store = _load_json()
    recs = [v for v in store.values() if (module is None or v.get("module") == module)]
    recs.sort(key=lambda r: (r.get("hits", 0), r.get("last_used", 0)), reverse=True)
    return [r["password"] for r in recs[:limit]]


def learned_stats() -> Dict:
    conn = _db_conn()
    if conn is not None:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT module, COUNT(*), SUM(hits) FROM learned_passwords "
                            "GROUP BY module")
                rows = cur.fetchall()
            conn.close()
            return {"backend": "MariaDB",
                    "by_module": [{"module": r[0], "count": r[1], "hits": int(r[2] or 0)}
                                  for r in rows]}
        except Exception:  # noqa
            pass
    with _lock:
        store = _load_json()
    by = {}
    for v in store.values():
        m = v.get("module", "?")
        by.setdefault(m, {"module": m, "count": 0, "hits": 0})
        by[m]["count"] += 1
        by[m]["hits"] += v.get("hits", 0)
    return {"backend": "本機 JSON", "by_module": list(by.values())}


def _load_json() -> Dict:
    if os.path.isfile(LEARNED_JSON):
        try:
            with open(LEARNED_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa
            return {}
    return {}


def _save_json(store: Dict) -> None:
    tmp = LEARNED_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)
    os.replace(tmp, LEARNED_JSON)


def test_db() -> Dict:
    """測試 MariaDB 連線是否可用。"""
    cfg = load_config()["db"]
    if not cfg.get("enabled"):
        return {"ok": False, "backend": "本機 JSON", "message": "未啟用 MariaDB，使用本機學習庫"}
    conn = _db_conn()
    if conn is None:
        return {"ok": False, "backend": "本機 JSON", "message": "MariaDB 連線失敗，已退回本機學習庫"}
    conn.close()
    return {"ok": True, "backend": "MariaDB",
            "message": f"已連線 {cfg['host']}:{cfg['port']}/{cfg['database']}"}
