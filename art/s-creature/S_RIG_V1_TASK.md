# EvoWild Run — S rig source v1

Status: READY TO EXECUTE
Source: `art/s-creature/output/S-gateC-v9.blend`

## Strategy

Keep the accepted visual source non-destructive and multi-object.

Create one shared armature:
- core + four limb meshes: weighted Armature deformation
- crest: rigid parent to head bone
- 12 toe meshes: rigid parent to corresponding foot bones
- eyes + Cue Band: rigid parent to head bone

Keep existing Subsurf/Bevel modifiers. Put Armature before Subsurf on core/limbs.

## Hard locks

Do not change:
- any existing mesh vertex coordinate/topology
- existing materials
- existing Subsurf/Bevel settings
- eye/Cue Band visual transforms in rest pose

Output:
- `art/s-creature/output/S-rig-v1.blend`
- `art/s-creature/output/S-rig-v1.json`
- five rest-pose renders under `output/review/rig-v1/`

No animation yet. Stop for rig/skin review.
