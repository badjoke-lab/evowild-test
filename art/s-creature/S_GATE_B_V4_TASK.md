# EvoWild Run — S-type Gate B v4 feet refinement

Status: READY TO EXECUTE
Branch: `feat/s-creature-model`
Input: `art/s-creature/output/S-gateB-v3.blend`

## Gate B v3 decision

Gate B v3 = **KEEP**.

## Gate B v4 scope

Modify only the 12 existing toe meshes:
- three fore toes per side
- three hind toes per side

Goal:
- preserve small multi-toed racing-foot read
- make each toe taper progressively toward the tip
- give the three-toe fan a restrained lateral separation
- keep the foot light; no paw mass, no hoof mass

## Hard locks

Exactly unchanged:
- core body/head/neck/thorax/waist/pelvis/tail
- crest
- all four limb meshes
- toe topology and vertex counts
- materials/animation/armature remain absent

No Gate C work.

Render SIDE / FRONT / FRONT34 / REAR34 / BACK, update state, commit/push, STOP.
