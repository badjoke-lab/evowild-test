# BlendCap S Motion Bench — Review Ledger

Branch: `exp/blendcap-s-motion-bench-20261003`

Status: `GATE2_PASS / GATE3_PENDING`

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

Required model access: `PASS — required model materials downloaded successfully in isolated Gate 1 workflow`

Gate 0 decision: `PASS_CPU_TEST`

Allowed values:

- `PASS_CPU_TEST`
- `PASS_GPU_TEST`
- `BLOCKED_ENV`
- `REJECT_COST_OR_DEPENDENCY`

Reason: `Pinned source, Blender 4.2.23, disk, Python 3.12, S asset, and headless add-on registration all passed on the free Linux runner. No NVIDIA GPU is present, so the next capture test is CPU-only unless moved to another environment.`

## Gate 1 — video -> BVH

Status: `PASS_REAL_BVH`

Input source: `Public-domain U.S. Marine Corps Sakura Sprint 5K B-Roll (DVIDS 1001990)`

Technical excerpt: `17.5s -> 20.5s, 3.0 seconds, 960x540, 30 fps, no audio`

Full body continuously visible: `YES for target runner after initial sampled frame`

Detector preview evidence: GitHub Actions run `37211846424`

Detector result: `29/30 sampled frames BODY OK; 1/30 initial sampled frame no person`

Target continuity: `PASS — one dominant runner tracked by YOLO11 bounding box throughout the usable motion`

Preview visual review: `PASS — bounding box stays on the intended black-shirt / pink-shorts runner as he approaches camera`

BVH generated: `YES`

Full-capture evidence: GitHub Actions run `37212143343`

Capture settings: `10 SAM samples across 90 input frames; capture-skip 8; no hands; fixed 50mm focal estimate`

Dense output: `81 frames at 30 fps / 2.66664 seconds`

CPU capture time: `15:00 wall clock`

Peak resident memory: `~5.97 GB`

BVH artifact: `output.bvh / 118,645 bytes / 54 body joints`

Tracking overlay: `PASS visual continuity on intended runner`

Tracking cleanup: `clean-tracking + grounding + footskate cleanup; 113 frame-foot pairs modified`

Tracking failures observed: `initial detector miss only; no recovered previous-bbox samples reported by full capture`

Decision: `PASS_TO_DECOMPOSITION`

## Gate 2 — motion decomposition

Status: `PASS_DECOMPOSITION`

Evidence: GitHub Actions run `37260085555`

S rig inspected: `19 bones / existing EvoWild_S_Run_V5 action / frame range 1-25`

Explicit S body mapping:

- source hips / pelvis signal -> `pelvis`
- source torso pitch/roll -> `spine` + `chest`
- delayed upper-body pitch -> `neck` + `head`
- source vertical oscillation -> small root/object-space vertical offset only
- existing S fore/hind limb animation remains authoritative

Root travel usable: `NO as literal world-speed input` — monocular/camera-relative forward translation is not trusted as race locomotion distance.

Pelvis drive usable: `YES` — captured pelvis pitch range 3.63 deg; roll range 4.73 deg.

COM rise/fall usable: `YES WITH LOW GAIN` — hips vertical range 0.1783 source units.

Torso pitch/roll usable: `YES WITH LOW GAIN` — average torso pitch range 2.2765 deg; roll range 2.54365 deg.

Launch timing usable: `NO` — this clip is an approach/run sample, not a launch/start clip.

Cadence envelope usable: `YES AS TIMING REFERENCE` — left/right leg pitch proxy both estimate ~23 frames / 0.7667 s / 1.304 cycles per second. Existing S V5 action is 25 frames, close enough for a first hybrid comparison without replacing the quadruped limb cycle.

Direct human limb mapping used: `NO`

Notes: `Gate 2 decision READY_FOR_EXPLICIT_HYBRID_MAPPING. Human limbs remain excluded. Gate 3 will layer only low-gain body signals over the existing S V5 quadruped animation.`

## Gate 3 — S hybrid render

Status: `V1_REVISE / V2_RUNNING`

V1 evidence: GitHub Actions run `37261156501`

V1 hypothesis: low-gain BlendCap body motion layered over the existing S V5 quadruped limb animation, with no direct human-limb mapping.

V1 SIDE artifact: `side-comparison.jpg`

V1 LOW artifact: `low-comparison.jpg`

V1 CHASE artifact: `chase-comparison.jpg`

V1 FRONT artifact: `front-comparison.jpg`

V1 visual review:

- SIDE: BlendCap body layer is visible, but the strongest visible change is whole-body/foot vertical displacement rather than clearly improved trunk dynamics.
- LOW: contact position changes are easy to see; the layer is not yet contact-neutral.
- CHASE / FRONT: the body-dynamics gain is too subtle to justify the contact perturbation.
- V1 maximum foot world displacement is 0.05004 on a 2.0-unit creature, about 2.50% of creature height; maximum vertical foot displacement is 0.02793.
- Therefore V1 is not accepted as a runtime hybrid.

V1 decision: `REVISE`

V2 exact hypothesis: remove direct captured root-vertical transfer, preserve existing S V5 world-space locomotion, keep only low-gain pelvis/spine/chest/neck/head rotations, and compensate the baseline stance foot vertically after the body layer is applied.

V2 workflow: `blendcap-gate3-hybrid-v2`

SIDE artifact: `PENDING_V2`

LOW artifact: `PENDING_V2`

CHASE artifact: `PENDING_V2`

FRONT artifact: `PENDING_V2`

| Check | Motion First baseline | BlendCap hybrid | Result |
|---|---|---|---|
| stance skating | existing V5 baseline | V1 static review only | V2 must preserve baseline stance height |
| penetration / float | baseline reference | V1 changed foot height up to 0.02793 | REVISE V1 |
| fore/hind phase | existing V5 authoritative | unchanged by BlendCap | KEEP V5 |
| root/cadence match | existing race/root motion | captured root translation rejected | KEEP race root |
| pelvis drive | V5 baseline | V1 body layer visible | CONTINUE V2 |
| torso contribution | V5 baseline | V1 subtle | CONTINUE V2 |
| spine compression/extension | V5 baseline | low-gain rotational proxy only | CONTINUE V2 |
| neck/head follow-through | V5 baseline | low-gain signal present | CONTINUE V2 |
| launch posture | not tested by source clip | not tested | DEFER |
| high-speed readability | existing V5 baseline | static Gate 3 review insufficient | ANIMATED REVIEW REQUIRED |

## Final decision

Decision: `NOT_RUN`

Allowed values:

- `PASS_TO_HYBRID`
- `KEEP_AS_REFERENCE`
- `REJECT`

Reason: `UNSET`

Exact next action: `COMPLETE_GATE3_V2_CONTACT_COMPENSATED_RENDER_THEN_RUN_SHORT_SIDE_LOW_ANIMATED_REVIEW_IF_V2_STATIC_PASS`
