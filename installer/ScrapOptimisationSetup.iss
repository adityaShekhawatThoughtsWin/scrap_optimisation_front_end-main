; Inno Setup script — ScrapOptimisation offline installer
; Build on Windows: npm run installer
; Requires Inno Setup 6: https://jrsoftware.org/isinfo.php

#define AppName "Mingo Scrap Optimisation Application"
#define AppVersion "1.0.0"
#define AppPublisher "JSW"
#define AppURL "http://127.0.0.1:3000"
#define DistDir "..\dist\ScrapOptimisation"
#define LauncherVbs "launcher\ScrapOptimisation.vbs"

[Setup]
AppId={{B8F4D02A-5C3E-5F9F-0B2D-7E6F4C3B2A21}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
; Per-user install — no admin required (better on locked-down corporate PCs)
DefaultDirName={localappdata}\ScrapOptimisation
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=..\release
OutputBaseFilename=ScrapOptimisationSetup
SetupIconFile=app.ico
UninstallDisplayIcon={app}\app.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=no
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Application bundle (exclude dev-only notes)
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "solver.BUILD_REQUIRED.txt,backend\node_modules\prisma\*,backend\node_modules\@prisma\dev\*,backend\node_modules\@prisma\studio-core\*"
Source: "app.ico"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Writable runtime folders (per-user install — current user already owns {app})
Name: "{app}\config"
Name: "{app}\uploads"
Name: "{app}\outputs"
Name: "{app}\backend\uploaded_files"
Name: "{app}\backend\prisma"

[Icons]
; Start Menu - double-click .vbs runs via wscript (no console window)
Name: "{group}\{#AppName}"; Filename: "{app}\{#LauncherVbs}"; WorkingDir: "{app}"; IconFilename: "{app}\app.ico"; Comment: "Launch ScrapOptimisation"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#LauncherVbs}"; WorkingDir: "{app}"; IconFilename: "{app}\app.ico"; Tasks: desktopicon; Comment: "Launch ScrapOptimisation"

; Debug launcher (visible console + pause on error)
Name: "{group}\{#AppName} (Debug)"; Filename: "{app}\launcher\ScrapOptimisation-Debug.bat"; WorkingDir: "{app}"; IconFilename: "{app}\app.ico"; Comment: "Launch with console output for troubleshooting"

[Run]
; Do not auto-start — user launches from shortcut

[UninstallDelete]
; Remove runtime data on uninstall
Type: filesandordirs; Name: "{app}\config"
Type: filesandordirs; Name: "{app}\backend\uploaded_files"
