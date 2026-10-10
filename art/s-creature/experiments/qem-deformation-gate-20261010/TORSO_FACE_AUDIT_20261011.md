# EvoWild Run — real QEM torso deformation face-ID localization, 2026-10-11

## Outcome

**Technical face-quality gate: PASS at the maximum tested 0.050, with very little safety margin. S-morphology gate: NOT APPROVED.**

Authoritative S image: `art/s-creature/references/00_s_type_modeling_image_v1.png`; SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
Original source TRELLIS2 QEM GLB: SHA-256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`. The source remains untouched (29,948 vertices, 59,932 faces), new work isolated to experimental Blender shape key on an independent object.

Source `exp/s-qem-torso-isolated-b-20261010` failed at its 0.060 minimum tested amplitude, leaving a localized failure. To isolate it, `art/s-creature/blender/s_qem_torso_face_localization.py` replays **13 separate strengths from 0.060 to 0.002**, evaluating actual Blender mesh triangles. Detailed proof is `torso-face-audit-20261011/TORSO_FACE_ID_LOCALIZATION.json`.

| Dorsal torso-only offset | Failing faces | Minimum evaluated area ratio | Decision |
| --- | ---: | ---: | --- |
| 0.060 | 1 | 0.442612 | FAIL |
| 0.050 | 0 | 0.511654 | **PASS (limited)** |
| 0.045 | 0 | 0.552189 | PASS |
| 0.040 | 0 | 0.595733 | PASS |
| 0.030 | 0 | 0.689441 | PASS |
| 0.020 | 0 | 0.789248 | PASS |
| 0.010 | 0 | 0.893211 | PASS |
| 0.002 | 0 | 0.978474 | PASS |

The actual failing triangle at 0.060 is **polygon 20958**, vertex indices **12566, 13507, 12944**, original world centroid `(-0.102783,+0.731176,+1.700315)`. Its very small original double area `0.00016991` shrank below the required half-area threshold. Original edge lengths were ~0.09092/0.05607/0.03493 model units. Its three original world coordinates and deformed coordinates are explicitly saved in the JSON.

Unlike A, this B-derived experiment masks all vertices in crest Z>2.20 and foot Z<0.70, numerical freeze error ~2.4e-7; no more unrelated crest bending. **It does not repair the thin triangle or the torso design shape**; 0.050 only proves an immediately bounded geometry-safe adjustment with a tight 0.01165 minimum-ratio safety gap.

Actual Blender five-direction source / bounded-variant images are preserved as `torso-face-audit-20261011/review/QEM_TORSO_FACE_DIAG_FIVE_VIEW.jpg`. Editable `.blend`: `torso-face-audit-20261011/S-QEM-torso-face-audit-TRIAL.blend`. [Actions 38065288233](https://github.com/badjoke-lab/evowild-test/actions/runs/38065288233) confirms real execution.

## Gate / next action

1. Do not call **0.050** anatomically approved; it is deliberately conservative and visually modest. No game integration.
2. Any significant torso contour change requires local retopology around polygon 20958, smooth weight transitions, and five-view authority comparison; identify additional skinny faces from **complete** face QA after local repair.
3. Recheck real 13-bone armature, 97-sample locomotion mesh/contacts and game-view readability only after variant topology and morphology actually meet the authority.
4. No main edits. Do not reuse QEM old gait PASS on a changed mesh. **Completed S type: 0.**
