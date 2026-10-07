#!/usr/bin/env bash
set -euo pipefail

# ARDY batch baseline. Interactive target-velocity/waypoint validation still
# requires launching ARDY's own browser demo on the CUDA host.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARDY_DIR="${ARDY_DIR:-}"
OUT="${1:-$ROOT/experiments/kimodo-ardy/output/ardy}"
MODEL="${ARDY_MODEL:-core}"
DURATION="${ARDY_DURATION:-5.0}"
SEED="${ARDY_SEED:-42}"

if [[ -z "$ARDY_DIR" || ! -f "$ARDY_DIR/scripts/generate.py" ]]; then
  echo "Set ARDY_DIR to a checkout of https://github.com/nv-tlabs/ardy" >&2
  exit 2
fi

python -c 'import numpy' >/dev/null 2>&1 || {
  echo "numpy is required by the EvoWild analysis helpers." >&2
  exit 2
}

mkdir -p "$OUT/motions" "$OUT/signals"

declare -A PROMPTS=(
  [steady_run]="A person runs forward quickly at a steady pace."
  [accelerate]="A person accelerates smoothly from a run into a fast sprint."
  [decelerate]="A person decelerates smoothly from a fast sprint into a run."
  [turn]="A person runs forward quickly and makes a controlled turn."
)

for CASE in steady_run accelerate decelerate turn; do
  STEM="$OUT/motions/${CASE}"
  (
    cd "$ARDY_DIR"
    python scripts/generate.py "${PROMPTS[$CASE]}" \
      --model "$MODEL" \
      --duration "$DURATION" \
      --seed "$SEED" \
      --output "$STEM"
  )

  python "$ROOT/scripts/kimodo-ardy/extract_motion_signals.py" \
    "${STEM}.npz" \
    --summary "$OUT/signals/${CASE}.json" \
    --timeseries "$OUT/signals/${CASE}.csv"
done

cat <<'EOF'
Batch baseline complete.
For Gate A1 interactive validation, from ARDY_DIR run:
  python scripts/run_demo.py
Then test target-velocity mode (t + arrows), waypoint mode (p + clicks),
speed changes, left/right steering, and export the session/motion.
EOF
