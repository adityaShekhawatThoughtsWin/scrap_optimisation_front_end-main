; Inno Setup script — Allocation Model offline installer
; Build on Windows: npm run installer
; Requires Inno Setup 6: https://jrsoftware.org/isinfo.php

#define AppName "Allocation Model"
#define AppVersion "1.0.0"
#define AppPublisher "JSW"
#define AppURL "http://127.0.0.1:3000"
#define DistDir "..\dist\AllocationModel"
#define LauncherVbs "launcher\AllocationModel.vbs"

[Setup]
AppId={{A7E3C91F-4B2D-4F8E-9A1C-6D5E4F3B2A10}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\AllocationModel
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=..\release
OutputBaseFilename=AllocationModelSetup
SetupIconFile=
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
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
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "solver.BUILD_REQUIRED.txt"

[Dirs]
; Writable runtime folders (per-user data survives upgrades)
Name: "{app}\config"; Permissions: users-modify
Name: "{app}\backend\uploaded_files"; Permissions: users-modify
Name: "{app}\backend\prisma"; Permissions: users-modify

[Icons]
; Start Menu — silent launcher via wscript (no console window)
Name: "{group}\{#AppName}"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\{#LauncherVbs}"""; WorkingDir: "{app}"; Comment: "Launch Allocation Model"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut
Name: "{autodesktop}\{#AppName}"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\{#LauncherVbs}"""; WorkingDir: "{app}"; Tasks: desktopicon; Comment: "Launch Allocation Model"

[Run]
; Do not auto-start — user launches from shortcut

[UninstallDelete]
; Remove runtime data on uninstall
Type: filesandordirs; Name: "{app}\config"
Type: filesandordirs; Name: "{app}\backend\uploaded_files"

[Code]
function GetDistDir: string;
begin
  Result := ExpandConstant('{src}..\dist\AllocationModel');
end;

function InitializeSetup(): Boolean;
var
  DistPath: string;
begin
  DistPath := GetDistDir;
  if not DirExists(DistPath) then
  begin
    MsgBox('Release folder not found.' + #13#10 +
      'Run "npm run dist" before building the installer.',
      mbError, MB_OK);
    Result := False;
  end
  else if not FileExists(DistPath + '\node.exe') then
  begin
    MsgBox('node.exe is missing from the release folder.' + #13#10 +
      'Run "npm run dist" (without SKIP_NODE_DOWNLOAD) on Windows.',
      mbError, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;
