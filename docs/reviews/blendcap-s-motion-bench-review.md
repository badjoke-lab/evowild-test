# BlendCap S Motion Bench — Review Ledger

Branch: `exp/blendcap-s-motion-bench-20261003`

Status: `GATE0_NOT_RUN`

Base main: `d25553169e4406f5af660fc5559e075163aac6ff`

BlendCap pin: `e3238699507c00e34b6c948931c4742915b8dc42`

EvoWild input: `public/models/evowild-s/focus-rigged-v5.glb`

## Gate 0A — upstream source audit

Status: `PASS_SOURCE_AUDIT`

Verified against pinned upstream source:

- Blender manifest minimum is 4.2.0
- source-build requirements target Python 3.12
- CPU-only execution is explicitly patched in `save_mhr_data.py`
- Apple Silicon has an MPS fallback path, but the paid build remains officially unsupported on macOS
- custom target rigs are supported through the bone-map editor
- SAM 3D Body weights are required and gated by Meta license acceptance
- YOLO11 pose weights are required
- source build is explicitly unsupported by the vendor even though source is available

This source audit does **not** prove the user's Intel Mac can complete capture at practical speed.

## Gate 0B — execution environment

Probe result: `UNSET`

OS: `UNSET`

Architecture: `UNSET`

Python: `UNSET`

Blender: `UNSET`

Free disk: `UNSET`

Git: `UNSET`

GPU path: `UNSET`

CPU-only fallback: `UNSET`

Required model access: `UNSET`

Gate 0 decision: `NOT_RUN`

Allowed values:

- `PASS_CPU_TEST`
- `PASS_GPU_TEST`
- `BLOCKED_ENV`
- `REJECT_COST_OR_DEPENDENCY`

Reason: `UNSET`

## Gate 1 — video -> BVH

Status: `NOT_RUN`

Input clip: `UNSET`

Clip duration: `UNSET`

Full body continuously visible: `UNSET`

BVH generated: `NO`

BVH path: `UNSET`

Tracking failures observed: `UNSET`

Decision: `NOT_RUN`

## Gate 2 — motion decomposition

Status: `NOT_RUN`

Root travel usable: `UNSET`

Pelvis drive usable: `UNSET`

COM rise/fall usable: `UNSET`

Torso pitch/roll usable: `UNSET`

Launch timing usable: `UNSET`

Cadence envelope usable: `UNSET`

Direct human limb mapping used: `NO`

Notes: `UNSET`

## Gate 3 — S hybrid render

Status: `NOT_RUN`

SIDE artifact: `UNSET`

LOW artifact: `UNSET`

CHASE artifact: `UNSET`

FRONT artifact: `UNSET`

| Check | Motion First baseline | BlendCap hybrid | Result |
|---|---|---|---|
| stance skating | UNSET | UNSET | UNSET |
| penetration / float | UNSET | UNSET | UNSET |
| fore/hind phase | UNSET | UNSET | UNSET |
| root/cadence match | UNSET | UNSET | UNSET |
| pelvis drive | UNSET | UNSET | UNSET |
| torso contribution | UNSET | UNSET | UNSET |
| spine compression/extension | UNSET | UNSET | UNSET |
| neck/head follow-through | UNSET | UNSET | UNSET |
| launch posture | UNSET | UNSET | UNSET |
| high-speed readability | UNSET | UNSET | UNSET |

## Final decision

Decision: `NOT_RUN`

Allowed values:

- `PASS_TO_HYBRID`
- `KEEP_AS_REFERENCE`
- `REJECT`

Reason: `UNSET`

Exact next action: `RUN_GATE0_EXECUTION_PROBE`
