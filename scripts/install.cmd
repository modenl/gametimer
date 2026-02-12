@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "REPO=modenl/gametimer"
if not "%GITHUB_REPO%"=="" set "REPO=%GITHUB_REPO%"
if not "%~1"=="" set "REPO=%~1"

set "ARCH=x86"
if /I "%PROCESSOR_ARCHITECTURE%"=="AMD64" set "ARCH=x86_64"
if /I "%PROCESSOR_ARCHITEW6432%"=="AMD64" set "ARCH=x86_64"

set "DEST_DIR=%LOCALAPPDATA%\PCTimer"
if not exist "%DEST_DIR%" mkdir "%DEST_DIR%"

set "TMP_DIR=%TEMP%\pctimer-%RANDOM%%RANDOM%"
mkdir "%TMP_DIR%" >nul 2>&1
if errorlevel 1 (
  echo Failed to create temp directory.
  exit /b 1
)

set "FOUND_ASSET="
for %%A in ("pctimer-windows-%ARCH%.zip" "pctimer-windows-x86_64.zip" "pctimer-windows-x86.zip") do (
  if defined FOUND_ASSET goto :after_download
  set "ASSET=%%~A"
  set "URL=https://github.com/%REPO%/releases/latest/download/!ASSET!"
  echo Downloading !ASSET! ...
  curl -fL --retry 5 --retry-delay 2 --retry-all-errors --connect-timeout 15 "!URL!" -o "%TMP_DIR%\!ASSET!" >nul 2>&1
  if not errorlevel 1 set "FOUND_ASSET=!ASSET!"
)

:after_download
if not defined FOUND_ASSET (
  echo Failed to download release asset from %REPO%.
  echo Check GitHub Release status and retry in 1-2 minutes.
  rmdir /s /q "%TMP_DIR%" >nul 2>&1
  exit /b 1
)

echo Extracting %FOUND_ASSET% ...
tar -xf "%TMP_DIR%\%FOUND_ASSET%" -C "%TMP_DIR%" >nul 2>&1
if errorlevel 1 (
  echo Failed to extract archive. Ensure Windows tar is available.
  rmdir /s /q "%TMP_DIR%" >nul 2>&1
  exit /b 1
)

if not exist "%TMP_DIR%\pctimer.exe" (
  echo Install failed: pctimer.exe not found in archive.
  rmdir /s /q "%TMP_DIR%" >nul 2>&1
  exit /b 1
)

copy /y "%TMP_DIR%\pctimer.exe" "%DEST_DIR%\pctimer.exe" >nul
if errorlevel 1 (
  echo Failed to copy pctimer.exe to %DEST_DIR%.
  rmdir /s /q "%TMP_DIR%" >nul 2>&1
  exit /b 1
)

start "" "%DEST_DIR%\pctimer.exe"
echo Installed to %DEST_DIR%\pctimer.exe

rmdir /s /q "%TMP_DIR%" >nul 2>&1
exit /b 0
