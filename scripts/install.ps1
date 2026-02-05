Param(
  [string]$Repo = $env:GITHUB_REPO
)

if ([string]::IsNullOrWhiteSpace($Repo)) {
  $Repo = "modenl/gametimer"
}

$arch = if ([Environment]::Is64BitOperatingSystem) { "x86_64" } else { "x86" }
$asset = "pctimer-windows-$arch.zip"
$url = "https://github.com/$Repo/releases/latest/download/$asset"

$destDir = Join-Path $Env:LOCALAPPDATA 'PCTimer'
if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir | Out-Null }

$tempDir = Join-Path $Env:TEMP ("pctimer-" + [Guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $tempDir | Out-Null

$zipPath = Join-Path $tempDir $asset

try {
  Invoke-WebRequest -Uri $url -OutFile $zipPath -UseBasicParsing
  Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force
  Copy-Item (Join-Path $tempDir 'pctimer.exe') (Join-Path $destDir 'pctimer.exe') -Force
} finally {
  Remove-Item $tempDir -Recurse -Force
}

Start-Process (Join-Path $destDir 'pctimer.exe')
Write-Host "Installed to $destDir\pctimer.exe"
