#!/usr/bin/env bash
set -euo pipefail

# EvoWild Run — isolated UniMate S motion bench.
#
# Required:
#   UNIMATE_DIR      checkout of Friedrich-M/UniMate
#   UNIMATE_EXP_DIR  downloaded released experiment directory containing
#                    config.json, dataset_stats.npy and checkpoints/
#
# Optional:
#   EVOWILD_REPO_DIR defaults to current repository root
#   WORK_DIR         defaults to <repo>/.unimate-bench/evo-s
#   REPETITIONS      defaults to 3
#
# This script does not provision or start GPU infrastructure.

PINNED_UNIMATE_COMMIT="2c5b384715aa63d8639b1ed7eb74bfe614570c7a"

EVOWILD_REPO_DIR="${EVOWILD_REPO_DIR:-$(git rev-parse --show-toplevel)}"
UNIMATE_DIR="${UNIMATE_DIR:?Set UNIMATE_DIR to the UniMate checkout}"
UNIMATE_EXP_DIR="${UNIMATE_EXP_DIR:?Set UNIMATE_EXP_DIR to the released UniMate experiment directory}"
WORK_DIR="${WORK_DIR:-$EVOWILD_REPO_DIR/.unimate-bench/evo-s}"
REPETITIONS="${REPETITIONS:-3}"

SOURCE_GLB="$EVOWILD_REPO_DIR/public/models/evowild-s/focus-rigged-v5.glb"
PRE_DIR="$WORK_DIR/preprocessed"
LOCAL_EXP="$WORK_DIR/exp"
SAMPLES_DIR="$WORK_DIR/samples"
ANIMATED_DIR="$WORK_DIR/animated"
CASES_JSON="$WORK_DIR/test_cases.json"

for p in "$SOURCE_GLB" "$UNIMATE_EXP_DIR/config.json" "$UNIMATE_EXP_DIR/dataset_stats.npy"; do
  [[ -e "$p" ]] || { echo "missing required path: $p" >&2; exit 2; }
done
[[ -d "$UNIMATE_EXP_DIR/checkpoints" ]] || { echo "missing checkpoints/: $UNIMATE_EXP_DIR/checkpoints" >&2; exit 2; }

actual_commit="$(git -C "$UNIMATE_DIR" rev-parse HEAD)"
if [[ "$actual_commit" != "$PINNED_UNIMATE_COMMIT" && "${ALLOW_UNPINNED:-0}" != "1" ]]; then
  echo "UniMate checkout is not pinned." >&2
  echo "expected: $PINNED_UNIMATE_COMMIT" >&2
  echo "actual:   $actual_commit" >&2
  echo "Set ALLOW_UNPINNED=1 only when intentionally testing a newer upstream." >&2
  exit 3
fi

rm -rf "$WORK_DIR"
mkdir -p "$PRE_DIR" "$LOCAL_EXP" "$SAMPLES_DIR" "$ANIMATED_DIR"

pushd "$UNIMATE_DIR" >/dev/null

# Do not guess facing-joint names. The first pass lets UniMate inspect and
# canonicalize the actual rig. If facing is wrong, rerun with exact raw names
# after inspecting the generated condition / preprocessing log.
CHAR_PATH="$SOURCE_GLB" OUTPUT_DIR="$PRE_DIR" FORMATS=glb KEEP_INTERMEDIATE=1 bash data_process/scripts/run_preprocess_char.sh

popd >/dev/null

python - "$PRE_DIR/cond.npy" "$CASES_JSON" <<'PY'
import json
import sys
import numpy as np

cond_path, out_path = sys.argv[1:3]
cond = np.load(cond_path, allow_pickle=True).item()
if len(cond) != 1:
    raise SystemExit(f"expected exactly one object type in {cond_path}, got {list(cond)}")
object_type = next(iter(cond))
cases = {
    f"{object_type}-steady-run": "An object runs forward at a steady athletic pace with coordinated four-limb locomotion.",
    f"{object_type}-fast-gallop": "An object gallops forward quickly with a powerful cyclic four-limb gait.",
    f"{object_type}-max-sprint": "An object sprints forward at maximum effort with strong whole-body propulsion.",
    f"{object_type}-launch": "An object lowers its body, launches explosively, and accelerates forward into a sprint.",
}
with open(out_path, "w") as f:
    json.dump(cases, f, indent=2)
print(object_type)
PY

cp "$UNIMATE_EXP_DIR/config.json" "$LOCAL_EXP/config.json"
cp "$UNIMATE_EXP_DIR/dataset_stats.npy" "$LOCAL_EXP/dataset_stats.npy"
ln -s "$UNIMATE_EXP_DIR/checkpoints" "$LOCAL_EXP/checkpoints"

python - "$LOCAL_EXP/config.json" "$PRE_DIR" <<'PY'
import json
import os
import sys

path, custom_feature_dir = sys.argv[1:3]
with open(path) as f:
    cfg = json.load(f)

cfg.setdefault("objaverse", {})
cfg["objaverse"]["path"] = os.path.abspath(custom_feature_dir)
cfg["objaverse"]["objects_num"] = -1
cfg["objaverse"]["filter_object"] = False
cfg["dataset"]["dataset_list"] = ["objaverse"]

# The released checkpoint's saved max_joints/max_depth must remain unchanged.
# Do not recompute model tensor dimensions from the EvoWild rig.
if int(cfg["dataset"].get("max_joints", 0)) <= 0 or int(cfg["dataset"].get("max_depth", 0)) <= 0:
    raise SystemExit(
        "released config is missing saved max_joints/max_depth; "
        "use the config shipped with the released checkpoint, not the training template"
    )

with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
PY

pushd "$UNIMATE_DIR" >/dev/null

python -m unimate.inference.sample   --exp_dir "$LOCAL_EXP"   --test_cases_json "$CASES_JSON"   --num_repetitions "$REPETITIONS"   --batch_size 4   --seed 20261001   --output_dir "$SAMPLES_DIR"

CANONICAL_GLB="$(find "$PRE_DIR" -maxdepth 1 -name '*_canonical.glb' -print -quit)"
[[ -n "$CANONICAL_GLB" ]] || { echo "canonical GLB was not produced" >&2; exit 4; }

CHAR_PATH="$CANONICAL_GLB" ANIM_PATH="$SAMPLES_DIR/motions" DATASET_TYPE=objaverse COND_PATH="$PRE_DIR/cond.npy" OUTPUT_DIR="$ANIMATED_DIR" SAVE=glb bash data_process/scripts/run_animate_lbs.sh

popd >/dev/null

echo "UniMate S bench complete."
echo "work:      $WORK_DIR"
echo "motions:   $SAMPLES_DIR/motions"
echo "animated:  $ANIMATED_DIR"
echo "next: fill docs/reviews/unimate-s-motion-bench-review-template.md with measured results"
