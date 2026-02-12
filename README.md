# PC Timer App

Cross-platform (macOS/Windows) fullscreen timer app that launches games, tracks session time, shows a last-minute overlay countdown, enforces a 1-hour cooldown, and kills the game if it is still running when the session ends.

## Run (from source)

```bash
python -m pip install -r requirements.txt
python app.py
```

## One-liner install (no dependencies)

macOS:
```bash
curl -fsSL https://raw.githubusercontent.com/modenl/gametimer/main/scripts/install.sh | bash
```

Windows (PowerShell):
```powershell
iwr -useb https://raw.githubusercontent.com/modenl/gametimer/main/scripts/install.ps1 | iex
```

## Build release assets

Build on each target OS/arch (no cross-compile).

macOS:
```bash
./scripts/build.sh
```

Windows (PowerShell):
```powershell
./scripts/build.ps1
```

Upload the generated artifacts from `dist/` to GitHub Releases using these names:
- `pctimer-macos-arm64.tar.gz` or `pctimer-macos-x86_64.tar.gz`
- `pctimer-windows-x86_64.zip`

## Notes
- Default games: Minecraft, Chrome.
- Windows Minecraft launcher path detection prioritizes `XboxGames` locations (for Xbox app installs).
- Default session time: 40.00 minutes (editable).
- Admin password to reset cooldown: `123456`.
- In locked state (no game running), macOS release builds use system kiosk mode to block app switching/menu bar.
- Manually selected paths are persisted in user config:
  - macOS: `~/Library/Application Support/PCTimer/settings.json`
  - Windows: `%APPDATA%\\PCTimer\\settings.json`
- Press `F11` to toggle fullscreen for testing.
