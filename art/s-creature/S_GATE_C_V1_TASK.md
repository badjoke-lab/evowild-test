# EvoWild Run — S-type Gate C v1 surface-continuity preview

Status: READY TO EXECUTE
Branch: `feat/s-creature-model`
Input: `art/s-creature/output/S-gateB-v4.blend`

## Gate B decision

Gate B = **PASS** at `S-gateB-v4.blend`.

The tail root is KEEP AS-IS: it is already continuous and tapered in SIDE/REAR34.

## Gate C v1 purpose

Test whether the accepted massing survives a first production-surface smoothing pass before any destructive retopology.

## Allowed change

Add one non-destructive Catmull-Clark subdivision level to:
- `S_rebuild_core_head_crest_neck_torso_tail`
- `S_forelimb_L`
- `S_forelimb_R`
- `S_hindlimb_L`
- `S_hindlimb_R`

Set those five meshes to smooth shading.

## Hard locks

Do not change:
- any base vertex coordinate
- any base topology / vertex count
- crest mesh
- all toe meshes
- materials / color
- armature / rig
- animation
- Cue Band

This is a reversible preview, not final retopology.

## Acceptance question

Does one-level production smoothing:
- preserve the S silhouette
- improve faceted body/limb continuity
- avoid collapsing the head/neck/waist/tail
- avoid visible gaps or root shrinkage at limb attachments

Render SIDE / FRONT / FRONT34 / REAR34 / BACK, update state, commit/push, STOP for review.
