# EvoWild Run — S-type Gate C v2 limb-root shrink compensation

Status: READY TO EXECUTE
Input: `art/s-creature/output/S-gateC-v1.blend`

Gate C v1 = **KEEP**.

## Scope

Modify only rings 0 and 1 of:
- S_forelimb_L
- S_forelimb_R
- S_hindlimb_L
- S_hindlimb_R

Goal:
- compensate the volume loss introduced by one-level Catmull-Clark
- keep shoulder/thigh roots embedded in the core surface
- reduce visible root seams in FRONT34 / REAR34
- preserve the accepted overall silhouette

## Hard locks

Exactly unchanged:
- core mesh
- crest mesh
- all toe meshes
- limb rings 2-11
- topology and vertex counts
- existing Subsurf modifier stack
- no materials, rig, animation or Cue Band

Render five views, update state, commit/push, STOP.
