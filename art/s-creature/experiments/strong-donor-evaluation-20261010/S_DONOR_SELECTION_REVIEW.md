# EvoWild S donor selection — 2026-10-10

**Decision: QEM is the PRIMARY BASE FOR THE NEXT GEOMETRY/DEFORMATION FEASIBILITY GATE, not an approved game creature.** R5 remains a secondary visual anatomy reference only. R1-A3 and simplification/procedural-reset lanes must not be promoted.

## Source of truth and actual same-camera evidence

The only authoritative production design is `art/s-creature/references/00_s_type_modeling_image_v1.png`, SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.

A previously hash-verified preview, `art/s-creature/experiments/authority-rebuild-20261009/reference-authority-preview.jpg`, was cropped to show the canonical SIDE, FRONT, FRONT34 and BACK view panels. The editable GLB geometry was NOT changed.

Actual fair-comparison workflow: [37960739385](https://github.com/badjoke-lab/evowild-test/actions/runs/37960739385) SUCCESS.
- `review/SOURCE_vs_QEM_vs_R5_same_camera_four_views.jpg` — canonical visual design (top), QEM (middle), R5 (bottom); both 3D candidates physically rendered with the same Blender Workbench camera, material, lighting, orthographic scale and normalized vertical height.
- `review/QEM_vs_R5_same_camera_rear34.jpg` — extra matched 3D-only camera with no false claim that the source art has a rear34 panel.
- `S-strong-donor-side-by-side-review.blend` — editable scene preserving both geometries side-by-side for direct inspection; no mesh remesh or new creature geometry.
- `DONOR_AUDIT.json` — original model SHA256, source geometry counts, nonmanifold counts, common orthographic scale, review transforms and source paths.

## Candidate facts

| | QEM donor | R5 donor |
|---|---:|---:|
| Actual source GLB | `art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb` | `art/s-creature/experiments/authority-rebuild-20261009/r5-crest-lamina/S-authority-crest-lamina-r5.glb` |
| SHA256 | `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f` | `1d917a059fd77052c974a9dde7d40e65f80722fb08e52817b5852bf2d5abddcd` |
| Mesh objects | 1 | 9 |
| Vertices | 29,948 | 194,739 |
| Triangles / faces | 59,932 | 276,444 |
| Boundary / non-manifold edges | 0 | 104,118 |
| Rig / deformation acceptance | **NOT TESTED** | **NOT TESTED / NONMANIFOLD** |
| Production status | NOT APPROVED | NOT APPROVED |

Original R5 geometry has the strongest layered chest, hip and feather-like tail cues of the two candidates, but a crude oversized crest, short body and a fragmented open topology that blocks straightforward rigging.

The QEM model's continuous long-body silhouette, overall neck line, skull and hind-limb bend are stronger starting geometry for the approved sprint body plan. The donor still has poor front foot anatomy, exaggerated smooth side panels, oversimplified whip-like rather than layered blade tail, and poorly integrated white thoracic armor and oversized/deformed front shoulder pads compared with the design. The eye, crest root and body markings also need anatomical/detail correction.

**The selection is provisional and strictly scoped:** QEM is the next **model source for shape-preserving tests** because it already has a single watertight usable geometric shell. No 3D production quality or motion is accepted.

## Critical correction in comparability

The initial scripted donor review falsely rotated QEM 90 degrees: actual proof rendered the animal upside down. This was a review-only transformation error. GitHub Actions 37960272569 generated an invalid upside-down comparison and is REJECT. Subsequent run 37960533350 was also not accepted. The correct run 37960739385 uses **no extra QEM axis rotation**, because the Blender GLB importer already yields long body along Y and upright anatomy along Z. Do not reuse the erroneous screenshots.

## Locked immediate next gate: QEM deformation feasibility BEFORE beautification

Do **not** sculpt a dozen QEM revisions before demonstrating skeletal utility. First inspect the original GLB and record anatomical joint landmarks (L/R front shoulder, elbow, wrist and L/R hip, stifle, hock) in consistent Blender model coordinates. Then make an **isolated rigging test** of a copy and render actual bent leg poses and side/front34/rear34 from the same mesh. Reject rig feasibility on stretching, crumpling, leg fusion, flipped faces, contact failure, or loss of silhouette.

Only after feasible deformation should the QEM body be anatomically reshaped against the canonical SIDE/FRONT/FRONT34/BACK; the R5 model may be viewed as shape reference but **its disconnected body cannot simply be welded into QEM**. All edits must retain source GLB and original model SHA as recovery points.

Never replace QEM with the R0 low-poly procedural cage merely for ease of rigging. If native QEM skinning fails, separate **visual shape transfer / retopology** from motion proxy; do not downgrade the visible creature without an explicit comparison and approval.

Unresolved: complete source-art fidelity; rig; run/jump animations; game camera; LOD and game integration. Production-ready S creatures: **0**. Production `main`, `feat/s-creature-model`, and Motion First are unchanged.
