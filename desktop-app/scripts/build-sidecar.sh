#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$DESKTOP_APP_DIR/.." && pwd)"
OUTPUT_DIR="$DESKTOP_APP_DIR/src-tauri/bin"
BUILD_DIR="$PROJECT_ROOT/build/pyinstaller"

TARGET_TRIPLE=$(rustc -vV | awk '/^host: / { print $2 }')
SIDE_CAR_BASE="$OUTPUT_DIR/ica-sidecar"
SIDE_CAR_TARGET="$OUTPUT_DIR/ica-sidecar-$TARGET_TRIPLE"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$BUILD_DIR"

needs_rebuild=false

if [[ ! -f "$SIDE_CAR_BASE" || ! -f "$SIDE_CAR_TARGET" ]]; then
  needs_rebuild=true
else
  if [[ "$PROJECT_ROOT/pyproject.toml" -nt "$SIDE_CAR_BASE" || "$PROJECT_ROOT/uv.lock" -nt "$SIDE_CAR_BASE" ]]; then
    needs_rebuild=true
  elif [[ "$SCRIPT_DIR/build-sidecar.sh" -nt "$SIDE_CAR_BASE" ]]; then
    needs_rebuild=true
  elif find "$PROJECT_ROOT/ica" -type f ! -path '*/__pycache__/*' -newer "$SIDE_CAR_BASE" -print -quit | grep -q .; then
    needs_rebuild=true
  fi
fi

if [[ $needs_rebuild == false ]]; then
  echo "Sidecar already up to date; skipping PyInstaller build."
  exit 0
fi

rm -f "$SIDE_CAR_BASE" "$SIDE_CAR_TARGET"

cd "$PROJECT_ROOT"

uv run pyinstaller \
  --name ica-sidecar \
  --onefile \
  --distpath "$OUTPUT_DIR" \
  --workpath "$BUILD_DIR" \
  --specpath "$BUILD_DIR" \
  --exclude-module pytest \
  --exclude-module _pytest \
  --exclude-module pandas.tests \
  --exclude-module pyarrow.tests \
  --exclude-module pandas.io.formats.style \
  ica/__main__.py

mv "$SIDE_CAR_BASE" "$SIDE_CAR_TARGET"

# Provide an unsuffixed binary for Tauri's externalBin lookup while keeping
# the target-specific filename available for packaging.
cp "$SIDE_CAR_TARGET" "$SIDE_CAR_BASE"
