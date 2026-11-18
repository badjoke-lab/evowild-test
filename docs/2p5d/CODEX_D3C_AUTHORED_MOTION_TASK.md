# EvoWild Run S — D3-C: authored shoulder / elbow / chest gait (Codex)

## Starting point (verified 2026-10-30)
- Repository `badjoke-lab/evowild-test`, branch `feat/2p5d-flow-persistence-20261025`, Draft PR #132, remote head at task creation `229a28e9a7d66e718378867040bb78fbfa3af8b9`. Fetch latest again before changes.
- D3-B numeric repair **COMPLETE**. Do NOT repeat its 36 focused tests or 8 video captures as a new work item. Evidence: `docs/2p5d/evidence/20261029-s-d3b-fore-reach/` including `VISUAL_REVIEW.md`, `NUMERICAL_REVIEW.md`, before/after four-view real MP4.
- D3-B speed-response correction only: max actual foot-vertex velocity residual .109690 -> .005987m/s, chest .083252 -> .0000643m/s. Limited numerical KEEP; full S visual REVISE.
- PR remains Draft, main/GLBs/manifests unchanged. Keep D2-D push-v3 baseline, D3-A push-v4 diagnostic and repaired D3-B push-v5 intact.
- **Authoritative modeling image** SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`; confirmed on read-only branch `exp/s-creature-vibe-modeling@48b39d8b64aa5146dc2028876b448c3e884295e6`, path `art/s-creature/references/00_s_type_modeling_image_v1.png`. The `art/s-creature/` path is *absent* from the current 2.5D child branch. Do not invent its local presence or overwrite that separate branch.
- Separate Blender R8C/R9 zero-rebuild and prior shoulder-sculpt branches exist. Do not silently substitute these modeling experiments for the rigged runtime review asset.

## User-facing goal
Make the **actual** S creature visibly sprint: coherent shoulder advance/retraction, foreleg elbow fold/swing/reach, chest load at fore-contact, hind push passing through the back, with natural whole-body compress/extend at steady .5x/1x/1.5x and acceleration. Do not chase smaller numerical epsilons or declare animation quality from tests alone.

## Execution order
1. Fetch latest remote, inspect `AGENTS.md`, `docs/2p5d/HANDOFF_STATE.json`, `src/s_contact_ik.js`, `src/s_body_coupling.js`, `src/s_run_review.js`, and four-view *actual* D3-B footage and source frames. Preserve all existing artifacts and findings.
2. **Rig feasibility gate BEFORE editing**: inspect the actual GLB `public/models/evowild-s/review/focus-contact-v3.glb` skeleton (bone names, parents, bind matrices, weights and animation tracks). Distinguish real shoulder/scapula control from `fore_L_upper` and `fore_R_upper` hip/upper pivot; identify which bones are overwritten by contact IK on every frame. Check whether true shoulder protraction and chest deformation are possible without reauthoring weights/rigger. Report a concrete chain and limiting joint before implementing.
3. **One authored-motion hypothesis**: if rig permits, create opt-in `push-v6` review candidate with physically coherent timing. Modify only the smallest necessary review-only motion and IK order. Do not mask locked-shoulder limitations by arbitrary body bob, increase of forefoot offset alone, fake stretching, joint penetration, root snaps or camera tricks. Preserve original S mesh and species identity. If rig lacks shoulder control, prepare an *explicit* separate Blender animation-authoring branch/task using the correct verified editable source and report the limit instead of fabricating a passing CSS/JS gesture.
4. Test only impacted functionality locally first. Verify exact mesh sole vertices and support anchors at contact; zero-time rate transitions, no penetration, no IK reach errors, hind recovery, D2-D corner, D3-B continuous response, build; no weakening existing thresholds. Speed .5/1/1.5 plus abrupt fore/hind and acceleration. Preserve v3/v5 frame probes exactly in a baseline comparison.
5. Capture actual same-camera, same-phase **SIDE, CHASE, LOW, REAR_3_4** before v5 versus opt-in v6 continuous full-cycle MP4; compare also source stills at hind push .20/.32 and fore support .64/.75/.90; verify PC and Pixel7 emulated layout. Show/read the real captures, not generated stand-ins. Evaluate fore reach *and shoulder/elbow shape*, torso load and recovery and overall silhouette; document negatives.
6. Save source, physical/rig diagnosis and real WebGL evidence under a new `docs/2p5d/evidence/` D3-C directory, commit and push the same Draft PR branch if review-only. If genuine new Blender animation requires independent source, isolate on new experimental branch and do not change existing 2.5D source until it is reviewed; link both lanes in handoff. Update `HANDOFF_STATE.json` and verify remote SHA. Never merge PR #132 without explicit user instruction.

## Reject criteria
- Unnatural stiffness persists even though numerical continuity passes.
- Fore reaches farther but upper arm/elbow/shoulder do not visibly coordinate.
- Any shift of planted sole >1mm, foot velocity residual >= .02m/s, 1ms-style speed pop, penetration, unsupported IK, altered S canonical silhouette, or loss of hind recovery.
- Evidence is only metrics, still renders or cosmetic images, rather than real full-cycle GLB animation.
- No source for rig authoring, unsupported GUI, or broken run environment: report true blocker and preserve/reuse results; don't claim completion.

## Final report
Exact latest branch SHA, code/rig changes, physical mechanism, focused tests (passing and failing), before/after real four-view footage links, canonical identity check and KEEP/REVISE verdict. If it still looks like independently cycling limbs under a rigid torso, say REVISE and identify the next *articulated* fix.
