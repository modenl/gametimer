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

ASSET="pctimer-macos-${ARCH}.tar.gz"
URL="https://github.com/${REPO}/releases/latest/download/${ASSET}"

DEST_DIR="$HOME/.local/bin"
mkdir -p "$DEST_DIR"

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

ARCHIVE="$TMP_DIR/$ASSET"

curl -fL "$URL" -o "$ARCHIVE"

tar -C "$TMP_DIR" -xzf "$ARCHIVE"

chmod +x "$TMP_DIR/pctimer"
cp "$TMP_DIR/pctimer" "$DEST_DIR/pctimer"

"$DEST_DIR/pctimer" &

echo "Installed to $DEST_DIR/pctimer"
