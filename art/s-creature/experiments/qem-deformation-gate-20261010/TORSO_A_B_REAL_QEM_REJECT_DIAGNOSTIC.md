# EvoWild S original-QEM torso refit trials A / B (2026-10-10)

**Decision: FAIL for topology-safe torso deformation. S-visual gate REJECT. No game use.**

- Canonical S image: `art/s-creature/references/00_s_type_modeling_image_v1.png` SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
- Immutable original TRELLIS2 QEM donor SHA-256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`.
- All experiments create a separate real Blender shape-key mesh retaining **29,948 vertices and 59,932 faces**. Original QEM source is unchanged.
- Renders: `torso-profile-a-v1/review/REAL_QEM_TORSO_A_FIVE_VIEW_COMPARE.jpg`, `torso-profile-b-v1/review/REAL_QEM_TORSO_B_FIVE_VIEW_COMPARE.jpg`. These are 10 actual source/variant Blender 5-view images each.
- Complete measured data: `torso-profile-a-v1/QEM_TORSO_A_QA.json` and `torso-profile-b-v1/QEM_TORSO_B_QA.json`.

## A (broad deformation) FAIL

At dorsal offset 0.10, lowered underside 0.065 and lateral broadening 0.030: **1 original triangle area <0.5x**; minimum 0.35647x. Larger dorsal offsets .14/.18/.22/.27 also FAIL. More importantly, broad upper region accidentally includes the S's very long backward swept crest; actual renders reveal unacceptable crest silhouette movement. The body shape target was *not* matched.

## B (crest-and-foot frozen) FAIL, narrower failure

B explicitly pins original vertices at Z>2.20 and Z<0.70 to source coordinate (max numerical difference ~2.4e-7), isolates dorsal Z1.52–2.16 and removes all abdomen/width edits. The crest contamination was fixed.

| Tested back-only peak offset | Face flips | Faces area <0.5x | Faces area >2x | Verdict |
| ---: | ---: | ---: | ---: | --- |
| 0.22 | 420 | 459 | 3 | FAIL |
| 0.18 | 192 | 543 | 2 | FAIL |
| 0.14 | 11 | 454 | 0 | FAIL |
| 0.10 | 1 | 194 | 0 | FAIL |
| 0.06 | 0 | 1 | 0 | FAIL |

B offset 0.06 moves 1,614 real source-QEM vertices, numerical max back-profile ROI Z lowers from 1.8315 to 1.7898, but one source triangle still reaches a minimum area ratio **0.44261**. No valid PASS; do **not** fold into subsequent model/gait.

## Consequences / precise next gate

Stop blindly lowering the dorsal hump; the triangle(s) near the transition must be localized by polygon ID and original coordinates, along with vertex groups / intended joint influence. Treat a directed patch retopology as a **new derived mesh**, not as original QEM preservation. Before any new deformation, prove the crest remains source-fixed and source donor unchanged; after repair, revalidate *all faces*, 5 actual views, and re-rig motion.

Neither A nor B changes `main`, the approved S count remains **zero**. Technical mesh QA and S-design silhouette approval are independent.
