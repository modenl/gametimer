$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
  Write-Error "python is required to build."
  exit 1
}

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install --upgrade pyinstaller

if (Test-Path build) { Remove-Item build -Recurse -Force }
if (Test-Path dist) { Remove-Item dist -Recurse -Force }

python -m PyInstaller --noconfirm --clean --name pctimer --onefile app.py

$arch = if ([Environment]::Is64BitOperatingSystem) { "x86_64" } else { "x86" }
$asset = "pctimer-windows-$arch.zip"

if (-not (Test-Path dist)) { New-Item dist -ItemType Directory | Out-Null }
Compress-Archive -Path (Join-Path dist 'pctimer.exe') -DestinationPath (Join-Path dist $asset) -Force

Write-Host "Built dist/$asset"
