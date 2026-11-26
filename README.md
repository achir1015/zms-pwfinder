# 資料助秘 密碼查找器

幫你找回「自己」忘記的密碼。全程在本機執行，給一般人用、打開即可用、關閉即停止。

> ⚠️ 本工具只用於回復**自己**電腦上、**自己**檔案與帳號的密碼。
> **不含**任何攻擊他人帳號的功能（密碼噴灑、撞庫、外洩帳密比對等一律排除）。

## 功能

| 模組 | 說明 |
|---|---|
| 📶 WiFi 密碼 | 顯示本機已儲存的無線網路密碼（`netsh wlan`） |
| 📝 文字抓密碼 | 從郵件／文件內文抓出「密碼是 XXX」這類明文密碼 |
| 🗜 壓縮檔密碼 | 回復自己的 ZIP / 7z / RAR 密碼（字典＋窮舉） |
| 📄 Office 密碼 | 回復自己的 Word / Excel / PPT 開啟密碼 |
| 👁 星號顯示 | 還原傳統 Windows 密碼框的 ●●● 文字 |
| ✉ 郵件密碼 | 還原本機 Thunderbird / Outlook 已存的帳號密碼 |

### 成功密碼學習庫（提高下次成功機率）
每次破解成功，密碼與特徵（模組、檔案類型、長度、字元組成）會存入學習庫；
下次破解時自動把學過的密碼排在最前面優先嘗試。預設用本機 JSON（零設定），
也可改接 MariaDB（埠 3558，沿用資料助秘系列的帳號權限機制、多人共用）。

## 執行（開發）

```powershell
pip install -r requirements.txt
python main.py
```

打開後是一個視窗程式，六個分頁即六大功能，右上角有語音教學、檢查更新、學習庫設定。

## 打包 Windows 版

```powershell
python tools/make_icon.py        # 產生圖示
pyinstaller packaging/pwfinder.spec
```

## 平台規劃
- ✅ Windows 11（本版）
- ⬜ macOS（pywebview）
- ⬜ 線上版（HTML，`web/` 部署 GitHub Pages，純前端退路見 `js/local.js`）
- ⬜ iPhone / iPad（線上安裝）、Android（WebView 外殼）

## 架構
- `main.py` — pywebview 入口（檔案選擇、檢查更新）
- `app/server.py` — 本機 Flask API（埠 47851）
- `app/recovery/` — 各回復模組
- `app/db.py` — 成功密碼學習庫 + 使用者權限（JSON／MariaDB）
- `web/` — 介面（純 JS、語音教學）
