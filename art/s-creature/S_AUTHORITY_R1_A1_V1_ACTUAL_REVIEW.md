# S Authority R1-A1 v1 — actual-image review

**Final result: REVISE. Technical gate PASS, visual quality NOT accepted.**

## Exact provenance
- Source: `art/s-creature/output/S-authority-r0-a5-v2.blend`, R0 morphology KEEP.
- Candidate: `art/s-creature/output/S-authority-r1-a1-v1.blend`.
- Generation: [GitHub Actions 37944170915](https://github.com/badjoke-lab/evowild-test/actions/runs/37944170915); Blender build, render and validation succeeded, but initial **git add failed** from sparse-checkout. Recovery completed without rerunning Blender in [37944420465](https://github.com/badjoke-lab/evowild-test/actions/runs/37944420465).
- Actual matched 5-view R0/R1 comparison: `output/review/authority-r1-a1-trial/S_R0_vs_R1A1_real_fiveview.jpg`.
- Actual local view comparison and delta: `output/review/authority-r1-a1-trial/R1_A1_three_region_actual_zoom_comparison.jpg`; `R1_A1_image_delta_QA.json`.
- Locked morphology source: `references/00_s_type_modeling_image_v1.png`, SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.

## Validated geometric invariants
- 1,854 body vertices edited within the allowed shoulder and pelvis support regions.
- Max vertex displacement 0.014328 (hard cap 0.025).
- Mean local roughness 0.00365055 → 0.00301096 (ratio 0.8248); **technical local smoothing** occurred.
- Fixed outside-support vertices unchanged exactly; all separate crest, toes and blades unchanged exactly.
- Topology unchanged; non-manifold edge count zero.
- Original five camera transforms unchanged, same model materials and lighting; render did not modify geometry.

## Actual-image inspection
- **FRONT34: REVISE** — large separate/faceted shoulder/scapular plate remains visually abrupt, with a stepped root and unintegrated side edges. Candidate improvement is scarcely perceptible.
- **REAR34: REVISE** — proximal hindlimb and pelvic junction are still a hard kink / segmented lump; smoothing is not visually consequential.
- **SIDE: REVISE** — high shoulder/chest seam and blocky hip are still present despite small local surface change.
- **FRONT/BACK: REVISE** — global proportions and centerline crests are unchanged; no new production-acceptance evidence.
- Magnified changed-pixel counts (threshold max RGB delta ≥14) are only 263/786432 FRONT34, 74/786432 REAR34, 249/786432 SIDE (about 0.033%, 0.009%, 0.032%). This is not proof of "no improvement," but **does demonstrate the visible delta is extremely small**.
- Do not claim the existing surface continuity problem is resolved because roughness decreased 17.5%. Technical PASS ≠ design KEEP.

## Disposition
- Keep original R0 morphology as the approved **blockout**.
- Preserve R1-A1 v1 as a **rejected trial**, do not promote or merge to production or Motion First.
- **Stop repeated Taubin/lambda/mu/smoothing cycles**: the remaining issue appears to involve part junction geometry and overlapping armor / shoulder meshes, not only local body surface noise.
- Next: identify exact geometry objects responsible for shoulder/scapular and hip intersections in the accepted R0 scene before editing their joins, compare actual renders. Do not change the preserved head/crest, body silhouette, feet or tail.
- Full production creature completion remains 0.
