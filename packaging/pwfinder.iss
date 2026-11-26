; 資料助秘 密碼查找器 — Inno Setup 安裝檔腳本
; 編譯： "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\pwfinder.iss
; 產生： dist-installer\資料助秘密碼查找器_安裝檔.exe

#define AppName "資料助秘密碼查找器"
#define AppVer "1.0.0"
#define AppPublisher "YU-JUH WU"
#define AppExe "資料助秘密碼查找器.exe"

[Setup]
AppId={{B7E2C9A4-3F1D-4E5B-9C8A-PWFINDER01}}
AppName={#AppName}
AppVersion={#AppVer}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\dist-installer
OutputBaseFilename=zms-pwfinder-v1.0.0-Windows-Setup
SetupIconFile=..\web\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Languages]
; Inno 6 預設未附繁中 isl，用內建 Default 確保可編譯；程式介面本身為繁中。
; 若已另外安裝繁中語言檔，可改為 compiler:Languages\ChineseTraditional.isl
Name: "default"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "建立桌面捷徑"; GroupDescription: "附加捷徑："; Flags: checkedonce

[Files]
Source: "..\dist\資料助秘密碼查找器\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\web\assets\icon.ico"
Name: "{group}\解除安裝 {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\web\assets\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "立即啟動 {#AppName}"; Flags: nowait postinstall skipifsilent
