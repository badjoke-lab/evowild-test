# S Morphology Reset — Execution Plan

Primary lock: `S_MODELING_IMAGE_LOCK.md`

## Immediate task

Stop editing `S-blockout-v12.blend` as the final body.

Create **S-rebuild-v1** as a new modeling source on the existing `feat/s-creature-model` branch.

The first deliverable is Gate A only: a low-complexity silhouette cage matching the approved S-type Modeling Image v1.0.

## Mandatory first pass

1. Build head and rear-swept layered crest first.
2. Establish neck length and angle.
3. Establish thorax/waist/pelvis masses.
4. Place fore/hind limb joint chains and small feet.
5. Add tail.
6. Render SIDE / FRONT / FRONT34 / REAR34 / BACK.
7. Stop. Do not refine surfaces before silhouette review.

## Forbidden in Gate A

- reusing the v12 single sagittal crown
- a central horn/spike
- chest micro-polish
- Cue Band
- colors/textures
- facial detail
- final retopology
- animation

## Save outputs

- `output/S-rebuild-v1.blend`
- `output/review/rebuild-v1/S_rebuild_side.png`
- `output/review/rebuild-v1/S_rebuild_front.png`
- `output/review/rebuild-v1/S_rebuild_front34.png`
- `output/review/rebuild-v1/S_rebuild_rear34.png`
- `output/review/rebuild-v1/S_rebuild_back.png`

Update CHECKPOINT/HANDOFF and stop for review.
