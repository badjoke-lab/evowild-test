# EvoWild Run — independent V2 visual review (2026-10-14)

**Shape quality gate: REVISE. NOT APPROVED.** Real Blender edit execution is technically **PASS**.

## Verified run and exact evidence

- GitHub Actions success: https://github.com/badjoke-lab/evowild-test/actions/runs/38503031716
- V2 asset: `review-v2/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V2.blend`
- Mesh: 38,802 vertices, 77,684 faces (same source topology).
- Changed versus V1: 12,504 vertices.
- Shoulder 2.5–97.5% X-width on fixed test region: 0.39216657 (V1) to 0.38198099 (V2), i.e. -0.01018558 Blender units (~2.6%).
- Local topology safety: 0 newly reversed normals, 0 newly degenerate faces, 2 existing degenerate faces unchanged; 8 displacement-damping rounds across 26 affected vertices for a previous triangle reversal.
- Input V1, original Hunyuan and highest-authority art exact SHA256 unchanged; saved/reloaded `.blend` verified. This is not a complete self-intersection or rig-readiness check.
- Real image evidence seen: `BASE_V1_V2_SHOULDER_DETAIL.jpg`, `BASE_V1_V2_REAL_FIVE_VIEW.jpg`, `CANONICAL_VS_V2_UNREGISTERED.jpg`.

## Art review (canonical = 00_s_type_modeling_image_v1.png)

1. **FRONT:** bilateral shoulders still look like big rounded balloons. Numerically narrower, but canonical depicts narrower high shoulder plates with clear articulated inner chest contours. Measured width change alone does not establish similarity.
2. **SIDE and FRONT34:** distinctive **unwanted thin dark cut/notch** has emerged on upper outer shoulder, appearing as a tearing-looking slit rather than a layered muscle/armor plane. Must not KEEP.
3. Shoulder-to-pectoral-to-humerus still reads as a single bulge/continuum, not the purposeful overlapping elongated diagonal planes and sharply readable upper-arm boundary in canonical.
4. Chest ventral silhouette and upper-arm connection remain blocky, without the canonical interlocking plate shapes.
5. Original crest, head, tail, limbs/feet still widely differ from canonical; these are outside the current isolated edit scope and must not be claimed solved.

## Required next corrective gate

- **Do not scale up the current brush field or accept the slit as a plate seam.**
- Preserve V1 and V2 as rejected examples, keep the source immutable, work in isolated V3 only.
- First isolate and quantitatively map the observed notch: per-face normals, local edge lengths, local thickness/occlusion; determine if actual intersection, highly concave fold, or material/lighting artifact.
- Repair offending area by local surface-following relocation and/or smoothing, preserving connectivity and true overlap where appropriate. No false primitives.
- Prefer forming a broad *distinct directional surface plane* over a narrow Gaussian crease. Thin sharp ridges without calibrated 3D normals are not sufficient.
- Keep matched SIDE/FRONT/FRONT34 closeups and full 5-direction comparisons at matched cameras/materials/exposure, alongside canonical illustration. The 3/4 images and front width gate are primary.
- If V3 still looks like a swollen trunk, cease repeated parametric deformation and switch to interactive art-directed Blender sculpting via a controllable GUI/MCP lane rather than producing superficial revisions.
- Rigging/animation/game merge remain forbidden until visually approved.

**Decision:** V2 = REVISE, not a canonical S model; technical proof only.
