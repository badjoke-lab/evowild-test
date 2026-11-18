# D2-C2 — deterministic native pose and matched return

**Implementation, targeted regression and actual browser comparison complete. D2-C numerical gates PASS; visual quality and S adoption remain REVISE.** C1 diagnosis was separately pushed at `4013beb7369af12122c001cd3e794ec8705c1ef2`. Final runtime is source checkpoint `e207f8188260cfeac755ea9e8366b6b9739b88c8`; later commits publish measurement/evidence/handoff only.

Review candidate: `s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v2`.

Comparison: D2-A `toe=roll-v2`; D2-B `toe=roll-v2&body=push-v1`. All remain selectable. `body=push-v2&toe=roll-v2` isolates the body change from clearance. No GLB, mesh/rest shape, production manifest, ground, camera, race/Agent/HUD changes. [All immutable asset hashes](asset-integrity.json) match the starting SHA.

## What C1 found, and what changed

[C1](../20261028-s-return-d2c1/README.md) found that D2-B's same-time evaluation could reapply its partial blend to already modified bones: protected body vertices jumped27.4655mm at phase.53 although the solved soles did not jump. It also isolated Float32 interpolant rounding: the previous .019398m/s sole maximum occurred at phase.394069, BEFORE the return window. Finally, the old exit crossfade traversed shifted/native linear key corners inside .44–.62.

`push-v2` explicitly evaluates native base and advanced channels into Float64 buffers; it does not rely on AnimationMixer restoring a property when time has not changed. All22 native channels (seven bones plus animated armature parent translation) stay coherent. Same-time re-evaluation is now idempotent, including protected actual body vertices.

Return occupies the **same .44–.62 interval**, preserving phaseLead.25 and full push before.44. A quintic Hermite connection matches the existing start/end poses and their first/second derivatives. Quaternion components share the same hemisphere and are normalized after evaluation. This removes interior crossfade/key corners without extending the window, attenuating amplitude, or adding a bob. IK still runs afterward using the existing C1/C2 integrated locomotion, stance anchors and swing trajectories. This is animation timing, not simulated force, momentum or COM dynamics.

`roll-v3` retains the actual support vertices, horizontal rolling path and pitch curve. It reduces the compact vertical rounding width from3 to1.5mm. The resulting positive clearance is measured, not hidden by ground/root translation or mesh penetration. Old v2 defaults remain unchanged. [All-rate boundary probe](clearance-probe.json).

## Quantitative results

[Seven final after traces and before/after summary](summary.json) cover .5/1/1.5 steady, continuous acceleration/deceleration, abrupt hind/fore cases at240Hz. Before numbers reuse the completed [D2-B traces](../20261028-s-body-d2b/summary.json); the new regression suite exports full after traces directly, avoiding a second independent final-profile run. Actual sole/guard vertices, body positions/quaternions, support IDs, travel/phase, joint lengths/angles and reach are recorded. Old whole-patch displacement remains distinct from active-support slip.

|Worst across seven profiles|D2-B|D2-C2|
|---|---:|---:|
|Sole velocity residual (10us probes), m/s|.019398|**.005987**|
|Zero-time actual sole jump, m|1.05e-8|0|
|Accumulated active-support horizontal slip, mm|.001062|.000893|
|Active-support gap, mm|.923424|**.423754**|
|Guard penetration / IK reach error, m|0 /0|0 /0|
|Minimum hind recovery peak, cm|47.980|47.980|
|Joint angle range, degrees|48.67–161.22|48.67–161.22|
|Maximum segment-length drift, m|8.35e-8|5.78e-8|

New all-body+sole zero-time/freeze tests at13 phases and4 rate commands show0 displacement. [Return-boundary actual mesh probes](mesh-boundaries.json) at all three rates across.44–.62 have worst residual.002788m/s, below both the unchanged.02 gate and additional.01 target. Existing tests/thresholds/timeouts were not weakened. Finite-difference residuals depend on the10us observation interval; they are not an assertion of zero acceleration.

[Dense return comparison](return-comparison.json), [raw after trace](after-return-trace.json.gz), [summary code](../../../../scripts/summarize_s_body_return.mjs): .0005-cycle samples (4800Hz at1x), actual body vertices and six anatomical parts plus root. World positions/rotations, linear/angular derivatives, planted-foot-relative pelvis positions and speed-command probes are retained. Over.44–.62:

|Measure|D2-B|D2-C2|
|---|---:|---:|
|Protected mesh peak relative speed, m/s|2.248|1.815|
|Protected mesh sampled acceleration peak, m/s²|2066.1|125.6|
|Pelvis sampled acceleration peak, m/s²|895.7|24.5|
|Spine sampled angular acceleration peak, rad/s²|1478.1|88.2|

The large old sampled spikes are native piecewise-key/blend effects, **not forces or physical acceleration**. Endpoint actual-body mesh differences are .000131mm at.44 and ~0 at.62 ([endpoint comparison](endpoint-preservation.json)). Original corresponding full/zero-blend poses remain protected: max vertex difference1.71e-8m ([native comparison](protected-shape.json)).

[Body summary](body-summary.json): at1x the pelvis still travels forward during complete hind support: L+2.10cm, R+2.75cm; knee extension+9.67°/+11.30°. D2-B was+2.49/+2.77cm and+9.84/+11.35°. The small L decrease includes removal of accumulated partial-blend error during entry; propulsion direction/extension are retained, not inverted or disabled. Pelvis vertical span1.549→1.544cm, chest11.46→11.21cm, no added vertical oscillation. No amplitude multiplier was introduced.

