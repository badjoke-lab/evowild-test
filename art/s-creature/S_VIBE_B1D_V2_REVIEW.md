# S Vibe B1d-v2 actual-image review

Decision: REVISE.
B1 shoulder/chest remains OPEN. B2 remains BLOCKED.

Reviewed actual five-view renders against:
- B1d-v1
- B1c-v2
- B0-v025
- repository reference 01_s_body_primary.png

The separately named Modeling Image v1.0 was not used as review evidence.

## Validation

PASS.

- source: S-vibe-b1c-v2.blend
- candidates / changed vertices: 61 / 61
- max displacement: 0.004800038188776581
- mean displacement: 0.004698134434935197
- candidate ratio range: 1.1013653646993296 .. 1.5637778004952572
- whole-body extent drift X/Y/Z: 0 / 0 / 0
- non-manifold edges: 0
- outside/support-boundary geometry exact
- topology unchanged from B1c-v2
- crest/toes preserved

## Actual-image result

SIDE:
- the shoulder-to-upper-limb direction is marginally clearer than B1d-v1
- the upper shoulder fold remains
- a distinct vertical/oblique join line still separates shoulder mass from the upper forelimb root

FRONT:
- width remains stable
- no barrel widening or collapse

FRONT34:
- tapered guide softens the patch slightly
- the root still reads as an inserted angular plate instead of a continuous shoulder-to-humerus bridge
- improvement is insufficient to close B1

REAR34 / BACK:
- no new gross drift

## Decision

**REVISE**

Do not:
- increase gain
- increase displacement cap
- accumulate from B1d-v2
- repeat outside-only projection

The mean displacement is already close to the maximum budget, so more outside-only inward projection would spend more displacement without addressing the concave side of the join.

## B1d-v3 — next single hypothesis

Source:
- output/S-vibe-b1c-v2.blend

Hypothesis:
The remaining join line is maintained by both outward high spots and inward/concave low spots. A signed, boundary-tapered projection toward the same tapered bridge surface can reduce both sides of the discontinuity without increasing the displacement budget.

Guide:
- same shoulder anchor / upper-limb anchor / radius taper as B1d-v2

Change:
- signed projection: vertices may move inward OR outward toward local capsule radius
- select only |distance/radius - 1| > 0.05
- boundary taper inside the same support
- gain 0.35
- max displacement 0.0042
- no topology change

Hard limits:
- candidate count 8..180
- support boundary/outside support exact
- max displacement <= 0.0042
- whole-body extent drift <= 0.002 per axis
- topology exact from B1c-v2
- non-manifold edges 0
- crest/toes exact

Expected:
- SIDE: vertical root join softens from both sides
- FRONT34: inserted-plate reading becomes a continuous bridge
- FRONT/BACK: width remains controlled

Stop after validation + five renders + actual-image review.
