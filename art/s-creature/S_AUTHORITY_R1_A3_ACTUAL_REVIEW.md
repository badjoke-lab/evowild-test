# EvoWild S R1-A3 actual shoulder-side-patch review — 2026-10-10

**Verdict: REVISE / DO NOT PROMOTE.** Experimental scene exists and passed mechanical checks, but **did not solve the visible triangular shoulder/chest seam**.

## Source and actual output

- Exact design authority `art/s-creature/references/00_s_type_modeling_image_v1.png` SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
- Existing protected donor and current locally retained candidate: `art/s-creature/output/S-authority-r1-a2-scapula-v2.blend`.
- Measured read-only edge audit: `art/s-creature/output/review/authority-r1-a3-seam/SEAM_EDGE_AUDIT.json` and `S_R1_A3_seam_edges_{front34,rear34,side}.png`; Actions [37954126786](https://github.com/badjoke-lab/evowild-test/actions/runs/37954126786) SUCCESS.
- R1-A3 test: `art/s-creature/output/S-authority-r1-a3-sidepatch-v1.blend`; actual matched-camera renders `S_R1_A3_sidepatch_v1_*.png`, comparison `R1A2v2_vs_R1A3_actual_fiveview.jpg`, detail `R1A2v2_vs_R1A3_actual_joint_closeup.jpg`, and exact QA `R1_A3_SIDEPATCH_QA.json` under `output/review/authority-r1-a3-sidepatch-v1/`. Actions [37954810243](https://github.com/badjoke-lab/evowild-test/actions/runs/37954810243) SUCCESS. First attempt [37954562779](https://github.com/badjoke-lab/evowild-test/actions/runs/37954562779) failed **correctly** because a local face-area distortion exceeded limits; it did not commit a model.

## Actual diagnosis

- The proposed shoulder ROI has **1,451 physical internal edges**. Only nine exceed 37° and six exceed 45°. The broad V-shaped triangular seam seen in FRONT34 is predominantly a connected anatomical *surface-plane shape*, not merely a group of sharp polygon edges.
- The eight highest-angle edges cluster on both sides at X≈±0.128–0.161, Y≈−0.063 to +0.006, Z≈1.095–1.106. Their indices and exact adjacent face IDs are recorded in `SEAM_EDGE_AUDIT.json`.
- A non-global boundary-conditioned 3D side-surface fit modified **270 original vertices**, affecting **382 faces**, with **no vertex or polygon count changes**.
- The full candidate deformed small faces too much. A backtracking geometric validity search picked **0.55 strength**, preserving face area and orientation, the exact original cameras, all separate mesh assets, and manifoldness.
- Max lateral displacement ±0.01485. Mechanical validation passed.

## Five-view visual judgement

- FRONT34 **FAIL**: large triangular shoulder connection and scapula-to-foreleg change of surface orientation remain visible. Apparent smoothing is too modest to justify the change.
- SIDE **REVISE**: slight thoracic planar shift, no meaningful anatomical transition improvement.
- REAR34 **REVISE**: changes too small; the broad side surface and chest corner still look generic.
- FRONT/BACK **REVISE**: no meaningful full-body fidelity improvement.
- Shoulder crease angles >37° **9 → 9**, >45° **6 → 6**; mean in tested ROI **9.386 → 9.577°** (slight worsening). Meaningful visual improvement not demonstrated.
- Actual local image changed-pixel fractions, max-channel delta >=14: FRONT34 0.1823%, REAR34 0.0572%, SIDE 0.0745%. Pixel changes are descriptive and do not establish design approval.

## Disposition

- **Reject R1-A3** as a next full-body donor. Preserve the actual asset as a failed bounded experiment for audit.
- **Keep R1-A2 v2 as the last limited local geometry donor**, while the original accepted R0 remains the immutable silhouette recovery baseline.
- Do not repeat blind apex lowering, progressive normal smoothing, automatic voxel hulls, or low-amplitude lateral patch fitting; these failed or provided insufficient visual gain.
- Next meaningful modeling gate is to explicitly **rebuild the shoulder-to-foreleg quad loops / anatomical side planes** using the known problematic connected faces and the locked multi-view art, with visual review before acceptance. Key starting physical edge pairs: RIGHT (4094–4108, 3727–3729, 3729–3732, 3726–3727), LEFT (1327–1346, 829–832, 827–829, 826–827). These are *diagnostic starting points*, not approved loop topology.
- Hip/knee still need separately verified deformation-ready loops and an actual run-animation test after shape acceptance.
- Do not merge `main`, `feat/s-creature-model`, Motion First, or any game branch.
- **Production-complete S creatures: 0.**
