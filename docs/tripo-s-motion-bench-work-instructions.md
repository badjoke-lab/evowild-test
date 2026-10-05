# Tripo S Motion Bench — Work execution instructions

Repository: `badjoke-lab/evowild-test`

Branch: `exp/tripo-s-motion-bench-20261003`

Do not create another branch.

## Read first

- `docs/tripo-s-motion-bench-v0.1.md`
- `docs/reviews/tripo-s-motion-bench-review.md`
- `art/motion/tripo-s/bench-manifest.json`

## Hard scope

This task is Tripo motion evaluation only.

Do not modify:

- `exp/s-creature-vibe-modeling`
- `feat/s-creature-model`
- Motion First production/runtime behavior
- UniMate bench
- 2.5D / Sakura / Sprite / Hunyuan lanes

Locked input:

`public/models/evowild-s/focus-rigged-v5.glb`

Do not substitute a Vibe Modeling asset.

## T0 — import / rig compatibility

1. Obtain the locked GLB from the repository.
2. Open Tripo Studio and import/upload that GLB.
3. Before spending rigging credits, run Tripo's riggability / rig check when available. Record whether Tripo recognizes the asset as riggable and whether it recommends `quadruped`.
4. If the check passes, run Auto Rig using the quadruped path. Do not use biped merely to force success.
5. Inspect the actual rigged model before generating motion.
6. Confirm all four limbs remain distinct, head / neck / tail remain present, left/right joint orientation is sane, and no destructive topology/orientation change prevents comparison.
7. Record T0 evidence in `docs/reviews/tripo-s-motion-bench-review.md`.

If import or rigging is broken, set T0 to `REJECT_IMPORT` and stop.

## T1 — Text to Motion, one sprint only

Only if T0 passes, use Tripo Studio's **Create Your Own Animation / AI Animation (Text to Motion)** flow.

Generate exactly **one** 5-second candidate first:

`maximum-effort forward quadrupedal sprint, explosive long stride, strong shoulder and pelvis drive, stable forward travel`

Do not add camera, appearance, environment, lore, race-strategy or lighting words.

Do not use Multi-stage Motion yet. Do not generate the other eleven clips yet.

The purpose of T1 is to answer one question only: does Tripo's generated custom motion survive on the locked EvoWild S rig well enough to justify expansion?

## Export

Export the real animated 3D result in the best reusable supported format.

Prefer FBX with skeleton + the generated animation when the Studio export offers it; GLB is acceptable if it preserves the required animation data more reliably.

Preserve an untouched copy under:

`art/motion/tripo-s/raw/`

If normalization is needed for EvoWild replay, write a separate artifact under:

`art/motion/tripo-s/normalized/`

Never overwrite the raw export.

## Review evidence

Replay the exported 3D animation, not only the Tripo viewport, and capture:

- SIDE
- LOW
- CHASE
- FRONT

Store evidence under:

`art/motion/tripo-s/review/`

Then fill the T1 comparison table against Motion First v5.

Required failure checks include foot skating, penetration/floating, reversed or collapsing knees, fore/hind phase coherence, shoulder/pelvis drive, spine behavior, head/neck follow-through, tail behavior, root-motion/cadence mismatch, export stability and replay stability.

Allowed T1 decisions:

- `EXPAND`
- `KEEP_AS_REFERENCE`
- `REJECT`

Stop after the T1 decision. Do not generate T2 unless the decision is explicitly `EXPAND`.

## T2 — only after T1 = EXPAND

At T2, test the existing four-motion matrix and three repetitions per motion.

Only here may Multi-stage Motion be evaluated, first as a separate experimental candidate such as:

`steady run -> accelerate to maximum sprint -> slight lateral move while maintaining forward speed -> return to straight sprint`

Do not replace the single-action T2 clips with one multi-stage clip; compare them separately.

## Completion report

Report:

- T0 rig-check result
- T0 decision
- T1 decision
- exact exported artifact paths
- exact review image/video paths
- whether runtime normalization was required
- commit SHA
- whether any paid credits were consumed

Do not claim motion quality from the Tripo viewport alone; base the decision on the exported/replayed artifact.
