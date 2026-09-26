#!/usr/bin/env bash
set -euo pipefail

PIN="fbd1a08d47e39c673c73eb494cfde8435b3b13b6"
BASE="${1:-}"
OUT="${2:-artifacts/spritegen-s}"
VENV=".spritegen-venv"

if [[ -z "$BASE" || ! -f "$BASE" ]]; then
  echo "usage: bash scripts/run-spritegen-s-poc.sh <side-source.png> [out-dir]" >&2
  exit 2
fi

for bin in python3 ffmpeg img2webp; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "missing required binary: $bin" >&2
    exit 3
  fi
done

if [[ ! -x "$VENV/bin/sprite-gen" ]]; then
  python3 -m venv "$VENV"
  "$VENV/bin/python" -m pip install --upgrade pip
  "$VENV/bin/python" -m pip install "git+https://github.com/aldegad/sprite-gen.git@$PIN"
fi

mkdir -p "$OUT"

"$VENV/bin/sprite-gen" video-set \
  --base "side=$BASE" \
  --states idle,run \
  --out-dir "$OUT"

echo "sprite-gen output: $OUT"
