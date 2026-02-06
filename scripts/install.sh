#!/usr/bin/env bash
set -euo pipefail

DEFAULT_REPO="modenl/gametimer"
REPO="${1:-${GITHUB_REPO:-$DEFAULT_REPO}}"

OS=$(uname -s)
ARCH=$(uname -m)

if [[ "$OS" != "Darwin" ]]; then
  echo "Only macOS is supported by this installer script." >&2
  exit 1
fi

case "$ARCH" in
  arm64|x86_64) ;; 
  *)
    echo "Unsupported architecture: $ARCH" >&2
    exit 1
    ;;
esac

DEST_DIR="$HOME/.local/bin"
mkdir -p "$DEST_DIR"

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

if [[ "$ARCH" == "arm64" ]]; then
  ASSETS=("pctimer-macos-arm64.tar.gz" "pctimer-macos-x86_64.tar.gz")
else
  ASSETS=("pctimer-macos-x86_64.tar.gz" "pctimer-macos-arm64.tar.gz")
fi

download_ok=0
selected_asset=""

for asset in "${ASSETS[@]}"; do
  archive="$TMP_DIR/$asset"
  url="https://github.com/${REPO}/releases/latest/download/${asset}"
  if curl -fL --retry 5 --retry-delay 2 --retry-all-errors --connect-timeout 15 "$url" -o "$archive"; then
    selected_asset="$asset"
    download_ok=1
    break
  fi
done

if [[ "$download_ok" -ne 1 ]]; then
  echo "Failed to download release asset from ${REPO}. GitHub may be temporarily unavailable or release artifacts are not ready." >&2
  echo "Check Actions/Release status and retry in 1-2 minutes." >&2
  exit 1
fi

tar -C "$TMP_DIR" -xzf "$TMP_DIR/$selected_asset"

chmod +x "$TMP_DIR/pctimer"
cp "$TMP_DIR/pctimer" "$DEST_DIR/pctimer"

"$DEST_DIR/pctimer" &

echo "Installed to $DEST_DIR/pctimer"
