# C2 — continuous acceleration/deceleration validation

C1 was saved at `c0d4d4a`, remote checkpoint `d711705`, before C2 started. This unit adds measurement, regression and visual evidence; it does not change the C1 runtime/controller or any GLB. v3 retains SHA-256 `78dd511cd82aa8afef04a7d61f21b68d4391a9a3143acbaa4b6473b9f8a42a6f`.

Before is detached commit `812c4a9` on port 4174, after is the C1 controller on 4173. The [baseline instrumentation patch](baseline-instrumentation.patch) only exposes rate setting, non-rendering steps and real mesh sampling; it preserves the old locomotion formula and renders the original WebGL poses. No fabricated mock, sprite warp, GLB modification, ground shift or camera adjustment.

## Reproduction and sampling

`scripts/s_contact_profiles.mjs` defines four profiles: continuous .5→1→1.5 acceleration over 2s, reverse deceleration over 2s, and abrupt .5→1.5→.5 at two initial phases over 1.2s. `scripts/measure_s_contact_acceleration.mjs` runs both versions and saves eight gzip traces. Every trace contains all 175 fixed sole vertex world positions, phase, target/velocity, anchor/touchdowns (after only), reach error and joint coordinates. [Full summary](summary.json). Sample frequency 240Hz.

At each command change, both sides of dt=0 are sampled from **actual SkinnedMesh vertices**. Actual mesh velocity is independently estimated over 10µs intervals immediately before/after the command; the residual includes finite acceleration and floating-point skinning noise, so a small nonzero value is not proof of a mathematical velocity discontinuity. This measurement never substitutes the IK target velocity for the mesh.

Normal integration uses effective speed/cadence with the C1 acceleration bound. Requested and effective values are both retained in traces; the command is not an instantaneous body-velocity teleport. Baseline and after share the same commands/time, not identical phases, because the after controller now integrates acceleration.

| Profile | Foot | Zero-time vertex jump mm, before → after | Mesh velocity residual m/s, before → after | After accumulated stance slip mm | Penetration mm | Recovery m | Reach error mm | Joint-angle range ° |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| acceleration | fore_L | 0.585 → 0.000 | 0.02513 → 0.00486 | 0.000288 | 0.000 | 0.3400 | 0.000 | 102.5–155.0 |
| acceleration | fore_R | 0.601 → 0.000 | 0.02512 → 0.00274 | 0.000365 | 0.000 | 0.3400 | 0.000 | 103.8–157.8 |
| acceleration | hind_L | 0.660 → 0.000 | 0.02709 → 0.00599 | 0.000796 | 0.000 | 0.4800 | 0.000 | 50.2–158.7 |
| acceleration | hind_R | 0.682 → 0.000 | 0.02709 → 0.00350 | 0.000626 | 0.000 | 0.4800 | 0.000 | 50.7–159.2 |
| deceleration | fore_L | 0.562 → 0.000 | 0.02512 → 0.00151 | 0.000244 | 0.000 | 0.3400 | 0.000 | 102.4–154.9 |
| deceleration | fore_R | 0.581 → 0.000 | 0.02513 → 0.00278 | 0.000331 | 0.000 | 0.3400 | 0.000 | 103.9–157.6 |
| deceleration | hind_L | 0.662 → 0.000 | 0.02709 → 0.00219 | 0.000647 | 0.000 | 0.4800 | 0.000 | 50.0–158.7 |
| deceleration | hind_R | 0.690 → 0.000 | 0.02709 → 0.00216 | 0.000472 | 0.000 | 0.4800 | 0.000 | 50.5–159.2 |
| abrupt-hind | fore_L | 128.364 → 0.000 | 6.07265 → 0.00173 | 0.000164 | 0.000 | 0.3399 | 0.000 | 102.4–154.9 |
| abrupt-hind | fore_R | 116.534 → 0.000 | 6.89656 → 0.00022 | 0.000201 | 0.000 | 0.3400 | 0.000 | 103.9–157.1 |
| abrupt-hind | hind_L | 131.656 → 0.000 | 6.27439 → 0.00128 | 0.000436 | 0.000 | 0.4800 | 0.000 | 50.2–157.7 |
| abrupt-hind | hind_R | 81.843 → 0.000 | 7.43978 → 0.00133 | 0.000336 | 0.000 | 0.4800 | 0.000 | 50.5–158.7 |
| abrupt-fore | fore_L | 124.591 → 0.000 | 5.14503 → 0.00073 | 0.000142 | 0.000 | 0.3400 | 0.000 | 102.4–154.3 |
| abrupt-fore | fore_R | 96.941 → 0.000 | 6.38742 → 0.00084 | 0.000190 | 0.000 | 0.3400 | 0.000 | 103.9–157.8 |
| abrupt-fore | hind_L | 142.344 → 0.000 | 7.11384 → 0.00023 | 0.000488 | 0.000 | 0.4800 | 0.000 | 48.7–158.7 |
| abrupt-fore | hind_R | 91.007 → 0.000 | 7.72115 → 0.00042 | 0.000349 | 0.000 | 0.4800 | 0.000 | 48.9–159.2 |

