# D3-B recovery — completed, visual REVISE

The speed-command velocity discontinuity is repaired without removing experimental fore reach or chest response. **Limited numerical KEEP; overall S gait REVISE.** No production promotion, GLB/manifest change, main merge, or D2-D rewrite. Source commit: `6f5ac0164897a86c5639c46cbfac468bf7c4184a`. Diagnosis and numerical evidence were saved separately at `5d11ead` and `779901b`.

## Cause and correction

The original guard failure was reproduced exactly: fore_L at t=.120833333s, phase .4050609665, residual .073528995m/s. The other forefoot and continuous ramps had larger errors, up to .109690m/s. New fore reach and chest amplitudes directly followed a speed signal whose derivative changes at commands. It was a real mesh-velocity corner, not toe contact, reach clamp or sampling noise. See [diagnosis](DIAGNOSIS.md).

Only `push-v5` now carries a critically damped posture-rate state and its velocity between elapsed-time steps. Both fore reach and chest gain use it. Diagnostic seek explicitly initializes it; zero speed freezes it. C1 travel, cadence, effective speed, anchors and swing replanning are unchanged. Steady reach (fore_L 4.72/6.04/7.36cm at .5/1/1.5x) and chest response (3.57265 degrees at phase .75/1.5x) are preserved. Runtime edits are confined to `src/s_contact_ik.js` and the pose-rate argument in `src/s_run_review.js`; `src/s_body_coupling.js`, including D2-D, is byte-identical. The posture response deliberately lags during acceleration; this is animation, not a floor-force/COM simulation.

## Results

- [Numerical review](NUMERICAL_REVIEW.md): worst all-foot residual .109690 → .005987m/s; actual chest mesh .083252 → .0000643m/s in the command probe. Zero-time jump/freeze displacement 0, penetration/reach error 0, support gap .424mm, support slip .000893mm, hind recovery 47.98cm. No thresholds relaxed.
- [14 focused D3-B/D2-D tests](focused-test.log) PASS, PC and Pixel 7 emulation. [Existing contact/sole/roll regressions](contact-regressions.log): 21 PASS plus one Android load timeout; [unchanged isolated rerun](isolated-retest.log) PASS in 13.2s. **36 unique cases passed across these runs**, not a clean first run.
- [Local build](build.log) PASS; existing bundle-size warning only.
- [Source Actions 40882876409](https://github.com/badjoke-lab/evowild-test/actions/runs/40882876409): **170 passed / 3 known failed / 81 skipped**. Build/page verification PASS. Failures: race-quality PUSH comparison on both projects, and desktop Motion First AGILITY holdRemaining. No S-specific new failure. Old failed D3-B run: [40872992098](https://github.com/badjoke-lab/evowild-test/actions/runs/40872992098). See [CI record](actions-summary.json). Final evidence-only commits skip CI and do not alter the tested runtime.
- [D2-D preservation](d2d-preserved.json): .64 residual stays .002257488m/s. [Six complete baseline snapshots](baseline-probe-preservation.json) match exactly before/after the source change. [Immutable asset hashes](asset-integrity.json).

## Actual WebGL comparison

Before is preserved D2-D `?rig=contact-v3&toe=roll-v3&body=push-v3`; after is corrected `body=push-v5`. Failed v5 is recoverable at `ca1c41d`/`5d11ead`; its numerical traces are labelled `failed-*`. Videos are **v3 vs fixed v5**, not failed-v5 vs fixed-v5. Existing v4 stays selectable.

|View|Before|After|Matched frames|
|---|---|---|---|
|SIDE|[MP4](before-SIDE.mp4)|[MP4](after-SIDE.mp4)|[Before](frames/before-SIDE) / [after](frames/after-SIDE)|
|CHASE|[MP4](before-CHASE.mp4)|[MP4](after-CHASE.mp4)|[Before](frames/before-CHASE) / [after](frames/after-CHASE)|
|LOW|[MP4](before-LOW.mp4)|[MP4](after-LOW.mp4)|[Before](frames/before-LOW) / [after](frames/after-LOW)|
|REAR 3/4|[MP4](before-REAR_3_4.mp4)|[MP4](after-REAR_3_4.mp4)|[Before](frames/before-REAR_3_4) / [after](frames/after-REAR_3_4)|

[PC before](desktop-before.png) / [after](desktop-after.png); [Pixel 7 emulation before](android-before.png) / [after](android-after.png). Eight clips contain 192 consecutive real browser frames, 24 per cycle at 1x, encoded at 57.6fps to preserve simulation time (period .416667s). They are short one-cycle clips intended for looping. No raster interpolation or generated poses. Deterministic captures do not measure wall-clock browser performance or physical Android hardware.

Sixty additional actual screenshots cover SIDE and REAR 3/4 at .5/1/1.5x and phases .20/.32/.64/.75/.90; filenames include rate and phase, e.g. [SIDE before](before-SIDE-1p5x-p75.png) / [after](after-SIDE-1p5x-p75.png), [rear before](before-REAR_3_4-1x-p20.png) / [after](after-REAR_3_4-1x-p20.png). These use explicit diagnostic seeks, unlike the integrated full-cycle sequences. [Cycle observations](visual-observations.json) and [phase observations](fore-reach-visual-probes.json) report no captured page errors. The existing generic on-screen “native body” label is unchanged; variant identity comes from capture URLs and observation metadata.

## Judgment and restart point

[Visual review](VISUAL_REVIEW.md) records actual frame comparisons. Fore reach and chest posture differ, but shoulder articulation, torso compression and a convincing forward-driving silhouette remain insufficient. Numeric continuity is fixed; visually this remains **REVISE**, with no user-approval claim.

Next useful unit: authored shoulder protraction/retraction and elbow recovery synchronized with chest support, in the separate animation-authoring lane. Preserve canonical shape and contact constraints; establish readable compression/extension before further amplitude tweaks. Do not repeat D2-D or this completed repair, and do not begin P/E/A or 18-creature integration. Start with this review and saved native clips, then scope that separate animation unit. No Blender/sculpt work was performed here.
