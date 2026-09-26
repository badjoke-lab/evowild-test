# EvoWild Run — S sprite-gen PoC lane

## Scope lock

This lane is **S / Sprint only**.

Do not generate or edit P / E / A here.

The geometry source of truth remains the repository's current canonical S family. The existing simplified procedural creatures are not shape references for this lane.

## Stage 1 implemented in this branch

Route:

`/evowild-test/preview-spritegen-s/`

The page loads:

`public/models/evowild-s/focus-rigged-v5.glb`

and the embedded run clip:

`EvoWild_S_Run_V5`

It then:

1. applies the canonical 180° runtime yaw;
2. places a fixed side camera on world `-X`, so runtime forward `+Z` reads screen-right;
3. samples one full run cycle at 8 evenly spaced phases;
4. renders each sample to a transparent RGBA frame;
5. builds a 4×2 contact sheet;
6. plays the extracted 2D frames as the visible loop;
7. exposes a PNG atlas export button.

After extraction, the visible loop is 2D canvas playback; the GLB is not rendered each animation frame.

## Why this stage exists before the external generator

sprite-gen's own documentation treats cyclic locomotion as experimental until motion continuity passes. EvoWild therefore needs a deterministic comparison target before accepting a generated run.

The gate is:

- S silhouette remains recognizable;
- motion reads as locomotion, not vertical bobbing;
- foot contact remains readable;
- the final frame wraps to the first without a visible jump.

This branch does **not** claim the current V5 rig is final art. It is only the stable source/runtime reference already used by EvoWild.

## sprite-gen pin

Evaluation target:

- repository: `aldegad/sprite-gen`
- commit: `fbd1a08d47e39c673c73eb494cfde8435b3b13b6`
- package version: `2.11.0`
- license: Apache-2.0

The next stage is to take an approved S side-view still through sprite-gen's video→loop path and compare its run contact sheet directly against this lane. Do not promote the generated motion if it fails the gate above.

## Promotion order

1. SIDE run
2. 3/4 front run
3. 3/4 rear run
4. rear run
5. only then wire camera/view selection into the 2.5D race runtime

No multi-view expansion happens until SIDE run passes.
