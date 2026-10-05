# S Vibe B1d-v2 actual-image review

Decision: REVISE.
B1 shoulder/chest remains OPEN. B2 remains BLOCKED.

Compared actual five-view renders:
- B0-v025
- B1c-v2
- B1d-v1
- B1d-v2
- approved repository S references

## Validation

PASS.

- source: S-vibe-b1c-v2.blend
- candidate vertices: 61
- changed vertices: 61
- max displacement: 0.004800038188776581
- mean displacement: 0.004698134434935197
- whole-body extent drift: 0
- non-manifold edges: 0
- outside/boundary exact
- topology unchanged
- crest/toes preserved

## Actual-image result

SIDE:
- root silhouette is only marginally altered
- the upper triangular shoulder-root edge remains
- the forelimb still reads as attaching through a distinct wedge

FRONT34:
- the angular shoulder patch remains visibly separate from the thorax
- bridge projection does not remove the seam

FRONT/BACK/REAR34:
- no new gross width or silhouette failure

## Decision

**REVISE**

Do not increase capsule gain/radius or displacement. Nearly every candidate already consumed most of the displacement budget.

## Method conclusion

The remaining artifact is likely tied to the fixed support seam itself:
- B1c introduced refined local topology inside a support box
- all later B1c/B1d tests kept the old support boundary fixed
- the visible triangular edge closely persists despite large interior changes

Therefore the next isolated test must allow the **old B1c support boundary** to move while anchoring a new, slightly larger outer support.

## B1e-v1 — next single hypothesis

Source:
- output/S-vibe-b1c-v2.blend

Target:
- old support seam / triangular root edge

Old B1c support:
- |X| 0.070..0.180
- Y -0.090..0.105
- Z 0.900..1.105

Expanded support:
- |X| 0.055..0.205
- Y -0.130..0.145
- Z 0.860..1.145

Editable:
- old support boundary vertices
- plus one mesh-neighbor ring around that old boundary
- only vertices strictly inside expanded support
- expanded support boundary remains fixed

Exact edit:
- topology unchanged
- same-side XYZ Laplacian seam blend
- lambda 0.25
- 2 passes
- residual threshold 0.0015
- cumulative displacement <=0.0035 from B1c-v2

Expected:
- remove the persistent triangular seam itself
- blend refined shoulder-root patch into surrounding thorax/upper limb
- retain root volume rather than shrinking the entire patch

Hard limits:
- editable count 40..260
- max displacement <=0.0035
- expanded-support outer boundary/outside exact
- whole-body extent drift <=0.002 per axis
- topology exact
- non-manifold edges 0
- crest/toes exact

Stop after five-view render + validation + actual-image review.
