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

## T0

1. Obtain the locked GLB from the repository.
2. Open Tripo and import/upload that GLB.
3. Use the animation / rigging workflow needed to make the imported model animatable.
4. Inspect the actual imported model before generating motion.
5. Confirm four limbs, head, neck and tail remain distinct and orientation is usable.
6. Record T0 evidence in `docs/reviews/tripo-s-motion-bench-review.md`.

If import/rigging is broken, set T0 to `REJECT_IMPORT` and stop.

## T1

Only if T0 passes, generate exactly **one** motion:

`maximum-effort forward quadrupedal sprint, explosive long stride, strong shoulder and pelvis drive, stable forward travel`

Do not add camera, appearance, environment, lore, race-strategy or lighting words.

Do not generate the other eleven clips yet.

## Export

Export the real animated 3D result in the best reusable supported format.

Preserve an untouched copy under:

`art/motion/tripo-s/raw/`

If normalization is needed for EvoWild replay, write a separate artifact under:

`art/motion/tripo-s/normalized/`

Never overwrite the raw export.

## Review evidence

Replay the actual 3D animation and capture:

- SIDE
- LOW
- CHASE
- FRONT

Store evidence under:

`art/motion/tripo-s/review/`

Then fill the T1 comparison table against Motion First v5.

Allowed T1 decisions:

- `EXPAND`
- `KEEP_AS_REFERENCE`
- `REJECT`

Stop after the T1 decision. Do not generate T2 unless the decision is explicitly `EXPAND`.

## Completion report

Report:

- T0 decision
- T1 decision
- exact exported artifact paths
- exact review image/video paths
- whether runtime normalization was required
- commit SHA
- whether any paid credits were consumed

Do not claim motion quality from the Tripo viewport alone; base the decision on the exported/replayed artifact.
