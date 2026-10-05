# S Vibe B1d-v3 actual-image review and B1 closure

Decision: REVISE for B1d-v3.
Gate B1 shoulder/chest working source: ACCEPT B1c-v2.
B2a forelimb-root massing: UNBLOCKED.

## B1d-v3 validation

PASS.

- raw signed candidates: 368
- selected candidates: 120
- selected positive / negative side: 60 / 60
- inside-guide candidates: 114
- outside-guide candidates: 6
- changed vertices: 120
- max displacement: 0.004200055079526168
- mean displacement: 0.0042000008307251585
- mean absolute guide error: 0.04961456695119836 -> 0.04541456596360861
- whole-body extent drift: X/Y/Z = 0/0/0
- non-manifold edges: 0
- outside/support-boundary geometry exact
- topology unchanged from B1c-v2
- crest/toes preserved

## Actual-image result

SIDE:
- the upper shoulder/root fold remains clearly readable
- the forelimb root still appears as a separate triangular/oblique wedge

FRONT34:
- signed projection changes the local surface but does not eliminate the inserted-plate reading
- improvement over B1c-v2 / B1d-v2 is insufficient

FRONT / REAR34 / BACK:
- no new gross width or silhouette failure

## B1d-v3 decision

**REVISE**

Do not increase signed-guide gain or displacement. Selected vertices already consume the full 0.0042 budget while the target artifact remains.

## Gate B1 conclusion

The persistent visible defect is no longer treated as a B1 shoulder/chest-surface problem.

Evidence:
- B1a isotropic cleanup exhausted displacement without removing it
- B1b X/YZ/root-local fairing did not remove it
- B1c local refinement improved surface freedom but the root wedge remained
- B1d anatomical guide projection changed the shoulder patch but the actual proximal forelimb attachment remained angular

The remaining triangle corresponds to the **proximal forelimb root / station0-to-station1 connection**, which belongs to Gate B2 fore/hind joint-root massing.

Selected safe B1 working source:
- **output/S-vibe-b1c-v2.blend**

Why B1c-v2:
- local refined topology is manifold and scoped
- shoulder/chest gross mass is stable
- no width/extents regression
- B1d variants did not justify carrying their deformations forward

Residual explicitly deferred to B2a:
- triangular proximal forelimb root
- shoulder-to-upper-arm continuity
- proximal joint-root mass rhythm

## B2a-v1 single hypothesis

Source:
- output/S-vibe-b1c-v2.blend

Reference landmarks from accepted Gate A3a:
- station0 shoulder/root center: X ±0.115, Y -0.030, Z 0.985
- station0 radii: lateral 0.068, sagittal 0.095
- station1 upper-arm center: X ±0.148, Y 0.035, Z 0.845
- station1 radii: lateral 0.056, sagittal 0.070

Target:
- proximal forelimb root only, station0 -> station1
- do not edit elbow/distal limb in this pass

Method:
- mirrored tapered elliptical-segment guide using the accepted A3a station0/1 centers and radii
- preserve segment axial position
- signed cross-section projection toward q=1
- candidate only if |q-1| > 0.12
- support bounds: |X| 0.055..0.215, Y -0.075..0.085, Z 0.780..1.060
- support boundary fixed
- gain 0.45
- max displacement 0.0050
- no topology change

Hard limits:
- candidate count 20..220
- max displacement <=0.0050
- whole-body extent drift <=0.002 per axis
- topology exact from B1c-v2
- non-manifold edges 0
- crest/toes exact
- all vertices outside support/boundary exact

Expected:
- SIDE: shoulder root flows into the upper arm instead of a triangular wedge
- FRONT34: inserted-plate reading is reduced
- FRONT/BACK: narrow racing stance remains controlled

Stop after five-view render + validation + actual-image review.
Do not start B2b hindlimb automatically.
