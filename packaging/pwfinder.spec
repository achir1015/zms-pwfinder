# -*- mode: python ; coding: utf-8 -*-
# 資料助秘 密碼查找器 — 跨平台打包（PyInstaller，onedir）
# Windows / macOS 皆用此 spec： pyinstaller packaging/pwfinder.spec
import os
import sys

ROOT = os.path.abspath(os.getcwd())
IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform == "win32"

# 圖示：Windows 用 .ico、macOS 用 .icns（CI 會先產生 icns）
icon_file = None
if IS_WIN and os.path.exists(os.path.join(ROOT, "web", "assets", "icon.ico")):
    icon_file = os.path.join(ROOT, "web", "assets", "icon.ico")
elif IS_MAC and os.path.exists(os.path.join(ROOT, "web", "assets", "icon.icns")):
    icon_file = os.path.join(ROOT, "web", "assets", "icon.icns")

hidden = ['msoffcrypto', 'pyzipper', 'py7zr', 'rarfile', 'pymysql', 'waitress', 'flask']
if IS_WIN:
    hidden += ['win32gui', 'win32con', 'win32api', 'win32timezone']

a = Analysis(
    [os.path.join(ROOT, 'main.py')],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(ROOT, 'web'), 'web'),
        (os.path.join(ROOT, 'version.json'), '.'),
    ],
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=['edge_tts', 'tkinter', 'matplotlib', 'PIL'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='資料助秘密碼查找器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='資料助秘密碼查找器',
)

if IS_MAC:
    app = BUNDLE(
        coll,
        name='資料助秘密碼查找器.app',
        icon=icon_file,
        bundle_identifier='com.zms.pwfinder',
        info_plist={
            'CFBundleName': '資料助秘密碼查找器',
            'CFBundleDisplayName': '資料助秘 密碼查找器',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
        },
    )
