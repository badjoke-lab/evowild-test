# S Vibe B2a-v1 actual-image review

Decision: REVISE.
Gate B2a proximal forelimb-root massing remains OPEN.
B2b hindlimb remains BLOCKED.

Reviewed actual five-view renders:
- SIDE
- FRONT
- FRONT34
- REAR34
- BACK

Compared against:
- B1c-v2 working source
- repository S reference 01_s_body_primary.png

The separately named Modeling Image v1.0 was not used as review evidence.

## Validation

PASS.

- raw candidates: 29
- selected candidates: 29
- positive / negative selected: 13 / 16
- changed vertices: 29
- max displacement: 0.005000025857376828
- mean displacement: 0.004976165156642711
- mean absolute elliptical q error: 0.32841449507529685 -> 0.2628565465389585
- whole-body extent drift X/Y/Z: 0 / 0 / 0
- non-manifold edges: 0
- outside/support-boundary geometry exact
- topology unchanged from B1c-v2
- crest/toes preserved

## Actual-image result

SIDE:
- proximal forelimb root changes only slightly
- the triangular shoulder/root wedge remains clearly visible
- station0-to-station1 still does not read as a continuous anatomical mass

FRONT:
- narrow racing stance is preserved
- no harmful widening or collapse

FRONT34:
- local root surface changes, but the inserted-plate / triangular-root reading remains
- visual improvement is too small to accept

REAR34 / BACK:
- no new gross drift

## Decision

**REVISE**

Do not:
- increase the B2a-v1 displacement cap
- accumulate B2a-v1 deformation
- start B2b

B1c-v2 remains the clean B2a recovery source.

## B2a-v2 — next single hypothesis

Source:
- output/S-vibe-b1c-v2.blend

Hypothesis:
The station0-to-station1 root does not have enough local degrees of freedom in the current topology. One support-contained subdivision of the proximal forelimb-root faces, followed by the same accepted A3a tapered elliptical guide, can round the triangular root without changing the rest of the body.

Support:
- |X| 0.055..0.215
- Y -0.075..0.085
- Z 0.780..1.060
- station-axis t restricted to 0..1
- same-side only

Topology:
- one subdivision cut only
- subdivide an edge only when all linked source-face vertices are inside support and station t 0..1 on the same side
- no object-wide remesh

Guide after subdivision:
- same accepted A3a station0/station1 centers and radii as B2a-v1
- preserve axial t
- signed elliptical cross-section projection toward q=1
- candidate if |q-1| > 0.10
- gain 0.30
- max displacement from post-subdivision starting position 0.0040

Keep fixed:
- every original vertex outside support
- all topology outside fully-contained support faces
- crest
- toes
- all other objects

Hard limits:
- new vertices 20..500
- max local displacement <= 0.0040
- whole-body extent drift <= 0.002 per axis
- non-manifold edges = 0
- original outside-support coordinates exact
- preserved crest/toes exact

Stop after validation + five-view render + actual-image review.
Do not start B2b automatically.
