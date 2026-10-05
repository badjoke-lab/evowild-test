# Tripo S Motion Bench — Review Ledger v0.2

Branch: `exp/tripo-s-motion-bench-20261003`

Status: `T0_BLOCKED_BROWSER_WEBGL`

## 2026-10-05 authenticated retry

- Authentication blocker resolved: signed-in `badjoke.lab` page confirmed, displayed credits **200 -> 200**.
- Latest remote verified: `ac078d8511706289fc4a10e29c9e0096e4bc8123`.
- Exact LOD2 file selected through Tripo Studio Rig upload. The `Find the Best Angle` preview stayed blank; `Confirm` did not advance. Upload persistence to Assets is **unverified**.
- Tripo console: `THREE.WebGLRenderer: Error creating WebGL context.` The detailed error identified `GL_VENDOR = Disabled` and `GL_RENDERER = Disabled`.
- One reload/retry ended at `Something went wrong / Please try again later`. This is a browser execution blocker, not a rig rejection or model-density failure.
- T0 has **no decision**: Auto Rig not submitted, rig type/version not actually used, no export or re-import. T1 and T2 not started. No credits consumed, purchase, conversion, or LOD4 fallback.
- Durable evidence: `art/motion/tripo-s/review/t0-session.json`, `t0-webgl-console-excerpt.txt`, and `t0-webgl-blocked-20261005.jpg` in the same review directory.
- Resume requires a supported WebGL-capable Tripo Studio execution surface. Do not request another login or manual download/re-upload as a solution to this renderer failure. Run T0 first, one T1 only if T0 passes, and stop after T1.

## 2026-10-05 initial execution attempt (superseded blocker)

- Latest remote checked out and fast-forward verified: `3d19579df88f4bb52ffd929595d98e4f8a5bf72a`.
- Session evidence: `art/motion/tripo-s/review/t0-session.json`.
- Exact LOD2 input parsed locally: valid GLB v2 header/length, 156,000 bytes, one mesh, **12,940 triangles**, zero skins, zero animation clips. The spec's approximate 13,270 count differs from the actual file; the prescribed path was retained unchanged.
- Tripo Studio was signed out. Google was selected through secure browser authentication, but the Tripo tab became unavailable. A fresh target-origin check still showed `Sign up/Log in`; another click on the selected Google control again lost the tab.
- **T0 not executed; no PASS or rig-quality rejection recorded.** Upload, rigging, export and re-import have not occurred. This is an access blocker, not evidence of an incompatible rig.
- T1 not generated; T2 not started. No density fallback and no conversion/normalization performed. No generation requests submitted; no credits spent by this attempt; account balance unavailable.
- CI currently skips both Tripo tests because the real T1 GLB is absent. A successful build is not motion-review evidence; `tripo-s-motion-review` is not expected yet.
- Resume with authenticated Tripo Studio, run T0 on the locked LOD2 input, then exactly one T1 only if T0 passes. Stop after T1 pending external review. Never substitute the existing EvoWild rig for a Tripo output.

## Model lock

Primary Tripo Auto Rig input:

`public/models/evowild-s/source-lod2.glb`

Geometry level: `LOD2`

Rig state: `UNRIGGED`

Approx triangles: `13270`

Fallback only for clear import/density failure:

`public/models/evowild-s/race-lod4.glb`

Geometry level: `LOD4`

Rig state: `UNRIGGED`

Approx triangles: `3316`

Existing EvoWild comparison reference:

`public/models/evowild-s/focus-rigged-v5.glb`

Role: current 19-bone near-camera Motion First reference, **not** primary Tripo Auto Rig input.

## T0 — Auto Rig / export compatibility

Input used: `UNSET`

Geometry LOD used: `UNSET`

Import result: `UNSET`

Rig check result: `UNSET`

Recommended/selected rig type: `UNSET`

Tripo creature/non-humanoid rig path used: `UNSET`

Four limbs intact: `UNSET`

Joint direction sane: `UNSET`

Head / neck / spine / tail intact: `UNSET`

Scale/orientation usable: `UNSET`

Rigged export re-opened successfully: `UNSET`

Primary repository artifact: `UNSET`

Fallback attempted: `NO`

T0 decision: `UNSET`

Allowed:

- `PASS_TO_T1`
- `PASS_TO_T1_WITH_LOD4_FALLBACK`
- `REJECT_IMPORT_OR_RIG`

Reason: `UNSET`

Exact next action: `RESTORE_WEBGL_CAPABLE_EXECUTION_THEN_RUN_T0_ON_SOURCE_LOD2`

## T1 — steady straight run

Generator: `Tripo Studio Text to Motion / Create Your Own Animation`

Duration target: `5s`

Prompt:

`A quadruped creature runs straight forward at a steady racing speed. Powerful hind-leg propulsion, clear alternating foot contacts, stable athletic torso, minimal vertical bouncing, head facing forward. Natural grounded foot contact. Continuous run.`

Raw artifact: `UNSET`

Review GLB:

`public/experiments/tripo-s/t1-steady-run.glb`

Normalization required: `UNSET`

CI artifact: `tripo-s-motion-review`

Actions run: `UNSET`

### T1 measurements

| Check | EvoWild focus-rigged-v5 reference | Tripo T1 | Note |
|---|---|---|---|
| stance foot skating | baseline | UNSET | UNSET |
| penetration / floating | baseline | UNSET | UNSET |
| fore/hind phase coherence | baseline | UNSET | UNSET |
| joint reversal / collapse | baseline | UNSET | UNSET |
| root / cadence match | baseline | UNSET | UNSET |
| shoulder / chest drive | baseline | UNSET | UNSET |
| pelvis drive | baseline | UNSET | UNSET |
| spinal compression / extension | baseline | UNSET | UNSET |
| torso vertical bounce | baseline | UNSET | UNSET |
| head / neck stability | baseline | UNSET | UNSET |
| tail behavior | baseline | UNSET | UNSET |
| SIDE readability | baseline | UNSET | UNSET |
| LOW readability | baseline | UNSET | UNSET |
| CHASE readability | baseline | UNSET | UNSET |
| FRONT readability | baseline | UNSET | UNSET |
| export / replay stability | baseline | UNSET | UNSET |

T1 decision: `UNSET`

Allowed:

- `PASS_TO_T2`
- `KEEP_AS_REFERENCE`
- `REJECT`

Reason: `UNSET`

## T2 — acceleration

Status: `BLOCKED_BY_T1`

Prompt:

`The quadruped continues a steady forward racing run, then smoothly accelerates into a fast sprint while staying grounded. Cadence increases naturally, hind-leg propulsion becomes stronger, torso remains athletic and stable, head stays forward.`

Decision: `UNSET`

## T3 — lateral shift / overtake

Status: `BLOCKED_BY_T2`

Order:

1. slight lateral shift while maintaining forward speed
2. overtake attempt without stopping forward locomotion

Decision: `UNSET`

## T4 — Multi-stage Motion

Status: `BLOCKED_BY_T3`

Target:

`steady run -> accelerate -> slight lateral shift -> overtake attempt -> return to straight sprint`

Decision: `UNSET`

## T5 — EvoWild runtime integration

Status: `BLOCKED`

Candidate architecture:

`Tripo motion -> contact correction -> speed/cadence mapping -> race-state blending -> Three.js runtime`

Final decision: `UNSET`
