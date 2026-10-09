# EvoWild S — QEM original geometry: actual deformation and armature gate

**Project-wide creature production acceptance: NOT APPROVED.**
**Local mechanical result: PASS limited 4-leg, small-angle ARMATURE skinning test.**
**First full-angle trial: FAIL.** This distinction is mandatory.

## Strict authority and preserved source

- Top-level S visual design: `art/s-creature/references/00_s_type_modeling_image_v1.png`, SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
- Trellis2 QEM source: `art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb`, SHA-256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`.
- Source has 29,948 vertices, 59,932 faces, and zero boundary/nonmanifold edges. All experiments retain the SAME original mesh geometry and vertex order. No return to simplified procedural R0.
- Isolated experimental branch `exp/s-qem-deformation-gate-20261010`; game `main` and Motion First remain untouched.

## Real source survey

GitHub Actions [37991867792](https://github.com/badjoke-lab/evowild-test/actions/runs/37991867792) SUCCESS.
Files in `art/s-creature/experiments/qem-deformation-gate-20261010/`:
- `JOINT_LANDMARK_SURVEY.json`: original-space to normalized review-space bounds, Y-axis surface bins, candidate foot vertex distributions by side.
- `S-QEM-pre-rig-source-review.blend`: actual QEM source (no rig).
- `landmark-survey/S_QEM_joint_survey_fiveview.jpg`: same unaltered QEM in real five view orthographic Blender renders.

Joint candidate locations derived directly from original mesh vertices, not a guessed skeleton:
- FORE_L (-0.3445, -0.6334, 0.6394), FORE_R (0.2996, -0.4380, 0.6400);
- HIND_L (-0.3761, 1.8080, 0.7219), HIND_R (0.3546, 1.9459, 0.7047).
These points are **not yet anatomically approved knee/ankle landmarks**.

## Real mesh-space four-limb bend: failed large / passed small

- Run [37992205481](https://github.com/badjoke-lab/evowild-test/actions/runs/37992205481), files `bend-probe-v1/`: original ±14° forelimb, ±12° hindlimb candidate lower joint bend, 7,660 moved vertices, two triangle flips, 239 triangles below half the original area, one above double the area. **FAIL.**
- Run [37992449863](https://github.com/badjoke-lab/evowild-test/actions/runs/37992449863), files `bend-probe-v2/`: safe stepwise strength scan found factor **0.3**. Approx forelimb ±4.2° / hindlimb ±3.6°, 7,579 moved vertices, 15,542 faces affected, zero flips, zero collapse, zero area shrink below 0.5 or expansion above 2.0, no topology damage. **Limited vertex-deformation gate PASS.** This is not an armature test.

## ACTUAL Blender armature, keyframed 16-frame test

Run [37992767303](https://github.com/badjoke-lab/evowild-test/actions/runs/37992767303) SUCCESS.
Files: `armature-test-v1/S-QEM-armature-weighted-16-frame-test.blend`, `armature-test-v1/ARMATURE_TEST_QA.json`, `armature-test-v1/review/QEM_actual_armature_before_after_5view.jpg` and `QEM_armature_5_keyframe_sample.jpg`.

- Real Blender ARMATURE modifier, 5 editable bones: ROOT_TORSO, FORE_L_LOWER_LIMB, FORE_R_LOWER_LIMB, HIND_L_LOWER_LIMB, HIND_R_LOWER_LIMB.
- Five weighted vertex groups correspond to these bones; source QEM remains available as a separate immutable object.
- Real pose-bone rotation keyframes 1 (rest), 8 (bend), 16 (rest) at 24 FPS, with frame-by-frame evaluated mesh measurements.
- Pose frame 8: 7,579 moved vertices, displacement max 0.076654 normalized world units, 59,932 original triangles preserved, zero triangle flips/collapses, zero area shrink below 0.5 or expansion above 2.0.
- Rest pose max-coordinate error **0**, source geometry and original GLB SHA preserved.
- Gate: **PASS_LIMITED_ARMATURE_SKINNING** only.

## Limitations and next required acceptance

This is **not** a quadruped running animation and **not** finished S creature rig. Hip, shoulder, stifle, elbow, wrist and fetlock joints are not anatomically placed and driven independently. No IK, stance/recovery cycle, root locomotion, balance, verified ground contact, avoidance of knee snapping, or muscle/armor deformation under large race gaits. The source visual design still has large unmodeled armour/foot/tail differences.

Next gate is **anatomical limb-joint/quad loop placement and deformation-ready retopology for larger ranges**, with actual 5-view image and 16-frame playback evidence. Do not increase hinge angles beyond measured passing range or simply relax face-damage thresholds. Do not merge or export to Motion First before running is physically/readably validated.

`armature-test-v1/motion-preview-16-frames/` (when present) contains original Blender keyed pose render frames and a slowed preview GIF, **not** a validated run-cycle video.

S production-ready creature count: **0**.
