# EvoWild Run — S R1-A2 anatomical correction review (2026-10-10)

**Local result: KEEP v2 as a measured shoulder-apex improvement.**
**Full creature / R1 anatomy gate: REVISE, NOT APPROVED.**

## Source and evidence
- Immutable authoritative artwork: `art/s-creature/references/00_s_type_modeling_image_v1.png`, SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
- Accepted silhouette/recovery base: `S-authority-r0-a5-v2.blend`.
- Previously kept local joint donor: `S-authority-r1-a1-v3-patch.blend`.
- R1-A2 v1: `output/S-authority-r1-a2-anatomy-v1.blend`. Real 5 views and close-ups in `output/review/authority-r1-a2-anatomy/`. Actions [37951050003](https://github.com/badjoke-lab/evowild-test/actions/runs/37951050003) SUCCESS.
- Vertex survey: `output/review/authority-r1-a2-anatomy/R1_A2_SCAPULAR_APEX_SURVEY.json`, read only and based on actual v1 Blender vertices. Actions [37951648680](https://github.com/badjoke-lab/evowild-test/actions/runs/37951648680) SUCCESS.
- R1-A2 v2: `output/S-authority-r1-a2-scapula-v2.blend`. Real five-view and zoom sheet in `output/review/authority-r1-a2-scapula-v2/`. Actions [37952075402](https://github.com/badjoke-lab/evowild-test/actions/runs/37952075402) SUCCESS.
- Verified image files: `R1_A2_v1_vs_scapula_v2_fiveview.jpg`, `R1_A2_scapula_v2_actual_closeup.jpg`, `V2_IMAGE_QA.json`.

## Geometry work, not image editing
- A2 v1 reshaped 1,249 vertices in four local shoulder/hip fields, with maximum displacement 0.02887. The source R1-A1 v3 model, 5-view cameras, other crest/foot/tail geometry and topology remained unchanged.
- A2 v1 still showed an apex; original control center underestimated its world-space height.
- Actual coordinate survey identified paired apex locations near X=±0.112, Y=-0.013, Z≈1.146.
- v2 adjusted only **50 body vertices**, no new vertices or faces, with measured left apex Z **1.146477 → 1.100000** and right apex **1.145319 → 1.100000**. Maximum actual displacement 0.04648.
- Locked X/Y, all other meshes, topology and five cameras unchanged. Body non-manifold edges: 0. Native BLEND saved.

## Five actual view verdict
- **SIDE: limited KEEP**. Obvious sharp shoulder silhouette tip lowered; chest/shoulder remains simplistic and angular.
- **REAR34: limited KEEP**. Small dorsal peak visibly reduced. Shoulder/trunk surfaces remain insufficiently integrated with the forelimb.
- **FRONT34: REVISE**. The large triangular scapular seam is still visible despite the tip reduction. Pixel change is only 0.245% within the enlarged comparison region at max-channel threshold 14; visually modest.
- **FRONT/BACK: REVISE**. Full-body silhouette, crest articulation, hind leg/knee details, split feet and tail are not production-quality.
- This is *actual geometry* movement. Pixel difference is not design acceptance.

## Decision and next bounded gate
- Keep v2 as the best measured local headroom improvement, **do not promote to `main` or Motion First**.
- Stop arbitrary repeated smoothing, silhouette voxel hulls and blind spike-height changes.
- Next corrective gate must be **scapular side-surface anatomical reconstruction**, not apex-only adjustments: remove/dissolve the residual long triangular *junction seam* by explicit forelimb-to-thorax face-plane modeling and coherent deformation loops. The hip/knee must later receive separate anatomy and bending tests, not only shape bulges.
- Compare actual five views against the locked source, and validate deformation before any game integration. Those acceptance steps have not been completed.
- **Production-ready creature count: 0.**
