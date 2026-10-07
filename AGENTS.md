# EvoWild Run repository agent rules

These rules apply to every creature implementation lane in this repository, including 2.5D, Motion First, 3D, sprite generation, asset regeneration, and visual experiments.

## Canonical creature design

The repository-wide canonical visual reference is:

- `docs/references/evowild-creature-reference-sheet-20260921.jpg`
- `docs/creature-reference-index-v0.1.md`

S / P / E / A are not free design prompts. They are locked morphological variants of the same species.

Before creating, regenerating, editing, rigging, animating, or promoting any creature asset, read the canonical reference and the relevant lock document.

## Hard rules

- Do not redesign S / P / E / A.
- Do not replace a morph with a different creature merely because it is easier to animate.
- Do not add armor, horns, plates, proportions, head shapes, tails, palettes, or anatomy that are not supported by the canonical reference.
- Do not turn a morph into a recognizable existing animal or unrelated monster.
- Motion donors may contribute pose, gait, timing, contact, recovery, body motion, or phase structure only.
- A donor's visual appearance must never become the target creature appearance unless it already matches the canonical reference.
- Image interpolation, optical flow, or raster deformation cannot justify shape drift.
- A technically smoother animation is a failure if the creature identity drifts from the canonical reference.
- S remains S, P remains P, E remains E, and A remains A in silhouette, body proportions, head family, limbs, tail, and species language.
- Cue Band compatibility remains part of the shared species design.

## Promotion gate

No creature asset may be promoted to production without all of the following:

1. canonical-reference comparison;
2. same-morph identity check;
3. silhouette check at race size;
4. motion / gait check;
5. PC and mobile runtime check where relevant;
6. explicit KEEP decision recorded in the repository.

If visual identity and animation quality conflict, preserve identity and revise the animation. Do not solve animation problems by inventing a different creature.

## 2.5D

For 2.5D specifically, also read:

- `docs/2p5d-creature-reference-lock.md`

P/E/A animation work may use Motion First direct gait states as motion donors, but the final sprite artwork must remain the canonical P/E/A designs.
