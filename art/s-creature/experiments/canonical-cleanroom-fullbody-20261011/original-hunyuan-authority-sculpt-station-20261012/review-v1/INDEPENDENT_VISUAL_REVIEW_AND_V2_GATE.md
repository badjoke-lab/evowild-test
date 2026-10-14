# EvoWild Run — Independent V1 visual review / V2 sculpture gate
Date: 2026-10-14 UTC (visual inspection)
Branch: `exp/s-hunyuan-shoulder-sculpt-20261013`
Source candidate: commit `3e54d59555d1f5a17f38ee9c7f2846b41bf9fd71`
Verdict: **REVISE**; do not approve / merge / rig / animate.

## Actual evidence inspected

- Real `review-v1/SHOULDER_CHEST_BEFORE_AFTER.jpg` (BEFORE / AFTER, SIDE / FRONT / FRONT34).
- Real `review-v1/FIVE_VIEW_BEFORE_AFTER.jpg` (BEFORE / AFTER, five real Blender camera views).
- The full canonical `art/s-creature/references/00_s_type_modeling_image_v1.png`, SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
- `review-v1/SCULPT_VERIFICATION.json`, `review-v1/FACE_QUALITY.json`, `review-v1/REVIEW.md`, and `art/s-creature/blender/s_hunyuan_shoulder_chest_sculpt_v1.py`.

## Separate numerical claims from visual/art success

- PASS (from V1 saved verification): one real source mesh edited, 8,674 vertices modified, 38,802 vertices / 77,684 faces retained, exact reload, protected files hashes unchanged.
- PASS (limited face tests): no newly reversed normal; two original degenerate faces still remain.
- NOT PROVEN: self-intersection-free, game topology/rigger suitability, accurate alignment to the canonical orthographic drawing or independently successful GitHub Actions reproduction.
- Artwork remains REVISE.

## Visual problems compared with canonical

1. **FRONT:** V1 creates oversized rounded bilateral shoulder/pectoral volumes. Canonical front has a comparatively restrained, elongated narrowing through neck and thorax, defined angular light shoulder plate over dark tissue. V1 does not match the widths/contours.
2. **SIDE:** Shoulder, pectoral and proximal upper arm still read as one continuous swollen mass. The illustrated shoulder plate rises and slopes *diagonally* into distinct layered transitions; don't equate round enlargement with anatomical separation.
3. **FRONT34:** No sufficiently readable facet/surface boundary across the top shoulder into lateral pectoral and humerus. V1 retains a blob-like shoulder instead of the layered oblique white/blue armor-muscle shapes in the illustration.
4. **AXILLA/UNDERSIDE:** Local indentation has been added, but the silhouette still lacks a credible change of planes from dark pectoral to slim abdominal underside and from shoulder into the forelimb.
5. **ORIGINAL MESH DEFECTS OUTSIDE V1 ROI:** Long crest/head, tail ribbon geometry, forefeet and limbs do not yet reproduce canonical; they were expressly outside V1 scope and must remain unapproved.

## Next V2 objective (not blanket inflation)

- **Start V2 from the V1 .blend in a new isolated destination**, preserve original authority and V1 intact.
- Address front silhouette width **first**, guided by the canonical front drawing and common-frame renders; do not simply amplify V1 brush amplitudes.
- Form an **oblique, anisotropic ridge** from upper shoulder/scapular crest toward humeral attachment, with identifiable overlapping outer plate/tissue volume and recessed underlying boundary. Must remain part of the genuine existing surface (no primitive overlay or substituted mesh).
- Produce a second distinct **pectoral-to-upper-arm plane break** readable in FRONT34 and SIDE, without a sharp crease or isolated ball. Preserve anatomical continuity in 3D.
- Keep chest floor from becoming a heavy ventral belly; taper into the abdomen with plausible continuous slope.
- Implement smoothly tapered ROI masks to protect outside vertices without abrupt hard displacement discontinuity; unchanged face connectivity and critical silhouettes.
- Keep camera, exposure, material, cropping, orientation, and lighting identical between BASE/V1/V2. Include *canonical artwork adjacent to renders*, with explicit warning that pixel registration is not exact.
- Generate SIDE / FRONT / FRONT34 / REAR34 / BACK and SIDE/FRONT/FRONT34 closeups. Add a 3-way contact sheet **BASE vs V1 vs V2** and numeric width / bounding measurements, plus before-after changed vertices count.
- Run saved-file reload and topology/normal/degeneracy tests; if feasible test self-intersections. Preserve original, V1 and canonical SHA.
- **V2 KEEP gate:** front width nearer the illustration, obvious separate oblique shoulder plate/pectoral/humerus volumes from SIDE and FRONT34, realistic silhouette continuity, no new defects. Otherwise REVISE and don't promote the model to game.
- No running animation, rigging, game deployment, or `main` merge prior to visual approval.

## Execution requirement

Run true Blender 4.3.2 `bpy` on the retained existing mesh, write a separate `S_HUNYUAN_SHOULDER_CHEST_SCULPT_V2.blend` under `review-v2`; produce actual image comparisons, exact verification data, and independent KEEP/REVISE. Avoid repeating environment setup or single-vertex proof.
