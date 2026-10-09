# EvoWild Run / S-type R1-A1 v3 actual-image decision

**Local result: KEEP as a limited surface-junction improvement.**
**Overall R1-A1 anatomical acceptance: REVISE; production creature NOT approved.**

## Exact work products and authority
- Isolated branch: `exp/s-authority-r1-a1-trial-20261009`.
- Unmodified source: `art/s-creature/output/S-authority-r0-a5-v2.blend` from accepted R0 morphology.
- Exact S-type primary image: `art/s-creature/references/00_s_type_modeling_image_v1.png`, SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
- New real Blender file: `art/s-creature/output/S-authority-r1-a1-v3-patch.blend`.
- Actual five matched-camera views: `art/s-creature/output/review/authority-r1-a1-v3-topology/S_R1_A1_v3_{side,front,front34,rear34,back}.png`.
- Full original-v3 contact sheet: `art/s-creature/output/review/authority-r1-a1-v3-topology/R0_vs_R1A1_v3_fiveview.jpg`.
- Real cropped evidence and delta stats: `S_R0_vs_R1A1v3_shoulder_pelvis_real_closeup.jpg`, `S_R1A1v3_pixels_QA.json`.
- Raw mechanical verification: `art/s-creature/output/S-authority-r1-a1-v3-patch-validation.json`.
- Successful 3D generation: Actions [37948048045](https://github.com/badjoke-lab/evowild-test/actions/runs/37948048045).
- Actual closeup evidence: Actions [37948368517](https://github.com/badjoke-lab/evowild-test/actions/runs/37948368517).

## Actual geometry change
- Subdividing original quads (BMesh grid expansion) was rejected: new vertices extended far outside anatomical ROIs (3,105 of 6,775). DO NOT resurrect that strategy.
- Current v3 uses **zero new vertices**. Re-routed the diagonals of 650 localized high-angle quads, resulting in 5,726 -> 6,376 faces with all 5,728 original vertices preserved.
- Geometrically moved 2,400 original vertices via bounded normal-oriented local correction, max displacement 0.0420.
- Within inspected shoulder/pelvis regions: high-angle edges **>60°: 272 -> 35; >90°: 71 -> 16**. Counts are region-specific and are not proof of anatomical fidelity.
- Exactly unchanged: original vertices outside ROIs, all separate crest/feet/tail meshes, all five camera transforms.
- Non-manifold edges 0; bbox maximum drift 0.006997.

## Real image appraisal
- FRONT34: the stair-stepped shoulder cap has become substantially smoother and the front leg root now visually continues into the chest, but a tapering *stuck-on triangular scapular fin* is still prominent. The result can be too soft/round to read as sculpted muscles.
- REAR34: the hip and hind-upper-limb facets are markedly reduced, but thigh/knee anatomy and topology are not yet validated under deformation.
- SIDE: the harsh lower shoulder steps are removed, but the high outer crest of the shoulder and the angular junction remain; do not declare a final sculpt.
- FRONT and BACK: silhouette stays similar; the overall character design, split racing feet and tail lamina still look primitive.
- The fixed crop pixel-change statistics are 7.74% FRONT34, 3.87% REAR34, 4.49% SIDE (max RGB channel difference >=14). Unlike R1-A1 v1, v3 made a visually meaningful change. **Pixel change measures magnitude, not artistic approval.**

## State and mandatory next work
- **Do not merge into `main`, `feat/s-creature-model`, Motion First or any gameplay branch.**
- Preserve this v3 native Blender file as the strongest *local shoulder/hip-junction refinement donor*. The approved **R0 morphology source remains the immutable recovery point**.
- Next stage: separate anatomical shape correction of shoulder-scapula/forelimb muscle planes, hip/knee joint construction, and face-loop routing for actual skin deformation, using approved S artwork and verified side/front/front34/rear34/back images.
- Do NOT attempt new Taubin smoothing cycles, unrestricted quad subdivision, or texture/material tricks to disguise remaining geometry issues.
- Before production acceptance: verify full creature five-view likeness, closed deforming mesh under skinning, running gait and game-camera readable motion. These are **NOT** achieved here.
- S production-complete creature count remains **0**.
