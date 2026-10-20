SORG GT Data Analyzer V1.6.2 - Build Projekt

1. Auf einem Windows-PC Python und Inno Setup 6 installieren.
2. build_release.bat doppelklicken.
3. Danach liegen unter release\:
   - SORG_GT_Data_Analyzer_Setup.exe
   - latest.json (mit echtem SHA256)
4. GitHub: neuen Release V1.6.2 anlegen und die Setup-EXE als Asset hochladen.
5. Den Inhalt von release\latest.json nach update/latest.json im Repository uebernehmen.

Wichtig: Der Installer behaelt die Nutzerdatenbank in %%LOCALAPPDATA%%\SORG Rennsport\GT Data Analyzer.
Die Datenbankmigration ergaenzt die neuen Tabellen/Felder beim Start.
