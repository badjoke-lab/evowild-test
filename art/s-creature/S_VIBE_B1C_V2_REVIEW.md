# S Vibe B1c-v2 actual-image review

Decision: REVISE.
Local refined-topology ridge reduction: KEEP as the next technical base.
B1 shoulder/chest remains OPEN. B2 remains BLOCKED.

## Validation

PASS.
- support vertices: 468
- boundary vertices: 80
- interior vertices: 388
- moved high-residual vertices: 86
- max additional displacement: 0.003450018744736528
- mean additional displacement: 0.00039921304165869753
- whole-body extent drift: X/Y/Z = 0/0/0
- non-manifold edges: 0
- topology unchanged from B1c-v1: true
- render hard-scope validation: true

## Actual-image review

Compared B0-v025, B1c-v1 and B1c-v2 with matched cameras.

SIDE:
- the shoulder-root ridge is softer than B1c-v1
- the upper cap remains visibly raised and the root still reads as a wedge

FRONT:
- width remains stable
- no collapse or barrel widening

FRONT34:
- the triangular cap is reduced but still clearly visible
- the remaining artifact is concentrated at the upper shoulder-root cap, not the entire root patch

REAR34 / BACK:
- no new gross drift

## Decision

**REVISE**

Do not strengthen generic XYZ fairing again.

## B1c-v3 single hypothesis

Source:
- output/S-vibe-b1c-v2.blend

Keep from v2:
- refined local topology
- reduced high-curvature ridge
- all outside-support geometry
- stable shoulder/chest width

Target:
- only the raised upper shoulder-root cap

Exact edit:
- X and Y of every body vertex exact fixed
- Z-only downward residual reduction
- cap mask: |X| 0.085..0.170, Y -0.075..0.055, Z 1.015..1.100
- same-side neighbors
- only if local vertex Z exceeds neighbor-average Z by >0.0015
- lambda 0.65
- 2 passes
- cumulative extra downward Z <=0.004

Expected visual change:
- remove the last raised triangular cap
- SIDE root becomes a smoother shoulder-to-upper-limb slope
- FRONT34 loses the bright triangular top ridge
- FRONT/BACK width unchanged by construction

Hard limits:
- X/Y delta = 0 for every body vertex
- outside-cap vertices exact
- max extra Z drop <=0.004
- topology exact
- non-manifold edges = 0
- whole-body extents unchanged
- crest/toes exact

Stop after five-view render + validation + actual-image review.
