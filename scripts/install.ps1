Param(
  [string]$Repo = $env:GITHUB_REPO
)

if ([string]::IsNullOrWhiteSpace($Repo)) {
  $Repo = "modenl/gametimer"
}

$arch = if ([Environment]::Is64BitOperatingSystem) { "x86_64" } else { "x86" }
$assets = @("pctimer-windows-$arch.zip")
if ($arch -eq "x86_64") {
  $assets += "pctimer-windows-x86.zip"
}

$destDir = Join-Path $Env:LOCALAPPDATA 'PCTimer'
if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir | Out-Null }

$tempDir = Join-Path $Env:TEMP ("pctimer-" + [Guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $tempDir | Out-Null

$zipPath = ""
$selectedAsset = ""

try {
  foreach ($asset in $assets) {
    $candidateUrl = "https://github.com/$Repo/releases/latest/download/$asset"
    $candidateZip = Join-Path $tempDir $asset
    try {
      Invoke-WebRequest -Uri $candidateUrl -OutFile $candidateZip -UseBasicParsing -MaximumRetryCount 5 -RetryIntervalSec 2
      $zipPath = $candidateZip
      $selectedAsset = $asset
      break
    } catch {
      continue
    }
  }

  if ([string]::IsNullOrWhiteSpace($zipPath)) {
    Write-Error "Failed to download release asset from $Repo. GitHub may be temporarily unavailable or release artifacts are not ready."
    exit 1
  }

  Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force
  Copy-Item (Join-Path $tempDir 'pctimer.exe') (Join-Path $destDir 'pctimer.exe') -Force
} finally {
  Remove-Item $tempDir -Recurse -Force
}

Start-Process (Join-Path $destDir 'pctimer.exe')
Write-Host "Installed to $destDir\pctimer.exe"
