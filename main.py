"""資料助秘 密碼查找器 — 桌面版入口（Windows 11 優先）。

啟動本機後端（Flask/waitress），再以 pywebview 開一個視窗連到它。
打開即用、關閉即停（符合使用慣例：不用命令列、給一般人用）。
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import urllib.request
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from app.server import serve, PORT  # noqa: E402
from app import paths  # noqa: E402

APP_TITLE = "資料助秘 密碼查找器"


def _version_info() -> dict:
    try:
        with open(paths.version_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa
        return {"version": "0.0.0"}


class Api:
    """pywebview 暴露給前端的原生能力。"""

    def pick_file(self):
        try:
            import webview
            win = webview.windows[0]
            result = win.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False)
            if result:
                return result[0]
        except Exception as e:  # noqa
            print("pick_file error:", e)
        return ""

    def check_update(self):
        """對照 GitHub Releases 的 version.json 判斷是否有新版。"""
        info = _version_info()
        repo = info.get("github_repo", "")
        cur = info.get("version", "0.0.0")
        if not repo:
            return {"has_update": False, "current": cur}
        url = f"https://raw.githubusercontent.com/{repo}/main/version.json"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "pwfinder-updater"})
            with urllib.request.urlopen(req, timeout=8) as r:
                remote = json.loads(r.read().decode("utf-8"))
            latest = remote.get("version", cur)
            if _newer(latest, cur):
                rel = f"https://github.com/{repo}/releases/latest"
                webbrowser.open(rel)
                return {"has_update": True, "latest": latest, "current": cur, "release": rel}
            return {"has_update": False, "latest": latest, "current": cur}
        except Exception as e:  # noqa
            return {"has_update": False, "current": cur, "error": str(e)}


def _newer(a: str, b: str) -> bool:
    def parse(v):
        return [int(x) for x in str(v).split(".") if x.isdigit()]
    pa, pb = parse(a), parse(b)
    pa += [0] * (3 - len(pa)); pb += [0] * (3 - len(pb))
    return pa > pb


def _start_backend():
    serve(port=PORT, use_waitress=True)


def main():
    # 背景起後端
    th = threading.Thread(target=_start_backend, daemon=True)
    th.start()
    # 等待後端就緒
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/version", timeout=1)
            break
        except Exception:  # noqa
            time.sleep(0.1)

    import webview
    icon = paths.icon_path("png")
    webview.create_window(
        f"{APP_TITLE} v{_version_info().get('version', '')}",
        f"http://127.0.0.1:{PORT}/",
        js_api=Api(),
        width=960, height=720, min_size=(760, 560),
    )
    webview.start(
        icon=icon if os.path.isfile(icon) else None,
    )
    # 視窗關閉 → 程式結束，daemon 後端隨之停止（符合「關閉即停止」）
    os._exit(0)


if __name__ == "__main__":
    main()
