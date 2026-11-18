# D2-B — hind support and native body coupling (2026-10-28 JST)

**Implementation and bounded validation complete; visual REVISE. No S production adoption.** D2-A was completed/pushed at `0d611d7c4f9caca9967c14207667c6181bd41380` before D2-B began. D2-B source checkpoint `b27ba9e2a933b4468b85e5181641a0ccb335adab` includes the final tested runtime; this final publication adds evidence and helpers.

Compare `s-run-review.html?rig=contact-v3&toe=roll-v2` with `s-run-review.html?rig=contact-v3&toe=roll-v2&body=push-v1`. D1 `toe=roll-v1` remains available. No GLB, mesh/rest shape, production manifest, camera/ground, race physics, Agent or HUD edits. The diagnostic API gains optional draw=false for repeated mesh assertions; ordinary rendering remains the default.

## Measurement-led implementation

[Native241-frame body trace](native-body.json) shows pelvis relative fore-aft position reaching its rearmost point at phase.4375, late in combined hind support (.15–.47). Native pelvis vertical trough is.3625. Its original motion has1.55cm vertical and5.27cm fore-aft span; the chest has12.89cm vertical span. Root travel is subtracted when reporting these local locomotion offsets.

`src/s_body_coupling.js` samples the **existing** pelvis/spine/chest/neck/head/tail/root tracks and their animated armature parent translation at a.25-cycle earlier pose. It blends with native time using a shared quintic support envelope: entry.06–.18, full.18–.44, exit.44–.62. Thus hind acceptance leads into forward pelvis travel, knee extension and toe roll, and the original fore-support/recovery pose is restored before fore contact. All channels use the same blend; no new sinusoidal bob, amplitude multiplier or independent head/neck/tail motion was invented. C1/C2 integrated phase, travel, stance anchors and swing target trajectories remain unchanged. IK is evaluated after the body pose so actual feet retain their support targets.

This is animation timing, **not simulated ground reaction force, momentum or COM dynamics**. Native armature displacement is retimed within the support window, not used as an arbitrary offset to hide penetration. Every actual foot surface and guard region is still tested against fixed worldY=0.

Two failed intermediate approaches are retained: unrestricted all-cycle body retiming overextended fore recovery (~4cm reach error), so it was rejected; the first limited-support trial omitted animated armature translation and failed protected-body shape comparison by2.86cm. Including that existing parent channel consistently fixes it. [Rejected test](rejected-unrestricted-test.log), [intermediate test](intermediate-supported-test.log). No test tolerances were relaxed.

## Before/after body and foot results

[Body summary](body-summary.json) and fourteen compressed traces record actual body world positions/quaternions, true sole/guard vertices, active support IDs, joint angles, reach, phase and travel at240Hz for0.5/1/1.5 steady speed and all four C2 continuous/abrupt profiles. [Foot summary](summary.json). [Summary code](../../../../scripts/summarize_s_body_coupling.py).

At1x, over complete hind-support intervals (relative to integrated forward travel):

|Measure|D2-A before|D2-B after|
|---|---:|---:|
|Left support: pelvis forward change|−4.13cm|+2.49cm|
|Left support: pelvis vertical change|−0.79cm|+0.69cm|
|Left support: knee extension|+3.92°|+9.84°|
|Right support: pelvis forward change|−1.80cm|+2.77cm|
|Right support: pelvis vertical change|−0.31cm|+1.03cm|
|Right support: knee extension|+5.84°|+11.35°|
|Left support: trunk pitch start→end|10.95→12.00°|11.63→6.75°|
|Right support: trunk pitch start→end|12.22→10.45°|9.78→5.32°|

The candidate now brings the pelvis forward/up while the hind chain extends and the tip rolls, rather than having pelvis travel oppose the push. These are measured pose correlations, not a propulsion-force claim.

Worst values across seven after profiles:

|Foot|Accumulated support slip mm|Maximum support gap mm|Minimum recovery peak cm|Command velocity residual m/s|Joint angles °|
|---|---:|---:|---:|---:|---:|
|fore_L|0.000317|0.5595|33.99|0.013031|95.41–152.86|
|fore_R|0.000288|0.9234|33.99|0.012445|90.77–146.23|
|hind_L|0.001062|0.5192|47.98|0.019398|48.67–159.50|
|hind_R|0.000863|0.5438|47.98|0.018627|48.87–161.22|

Guard penetration and IK reach error0 on all four feet. Maximum zero-time actual vertex jump1.05e−8m, well under the unchanged1mm gate. Support slip<0.002mm; hind recovery47.98–48cm. D2-A's bounded clearance is retained (worst0.92343mm), not misreported as exact continuous zero-gap contact. Original whole-sole movement and active-support movement remain separately recorded.

