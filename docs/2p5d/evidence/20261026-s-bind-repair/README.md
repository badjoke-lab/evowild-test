# S bind/skin repair v1 — isolated candidate, REVISE

The original S model was bound in the wrong coordinate frame: head/neck bones lay below the mesh body, hind-foot weights were on the upper body, and fore-foot bones had no influence. This unit corrects the skeleton frame around the existing root pivot, rebuilds inverse-bind matrices, rotates root animation tracks consistently, and reassigns weights against the corrected limb chains. **The original GLBs and production manifest remain unchanged.**

Open `/evowild-test/s-run-review.html?rig=bind-v1`. Without the query the page still loads the untouched native v5. Both use the actual `EvoWild_S_Run_V5` animation; non-root clip tracks/times are byte-identical. This is one skinned S moving in WebGL, not a raster warp, static mock, or production race integration.

## Preserved shape and provenance

- Source: `public/models/evowild-s/focus-rigged-v5.glb`, SHA-256 `e879cae6835f405f93787b96dfbcc1858ff540dadaf12988d549d56d922362a2`.
- Candidate: `public/models/evowild-s/review/focus-bind-repair-v1.glb`, SHA-256 `336161573b0ee22993b83dc1067ae2590237c023cf3c5d5e550b06c2ef0fab15`.
- All 38,813 POSITION vertices, NORMAL attributes and triangle indices are **byte-exact** copies; materials and bone hierarchy are unchanged. No mesh regeneration, sculpt, headfix, silhouette redesign, or palette substitution.
- Proper rotation (determinant +1), not a mirrored mesh. [Asset report](asset-report.json) contains geometry hashes, corrected bind positions, and weight statistics.
- Rebuild: `python3 scripts/repair_s_bind_candidate.py` (NumPy; refuses an unexpected source hash). No external API.

## Actual browser comparison

| View | Native v5 before | Bind/weight candidate after |
| --- | --- | --- |
| SIDE | [12 phases](../20261026-s-run/aligned/SIDE) | [12 phases](frames/SIDE) |
| CHASE | [12 phases](../20261026-s-run/aligned/CHASE) | [12 phases](frames/CHASE) |
| LOW | [12 phases](../20261026-s-run/aligned/LOW) | [12 phases](frames/LOW) |
| REAR 3/4 | [12 phases](../20261026-s-run/aligned/REAR_3_4) | [12 phases](frames/REAR_3_4) |

Same native phases 0..11/12, 960×640, camera positions, light, ground and diagnostic translation. [PC](desktop-rear-quarter.png) / [Pixel 7 emulation](android-rear-quarter.png) also show the candidate in the browser. Physical Android untested. [rear-quarter.mp4](rear-quarter.mp4) encodes the 12 actual after frames at 288/25fps (one native cycle); no generated/interpolated poses.

The review telemetry now updates the parent world matrix before sampling: previously the marker/JSON Z coordinate could lag one render after a phase jump. A regression checks that repeated identical phases produce identical world positions. **Old native Z telemetry must not be used for slip comparisons**; Y height observations are unaffected. This was a newly found review-tool defect, fixed here, not a race-engine change.

Reproduce after frames with server on 4173: `CHROMIUM_PATH=/usr/bin/chromium node scripts/capture_s_run_review.mjs docs/2p5d/evidence/20261026-s-bind-repair/frames '?rig=bind-v1'`.

## Motion judgment

| Stage | Observed after repair | Judgment |
| --- | --- | --- |
| Contact | Fore/hind weight groups now follow legs instead of the head. Ground penetration remains (hind group centroid reaches about -0.12m). | REVISE |
| Push | Extension appears, but contact is not planted relative to ground; diagnostic translation and stride are not matched. | REVISE |
| Recovery | Legs move through distinct poses; hind knee/hock placement and skin blending still need anatomical fitting. | REVISE |
| Flight | An airborne interval is visible, with stable torso instead of the prior chest/neck collapse. | Improvement; no approval |
| Extension | Side and rear-quarter show limb travel; gait still reads too stiff and lacks convincing propulsion. | REVISE |
| Speed | Shared native/candidate runtime scales animation and translation at 0/.5/1/1.5. This proves rate control, not planted contact over speeds. | Contact-aware stride/cadence remains pending |

Shape bytes were preserved, but inherited gray material / split crest and formal S identity still need review. Mock01's readable rear-quarter sprint is not achieved. **No KEEP, production asset replacement, 2.5D export, P/E/A work or 18-runner expansion.** Race physics, Agent, HUD, course and persistence are untouched.

## Validation and next unit

[Focused Playwright log](tests.log): **6/6 PASS** on desktop + Pixel 7 emulation (geometry/clip invariants; four functioning foot groups; rear-quarter skin movement; no stale telemetry; native runtime/views/freeze/speed scaling). [Production build](build.log): PASS, existing chunk-size warning only. Full 54-case journey/18-finisher verification was not repeated.

Prior head 9f0ba10 [Actions 40196894773](https://github.com/badjoke-lab/evowild-test/actions/runs/40196894773): 103 passed / 2 known PUSH failures / 81 skipped. First S unit e66969a [Actions 40274904424](https://github.com/badjoke-lab/evowild-test/actions/runs/40274904424): build passed; 104 passed / 3 failed / 81 skipped. Failures are the two historical PUSH comparisons and previously recorded intermittent desktop AGILITY (`motion-first.spec.js:3146`); no new S-test failure. This candidate's Actions will be recorded after push; no full-CI-green claim.

Next bounded unit: fit hind hip/knee/hock/toe bind locations to the unchanged canonical mesh; hand-check weights at joints, then add explicit sole contact targets and stride/cadence matching for stance, push, recovery, flight and extension. Reverify at .5×/1×/1.5× from all four views, with world-space sole slip/penetration evidence. Do not fix sliding by hiding feet, altering the race engine, or returning to side-sheet camera/scale adjustments.