Stance slip includes each fixed vertex's horizontal displacement while consecutive samples retain the same contact anchor. The baseline has no persistent anchors; its stage labels are used, while zero-time jump remains a separate metric so a changing stage cannot hide a teleport. All four feet are checked. Maximum after segment-length drift is below 0.00001m. Rear recovery remains ~.48m; no foot hiding or knee inversion was used to obtain the result.

## Distance, cadence and stride

| Profile | Time s | Travel m | Integrated cycles | Travel vs speed-integral residual mm | Cycle vs cadence-integral residual |
| --- | ---: | ---: | ---: | ---: | ---: |
| acceleration | 2.000 | 8.783527 | 4.946370 | 0.194 | 0.0000611 |
| deceleration | 2.000 | 7.216538 | 4.459690 | 0.129 | 0.0000396 |
| abrupt-hind | 1.200 | 4.516684 | 2.721611 | 0.017 | 0.0000113 |
| abrupt-fore | 1.200 | 4.516638 | 2.721595 | 0.029 | 0.0000045 |

The independent integral uses the sampled effective speed/cadence trapezoid, while the controller uses event-split substeps <=1/480s; small quadrature residuals are expected. Instantaneous stride is `speed/cadence`, so stride×cadence agrees with travel speed. It changes through acceleration rather than multiplying a fixed clip and travel by the same number. Exact per-frame values remain in the traces.

## Browser evidence

156 real WebGL frames: acceleration from SIDE/CHASE/LOW/REAR 3/4, rear deceleration, and a dense rear sequence around an abrupt command, each before/after. [Observations](visual-observations.json) match every screenshot and record zero browser errors. Frames are advanced sequentially through elapsed time; only the **start** of each run uses an explicit diagnostic seek. No mid-run pose resets.

| Recording | Before | After |
| --- | --- | --- |
| Acceleration | [video](before-acceleration-rear.mp4) | [video](after-acceleration-rear.mp4) |
| Deceleration | [video](before-deceleration-rear.mp4) | [video](after-deceleration-rear.mp4) |
| Abrupt switch close-up | [video](before-abrupt-closeup-rear.mp4) | [video](after-abrupt-closeup-rear.mp4) |
| PC 1280×800 | [image](desktop-before.png) | [image](desktop-after.png) |
| Pixel 7 emulation | [image](android-before.png) | [image](android-after.png) |

Frame folders: [before SIDE](frames/before-acceleration-SIDE), [after SIDE](frames/after-acceleration-SIDE), [after CHASE](frames/after-acceleration-CHASE), [after LOW](frames/after-acceleration-LOW), [after REAR](frames/after-acceleration-REAR_3_4). Videos encode actual sequential browser frames at their simulation sampling interval, without interpolating poses. Full-profile sequences sample at 6fps and cannot establish refresh-rate smoothness; the .1s abrupt close-up samples at 120Hz. These are diagnostic animation recordings, not a claim of realtime headless or physical-phone performance. Physical Android is untested. Scripted intermediate rates can leave the fixed-option selector blank; the displayed numeric rate and trace record the actual request.

Visual comparison: the old abrupt sequence shifts feet even without normal stance travel; after C1 the contact relation persists as the body moves over it. SIDE/LOW show the same knee/hock folding and elevated recovery; CHASE/rear retain the existing S torso/neck silhouette and ground relation. No new broad mesh collapse was observed in these views. Feet still keep a mechanically constant pitch, pushing lacks a rolling toe-off, and weight transfer/flight/extension are not yet convincing sprint motion. Those deficiencies remain visible and are deliberately not disguised by this speed fix.

**KEEP for the scoped C1/C2 speed-continuity correction; S visual/production gate remains REVISE.** This is not formal creature-art approval or a production promotion. Next separate unit: rolling toe-off/foot rotation, then load transfer and natural flight/extension, retaining this acceleration regression.

## Tests, CI and checkpoint

[Dedicated PC/Pixel 7 regression log](tests.log): 2 tests PASS, each covers all four continuous/abrupt profiles; actual-mesh jump <1mm, velocity residual <.02m/s, total stance slip <1mm, penetration/reach <1mm, joint angles35..178°, segment-length drift <.00001m, preserved recovery. [C1 build PASS](../20261026-s-continuity-c1/build.log); C2 does not change bundled runtime code. Existing complete race suites were not repeated.

Prior head `812c4a9` [Actions 40325691813](https://github.com/badjoke-lab/evowild-test/actions/runs/40325691813): build PASS, 120 passed / 3 known failed / 81 skipped (desktop/Android PUSH comparison, desktop AGILITY). C1 [Actions 40331622158](https://github.com/badjoke-lab/evowild-test/actions/runs/40331622158) was in progress at the first inspection. New C2 CI is pending publication; no global-green claim.
