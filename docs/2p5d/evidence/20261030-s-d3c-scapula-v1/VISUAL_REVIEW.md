# EvoWild Run S — D3-C scapula authoring v1: real-asset review

## What was actually created
- Independent experimental branch `exp/d3c-scapula-authoring` based on Draft PR #132 code; no merge, no edit of original `focus-contact-v3.glb`, no production manifest/main change.
- New standalone skinned GLB `public/models/evowild-s/review/d3c-scapula-author-v1.glb`; SHA256 `963b52b0f82e58edb02423615415502f50e6245fa4f50a1606d192f0bae64a2d`.
- 21→**23** actual skin joints, `fore_L_scapula` and `fore_R_scapula` inserted between chest and upper arms. Two native GLTF rotation-animation channels are authored in `EvoWild_S_Run_V5` (58→60).
- Chest skin slots near actual shoulder influence are transferred to scapula: **1,593 vertices on L**, **1,036 on R** (chest-equivalent weight sums 174.94 and 141.39); no mesh position, topology or UV modification.
- Existing fore-upper translation keys were rebased by their prior local translation to preserve the original upper-arm world transform at neutral shoulder. With scapular rotation disabled, transferred chest weighting has the same skin transform as before.

## Reproducible real evidence
- [Generation, neutral/active mesh tests and actual five-view clips](https://github.com/badjoke-lab/evowild-test/actions/runs/41075353979): all steps SUCCESS.
- [Separate true sole-contact regression](https://github.com/badjoke-lab/evowild-test/actions/runs/41076224940): all steps SUCCESS.
- [Detailed author report](author-report.json), [4 original-vs-neutral/active Playwright cases on PC/Pixel 7 emulation](targeted-test.log), [2 sole-contact Playwright cases on PC/Pixel 7 emulation](contact-test.log).
- Actual real WebGL before/after full-cycle `before-{SIDE,FRONT,CHASE,LOW,REAR_3_4}.mp4` and `after-*.mp4`; consecutive original frames in `frames/`, desktop/Pixel7 emulated screenshots. These are **not** image-generated creatures or interpolated motion frames.

## Quantitative boundaries (no threshold changes)
- Max neutral displacement from original across six sampled phases: **1.125e-8 m** (310 sampled actual skinned vertices; not a mathematical proof for all 38,813 vertices).
- Opt-in authored shoulder movement displaced sampled actual skinned vertices by as much as **0.026689 m** at phase .20; other examined phases range ~0.0123–0.0254m. This proves deforming skin, not animation quality.
- Contact on authored rig: six profiles (steady 0.5, 1, 1.5; abrupt fore/hind; acceleration), both browser projects. Worst sole-vertex speed residual **0.005987m/s**, support gap **0.423752mm**, support slip < **0.0009mm**, foot zero-time jumps 0, penetration 0, IK reach error 0. Hind recovery ~47.98cm. Physical Pixel 7 device and 18-racer performance were not tested.

## Direct inspection / visual verdict

**SCOPED KEEP: actual new shoulder rig, correct neutral-source continuity and contact tests.**

**FULL S RUN VISUAL: REVISE.** Viewed actual stored SIDE/REAR_3_4/FRONT source frames 00,08,16 before and after (phases .64, .97, .31). The authored scapular deformation is measurable but the animal remains nearly identical at these ordinary game-size views: upper arms and elbows still cycle beneath a comparatively rigid thorax. The real images do not establish convincing shoulder advance during landing, chest loading and propulsion or a true coordinated gallop. The front view is strongly shadowed; it is useful for outline checking but does not resolve shoulder-surface quality. This is a review of saved frames, not a claim of personally watching the MP4 at normal playback or user approval.

This trial is not the final creature, and its gray inherited canonical likeness is **not** approved against `art/s-creature/references/00_s_type_modeling_image_v1.png` (source available on separate `exp/s-creature-vibe-modeling` branch). No R9 zero-rebuild geometry was merged.

## Next physical authoring hypothesis
Using the new independent scapular joint, **author a shoulder–upper-arm–elbow–chest motion cycle rather than just increasing scapula angle**. Aim for visible scapula protraction during foreleg swing, elbow fold/recovery, then chest compression and scapula retraction on support, retaining native sole IK. Diagnose the remaining partial cancellation between IK upper-arm solving and the scapula cycle. Improve the local shoulder-weight transition only if actual shaded side/low views show a deformation problem. Preserve the tested neutral/push-v5 baseline and all contact thresholds; retain this candidate as v1 until a visibly superior v2 has same-view videos and contact probes. No production integration or PR merge.
