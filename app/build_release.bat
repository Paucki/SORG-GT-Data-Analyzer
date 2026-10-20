@echo off
setlocal EnableExtensions

rem Immer in den Ordner wechseln, in dem diese BAT-Datei liegt.
rem pushd kann auch UNC-Pfade (\\server\...) temporaer als Laufwerk einbinden.
pushd "%~dp0" || goto :fail

echo === SORG GT Data Analyzer V1.6.2 Build ===
echo Arbeitsordner: %CD%
echo.

rem Python finden: bevorzugt Windows Python Launcher "py", sonst "python".
where py >nul 2>nul
if %errorlevel%==0 (
    set "PYBASE=py"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PYBASE=python"
    ) else (
        echo FEHLER: Python wurde nicht gefunden.
        echo Bitte Python installieren und "Add Python to PATH" aktivieren.
        goto :fail
    )
)

rem Alte/defekte virtuelle Umgebung bewusst entfernen.
if exist ".venv" (
    echo Alte .venv wird entfernt...
    rmdir /s /q ".venv"
    if exist ".venv" (
        echo FEHLER: .venv konnte nicht geloescht werden.
        echo Schliesse offene Python-Fenster und versuche es erneut.
        goto :fail
    )
)

echo Virtuelle Umgebung wird neu erstellt...
%PYBASE% -m venv ".venv" || goto :fail

set "VENV_PY=%CD%\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo FEHLER: %VENV_PY% wurde nicht erstellt.
    goto :fail
)

echo.
echo pip wird aktualisiert...
"%VENV_PY%" -m pip install --upgrade pip || goto :fail

echo.
echo Abhaengigkeiten werden installiert...
"%VENV_PY%" -m pip install -r "requirements.txt" || goto :fail

echo.
echo PyInstaller-Build wird erstellt...
rmdir /s /q "build" 2>nul
rmdir /s /q "dist" 2>nul
"%VENV_PY%" -m PyInstaller --noconfirm "SORG_GT_Data_Analyzer.spec" || goto :fail

if not exist "dist\SORG GT Data Analyzer\SORG_GT_Data_Analyzer.exe" (
    echo FEHLER: PyInstaller lief durch, aber die EXE wurde nicht gefunden.
    goto :fail
)

echo.
echo Windows-Setup wird erstellt...
set "ISCC=C:\Users\programmierer06\AppData\Local\Programs\Inno Setup 6\ISCC.exe"

if not exist "%ISCC%" (
    echo FEHLER: Inno Setup wurde nicht gefunden.
    pause
    exit /b 1
)

echo Windows-Setup wird erstellt...
"%ISCC%" installer.iss || goto :fail

if not exist "release\SORG_GT_Data_Analyzer_Setup.exe" (
    echo FEHLER: Setup-EXE wurde nicht erzeugt.
    goto :fail
)

echo.
echo latest.json und SHA256 werden erstellt...
powershell -NoProfile -ExecutionPolicy Bypass -File "make_latest.ps1" || goto :fail

if not exist "release\latest.json" (
    echo FEHLER: release\latest.json wurde nicht erzeugt.
    goto :fail
)

echo.
echo ===============================================
echo BUILD ERFOLGREICH
echo ===============================================
echo release\SORG_GT_Data_Analyzer_Setup.exe
echo release\latest.json
echo.
start "" "%CD%\release"
popd
pause
exit /b 0

:fail
echo.
echo ===============================================
echo BUILD FEHLGESCHLAGEN
 echo ===============================================
echo Kopiere bei einem weiteren Fehler die letzten Zeilen hierher.
echo.
popd
pause
exit /b 1
