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

Probe result: `PASS`

Execution evidence: GitHub Actions run `37183790209`

OS: `Linux / x86_64`

Architecture: `x86_64`

Python: `3.12.3`

Blender: `4.2.23 LTS`

Free disk: `84.43 GB`

Git: `PASS`

GPU path: `NO NVIDIA ON HOSTED RUNNER`

CPU-only fallback: `AVAILABLE`

Pinned BlendCap checkout: `e3238699507c00e34b6c948931c4742915b8dc42`

Blender add-on import: `PASS`

Blender add-on register: `PASS`

Blender add-on unregister: `PASS`

Required model access: `NOT DOWNLOADED — SAM License acceptance required before accessing model materials`

Gate 0 decision: `PASS_CPU_TEST`

Allowed values:

- `PASS_CPU_TEST`
- `PASS_GPU_TEST`
- `BLOCKED_ENV`
- `REJECT_COST_OR_DEPENDENCY`

Reason: `Pinned source, Blender 4.2.23, disk, Python 3.12, S asset, and headless add-on registration all passed on the free Linux runner. No NVIDIA GPU is present, so the next capture test is CPU-only unless moved to another environment.`

## Gate 1 — video -> BVH

Status: `DETECTOR_PREVIEW_PASS / FULL_CAPTURE_PENDING`

Input source: `Public-domain U.S. Marine Corps Sakura Sprint 5K B-Roll (DVIDS 1001990)`

Technical excerpt: `17.5s -> 20.5s, 3.0 seconds, 960x540, 30 fps, no audio`

Full body continuously visible: `YES for target runner after initial sampled frame`

Detector preview evidence: GitHub Actions run `37211846424`

Detector result: `29/30 sampled frames BODY OK; 1/30 initial sampled frame no person`

Target continuity: `PASS — one dominant runner tracked by YOLO11 bounding box throughout the usable motion`

Preview visual review: `PASS — bounding box stays on the intended black-shirt / pink-shorts runner as he approaches camera`

BVH generated: `NO — SAM 3D Body full capture not run yet`

BVH path: `UNSET`

Tracking failures observed: `none at detector-preview stage except first sampled frame`

Decision: `PROCEED_TO_FULL_CAPTURE`

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

Exact next action: `RUN_GATE1_SHORT_CPU_SAM_CAPTURE_THEN_CONVERT_REAL_NPZ_TO_BVH`
