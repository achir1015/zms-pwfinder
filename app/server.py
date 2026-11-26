"""資料助秘 密碼查找器 — 本機後端 API（Flask + waitress）。

桌面版：pywebview 連到 http://127.0.0.1:PORT。
線上/手機版：同一份 web/ 部署到 Pages，改用 web/js/local.js 的純前端退路。
"""
from __future__ import annotations

import os
import sys
import threading
import time
import uuid
from typing import Dict

from flask import Flask, jsonify, request, send_from_directory

# 允許以 `python app/server.py` 或被 main.py 匯入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db  # noqa: E402
from app import paths  # noqa: E402
from app.recovery import wifi, textscan, archive, office, star, mail  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = paths.web_dir()
PORT = 47851  # 本工具本機埠（避開其他小柯/資料助秘工具）

app = Flask(__name__, static_folder=None)

# ---------------- 背景破解工作管理 ----------------
JOBS: Dict[str, Dict] = {}
_jobs_lock = threading.Lock()


def _new_job() -> str:
    jid = uuid.uuid4().hex[:12]
    with _jobs_lock:
        JOBS[jid] = {"status": "running", "tried": 0, "current": "", "elapsed": 0,
                     "found": False, "password": None, "stop": False, "created": time.time()}
    return jid


def _run_crack(jid: str, kind: str, path: str, options: Dict):
    module = "archive" if kind == "archive" else "office"
    try:
        learned = db.get_learned(module=module, limit=1000)

        def progress(info):
            with _jobs_lock:
                j = JOBS.get(jid)
                if j:
                    j.update(tried=info["tried"], current=info["current"],
                             elapsed=info["elapsed"])

        def should_stop():
            with _jobs_lock:
                return JOBS.get(jid, {}).get("stop", False)

        runner = archive.crack if kind == "archive" else office.crack
        result = runner(path, options, learned=learned,
                        progress_cb=progress, should_stop=should_stop)
        # 成功 → 寫入學習庫，增加下次命中率
        if result.get("found") and result.get("password"):
            db.learn_success(result["password"], module, result.get("kind", ""))
        with _jobs_lock:
            j = JOBS.get(jid, {})
            j.update(status="stopped" if result.get("stopped") else "done",
                     found=result.get("found", False), password=result.get("password"),
                     tried=result.get("tried", 0), elapsed=result.get("elapsed", 0),
                     file_kind=result.get("kind", ""), note=result.get("note", ""))
    except Exception as e:  # noqa
        with _jobs_lock:
            j = JOBS.get(jid, {})
            j.update(status="error", error=str(e))


# ---------------- 靜態檔 ----------------

@app.route("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.route("/<path:p>")
def static_files(p):
    full = os.path.join(WEB_DIR, p)
    if os.path.isfile(full):
        d, fn = os.path.split(full)
        return send_from_directory(d, fn)
    return send_from_directory(WEB_DIR, "index.html")


# ---------------- API：WiFi ----------------

@app.route("/api/wifi/list")
def api_wifi():
    return jsonify({"ok": True, "items": wifi.all_passwords()})


# ---------------- API：文字抓密碼 ----------------

@app.route("/api/text/extract", methods=["POST"])
def api_text():
    data = request.get_json(force=True, silent=True) or {}
    return jsonify({"ok": True, "items": textscan.extract(data.get("text", ""))})


# ---------------- API：星號密碼 ----------------

@app.route("/api/star/reveal")
def api_star():
    return jsonify(star.reveal_at_cursor())


# ---------------- API：郵件密碼 ----------------

@app.route("/api/mail/list")
def api_mail():
    return jsonify({"ok": True, **mail.all_mail_passwords()})


# ---------------- API：壓縮檔 / Office 破解 ----------------

@app.route("/api/crack/start", methods=["POST"])
def api_crack_start():
    data = request.get_json(force=True, silent=True) or {}
    path = data.get("path", "")
    if not path or not os.path.isfile(path):
        return jsonify({"ok": False, "error": "找不到檔案，請確認路徑"})
    kind = data.get("target")  # 'archive' | 'office'
    if kind not in ("archive", "office"):
        # 自動依副檔名判斷
        ext = os.path.splitext(path)[1].lower()
        kind = "office" if ext in (".doc", ".docx", ".docm", ".xls", ".xlsx",
                                    ".xlsm", ".ppt", ".pptx", ".pptm") else "archive"
    options = data.get("options", {}) or {}
    jid = _new_job()
    t = threading.Thread(target=_run_crack, args=(jid, kind, path, options), daemon=True)
    t.start()
    return jsonify({"ok": True, "job": jid, "kind": kind})


@app.route("/api/crack/status/<jid>")
def api_crack_status(jid):
    with _jobs_lock:
        j = JOBS.get(jid)
        if not j:
            return jsonify({"ok": False, "error": "工作不存在"})
        return jsonify({"ok": True, **{k: v for k, v in j.items() if k != "stop"}})


@app.route("/api/crack/stop/<jid>", methods=["POST"])
def api_crack_stop(jid):
    with _jobs_lock:
        j = JOBS.get(jid)
        if j:
            j["stop"] = True
    return jsonify({"ok": True})


# ---------------- API：學習庫 / 資料庫 ----------------

@app.route("/api/learn/stats")
def api_learn_stats():
    return jsonify({"ok": True, **db.learned_stats()})


@app.route("/api/db/config", methods=["GET", "POST"])
def api_db_config():
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        cfg = db.load_config()
        cfg.setdefault("db", {}).update(data.get("db", {}))
        db.save_config(cfg)
        return jsonify({"ok": True, **db.test_db()})
    cfg = db.load_config()
    # 不回傳密碼明文
    safe = dict(cfg["db"])
    safe["password"] = "***" if safe.get("password") else ""
    return jsonify({"ok": True, "db": safe})


@app.route("/api/db/test")
def api_db_test():
    return jsonify(db.test_db())


# ---------------- API：版本 ----------------

@app.route("/api/version")
def api_version():
    import json
    vp = paths.version_path()
    try:
        with open(vp, "r", encoding="utf-8") as f:
            return jsonify({"ok": True, **json.load(f)})
    except Exception:  # noqa
        return jsonify({"ok": True, "version": "0.0.0"})


def serve(port: int = PORT, use_waitress: bool = True):
    if use_waitress:
        from waitress import serve as wserve
        wserve(app, host="127.0.0.1", port=port, threads=8)
    else:
        app.run(host="127.0.0.1", port=port, threaded=True)


if __name__ == "__main__":
    print(f"資料助秘 密碼查找器 後端啟動：http://127.0.0.1:{PORT}")
    serve()