**Worse than baseline:** maximum speed-command finite-difference mesh velocity residual increases from~0.00636 to~0.01940m/s. It passes the unchanged0.02 gate but has little margin; this remains a D2 review concern. Body blending near exit.44–.62 should be inspected before any further flight/extension work. No tests were weakened to absorb this change.

## Actual WebGL comparison

All four cameras/ground/scale remain identical. D2-A after movies are the D2-B before comparison, phase.64 start,24 consecutive frames over one native cycle:

|View|Before|After|
|---|---|---|
|SIDE|[D2-A](../20261028-s-continuous-d2a/after-SIDE.mp4)|[D2-B](after-SIDE.mp4)|
|LOW|[D2-A](../20261028-s-continuous-d2a/after-LOW.mp4)|[D2-B](after-LOW.mp4)|
|CHASE|[D2-A](../20261028-s-continuous-d2a/after-CHASE.mp4)|[D2-B](after-CHASE.mp4)|
|REAR3/4|[D2-A](../20261028-s-continuous-d2a/after-REAR_3_4.mp4)|[D2-B](after-REAR_3_4.mp4)|

[96 after frames](frames/) and [before frames](../20261028-s-continuous-d2a/frames/), [per-frame observations](visual-observations.json).

Active push at phase.35: PC [before](desktop-push-before.png)/[after](desktop-push-after.png); Pixel7 emulation [before](android-push-before.png)/[after](android-push-after.png). The retained phase.80 PC/Pixel7 screenshots document the return to the unchanged fore-support portion.

[Speed-change before video](before-speed-changes.mp4) / [after video](after-speed-changes.mp4) cover0.5/1/1.5 holds, continuous acceleration/deceleration, and abrupt changes. [194 per-frame observations](speed-video-observations.json) store real mesh and body state. Main comparison videos are simulation-time57.6fps, speed clips30fps, no interpolation. Idle draw callbacks are disabled only in capture pages; explicit simulation and rendering still occur. These are genuine WebGL captures, not artwork, and not a realtime performance/physical Android claim. Page errors0.

SIDE/LOW late support frames17–20 show the torso lower/forward relative to the rising pelvis with more knee extension; REAR3/4 shows a modest forward push posture. No obvious new joint flip or broken foot fold was found in these sampled views. The change is restrained, but the exit back to native posture can still read as a posed transition and does not yet convey convincing sustained forceful running. Pixel7 preserves operation and foot visibility; its smaller scale makes the improvement less clear.

**D2-B: REVISE.** Numerical coupling improves and original protected body geometry/rotations are preserved at full/zero blend (max skinned-vertex difference1.70e−7m against the corresponding native poses), but natural propulsion is not approved. **D2-A separately remains REVISE** for short/fast roll and small clearance tradeoff. S overall adoption stays pending. No P/E/A or18-runner expansion, no separate whole-flight/extension adjustment.

## Tests, CI and restart

- Six distinct D2-B PC/Pixel7 cases PASS: five in [full run](targeted-tests.log), one desktop page-load30s timeout passed [isolated retest](shape-retest.log) in9.6s, unchanged timeout and assertions. Includes all seven speed profiles per device, support/lift/landing/freeze boundaries, protected body shape. [Protected native comparison](protected-shape.json).
- [BuildPASS](build.log), existing bundle-size warning only. [Immutable asset hashes](asset-integrity.json).
- D2-A Actions[40532716694](https://github.com/badjoke-lab/evowild-test/actions/runs/40532716694):136passed /3knownfailed /81skipped.
- D2-B source Actions[40535583834](https://github.com/badjoke-lab/evowild-test/actions/runs/40535583834):**141passed /4failed /81skipped**, buildPASS, no new S failure. [CI excerpt](actions-40535583834.log). Three failures are the known PUSH desktop/Android and desktop AGILITY assertions. The additional Android pressure:125 failure (pressure0 vs>0.08) is a recurrence documented before these changes in [parent baseline evidence](../20261025-flow/README.md), runs40152147602/40153348139. Do not call the full CI green or hide the extra recurrence.

Reproduce `CHROMIUM_PATH=/usr/bin/chromium node scripts/measure_s_body_coupling.mjs`, `python3 scripts/summarize_s_body_coupling.py`, `npx playwright test tests/s-body-coupling.spec.js`; capture via `capture_s_motion_compare.mjs` with `S_COMPARE_OUT=docs/2p5d/evidence/20261028-s-body-d2b` and `S_COMPARE_AFTER='&toe=roll-v2&body=push-v1'`, then `capture_s_body_speed_changes.mjs` and `capture_s_body_push.mjs`.

Next bounded unit: review/smooth the D2-B blend exit (.44–.62) and increase actual mesh velocity-continuity margin without degrading support, recovery or native head/neck/tail motion. Keep all earlier candidates and thresholds. D1/B/C work is complete and must not be repeated; full-flight/extension work remains deferred until D2 quality is reviewed.
