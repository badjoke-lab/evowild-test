# S Vibe B1c-v3 actual-image review

Decision: REVISE.
B1 shoulder/chest remains OPEN. B2 remains BLOCKED.

## Validation

PASS.
- cap mask vertices: 166
- boundary vertices: 52
- interior vertices: 114
- actual candidate vertices: 4
- changed vertices: 4
- max extra Z drop: 0.0014443397521972656
- mean extra Z drop: 0.000040887740620395595
- whole-body extent drift: 0
- all body X/Y unchanged: true
- topology unchanged from B1c-v2: true

## Actual-image result

SIDE / FRONT34:
- difference from B1c-v2 is visually negligible
- triangular shoulder-root cap remains
- root still reads as a separate wedge rather than one continuous shoulder mass

The reason is consistent with validation: only four cap vertices moved and the maximum change was ~0.00144.

## Decision

**REVISE**

Close the micro-fairing / micro-cap-deformation approach.
Do not increase passes, thresholds, or displacement budgets.

## B1d-v1 — next single hypothesis

Source:
- output/S-vibe-b1c-v2.blend

Keep:
- B1c refined local topology
- B1c-v2 ridge reduction
- outside-support geometry
- crest/toes

Hypothesis:
The residual triangular root is a shape-target problem, not a smoothing-strength problem.
Project only outward shoulder-root outliers toward a rounded anatomical shoulder guide.

Guide, mirrored per side:
- center: X ±0.115, Y -0.020, Z 0.985
- radii: X 0.085, Y 0.105, Z 0.095

Support:
- |X| 0.070..0.180
- Y -0.090..0.105
- Z 0.900..1.105
- support boundary fixed

Exact edit:
- topology fixed
- for support-interior vertices only
- evaluate normalized ellipsoid radius q
- only q > 1.04 may move
- project toward ellipsoid surface
- blend gain 0.55
- max displacement from B1c-v2 <= 0.005
- no expansion: only vertices outside the guide are pulled inward

Expected visual change:
- remove triangular upper/root protrusion
- produce a rounder continuous shoulder-to-upper-limb mass
- preserve limb placement and gross thorax silhouette

Hard limits:
- boundary/outside support exact
- max local displacement <= 0.005
- whole-body extent drift <= 0.002 per axis
- topology exact
- non-manifold edges 0
- crest/toes exact

Stop after five-view render + validation + actual-image review.
