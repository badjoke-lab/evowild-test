# EvoWild Run — S-type Gate A v12 crest fan correction

Status: READY TO EXECUTE
Branch: `feat/s-creature-model`
Input: `art/s-creature/output/S-rebuild-v11.blend`

## Decision

Gate A v11 = **REVISE**.

The paired crest topology was removed successfully, but FRONT/BACK now collapse into one triangular central spike. That is a hard fail.

## Allowed edit

Replace the v11 crest object only.

Required v12 crest:
- five narrow overlapping laminar plates
- one compact skull-integrated crest group
- rear-upward flow in SIDE
- staggered plate lengths / heights / lateral centers
- nonzero tip width
- narrow overall frontal envelope
- FRONT/BACK must visibly contain multiple layered plates
- no single central spike
- no paired horns
- no antlers
- no wide ear/fan read

## Hard locks

Every non-crest mesh coordinate must remain exactly identical to v11:
- core body/head/neck/tail
- all four limb meshes
- all toe meshes

No Gate B, materials, rigging, animation or final retopology.

Render SIDE / FRONT / FRONT34 / REAR34 / BACK, update checkpoint/handoff, commit/push, then STOP.
