# -*- mode: python ; coding: utf-8 -*-
# 資料助秘 密碼查找器 — Windows 打包設定（PyInstaller，onedir）
# 用法（在專案根目錄）： pyinstaller packaging/pwfinder.spec
import os

ROOT = os.path.abspath(os.getcwd())

a = Analysis(
    [os.path.join(ROOT, 'main.py')],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(ROOT, 'web'), 'web'),
        (os.path.join(ROOT, 'version.json'), '.'),
    ],
    hiddenimports=[
        'pymysql', 'msoffcrypto', 'pyzipper', 'py7zr', 'rarfile',
        'win32gui', 'win32con', 'win32api', 'waitress', 'flask',
        'win32timezone',
    ],
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
    icon=os.path.join(ROOT, 'web', 'assets', 'icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='資料助秘密碼查找器',
)
