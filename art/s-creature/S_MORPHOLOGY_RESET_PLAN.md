# S Morphology Reset — Execution Plan

Primary lock: `S_MODELING_IMAGE_LOCK.md`
Process lock: `S_CREATURE_MODELING_WORKFLOW.md`

## Current state

`S-rebuild-v1.blend` is the active fresh-rebuild checkpoint.

Gate A v1 decision: REVISE.

The old instruction to correct crest/head, neck, torso, limbs and tail in one `S-rebuild-v2` pass is cancelled.

## Immediate task

Do not perform a full-body v2 correction.

Run **Gate A1 only: head / crest / neck** from `output/S-rebuild-v1.blend`.

### Before geometry edits

1. Read the approved S references and process lock.
2. Establish SIDE / FRONT reference comparison.
3. Record the A1 landmarks for head, crest and neck.
4. Record target / keep_fixed / intended silhouette change / forbidden edits.
5. Only then edit geometry.

### Editable in A1

- head
- crest
- neck

### Hard keep-fixed in A1

- thorax
- waist
- pelvis
- forelimbs
- hindlimbs
- feet
- tail
- topology outside A1 target

### A1 target

- preserve small wedge-head intent
- remove any FRONT/BACK reading as paired horns
- make crest skull-integrated, layered and strongly rear-swept
- reduce the rebuild-v1 long/tubular neck read
- create a shorter, thicker, more organic neck transition without turning it into a deer/horse neck

### A1 required renders

- SIDE
- FRONT
- FRONT34
- BACK

Stop after A1 renders. Do not continue to thorax.

## Subsequent gates

Only after explicit acceptance:
- A2: thorax / waist / pelvis
- A3: limb joint rhythm / feet
- A4: tail
- A5: full five-view silhouette review

## Forbidden in Gate A

- v12 sagittal crown reuse
- horn/spike interpretation
- full-body simultaneous correction
- chest micro-polish during A1
- Cue Band
- colors/textures
- facial detail
- final retopology
- rigging
- animation
- non-target smoothing

## Save convention

A1 output:
- `output/S-rebuild-v2-a1.blend`
- `output/review/rebuild-v2-a1/S_rebuild_side.png`
- `output/review/rebuild-v2-a1/S_rebuild_front.png`
- `output/review/rebuild-v2-a1/S_rebuild_front34.png`
- `output/review/rebuild-v2-a1/S_rebuild_back.png`

Update CHECKPOINT/HANDOFF and stop for review.
