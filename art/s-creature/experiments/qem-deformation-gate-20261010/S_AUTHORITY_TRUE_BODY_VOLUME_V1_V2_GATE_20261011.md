# EvoWild Run / S-type — canonical reference vs original-QEM body volume v1/v2 (2026-10-11)

## Immutable highest authority

The sole **user-approved** S Type "Sprint Morph" modeling source:
`art/s-creature/references/00_s_type_modeling_image_v1.png`
SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.

**Do not** treat any screenshot from downkr.com, newly generated creature concept art, or a prior surrogate as modeling authority. Every GH Actions in this study checks the actual repository PNG bytes directly.

Real TRELLIS2 QEM GLB donor: `art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb`. SHA-256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`.
Original 29,948 vertices / 59,932 triangles, **unchanged**. Input derived tail core M 31,948 vertices / 63,932 triangles, **unchanged**.

## What was executed

1. **Actual M-QEM anatomy survey**: Blender measured shoulder, chest, upper back, waist, haunch and head vertex positions in world coordinates, plus Y-sliced 3D cross-section widths/heights. Saved `body-authority-survey-20261011/ORIGINAL_QEM_S_BODY_REAL_COORDINATE_SURVEY.json`. Actions run [38144102225](https://github.com/badjoke-lab/evowild-test/actions/runs/38144102225) PASS.
2. **Real QEM body-v1**: Original M copied with original skin and triangle topology. Applied 8 direct 3D shoulder and haunch vertex-width volume changes, compared full evaluated triangle area/inversion and torso BVH against identical M, protected feet, tail and head. All eight failed quality threshold: even lowest 0.04/0.04 yielded one triangle >2x reference area. Saved actual Blender source and real five views **as FAIL**. `body-mass-shoulder-haunch-v1/REAL_QEM_SHOULDER_HIP_MASS_QA.json`. Actions [38144444496](https://github.com/badjoke-lab/evowild-test/actions/runs/38144444496) SUCCESS for execution, geometry FAIL.
3. **Real QEM body-v2**: Kept the same original M donor and anatomical volume method, added an iterative local surface strain projection: damp only vertex displacements of violating triangle faces. All eight cases re-tested with actual Blender evaluation and torso BVH; **3 passed numerically**. Chosen shoulder/hip strengths 0.08 / 0.07 with maximum actual vertex world movement 0.0693946 and 15,269 vertices moving more than 0.003 units. Torso ROI shoulder 5–95%-tile transverse-width +0.0866671 model units; hindquarter +0.1082514. Zero reversed triangles, zero degenerate triangles, zero triangles under half or above twice source face area. Min face area ratio 0.581616, max 1.911451. No new torso-BVH self-overlaps (0 -> 0). Protected head/tail/feet ROI max movement 0.00000185. Repeated Blender save-read test PASS. `body-mass-shoulder-haunch-v2/REAL_QEM_SHOULDER_HIP_PROJECTED_V2_QA.json`.
   - First v2 workflow failed the replay gate because of inappropriate exact floating-point face-area-extrema equality after Blender float32 world/local roundtrip; corrected by exact defect counts / BVH with a small tolerance on only numeric area extrema.
   - Final Actions [38144783331](https://github.com/badjoke-lab/evowild-test/actions/runs/38144783331) **SUCCESS and actual limited geometry PASS**.
   - Actual editable Blender: `body-mass-shoulder-haunch-v2/S-QEM-genuine-body-mass-v2-STRAIN-PROJECTED.blend`.
   - Real same-view 5 direction comparison: `body-mass-shoulder-haunch-v2/review/ACTUAL_S_QEM_BODY_FIVE_VIEW_COMPARE.jpg`.
   - Source-canonical-S and actual Blender side views: `body-mass-shoulder-haunch-v2/review/CANONICAL_S_VS_REAL_BODY_MASS_V2.jpg`.

## Mandatory visual review: **REJECT S design**

Compared the actual Blender five views and **exact canonical S source side image crop**:

- Original S has a major angular white/navy/blue plated shoulder, compact muscular deep thorax, articulated thigh armor, rearward layered tail plumes, full head and crest.
- The v2 QEM remains very narrow/crescent-shaped in profile, long antelope/snake-necked, with an oversized open head horn and almost no segmented shoulder/thigh armor compared with the reference. Five-view render confirms the anatomical volume increase is **subtle**, not a solved body sculpt.
- There is **no canonical 3D appearance match**. Numeric +0.08 units of transverse width does not substitute for the missing forms. Neither v1 nor v2 is approved as final S.
- The original grayscale Workbench views do not validate surface colors or painted armor.
- Existing 13-bone and old IK cycles are not revalidated on the altered vertices. No claimed gait/rig compatibility, game performance or actual race scene pass.

## Actual next gate, no further generic bulking loops

**STOP Gaussian shoulder/hip broadening at v2.** Keep v2 as a safe local deformation prototype only, not a new modeling base asserted to be canonical.

The next true-shape pass must build the missing **recognizable 3D shoulder/chest plate geometry and thigh/hip anatomical volume**, using the source reference SIDE+FRONT+FRONT34+REAR34+BACK forms and explicit outline/roots/face thickness; review in actual 5-view Blender renders, not fresh concept images. Reconstruct torso and head/neck silhouette at meaningful proportions, then rerig and test after visual design agreement. The missing segmented plates cannot be created by a scalar radial inflation of the thin original torso.

Production / `main` remains unchanged. Total canonical-approved S creatures: **0**.
