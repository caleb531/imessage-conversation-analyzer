#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$DESKTOP_APP_DIR/.." && pwd)"
OUTPUT_DIR="$DESKTOP_APP_DIR/src-tauri/bin"
BUILD_DIR="$PROJECT_ROOT/build/pyinstaller"

TARGET_TRIPLE=$(rustc -vV | awk '/^host: / { print $2 }')

mkdir -p "$OUTPUT_DIR"
rm -f "$OUTPUT_DIR/ica-sidecar" "$OUTPUT_DIR/ica-sidecar-$TARGET_TRIPLE"

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

mv "$OUTPUT_DIR/ica-sidecar" "$OUTPUT_DIR/ica-sidecar-$TARGET_TRIPLE"

# Provide an unsuffixed binary for Tauri's externalBin lookup while keeping
# the target-specific filename available for packaging.
cp "$OUTPUT_DIR/ica-sidecar-$TARGET_TRIPLE" "$OUTPUT_DIR/ica-sidecar"
