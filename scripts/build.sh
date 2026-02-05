#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to build." >&2
  exit 1
fi

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install --upgrade pyinstaller

rm -rf build dist
pyinstaller --noconfirm --clean --name pctimer --onefile app.py

ARCH=$(uname -m)
ASSET="pctimer-macos-${ARCH}.tar.gz"
mkdir -p dist

tar -C dist -czf "dist/${ASSET}" pctimer

echo "Built dist/${ASSET}"