**Remaining continuity limit:** outside the repaired interval, the original animation still has piecewise key velocity corners. For example, phase.64 yields an actual body velocity residual~.240m/s at10us (native baseline and candidate). This is separately exposed in dense diagnostic boundary records, not hidden by the successful sole/profile gates. Thus the repaired return and requested speed-change gates pass, while **whole-cycle body continuity remains REVISE**. A future bounded D2 review should examine that native-key join into fore support, not restart B/C/D1 or begin a new whole-flight performance.

## Real WebGL comparison and judgment

High-density .40–.66 comparison:53 consecutive rendered frames/view, .005-cycle spacing. Videos explicitly play16× slower (480Hz simulation,30fps playback); no interpolated/raster-deformed creature frames.

|View|Before|After|
|---|---|---|
|SIDE|[D2-B slow](../20261028-s-return-d2c1/before-SIDE-return-slow16x.mp4)|[new slow](after-SIDE-return-slow16x.mp4)|
|LOW|[D2-B slow](../20261028-s-return-d2c1/before-LOW-return-slow16x.mp4)|[new slow](after-LOW-return-slow16x.mp4)|
|CHASE|[D2-B slow](../20261028-s-return-d2c1/before-CHASE-return-slow16x.mp4)|[new slow](after-CHASE-return-slow16x.mp4)|
|REAR3/4|[D2-B slow](../20261028-s-return-d2c1/before-REAR_3_4-return-slow16x.mp4)|[new slow](after-REAR_3_4-return-slow16x.mp4)|

[Before212 frames](../20261028-s-return-d2c1/frames/) / [after212 frames](frames/). Same cameras, lighting, ground, scale and phases. Captures retain the real old repeated-evaluation behavior for before, rather than silently fixing it while recording.

Normal simulation-time full-cycle clips (57.6fps,24 real frames/cycle, phase.64 start) use identical conditions to completed D2-B:

|View|Before|After|
|---|---|---|
|SIDE|[D2-B](../20261028-s-body-d2b/after-SIDE.mp4)|[new](full-cycle/after-SIDE.mp4)|
|LOW|[D2-B](../20261028-s-body-d2b/after-LOW.mp4)|[new](full-cycle/after-LOW.mp4)|
|CHASE|[D2-B](../20261028-s-body-d2b/after-CHASE.mp4)|[new](full-cycle/after-CHASE.mp4)|
|REAR3/4|[D2-B](../20261028-s-body-d2b/after-REAR_3_4.mp4)|[new](full-cycle/after-REAR_3_4.mp4)|

[Full-cycle96 frames](full-cycle/frames/). Speed-change [before](before-speed-changes.mp4) / [after](after-speed-changes.mp4) cover steady holds, ramps and abrupt reversals;194 real observations are in [speed capture](speed-video-observations.json). These are deterministic WebGL simulation-time captures, not a realtime performance claim.

Phase.53 PC [before](../20261028-s-return-d2c1/desktop-before.png)/[after](desktop-after.png); Pixel7 emulation [before](../20261028-s-return-d2c1/android-before.png)/[after](android-after.png). No physical Android device was tested. Page errors0 in completed captures.

SIDE/LOW show the return spreading continuously between the preserved endpoint postures, without the old repeated-evaluation snap or a new obvious foot/joint inversion. The change is restrained; REAR3/4 still reads as a relatively rigid body with individually articulated legs, and the original key joins/fast toe roll do not yet convey convincing sustained sprint propulsion. Pixel7 preserves visibility but makes the subtle body improvement harder to judge.

- **Return-window/speed-command numerical continuity: PASS (bounded KEEP for this correction only).** Native whole-cycle key continuity remains REVISE as noted above.
- **Visual quality: REVISE. S-wide adoption: pending/REVISE.** No production promotion, no claim that numerical success proves natural running.

## Tests, CI and restart

- 30 distinct requested PC/Pixel7 cases pass: [main run](targeted-tests.log)29pass+one old D2-A Android page-load30s timeout; [isolated retest](isolated-retest.log) passes that case in15.7s under unchanged30s limit. Tests cover existing C1/C2/D1/D2-A/D2-B and10 new D2-C cases. The timeout happened during concurrent capture; no assertions or timeouts changed. The same full S set passes in CI.
- [Build PASS](build.log), preexisting chunk-size warning only.
- Source [Actions40615717824](https://github.com/badjoke-lab/evowild-test/actions/runs/40615717824): **152passed /3knownfailed /81skipped**, buildPASS. [Log](actions-40615717824.log). Known failures: PUSH desktop/Android and desktop AGILITY. No new S failures; historical Android pressure recurrence absent in this run.
- Newly diagnosed preexisting D2-B issues (repeated body blend and Float32 microstep noise) are fixed in the opt-in v2 candidate. Old v1 is deliberately preserved for comparison. Remaining native key corner at.64 is explicitly measured, not a new defect introduced by this return correction.

Reproduce with dev server4173: `CHROMIUM_PATH=/usr/bin/chromium S_RETURN_OUT=docs/2p5d/evidence/20261028-s-return-d2c2 S_RETURN_QUERY='&toe=roll-v3&body=push-v2' node scripts/measure_s_body_return.mjs`; `node scripts/summarize_s_body_return.mjs`. Final profile traces are exported by `tests/s-body-return.spec.js` when `S_BODY_EVIDENCE` is set. See capture scripts for the matching query/output environment variables; no new art generation is used.

Next bounded unit: inspect the preserved native body key join near.64 into fore support, with the same body+sole microstep diagnostics and four-view comparison. Preserve push-v2's.44–.62 endpoint connection, all anchors/recovery/contact gates and canonical identity. Do not restart completed stages, expand to P/E/A/18 runners, alter flight/extension globally or merge main.
