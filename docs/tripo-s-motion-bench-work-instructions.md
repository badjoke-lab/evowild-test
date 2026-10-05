# Tripo S Motion Bench — Work execution instructions v0.2

Repository: `badjoke-lab/evowild-test`

Branch: `exp/tripo-s-motion-bench-20261003`

Do not create another branch.

## Read first

- `docs/tripo-s-motion-bench-v0.1.md`
- `docs/reviews/tripo-s-motion-bench-review.md`
- `art/motion/tripo-s/bench-manifest.json`

## Hard rule: repository-first handoff

Do not finish by attaching files only in chat.

Before reporting a gate complete:

1. commit the real export or the repository-safe normalized GLB;
2. commit/update the review metadata and ledger;
3. push this exact branch;
4. wait for the branch/PR CI review job;
5. report the commit SHA and Actions run ID.

The downstream reviewer will fetch the evidence directly from GitHub / Actions. Manual user download-and-reupload is not part of the workflow.

Never commit credentials, API keys, session cookies, signed private URLs, or other secrets.

## Model and geometry LOD

### Primary Tripo input

Use exactly:

`public/models/evowild-s/source-lod2.glb`

This is the canonical unrigged S shape source (~13,270 triangles).

Reason: Tripo Auto Rig is being evaluated. It should create its own quadruped skeleton from clean canonical geometry rather than being confused with the existing EvoWild v5 rig.

### Density fallback only

If and only if LOD2 fails for an import/geometry-density reason, try:

`public/models/evowild-s/race-lod4.glb`

This is the unrigged lower-density S (~3,316 triangles).

Do not use LOD4 merely because the LOD2 quadruped skeleton looks bad. A bad skeleton is a T0 failure, not permission to hide the problem.

### Comparison reference

Use:

`public/models/evowild-s/focus-rigged-v5.glb`

only as the current EvoWild near-camera motion reference.

Do not Auto Rig this first. It already contains the existing 19-bone v5 rig and would confound the Tripo rigging test.

Do not substitute:

- `focus-rigged-v5-headfix.glb`
- v31
- current Vibe Modeling/B1 assets

## T0 — Auto Rig / export compatibility

1. Fetch latest remote branch before work.
2. Upload `source-lod2.glb` to Tripo Studio.
3. Run rig-check / compatibility check if the Studio UI exposes it.
4. Select the creature/non-humanoid rig path and `quadruped`.
5. Do not force `biped`.
6. Run Auto Rig.
7. Inspect neutral pose and actual skeleton result.
8. Confirm four limbs, joints, spine, neck, head and tail remain usable.
9. Export the rigged result as GLB if available. FBX may also be preserved.
10. Re-open/re-import the export before passing T0.

Required repository output:

- `public/experiments/tripo-s/t0-rigged-lod2.glb`
- optional untouched raw export under `art/motion/tripo-s/raw/`
- `art/motion/tripo-s/review/t0-session.json`
- updated `docs/reviews/tripo-s-motion-bench-review.md`

If LOD2 fails specifically from density/import handling, record the failure and run one LOD4 fallback. Name it explicitly:

`public/experiments/tripo-s/t0-rigged-lod4-fallback.glb`

T0 decision:

- `PASS_TO_T1`
- `PASS_TO_T1_WITH_LOD4_FALLBACK`
- `REJECT_IMPORT_OR_RIG`

If rejected, stop.

## T1 — Text to Motion: steady straight run only

Only after T0 passes.

Use Tripo Studio's Text to Motion / Create Your Own Animation flow.

Generate exactly one 5-second candidate using this prompt:

`A quadruped creature runs straight forward at a steady racing speed. Powerful hind-leg propulsion, clear alternating foot contacts, stable athletic torso, minimal vertical bouncing, head facing forward. Natural grounded foot contact. Continuous run.`

Do not add:

- maximum sprint
- acceleration
- turning
- lateral movement
- overtaking
- fatigue
- camera
- appearance
- environment
- lore
- Multi-stage Motion

The purpose is to isolate basic quadruped locomotion quality.

## T1 export

Prefer an animation-bearing GLB because the repository review page can replay it directly.

Required review asset:

`public/experiments/tripo-s/t1-steady-run.glb`

If Tripo's best untouched export is FBX, also preserve it under:

`art/motion/tripo-s/raw/t1-steady-run.fbx`

Then create a separate GLB review copy without overwriting the raw FBX.

Record conversion/normalization details in:

`art/motion/tripo-s/review/t1-session.json`

## T1 review automation

Once `public/experiments/tripo-s/t1-steady-run.glb` is committed and pushed, CI must run the Tripo review page and produce:

- `tripo-t1-side.png`
- `tripo-t1-low.png`
- `tripo-t1-chase.png`
- `tripo-t1-front.png`
- `tripo-t1-motion-review.webm`

as GitHub Actions artifact:

`tripo-s-motion-review`

Do not ask the user to download and paste these back. The reviewer will fetch the artifact directly.

Required failure checks:

- foot skating
- penetration / floating
- reversed/collapsing knees or ankles
- fore/hind phase coherence
- root-motion/cadence mismatch
- shoulder/pelvis drive
- spine behavior
- excessive torso bounce
- head/neck stability
- tail behavior
- export stability
- replay stability

T1 decision:

- `PASS_TO_T2`
- `KEEP_AS_REFERENCE`
- `REJECT`

Stop after T1 decision unless it is `PASS_TO_T2`.

## T2 — acceleration

One candidate only first. Use the prompt from the bench spec.

Commit/export/review with the same repository-first rule before any T3 work.

## T3 — lateral shift / overtake

Test slight lateral shift before overtake attempt.

Do not generate Multi-stage Motion yet.

## T4 — Multi-stage Motion

Only after T1–T3 have usable individual results.

## T5 — runtime integration

Only after the motion itself earns adoption.

## Completion report

Report only after push:

- input model and geometry LOD used
- T0 result
- T1 result
- exact repository artifact paths
- exact CI artifact name
- Actions run ID
- commit SHA
- any normalization/conversion performed
- credits consumed, if visible
- whether paid credits were required

Do not report a pass from the Tripo viewport alone.
