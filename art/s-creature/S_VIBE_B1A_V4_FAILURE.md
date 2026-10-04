# EvoWild Run — S Vibe Gate B1a-v4 Failure / B1a Closure

Status: HARD_FAIL / B1a METHOD CLOSED
Lane: exp/s-creature-vibe-modeling
Source: output/S-vibe-b0-v025.blend

## B1a-v4 hypothesis

Keep:
- same B1a Y/Z region
- lambda 0.32
- mu -0.33
- cycles 8
- B0-v025 source
- hard-scope locks

Change only:
- Y boundary margin 0.060 -> 0.030
- Z boundary margin 0.070 -> 0.035

## Result

HARD FAIL before render.

Measured maximum displacement:
- 0.012710190655851921

Hard limit:
- 0.010

The script stopped before rendering as required.

## B1a conclusion

B1a isotropic Taubin-relax escalation is exhausted.

Evidence:
- v1: safe, visually negligible
- v2: larger effect, still visually insufficient
- v3: max displacement 0.0096156, still visually insufficient
- v4: narrower taper exceeds hard limit at 0.0127102 before render

Do not:
- increase cycles further
- reduce taper further
- accumulate from v1/v2/v3
- relax the hard limit

B1a did not produce an accepted candidate. B0-v025 remains the immutable recovery/source model.

## Reclassification of remaining problem

Actual render review shows the dominant residual as a lateral shoulder-root / chest-side plane problem in FRONT34 rather than only high-frequency voxel waviness.

That belongs to B1 anatomical plane shaping, not further isotropic cleanup.

## B1b-v1 — next single hypothesis

Source:
- output/S-vibe-b0-v025.blend

Target:
- lateral shoulder-root / chest-side protrusion visible in FRONT34

Method:
- X-axis-only local fairing
- Y and Z coordinates remain exact
- topology and vertex count remain exact
- use adjacency smoothing only for X
- symmetric rule on both sides
- cumulative per-vertex |delta X| clamped to 0.006

Editable region:
- Y: -0.12 to 0.18
- Z: 0.80 to 1.12
- only vertices with |X| >= 0.055
- boundary taper to zero at Y/Z region edges

Hard fixed:
- every vertex outside the B1b mask
- Y/Z of every body vertex
- crest
- toes
- topology / vertex count

Expected visual change:
- FRONT34 shoulder-root bump becomes a cleaner continuous lateral plane
- SIDE profile remains mathematically unchanged because Y/Z are fixed
- shoulder mass remains present; no barrel widening

Hard limits:
- max |delta X| <= 0.006
- Y/Z delta = 0 for every body vertex
- whole-body X min/max change <= 0.006
- fixed vertices exact

Stop after five-view render and validation.
