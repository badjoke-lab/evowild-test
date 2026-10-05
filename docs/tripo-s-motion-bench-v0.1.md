# EvoWild Run — Tripo S Motion Bench v0.2

Status: **isolated experiment / not production-approved**

Branch: `exp/tripo-s-motion-bench-20261003`

Current main reference at v0.2 rewrite: `475e1ff6c1e047b227fa400215714994edc40368`

## Purpose

Determine whether Tripo Auto Rig + Text to Motion can produce reusable race locomotion for EvoWild S without weakening grounded contact, gait phase, body mechanics, export stability, or runtime control.

## Critical target distinction

This bench does **not** define the final S morphology.

The current Tripo primary input `public/models/evowild-s/source-lod2.glb` is the older Hunyuan-derived S family currently present on main. It is used here as a **motion/rig feasibility carrier only** because it is a clean unrigged quadruped-family mesh already available to the runtime.

A T0/T1 pass on that asset proves only that Tripo can rig/animate that carrier well enough to justify deeper testing. It does **not** prove that the final EvoWild S shape is correct, and it does **not** authorize the Hunyuan source-lod2 silhouette as the final S target.

Final S morphology authority remains in the dedicated S modeling lane, led by `art/s-creature/S_MODELING_IMAGE_LOCK.md` and its approved reference set. The current Vibe lane has an accepted Gate-A silhouette family but Gate-B anatomical massing remains open; therefore there is no production-final S mesh yet.

No Tripo motion result may be promoted to production-final S animation until it is rerun or retargeted onto a morphology-approved, rig-ready S asset.

If the primary “S-type Modeling Image v1.0” is not repository-accessible to the reviewer, no automated lane may claim final morphology conformance from repository evidence alone. That missing authority must be resolved before final S visual acceptance.

This lane is isolated. It must not modify the active Vibe Modeling, Motion First, UniMate, 2.5D, Sakura, Sprite, or Hunyuan production lanes.

## Repository-first evidence rule

**No manual file handoff through chat is part of this workflow.**

Every real Tripo result required for a decision must be placed on this branch before the task is reported complete.

Required repository locations:

- `art/motion/tripo-s/raw/` — untouched Tripo exports when repository-safe
- `art/motion/tripo-s/normalized/` — any DCC/runtime-normalized copy
- `public/experiments/tripo-s/` — web-reviewable GLB used by the review page
- `art/motion/tripo-s/review/` — metadata and durable review records
- `docs/reviews/tripo-s-motion-bench-review.md` — gate decision ledger

Required CI evidence after a real T1 asset is committed:

- SIDE screenshot
- LOW screenshot
- CHASE screenshot
- FRONT screenshot
- continuous review video
- animation/runtime metadata

CI evidence is uploaded as a GitHub Actions artifact named `tripo-s-motion-review`.

The reviewer must be able to fetch the branch and the Actions artifact directly. A completion report that only says “download this attachment” or requires the user to paste files manually is invalid.

If a raw Tripo export is too large for normal GitHub storage, do not omit the reviewable result. Commit a normalized GLB under `public/experiments/tripo-s/` plus metadata recording the raw file name, byte size, Tripo export format, and any external source URL available to the Work session. Never commit credentials, signed private URLs, tokens, or API keys.

## Model policy

There are three different model roles. Do not mix them.

### Tripo primary Auto Rig input — Geometry LOD2

Use:

`public/models/evowild-s/source-lod2.glb`

Repository manifest role:

- canonical S shape/edit source
- unrigged
- approximately 13,270 triangles

Reason:

Tripo Auto Rig creates a new skeleton and skin binding. Testing Auto Rig on the already-rigged v5 asset would confound Tripo rig quality with the existing EvoWild 19-bone rig. The clean test is the canonical unrigged S geometry.

Tripo settings:

- rig model/version: `v2.5-20260210` when Studio/API exposes the version explicitly
- rig family: non-humanoid / creature
- rig type: `quadruped`
- output preference: `GLB` for repository/Web review
- do not force `biped`

### Tripo fallback Auto Rig input — Geometry LOD4

Use only if LOD2 fails for a clearly geometry-density/import-performance reason:

`public/models/evowild-s/race-lod4.glb`

Repository manifest role:

- unrigged
- approximately 3,316 triangles
- same canonical S family

