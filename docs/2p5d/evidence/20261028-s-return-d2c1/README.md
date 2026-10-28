# D2-C1 — measured body return, before any runtime change

Baseline `6ff4a316be208334a65abb4780fef162c2456200`, PR132. Diagnostic only; no existing motion reimplemented. **REVISE.**

`measure_s_body_return.mjs` records native and D2-B at .0005-cycle spacing (4800Hz at1x) across .38–.68 and entry .04–.20. These are sequential integrated steps, not successive resets. Seven body bones (root/pelvis/spine/chest/neck/head/tail), 80 protected real skinned vertices, all four actual sole patches, contact anchors/joints, world distance and rotation are in the compressed traces. Relative motion can be obtained by subtracting integrated travel or the recorded planted foot anchor. No target-only surrogate. Summary computes body linear/angular velocities and finite-difference accelerations. Tiny-time boundary probes use explicit diagnostic initialization, then normal integration; dt0 command and epsilon1e-4/1e-5/1e-6 are recorded separately.

## Findings

1. **Repeated evaluation is not idempotent in partial blend.** At phase.53 a zero-time speed command plus `step(0)` changes protected actual body vertices by **27.4655mm**. The mixer may skip restoring an unchanged property at identical time; `apply()` blends its prior modified bone again. Solved terminal foot vertices mask this because IK restores the support target. Prior foot-only C1/C2 tests therefore did not detect it. This is an existing D2-B runtime bug newly diagnosed here, not a new regression introduced by C1.
2. **Float32 interpolation output contaminates microstep velocities.** `track.createInterpolant()` allocates a Float32 result, while native mixer output uses its double property buffer. At fully blended phase.394069, body residual is .000313m/s at100us, .042879 at10us, .345215 at1us: it grows as the observation interval shrinks. D2-B's previous worst sole residual .019398 is at phase.394069 during deceleration, BEFORE the .44–.62 exit. Do not attribute that maximum solely to exit timing.
3. **Exit crossfade mixes two differently timed piecewise native trajectories.** The .25 lead shifts native key corners into the return interval (e.g. .47 from native.72); the blend's changing weight adds motion between those poses. At1x the head peak relative speed grows from native1.532 to D2-B2.128m/s around.5115; spine angular speed1.182→1.669rad/s. D2-B position-acceleration peaks occur near .47/.60; pelvis~896m/s² and head~1938m/s² at this dense sampling. These are sampled derivative spikes at native piecewise keys, NOT physical acceleration/forces. Native itself contains corners, so global smooth motion is not claimed.

The blend envelope has zero first/second endpoint derivatives, but that alone neither removes internal native corners nor makes repeated evaluation deterministic. C2 should first explicitly evaluate base+advanced native channels into double buffers, then construct a bounded position/velocity-matched return over the SAME .44–.62 duration. Preserve hind push/full lead and compare stance extension; do not attenuate amplitudes or lengthen the window just to lower a number.

## Actual WebGL before evidence

[53 SIDE frames](frames/before-SIDE), [LOW](frames/before-LOW), [REAR3/4](frames/before-REAR_3_4), [CHASE](frames/before-CHASE). Four `before-*-return-slow16x.mp4` videos show phase.40–.66 at .005 increments, 480Hz simulation/30fps playback (**16× slow motion**, no synthetic frames). [PC](desktop-before.png), [Pixel7 emulation](android-before.png), [observations](before-visual-observations.json), page errors0. Rendering calls in this before capture retain the repeated-evaluation behavior being diagnosed; the sequence reproduces its visible consequence.

SIDE at.44/.53 shows the torso moving out of the push posture as the legs recover, with a more abrupt catch-up around the middle of exit. LOW/REAR show a relatively rigid posture reset rather than a convincing continuous push/recovery. Head/tail retain native identity, but sampled motion does not merit KEEP. The real frame sequence and numerical traces are separate evidence; neither approves S globally.

## CI / reproduction

Latest baseline [Actions40612003623](https://github.com/badjoke-lab/evowild-test/actions/runs/40612003623): build PASS, **142 passed /3 known failed /81 skipped**. Known failures: PUSH both devices and desktop AGILITY. Prior Android pressure recurrence is absent in this run. No S test failed. [Excerpt](baseline-actions.log).

Run `CHROMIUM_PATH=/usr/bin/chromium node scripts/measure_s_body_return.mjs` and `CHROMIUM_PATH=/usr/bin/chromium node scripts/capture_s_body_return.mjs` (dev server4173). Diagnostic execution completed without page errors; no runtime test was altered. C1 must be pushed before C2 runtime edits. Next: deterministic double-buffer channel evaluation and same-duration velocity-matched return, new explicit candidate, regression and real before/after comparison.
