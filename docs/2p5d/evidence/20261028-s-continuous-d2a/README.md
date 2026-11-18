# D2-A — continuous S support roll (2026-10-28 JST)

Baseline: `fbfdd57`, D1 `?rig=contact-v3&toe=roll-v1`. New isolated candidate: `?rig=contact-v3&toe=roll-v2`. The v1 path, C1/C2 state/anchors/recovery, GLBs, manifest, camera, ground and race systems are preserved. No D2-B body modification in this unit.

## Cause and bounded correction

D1 reaches zero angular velocity/acceleration at every mesh support vertex change: two intermediate stops on left fore, four on right fore and one on each hind foot. Actual skinned foot pitch tests confirm near-zero speed at those boundaries. D2 uses one quintic roll over the same stance time and unchanged22°/28° range. Pitch continues through the boundaries (measured79–996°/s at1x); it still eases into/out of roll and the unchanged recovery return.

A rigid polygonal sole cannot switch planted vertices at nonzero rotation speed while maintaining both exact zero gap and continuous vertical velocity. The candidate retains the exact horizontal rolling path, but uses a compact quartic upper envelope for vertical IK translation. This is a **bounded sub-mm clearance tradeoff**, not a force/contact-pressure simulation or exact all-time Y=0 claim. Real terminal/guard mesh vertices are still measured; targets never substitute for observations. Initial/final stance orientation, peak pitch and original leg lengths are retained. Only the terminal endpoint receives the local correction; the ground/camera/model root is not moved to hide a defect.

The first attempt tapered the final height correction across an early vertex transition and left a0.237m/s velocity discontinuity. The fix grows the smoothing width *before* the first real transition; boundary residual is now≤0.002285m/s against the unchanged0.02m/s gate. Initial failure retained below. No threshold changes.

## Numerical comparison

[Fourteen before/after profiles](summary.json) and compressed traces:0.5/1/1.5 steady, continuous acceleration/deceleration, abrupt fore/hind cases,240Hz. All feet: zero-time speed-switch jump0, guard penetration0, IK reach error0. Same-material support horizontal slip stays below0.001mm; the prior whole-patch metric is retained separately. Maximum observed support gap rises from D1~0.00076mm to D2~0.92343mm, within the existing1mm criterion but explicitly worse than D1. The maximum command velocity residual falls from0.00752 to0.00599m/s. Hind recovery remains47.98–48cm.

|Foot|Support slip mm|Maximum support gap mm|Penetration m|Minimum recovery peak cm|Command velocity residual m/s|
|---|---:|---:|---:|---:|---:|
|fore_L|0.000317|0.5595|0|33.99|0.006262|
|fore_R|0.000288|0.9234|0|33.99|0.006359|
|hind_L|0.000812|0.5192|0|47.98|0.005987|
|hind_R|0.000695|0.5438|0|47.98|0.003500|

## Actual browser comparison / decision

The D1 after movies are the unchanged before baseline, using identical four cameras,1x,phase0.64 start and24 sequential frames per cycle:

|View|D1 before|D2 after|
|---|---|---|
|SIDE|[video](../20261027-s-toe-roll-d1b/after-SIDE.mp4)|[video](after-SIDE.mp4)|
|LOW|[video](../20261027-s-toe-roll-d1b/after-LOW.mp4)|[video](after-LOW.mp4)|
|CHASE|[video](../20261027-s-toe-roll-d1b/after-CHASE.mp4)|[video](after-CHASE.mp4)|
|REAR3/4|[video](../20261027-s-toe-roll-d1b/after-REAR_3_4.mp4)|[video](after-REAR_3_4.mp4)|

[After frames](frames/) / [before frames](../20261027-s-toe-roll-d1b/frames/). PC [before](../20261027-s-toe-roll-d1b/desktop-after.png)/[after](desktop-after.png); Pixel7 emulation [before](../20261027-s-toe-roll-d1b/android-after.png)/[after](android-after.png). [Per-frame state](visual-observations.json). These are deterministic real WebGL steps encoded at57.6fps, not a realtime GPU/physical Android performance claim. Existing D1 recordings are reused as comparison, not remade.

SIDE/LOW sequence inspection shows a less interrupted foot pitch with no obvious new fold or bounce. The difference is modest at the fixed scale. REAR3/4 still lacks strong whole-body propulsion; the body is intentionally unchanged here. **D2-A visual decision: REVISE**, despite solving the internal stops. The small transition clearance and fast short-stance roll remain review limitations. S overall adoption stays pending. D2-B must be independently measured and saved after this unit is remote.

## Validation status

**All10 distinct target cases PASS across final/retest runs:** initial full run7PASS plus2Android trace-output ENOENT failures and1desktop30s timeout under overlapping browser load. Separate-output Android rerun2/2PASS; isolated desktop comparison1/1PASS in14.4s, unchanged30s timeout. All numeric assertions and sample counts remain unchanged. [Full run](d2a-final-tests.log), [Android retest](d2a-android-retest.log), [desktop retest](d2a-desktop-boundary-retest.log). [Measured boundary pitch speeds](rotation-boundaries.json). [BuildPASS](build.log), [immutable asset check](asset-integrity.json). Final96 frames/four videos/PC+Pixel7 captures completed with zero page errors. D2-A implementation/evidence pushed at `ee86eb000580a27d4abf2798c3f2600d11d8f80c`; Actions[40532716694](https://github.com/badjoke-lab/evowild-test/actions/runs/40532716694) completed:136passed/3knownfailed/81skipped, buildPASS; [excerpt](actions-40532716694.log). D2-B was started only after this completion checkpoint was pushed.

Reproduce: `CHROMIUM_PATH=/usr/bin/chromium node scripts/measure_s_continuous_roll.mjs`; `CHROMIUM_PATH=/usr/bin/chromium node scripts/capture_s_motion_compare.mjs`; `npx playwright test tests/s-toe-continuous.spec.js tests/s-contact-transitions.spec.js tests/s-contact-acceleration.spec.js`. Baseline CI40435078297:130passed/3knownfailed/81skipped; buildPASS. No baseline game tests are changed.