LOD4 is **not** allowed to rescue a bad quadruped skeleton caused by S morphology. It is only a density/import fallback.

### Existing EvoWild motion comparison reference

Use:

`public/models/evowild-s/focus-rigged-v5.glb`

Repository manifest role:

- near-camera/current gait-review candidate
- rigged
- 19 bones
- stance-direction corrected

This is the Motion First comparison reference. It is **not the primary Tripo Auto Rig input**.

Do not use:

- `focus-rigged-v5-headfix.glb` as primary input; it is a candidate, not the canonical motion baseline
- current Vibe Modeling B1 assets; morphology is still under separate approval
- v31; repository history already rejects it as the active motion baseline

## Test levels

“Level” in this bench means motion-test complexity, not geometry LOD.

### T0 — Auto Rig / export compatibility

Input: canonical unrigged LOD2.

Confirm:

- upload/import intact
- Tripo rig check accepts or meaningfully classifies the model
- `quadruped` path completes
- four limbs remain distinct
- knees/ankles do not reverse or collapse at neutral
- head, neck, spine and tail remain usable
- exported rigged GLB/FBX can be re-opened
- no destructive scale/orientation change prevents comparison

Primary T0 output:

`public/experiments/tripo-s/t0-rigged-lod2.glb`

If LOD2 fails only because of density/import handling, run one controlled LOD4 fallback and record that fact. Do not silently switch models.

T0 decisions:

- `PASS_TO_T1`
- `PASS_TO_T1_WITH_LOD4_FALLBACK`
- `REJECT_IMPORT_OR_RIG`

### T1 — steady straight run, one generation only

Do **not** start with max sprint.

Generate one 5-second Text to Motion candidate using exactly this motion target:

`A quadruped creature runs straight forward at a steady racing speed. Powerful hind-leg propulsion, clear alternating foot contacts, stable athletic torso, minimal vertical bouncing, head facing forward. Natural grounded foot contact. Continuous run.`

Do not add appearance, camera, environment, lore, lighting, race tactics, overtaking, fatigue, or Multi-stage instructions.

Primary review asset:

`public/experiments/tripo-s/t1-steady-run.glb`

Required checks:

- stance foot skating
- penetration / floating
- fore/hind phase coherence
- reversed/collapsing joints
- root travel vs cadence
- shoulder/chest contribution
- pelvis drive
- spine compression/extension
- torso vertical bounce
- head/neck stability
- tail behavior
- export/re-import stability
- SIDE / LOW / CHASE / FRONT readability

T1 decisions:

- `PASS_TO_T2`
- `KEEP_AS_REFERENCE`
- `REJECT`

No T2 work is allowed unless T1 = `PASS_TO_T2`.

### T2 — acceleration

One candidate first:

`The quadruped continues a steady forward racing run, then smoothly accelerates into a fast sprint while staying grounded. Cadence increases naturally, hind-leg propulsion becomes stronger, torso remains athletic and stable, head stays forward.`

Review cadence transition, root-speed continuity, stance slip, body compression, head stability and export replay.

### T3 — lateral race movement / overtake mechanics

Only after T2 passes.

Test in this order:

1. slight lateral shift while preserving forward speed
2. overtake-attempt motion while preserving continuous forward locomotion

Do not jump directly to a complex multi-agent choreography.

### T4 — Multi-stage Motion

Only after T1–T3 are individually usable.

Target sequence:

`steady run -> accelerate -> slight lateral shift -> overtake attempt -> return to straight sprint`

Multi-stage must be compared against the separately generated single-stage motions. A visually impressive sequence does not override bad contact or uncontrollable root motion.

### T5 — EvoWild runtime integration

Only after T4 or a subset of T1–T3 is worth keeping.

Candidate architecture:

`Tripo motion -> EvoWild contact correction -> speed/cadence mapping -> race-state blending -> Three.js runtime`

Tripo must not replace:

- Race Engine movement/state
- Race Agent decisions
- camera director
- Creature morphology authority

## Acceptance rule

Tripo viewport quality alone never passes a gate.

Every pass requires:

`Tripo generation -> export -> repository commit -> EvoWild review page / runtime replay -> CI multi-view evidence -> decision`

## Stop rule

After each test level:

`generate/export -> commit real artifact -> CI review -> inspect evidence -> decision -> next level`

No speculative expansion.
