# 資料助秘 密碼查找器 — Windows 一鍵建置
# 用法（在專案根目錄）： powershell -ExecutionPolicy Bypass -File packaging\build-win.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "==> 1/4 產生圖示" -ForegroundColor Cyan
python tools\make_icon.py

Write-Host "==> 2/4 產生語音教學 MP3（需網路，一次即可）" -ForegroundColor Cyan
if (-not (Test-Path "web\assets\voice\welcome.mp3")) {
    python tools\make_voice.py
} else {
    Write-Host "    已存在，略過（要重做請刪 web\assets\voice）"
}

Write-Host "==> 3/4 PyInstaller 打包" -ForegroundColor Cyan
if (Test-Path build) { Remove-Item build -Recurse -Force }
if (Test-Path dist)  { Remove-Item dist  -Recurse -Force }
python -m PyInstaller --noconfirm --clean packaging\pwfinder.spec

Write-Host "==> 4/4 Inno Setup 製作安裝檔" -ForegroundColor Cyan
$iscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($iscc) {
    & $iscc "packaging\pwfinder.iss"
    Write-Host "完成：dist-installer\資料助秘密碼查找器_安裝檔.exe" -ForegroundColor Green
} else {
    Write-Host "未找到 Inno Setup，略過安裝檔。可執行：winget install JRSoftware.InnoSetup" -ForegroundColor Yellow
    Write-Host "免安裝版已在：dist\資料助秘密碼查找器\資料助秘密碼查找器.exe" -ForegroundColor Green
}
