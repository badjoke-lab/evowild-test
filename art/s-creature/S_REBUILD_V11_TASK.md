# EvoWild Run — S-type Gate A v11 crest topology reset

Input: `art/s-creature/output/S-rebuild-v10.blend`
Branch: `feat/s-creature-model`

Gate A v10 = **REVISE**.

## Root cause
The current six crest plates are organized as three left/right pairs. Raising them toward the canonical S line makes FRONT/BACK read as two horns; flattening them removes that hard fail but misses the canonical SIDE silhouette.

## v11
Remove the paired crest topology. Preserve all non-crest coordinates exactly.

Rebuild the crest as one narrow central overlapping group:
- several laminar plates in one group
- roots embedded into the posterior skull
- long rearward + modest upward sweep
- narrow FRONT/BACK silhouette
- multiple overlapping tips, not one central needle
- no left/right horn pair
- no antlers
- no broad ear/fan read

Keep all body, limbs, toes and tail fixed. Gate A only. Render five views, commit/push, STOP.
