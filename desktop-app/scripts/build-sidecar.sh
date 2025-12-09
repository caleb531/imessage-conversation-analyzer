#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$DESKTOP_APP_DIR/.." && pwd)"
OUTPUT_DIR="$DESKTOP_APP_DIR/src-tauri/bin"
BUILD_DIR="$PROJECT_ROOT/build/pyinstaller"

TARGET_TRIPLE=$(rustc -vV | awk '/^host: / { print $2 }')
SIDE_CAR_TARGET_DIR="$OUTPUT_DIR/ica-sidecar-$TARGET_TRIPLE"
SIDE_CAR_EXTERNAL_EXE="$DESKTOP_APP_DIR/src-tauri/ica-sidecar"
SIDE_CAR_RUNTIME_DIR="$DESKTOP_APP_DIR/src-tauri/_internal"
SIDE_CAR_ENTRY="ica-sidecar"
SIDE_CAR_SUFFIXED_DIR="$DESKTOP_APP_DIR/src-tauri/${SIDE_CAR_ENTRY}-${TARGET_TRIPLE}"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$BUILD_DIR"

needs_rebuild=false

if [[ ! -f "$SIDE_CAR_EXTERNAL_EXE" || ! -d "$SIDE_CAR_RUNTIME_DIR" || ! -d "$SIDE_CAR_TARGET_DIR" || ! -d "$SIDE_CAR_SUFFIXED_DIR" ]]; then
  needs_rebuild=true
else
  if [[ "$PROJECT_ROOT/pyproject.toml" -nt "$SIDE_CAR_EXTERNAL_EXE" || "$PROJECT_ROOT/uv.lock" -nt "$SIDE_CAR_EXTERNAL_EXE" ]]; then
    needs_rebuild=true
  elif [[ "$SCRIPT_DIR/build-sidecar.sh" -nt "$SIDE_CAR_EXTERNAL_EXE" ]]; then
    needs_rebuild=true
  elif find "$PROJECT_ROOT/ica" -type f ! -path '*/__pycache__/*' -newer "$SIDE_CAR_EXTERNAL_EXE" -print -quit | grep -q .; then
    needs_rebuild=true
  fi
fi

if [[ $needs_rebuild == false ]]; then
  echo "Sidecar already up to date; skipping PyInstaller build."
  exit 0
fi

rm -rf "$SIDE_CAR_RUNTIME_DIR" "$SIDE_CAR_TARGET_DIR" "$SIDE_CAR_EXTERNAL_EXE" "$SIDE_CAR_SUFFIXED_DIR" "$OUTPUT_DIR/_internal"

cd "$PROJECT_ROOT"

uv run pyinstaller \
  --name ica-sidecar \
  --onedir \
  --collect-submodules ica.analyzers \
  --add-data "$PROJECT_ROOT/ica/analyzers:ica/analyzers" \
  --add-data "$PROJECT_ROOT/ica/queries:ica/queries" \
  --distpath "$OUTPUT_DIR" \
  --workpath "$BUILD_DIR" \
  --specpath "$BUILD_DIR" \
  --exclude-module pytest \
  --exclude-module _pytest \
  --exclude-module pandas.tests \
  --exclude-module pyarrow.tests \
  --exclude-module pandas.io.formats.style \
  ica/__main__.py

mv "$OUTPUT_DIR/$SIDE_CAR_ENTRY" "$SIDE_CAR_TARGET_DIR"

# Surface the executable and Python runtime alongside the Tauri app so the shell
# plugin loads the sidecar without searching inside architecture-specific
# directories at runtime.
cp "$SIDE_CAR_TARGET_DIR/$SIDE_CAR_ENTRY" "$SIDE_CAR_EXTERNAL_EXE"
cp -R "$SIDE_CAR_TARGET_DIR/_internal" "$SIDE_CAR_RUNTIME_DIR"
cp -R "$SIDE_CAR_TARGET_DIR" "$SIDE_CAR_SUFFIXED_DIR"
