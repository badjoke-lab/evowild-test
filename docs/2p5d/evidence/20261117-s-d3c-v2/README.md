# D3-C v2 recovery and completion — review only

The prior environment was replaced before its local-only v2 work could be published (GitHub git/API returned account-suspended HTTP403 then). This session fetched the actual remote v1 head `aaebb78` and restored the documented final authoring, without regenerating v1. The restored independent GLB SHA256 is **6edb45e7aeb3179104d5b406d09eaa1f34da6baf09ddc9a6a0535d7e96f3f1c0**, exactly matching the previous session's final asset. Lost logs and captures are not represented as present; fresh tests and actual five-view evidence follow this checkpoint.

v2 retains all 23 joints, mesh bytes, weights, bind matrices, materials and v1 native clip. It adds a full authored pose clip and cubic review tracks for scapular glide/rotation, humerus advance, elbow recovery, chest loading, pelvis push and head/neck/tail follow-through. `src/s_authored_drive.js` applies GLB poses; existing IK anchors govern stance, and forward kinematics of the authored arm/elbow guides swing. Full standalone pose animation still needs the runtime IK adapter for the measured contact behavior; it is not an offline IK-baked export.

Two previously diagnosed fixes are included: restore scapular rest translation each evaluation (no accumulated glide); author analytic scapular tangents (the v1 LINEAR shoulder key at .75 had a velocity corner). Fore humerus/elbow amplitudes retain the last visually refined 18/-34 degrees, not the earlier cramped 26/-42 trial. v1 and original GLBs remain intact; no source image, production manifest, race logic, other species or main changes.

Fresh verification is now complete: asset integrity and production build PASS; **16/16 targeted tests PASS** on desktop Chromium and Pixel 7 emulation. Existing v1 rig and D2-D checks are included, without lowering thresholds. Seven speed profiles show zero penetration/reach error/zero-time jumps, maximum support gap .423742mm, slip .000870mm and hind recovery >=47.98cm. Actual sampled body/limb velocity residual is .003592m/s; sole residual .005987m/s.

**Full S visual verdict remains REVISE.** Shoulder travel and elbow recovery are visibly stronger, but fore feet crowd beneath the chest during recovery and the rear-quarter view still lacks convincing whole-body propulsion. See [the five-view review](VISUAL_REVIEW.md) for improvements and deficiencies, not just numerical results.

The fresh artifacts are [paired video viewer](compare.html), ten `before/after-{SIDE,FRONT,CHASE,LOW,REAR_3_4}.mp4` files, 240 full original PNGs in `frames/`, five cropped inspection sheets in `previews/`, and desktop/Pixel 7 before/after screenshots. [Capture validation](capture-validation.json) records 24 real WebGL frames per clip, 57.6fps/.416667sec one-cycle loops, zero capture page errors. These are simulation-time captures, not physical-device frame-rate measurements.

[Test log](targeted-tests.log), [build log](build.log), [asset integrity](asset-integrity.json), [contact summary](contact-summary.json) and [articulation comparison](articulation-summary.json) are saved. The `.json.gz` files contain integrated actual-vertex traces. Phase-seek `articulation-samples.json` is separate and does not claim elapsed-time continuity.

Source/model recovery was pushed as `ef2cc60`; tests, raw contact traces and a focused CI workflow as `995f9ea`; both remote SHAs were verified. The new push workflow is `.github/workflows/s-d3c-v2.yml`. **Its GitHub Actions result is not verified**: `gh run list` and direct API access hit the environment's HTTP403 tunnel restriction. Git pushes and the connected GitHub file reader work. Do not confuse this with a failing test or the earlier account suspension. Historical main-lane CI failures (PUSH comparison on both projects, desktop AGILITY) were not rerun; no new local S test failed. See [Actions access record](actions-status.json).

Reproduce from the repository root with the development server on port4173:

```sh
python3 scripts/verify_s_d3c_v2.py
npm run build
npx playwright test tests/s-d3c-v2.spec.js tests/s-d3c-scapula.spec.js tests/s-native-join.spec.js --workers=1
CHROMIUM_PATH=/usr/bin/chromium node scripts/measure_s_d3c_articulation.mjs
CHROMIUM_PATH=/usr/bin/chromium \
  S_COMPARE_OUT=docs/2p5d/evidence/20261117-s-d3c-v2 \
  S_COMPARE_BEFORE='&toe=roll-v3&body=push-v5&shoulder=authored-v1' \
  S_COMPARE_AFTER='&toe=roll-v3&body=push-v5&shoulder=authored-v2' \
  node scripts/capture_s_motion_compare.mjs
```

This environment's local Playwright run used installed `/usr/bin/chromium` via an untracked config importing the normal config with only executable path, testDir and existing-server reuse adjusted. The Actions workflow uses Playwright's installed Chromium. No test thresholds were overridden.

The active experimental branch is `exp/d3c-scapula-authoring`, based on the prior PR132 lane. PR132's head has not been changed or merged; these experimental commits are not represented as part of that PR.

Review URLs: v1 `?rig=contact-v3&toe=roll-v3&body=push-v5&shoulder=authored-v1`, v2 same with `shoulder=authored-v2`.
