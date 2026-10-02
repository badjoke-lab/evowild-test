# EvoWild Run — S-type Gate A v9 limb topology rebuild

Status: READY TO EXECUTE
Branch: `feat/s-creature-model`
Input: `art/s-creature/output/S-rebuild-v8.blend`

## Decision

Gate A v8 = **REVISE**.

Do not modify the locked v8 core again.

## Locked exactly

- head
- crest
- neck
- thorax
- waist
- pelvis
- tail
- all toe meshes
- materials/animation state
- S-only scope

## Rebuild only these four meshes

- `S_forelimb_L`
- `S_forelimb_R`
- `S_hindlimb_L`
- `S_hindlimb_R`

The existing sparse limb ring topology is replaced by a denser low-complexity Gate A structure.

### Required forelimb read
- root buried into shoulder mass
- broad shoulder transition, not a pasted cone
- readable upper segment
- explicit elbow
- progressively tapered distal segment
- narrow wrist before toe roots
- frontal-plane axis is not a straight parallel rod

### Required hindlimb read
- root buried into pelvis
- broad thigh transition
- explicit forward knee
- explicit rearward hock rhythm
- progressive taper below hock
- visibly different chain from forelimb

## Still Gate A

Do not add:
- surface/anatomical detail
- welding/retopology
- materials/color
- Cue Band
- rigging
- animation

## Outputs

- `output/S-rebuild-v9.blend`
- `output/S-rebuild-v9-gate-A.json`
- five PNGs under `output/review/rebuild-v9/`

Update CHECKPOINT/HANDOFF, commit/push, then STOP for review.
