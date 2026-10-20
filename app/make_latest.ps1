$ErrorActionPreference = "Stop"
$version = "1.6.2"
$exe = Join-Path $PSScriptRoot "release\SORG_GT_Data_Analyzer_Setup.exe"
if (!(Test-Path $exe)) { throw "Installer nicht gefunden: $exe" }
$hash = (Get-FileHash -Algorithm SHA256 $exe).Hash.ToLower()
$data = [ordered]@{
  version = $version
  url = "https://github.com/Paucki/SORG-GT-Data-Analyzer/releases/download/V1.6.2/SORG_GT_Data_Analyzer_Setup.exe"
  sha256 = $hash
  notes = "Mehrere Fahrer pro Fahrzeug | Slick/Wet und Reifensaetze pro Rennwochenende | Reifen Notiz mit Historie, Marke und Zustand | Startnummer pro Fahrzeug | neue Kaltdruck-Empfehlung aus Referenz-Kaltdruck und Ziel-Heissdruck"
}
$data | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $PSScriptRoot "release\latest.json")
Write-Host "SHA256:" $hash
