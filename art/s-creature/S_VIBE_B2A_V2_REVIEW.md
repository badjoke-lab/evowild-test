# S Vibe B2a-v2 actual-image review

Decision: REVISE.
Local topology refinement: KEEP as a technical method.
Gate B2a remains OPEN. B2b remains BLOCKED.

Reviewed actual five-view renders against:
- B2a-v1
- B1c-v2 working source
- repository reference 01_s_body_primary.png

The separately named Modeling Image v1.0 was not used as review evidence.

## Validation

PASS.

- source vertices / polygons / edges: 5940 / 6010 / 11948
- result vertices / polygons / edges: 6432 / 6555 / 12985
- eligible subdivided edges: 374
- affected source faces: 228
- new vertices: 492
- local vertices after subdivision: 770
- guide candidates: 74
- changed local vertices: 74
- max local displacement: 0.004000008151972785
- mean local displacement: 0.0003369689738466263
- mean absolute q error: 0.27924545445769716 -> 0.23299263505383827
- whole-body extent drift: X/Y/Z = 0/0/0
- non-manifold edges: 0
- outside-local original geometry unchanged
- crest/toes preserved

## Actual-image result

SIDE:
- the proximal root changes slightly
- the large triangular/plate-like shoulder-root join remains clearly visible
- the upper part of the wedge is almost unchanged

FRONT34:
- the local station0-to-station1 surface is slightly smoother
- the inserted-plate reading remains
- improvement is insufficient to accept

FRONT / REAR34 / BACK:
- no new gross width or silhouette failure

## Decision

**REVISE**

The local subdivision itself is safe and useful, but extra degrees of freedom alone do not solve the root.

## Cause reclassification

B2a-v1/v2 only shape the accepted A3a **station0 -> station1** segment.

The actual-image residual sits partly on the thorax side of station0:
- the upper triangular root begins proximal to station0
- those thorax-side vertices are outside the current segment guide by construction
- therefore refining only t=0..1 cannot remove the whole wedge

The approved S reference reads as a continuous thorax -> shoulder-root -> upper-arm transition, not a plate inserted at station0.

## B2a-v3 — next single hypothesis

Source:
- output/S-vibe-b1c-v2.blend

Do not accumulate B2a-v2 shape.

Topology:
- repeat the accepted single support-contained subdivision strategy
- keep the 0.005 subdivision inset that produced 492 new vertices
- one cut only
- no object-wide remesh

Three-station guide:
- station -1 (thorax embed):
  - center X ±0.088
  - Y -0.070
  - Z 1.035
  - lateral radius 0.086
  - sagittal radius 0.112
- station 0:
  - existing accepted A3a center/radii
  - X ±0.115, Y -0.030, Z 0.985
  - lateral radius 0.068
  - sagittal radius 0.095
- station 1:
  - existing accepted A3a center/radii
  - X ±0.148, Y 0.035, Z 0.845
  - lateral radius 0.056
  - sagittal radius 0.070

Method:
- piecewise tapered elliptical guide:
  - station -1 -> station0
  - station0 -> station1
- choose the segment giving the closest valid axial projection
- preserve segment axial coordinate
- signed cross-section projection toward q=1
- candidate only if |q-1| > 0.10
- q clamp 0.45..1.90
- gain 0.30
- max local displacement 0.0040

Support:
- same B2a support box:
  - |X| 0.055..0.215
  - Y -0.075..0.085
  - Z 0.780..1.060
- same-side only
- outer/original geometry outside support fixed

Expected:
- SIDE: thorax-side upper wedge blends into station0 instead of terminating as a triangular plate
- FRONT34: shoulder/root reads as one continuous thorax-to-upper-arm mass
- FRONT/BACK: narrow racing stance remains controlled

Hard limits:
- new vertices 20..500
- guide candidates 20..240
- max local displacement <= 0.0040
- whole-body extent drift <= 0.002 per axis
- non-manifold edges = 0
- original outside-support coordinates exact
- crest/toes exact

Stop after validation + five-view render + actual-image review.
Do not start B2b automatically.
