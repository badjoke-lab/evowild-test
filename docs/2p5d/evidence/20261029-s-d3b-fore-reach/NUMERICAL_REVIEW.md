# D3-B recovery: numerical review

The correction is confined to `src/s_contact_ik.js` and the rate passed to body pose in `src/s_run_review.js`. `src/s_body_coupling.js` itself, including the completed D2-D splice, is byte-identical to the starting SHA. All GLBs and manifest are unchanged ([hashes](asset-integrity.json)). Existing v3/v4 selectors and production defaults are intact; failed v5 is recoverable at ca1c41d/5d11ead.

A critically damped posture-rate response (omega20/s,50ms time constant) carries its derivative between integrated substeps. A rate command does not alter its position or velocity at zero elapsed time. Seek initializes it explicitly to the selected steady speed; speed0 freezes it. Both v5 fore-reach and chest-load amplitudes use that response. Under rapid acceleration the pose amplitude deliberately lags the locomotion speed; a constant input settles in about.24s to95%, without overshoot. This is a kinematic animation response, not physical force/mass simulation. Travel, cadence, effective speed, original swing replanning and stance anchors continue using the unchanged locomotion state.

[Seven profiles](recovery-comparison.json): .5/1/1.5 steady, continuous acceleration/deceleration, abrupt fore/hind cases; actual soles and guards, body bones, joints, anchors and integrated travel sampled at240Hz. Final traces are exported by the focused tests, not synthesized from targets. Failed and baseline traces were captured before runtime edits.

|Measure|Failed v5|Fixed v5|
|---|---:|---:|
|Worst fore_L mesh velocity residual, m/s|.109659|.004747|
|Worst fore_R mesh velocity residual, m/s|.109690|.004515|
|Worst all-foot residual, m/s|.109690|.005987|
|Actual body residual at.75 under .5→1.5, m/s|.083252|.0000643|
|Maximum support clearance, mm|within existing gate|.423752|
|Maximum accumulated horizontal support slip, mm|within existing gate|.000893|
|Guard penetration / IK reach error, m|0 /0|0 /0|
|Minimum hind recovery peak, cm|47.98|47.98|

Microstep residual uses10us observations. Both value and its epsilon convergence are recorded in [failed](failed-speed-probes.json)/[fixed](fixed-speed-probes.json) probes; these include actual body and sole vertices. The new all-body+sole boundary regression across three rates has worst residual.002357m/s, zero-time jump0 and freeze displacement0 ([results](mesh-speed-regression.json)). Joint angles stay48.67–161.22°, maximum segment-length drift5.78e-8m. No previous threshold was relaxed.

The exact original first failure is fore_L at t.120833333s, phase.4050609665 in EXTENSION, .073528995m/s. fore_R at the same instant is.100112122m/s. The initial test stopped on the left foot, so neither that right-foot error nor the larger continuous-ramp failures appeared in its first assertion. The correction addresses the common derivative discontinuity rather than tuning only that time/phase.

Preserved reach at phase.20 (actual fore foot joint displacement from v3): L4.7165/6.0372/7.3578cm at.5/1/1.5, R3.8156/4.8840/5.9524cm. These equal the prior v5 amplitudes. Chest quaternion difference at.75/1.5 remains3.57265°, outside-load comparisons.53/.96 remain native. No amplitude has been removed to make a guard pass.

D2-D [native-join regression](d2d-preserved.json) still reports.002257488m/s at.64 vs old unsmoothed.240761m/s. Its probe uses phase increment.0001, not the10us speed-command interval; the two metrics must not be conflated. Six complete v3 mesh/body/contact probe snapshots before and after the source edit are exactly equal ([comparison](baseline-probe-preservation.json)). The focused evolution test also verifies identical v3/v5 cycles, distance, effective rate, support anchors and stages over240 integrated steps, while hind sole vertices agree within1µm.

Numerical recovery is a limited PASS, not visual adoption. Inspect the actual four-view videos and canonical S reference before judging sprint quality; no physical Android timing, ground-reaction force or true COM simulation is asserted.
