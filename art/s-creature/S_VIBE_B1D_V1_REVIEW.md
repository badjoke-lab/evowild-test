# S Vibe B1d-v1 actual-image review

Decision: REVISE.
B1 shoulder/chest remains OPEN. B2 remains BLOCKED.

Reviewed actual five-view renders against:
- B0-v025
- B1c-v2
- repository approved S references

The separately named Modeling Image v1.0 was not used as review evidence unless present in the repository.

## Validation

PASS.

- source: S-vibe-b1c-v2.blend
- support vertices: 468
- boundary vertices: 80
- interior vertices: 388
- candidate / changed vertices: 42
- max displacement: 0.004900035875453131
- mean displacement: 0.00356192947535932
- whole-body extent drift: 0
- non-manifold edges: 0
- outside/boundary geometry fixed
- topology unchanged
- crest/toes preserved

## Actual-image result

SIDE:
- shoulder root is marginally rounder than B1c-v2
- the upper shoulder/root fold remains visible
- the proximal forelimb still joins through a distinct angular shoulder patch

FRONT:
- width is stable
- no collapse or barrel widening

FRONT34:
- the root is less lumpy, but the front-limb attachment still reads as an angular/quadrilateral patch rather than one continuous shoulder-to-upper-limb bridge
- the improvement is not sufficient to close B1

REAR34 / BACK:
- no new gross drift

## Decision

**REVISE**

Do not increase ellipsoid projection gain or displacement.
The problem is not only an outward shoulder blob; it lacks a continuous shoulder-to-humerus connection axis.

## B1d-v2 — next single hypothesis

Source:
- output/S-vibe-b1c-v2.blend

Keep:
- B1c refined topology
- B1c-v2 ridge reduction
- all outside-support geometry
- support boundary
- crest/toes
- topology

Hypothesis:
A tapered capsule/bridge guide aligned from shoulder mass toward the upper forelimb root will remove the angular attachment patch better than a single shoulder ellipsoid.

Guide per side:
- shoulder anchor: X ±0.105, Y -0.050, Z 1.030
- upper-limb anchor: X ±0.135, Y 0.045, Z 0.925
- radius tapers 0.082 -> 0.058
- evaluate perpendicular distance to the segment
- only vertices outside 1.06 * local radius are candidates
- pull inward toward local radius
- gain 0.50
- max displacement 0.0048

Hard limits:
- support boundary/outside support exact
- candidate count must be between 6 and 120
- max local displacement <= 0.0048
- whole-body extent drift <= 0.002 per axis
- topology exact from B1c-v2
- non-manifold edges 0
- crest/toes exact

Expected:
- SIDE: upper shoulder fold becomes a continuous descending root
- FRONT34: angular attachment patch becomes a rounded shoulder-to-upper-limb bridge
- FRONT/BACK: no material width change

Stop after validation + five renders + actual-image review.
