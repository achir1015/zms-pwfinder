"""資源路徑解析 — 同時支援開發模式與 PyInstaller 打包（frozen）。"""
from __future__ import annotations

import os
import sys


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def resource_root() -> str:
    """打包資源（web/、version.json）的根目錄。

    - 開發模式：專案根目錄。
    - PyInstaller onefile：sys._MEIPASS。
    - PyInstaller onedir：exe 所在目錄。
    """
    if is_frozen():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    # app/paths.py → 專案根
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def web_dir() -> str:
    return os.path.join(resource_root(), "web")


def version_path() -> str:
    return os.path.join(resource_root(), "version.json")


def icon_path(ext: str = "ico") -> str:
    return os.path.join(web_dir(), "assets", f"icon.{ext}")
