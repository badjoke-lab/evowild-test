#!/usr/bin/env bash
set -euo pipefail

# Offline Kimodo baseline for the isolated EvoWild feasibility lane.
# Prerequisite: an NVIDIA/CUDA host with Kimodo installed and model access.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${1:-$ROOT/experiments/kimodo-ardy/output/kimodo}"
MODEL="${KIMODO_MODEL:-Kimodo-SOMA-RP-v1.1}"
DURATION="${KIMODO_DURATION:-5.0}"
FPS="${KIMODO_FPS:-30}"
SPEED="${KIMODO_ROOT_SPEED:-4.0}"
SEED="${KIMODO_SEED:-42}"

command -v kimodo_gen >/dev/null 2>&1 || {
  echo "kimodo_gen not found. Install NVIDIA Kimodo on a CUDA host first." >&2
  exit 2
}
python -c 'import numpy' >/dev/null 2>&1 || {
  echo "numpy is required by the EvoWild analysis helpers." >&2
  exit 2
}

mkdir -p "$OUT/constraints" "$OUT/motions" "$OUT/signals"

# CPU text encoding is the conservative default for smaller GPUs.
export TEXT_ENCODER_DEVICE="${TEXT_ENCODER_DEVICE:-cpu}"

declare -A PROMPTS=(
  [steady_sprint]="A person sprints forward at a steady fast pace."
  [accelerate]="A person accelerates smoothly from a run into a fast sprint."
  [decelerate]="A person decelerates smoothly from a fast sprint into a run."
  [curve]="A person runs quickly while following a smooth curved path."
  [lane_change]="A person runs forward quickly and makes a controlled lateral direction change."
)

declare -A MODES=(
  [steady_sprint]="straight"
  [accelerate]="accel"
  [decelerate]="decel"
  [curve]="curve"
  [lane_change]="lane-change"
)

for CASE in steady_sprint accelerate decelerate curve lane_change; do
  CONSTRAINT="$OUT/constraints/${CASE}.json"
  STEM="$OUT/motions/${CASE}"

  python "$ROOT/scripts/kimodo-ardy/make_kimodo_constraints.py" \
    --mode "${MODES[$CASE]}" \
    --duration "$DURATION" \
    --fps "$FPS" \
    --speed "$SPEED" \
    --output "$CONSTRAINT"

  kimodo_gen "${PROMPTS[$CASE]}" \
    --model "$MODEL" \
    --duration "$DURATION" \
    --constraints "$CONSTRAINT" \
    --output "$STEM" \
    --bvh \
    --bvh_standard_tpose \
    --seed "$SEED"

  python "$ROOT/scripts/kimodo-ardy/extract_motion_signals.py" \
    "${STEM}.npz" \
    --fps "$FPS" \
    --summary "$OUT/signals/${CASE}.json" \
    --timeseries "$OUT/signals/${CASE}.csv"
done

echo "Kimodo baseline complete: $OUT"
