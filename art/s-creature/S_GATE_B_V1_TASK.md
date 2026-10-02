# EvoWild Run — S-type Gate B v1 limb-root massing

Status: READY TO EXECUTE
Branch: `feat/s-creature-model`
Input: `art/s-creature/output/S-rebuild-v14.blend`

## Gate A decision

`S-rebuild-v14` = **PASS** for Gate A silhouette.

Do not revisit the Gate A global silhouette unless a hard regression is introduced.

## Gate B v1 scope

Only the proximal six cross-section rings of:
- `S_forelimb_L`
- `S_forelimb_R`
- `S_hindlimb_L`
- `S_hindlimb_R`

may change.

Goal:
- roots sit deeper into shoulder/pelvis masses
- proximal size falloff becomes gradual
- shoulder -> upper forelimb -> elbow reads as one anatomical chain
- pelvis/thigh -> knee reads as one anatomical chain
- preserve the existing distinct fore/hind rhythm
- no new silhouette exaggeration

## Hard locks

Must remain exactly unchanged:
- core head / neck / thorax / waist / pelvis / tail mesh
- v14 crest mesh
- all toe meshes
- limb vertices from ring 6 onward
- all topology
- materials/animation/armature remain absent

## Outputs

- `art/s-creature/output/S-gateB-v1.blend`
- `art/s-creature/output/S-gateB-v1.json`
- five renders under `art/s-creature/output/review/gate-b-v1/`

Update CHECKPOINT/HANDOFF, commit/push, STOP. No Gate B v2 in the same run.
