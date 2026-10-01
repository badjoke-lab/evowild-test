# EvoWild Run — S-type Gate A v6 crest-only correction

Status: READY TO EXECUTE
Branch: `feat/s-creature-model`
Input: `art/s-creature/output/S-rebuild-v5.blend`

## Decision

Gate A v5 = **REVISE** because FRONT/BACK read as two tall upright horns.

## One allowed edit

Modify **crest vertices only**.

Keep:
- the v5 body
- head wedge
- neck
- thorax / waist / pelvis
- all four limbs
- all feet/toes
- tail
- topology / vertex count

Required crest result:
- multiple rear-swept laminar plates
- long rearward projection in SIDE
- low vertical envelope in FRONT/BACK
- modest lateral separation
- no paired horns
- no central horn
- no antlers
- no wide ear/fan read

## Hard validation

Every non-crest vertex must remain exactly identical to v5.

## Outputs

- `output/S-rebuild-v6.blend`
- `output/S-rebuild-v6-gate-A.json`
- five review renders under `output/review/rebuild-v6/`

Then update CHECKPOINT/HANDOFF, commit/push and STOP. Do not enter Gate B.
