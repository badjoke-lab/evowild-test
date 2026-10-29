# EvoWild Run S — Codex D3-B recovery task (2026-10-29)

## Actual objective
Do not just rerun Actions or propose a plan. Diagnose and correct the D3-B experimental forelimb/chest movement so that actual skinned S looks like a quadruped driving forward, without breaking sole contact. Preserve all completed D2-D work and existing S canonical identity. Actual video evidence is a required result, not a numerical PASS substitute.

## Repository / branch
- Repository: `badjoke-lab/evowild-test`
- ONLY branch: `feat/2p5d-flow-persistence-20261025`; Draft PR #132; do not modify main.
- Before touching files, fetch latest origin, compare local HEAD to origin, inspect clean/dirty worktree and read `AGENTS.md`, `docs/2p5d/HANDOFF_STATE.json`, `docs/2p5d/CODEX_QUOTA_RECOVERY_PROTOCOL.md`, `docs/2p5d/evidence/20261029-s-d3-flex-trial/D3_VISUAL_REVIEW.md`.
- Canonical S identity: `art/s-creature/references/00_s_type_modeling_image_v1.png` (SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`).
- Preserve original `focus-contact-v3.glb`, native rest geometry, manifest, HUD, camera, Agent, P/E/A creatures, other Blender R9 sculpt lane, race production and 18-creature rollout.

## Current experiment
- Baseline `s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v3`: D2-D numerically scoped KEEP, visually REVISE.
- D3-A `body=push-v4`: speed-responsive pelvis/spine bend, targeted tests 8 passed, full S visuals still REVISE.
- D3-B `body=push-v5`: optional `foreReach` in `src/s_contact_ik.js` (for swing only) and `foreLoad` in `src/s_body_coupling.js` (chest fore-support). Selection is in `src/s_run_review.js`.
- D3-B current implementation is on branch but **FAILED** guard test. Actions run `40872992098` completed failure on 2026-10-29. No D3-B four-view videos were saved by that run.
- `tests/s-d3-fore-reach.spec.js` in both desktop and android-chromium failed `maxMeshVelocityResidual < .02m/s`: observed **.07352899508547898m/s**. Don't loosen threshold, mark PASS without correction or hide test failures.
- The other eight tests passed. At phase .20 fore visual reach was ~0.04716m at 0.5x, ~0.06037m at 1x and ~0.07358m at 1.5x for fore_L; chest quaternion difference ~3.57265° at phase .75 (1.5x). No verified visual improvement is implied by these numbers.
- Previous D2-D near phase .64 body velocity corner improved .240761→.00225749m/s; preserve this.
- See failing run: https://github.com/badjoke-lab/evowild-test/actions/runs/40872992098

## Required execution (not planning only)
1. Reproduce the failing D3-B 0.07353m/s velocity residual using local Playwright. Identify which **forelimb and exact time/phase**, whether it is swing->contact continuity, toe roll, IK reach/skin, body load timing, or finite-difference sampling. Log before push-v3 vs push-v5 across 0.5x,1x,1.5x, abrupt rate changes; include actual foot mesh samples and native body tracks. Root-cause first.
2. Make the smallest isolated D3-B change that fixes the discontinuity **without reducing the measured forward reach to zero** or injecting global bob. Do not merely change test thresholds. Keep supporting soles world anchored, all existing D2-D/fore/hind phase work and zero-time speed-change invariance.
3. Run build, `tests/s-d3-fore-reach.spec.js`, `tests/s-native-join.spec.js`, and relevant contact/sole/roll/continuous tests on desktop-chromium and Pixel7 emulation. Ensure baseline `push-v3` remains unchanged. Report failures even if unrelated.
4. Produce actual before `push-v3` and after `push-v5` **full-cycle SIDE / CHASE / LOW / REAR_3_4 videos** plus matching rendered frames, using the existing GLB and same lighting/camera/phase. Use `scripts/capture_s_motion_compare.mjs` or equivalent; also fixed phase .20, .32, .64, .75, .90 and speeds 0.5x/1x/1.5x from `scripts/capture_s_d3b_fore_reach.mjs`. No generated creature or proxy images.
5. Judge actual gait quality: foreleg forward reach, shoulder/chest loading, hind push, weight transfer, full body stretch/compression, rear three-quarter silhouette and native S reference. If still visibly bad, declare **REVISE**, isolate the major remaining defect, and do not promote to production.
6. Commit source and diagnostics to same child branch in small coherent units and push; preserve a safe rollback candidate. Save actual evidence under `docs/2p5d/evidence/20261029-s-d3b-fore-reach/`; update `docs/2p5d/HANDOFF_STATE.json`. Verify remote SHA and Draft PR #132; no merge. Work continuously through the bounded task, not repeated "waiting for validation" reports.

## Guardrails
- No change to original S GLB, canonical PNG, rest/topology, manifests, `main`, unrelated species, or race gameplay.
- No paid external generation or AI image stand-ins.
- Numerical tests are necessary but not sufficient. Overall S quality remains REVISE until evidence-based visual review.
- Do not run all GitHub Actions on every tiny commit if a local targeted test suffices. Avoid queuing redundant workflows.
- If the native animation cannot physically achieve a strong forelimb action through safe contact IK, report that failure with actual frames and route animation-authoring to the separate Blender lane; do not cover it with cosmetic oscillation.

## Final required report
- latest remote confirmed SHA / PR #132 Draft state
- root cause and changed files
- exact results / failed tests
- four-view original WebGL evidence paths / video links
- KEEP (limited) or REVISE (visual) with reasons
- next physically important change, not another tiny epsilon chase
