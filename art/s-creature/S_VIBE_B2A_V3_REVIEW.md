# S Vibe B2a-v3 actual-image review

Decision: REVISE.
Gate B2a remains OPEN. B2b remains BLOCKED.

Reviewed actual five-view renders against:
- B2a-v2
- B2a-v1
- B1c-v2
- repository reference 01_s_body_primary.png

The separately named Modeling Image v1.0 was not used as review evidence.

## Validation

PASS.

- source: S-vibe-b1c-v2.blend
- raw eligible subdivision edges: 500
- selected subdivision edges: 360
- new vertices: 461
- local vertices after subdivision: 855
- raw guide candidates: 140
- selected candidates: 140
- applied candidates: 134
- skipped support-exit candidates: 6
- station-1->0 candidates: 73
- station0->1 candidates: 61
- max local displacement: 0.004000036701419841
- mean local displacement: 0.0005894013743702801
- mean absolute q error: 0.3380637429770767 -> 0.2946195618617372
- whole-body extent drift: X/Y/Z = 0/0/0
- non-manifold edges: 0
- outside-local original geometry unchanged
- crest/toes preserved

## Actual-image result

SIDE:
- thorax-side station-1 extension changes the local root slightly
- the triangular/plate-like root remains clearly visible
- upper root edge is still too straight and separate from the thorax

FRONT34:
- the inserted-plate reading remains
- the three-station guide does not create enough visible root continuity at the 0.004 displacement budget

FRONT / REAR34 / BACK:
- no new gross width or silhouette failure

## Decision

**REVISE**

## Method conclusion

The B2a target and topology are now correct:
- the root is part of S_B0_continuous_body_v025, not a separate visible source mesh
- B0 joined the original forelimbs into the core and voxel-remeshed them
- local subdivision is manifold and safely scoped
- station-1 successfully includes the thorax-side connection

The remaining failure is magnitude, not target selection:
- mean q error improves, but only modestly
- most visible shape remains close to the B1c-v2 voxel-remeshed wedge because the max local movement is only 0.004

Do not return to B1.
Do not start B2b.
Do not accumulate B2a-v3.

## B2a-v4 — next single hypothesis

Source:
- output/S-vibe-b1c-v2.blend

Purpose:
- locally reconstruct the baked-in voxel-remesh forelimb root rather than micro-adjust it

Topology:
- repeat one support-contained subdivision only
- expanded but still local support:
  - |X| 0.045..0.225
  - Y -0.105..0.095
  - Z 0.760..1.090
- subdivision inset 0.007
- at most 360 selected subdivision edges
- one cut only

Guide:
- same station-1 / station0 / station1 centers and radii as B2a-v3
- piecewise tapered elliptical guide
- signed projection toward q=1
- boundary taper to zero at expanded support edge

Shape reconstruction:
- q error threshold 0.08
- q range 0.35..2.20
- gain 0.80
- cumulative local displacement <= 0.012
- select at most 120 strongest q-error candidates per side

Expected:
- SIDE: root upper edge visibly loses the straight triangular plate profile
- FRONT34: root becomes a continuous shoulder/chest-to-upper-arm mass
- FRONT/BACK: width and stance remain controlled

Hard limits:
- new vertices 20..500
- selected candidates 30..240
- max local displacement <= 0.012
- mean absolute q error after <= 0.85 * before
- whole-body extent drift <= 0.002 per axis
- non-manifold edges = 0
- all original geometry outside support exact
- crest/toes exact

Stop after validation + five-view render + actual-image review.
Do not start B2b automatically.
