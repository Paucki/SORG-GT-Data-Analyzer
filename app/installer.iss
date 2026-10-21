#define MyAppName "SORG GT Data Analyzer"
#ifndef MyAppVersion
#define MyAppVersion "1.6.3"
#endif
#define MyAppPublisher "SORG Rennsport"
#define MyAppExeName "SORG_GT_Data_Analyzer.exe"

[Setup]
AppId={{8E06F5E7-D8C3-4F8D-A166-0A8CF19F1600}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SORG Rennsport\SORG GT Data Analyzer
DisableProgramGroupPage=yes
OutputDir=release
OutputBaseFilename=SORG_GT_Data_Analyzer_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=sorg_gt.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "dist\SORG GT Data Analyzer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknuepfung erstellen"; GroupDescription: "Zusaetzliche Symbole:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{#MyAppName} starten"; Flags: nowait postinstall skipifsilent
