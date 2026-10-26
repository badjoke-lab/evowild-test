# C1 — persistent S contact anchors and continuous speed changes

Started from verified `812c4a987814201e76b9039d1ec9e526b8a95e18`; B1/B2/B3 were not recreated. Same immutable `focus-contact-v3.glb`, SHA-256 `78dd511cd82aa8afef04a7d61f21b68d4391a9a3143acbaa4b6473b9f8a42a6f`. No GLB, geometry, bind joint, camera, ground, production manifest or race-code edit.

`src/s_contact_ik.js` now owns elapsed active time, integrated distance/cycles, effective rate, per-foot contact anchor, target velocity, touchdown count and next phase event. `advance(dt, requestedRate)` updates that state; `apply()` only solves the existing articulated limbs against stored targets. Rate commands with zero elapsed time cannot change positions. Rate 0 freezes distance/cycles/feet immediately. Active rate approaches its command at up to 4 rate units/s; travel/cadence are integrated in event-split steps no larger than 1/480s. These are isolated review-controller settings, not race balance changes.

A foot's actual touchdown target becomes a fixed world anchor until toe-off. At lift, current position and zero stance velocity seed the next swing. The longitudinal cubic is replanned from its **current position and world velocity** toward a velocity-dependent predicted landing, with zero landing velocity; it never resets the foot to the predicted endpoint. The recovery arc retains the prior phase curve; continuously integrated effective cadence keeps its motion continuous. Event splitting preserves exact contact/lift boundaries. Foot orientation and the original analytic limb solve/segment lengths are unchanged.

`reset(cycles,distance,rate)` is an explicit diagnostic seek only. `s_run_review.js` separates `step(dt)` / normal time progression from `setPhase()` / diagnostic reset. Repeated seeks are deterministic; normal updates do not rebuild anchors. Steady-cycle measurement now advances state sequentially rather than seeking each sample.

## Regression gate

[Dedicated test](../../../../tests/s-contact-transitions.spec.js), [test log](tests.log), [actual-mesh results](regression-results.json), [build log](build.log). Both PC and Pixel 7 emulation PASS; build PASS (existing chunk warning only). Every measurement uses all fixed sole SkinnedMesh vertex IDs, not targets alone.

| Case | Before B3 jump | After C1 jump at dt=0 | Max stance vertex slip per sampled step | Penetration / reach error |
| --- | ---: | ---: | ---: | ---: |
| Phase .2, .5→1.5 | .126981m | 0m | 1.2851e-8m | 0 / 0 |
| Phase .7, .5→1.5 | .112702m | 0m | 1.2104e-8m | 0 / 0 |

Each case then advances 360 samples at 240Hz, changes command back to .5, and checks all four feet during stance. Joint angles stay ~49–159°, inside existing 35–178° bounds. Each foot has >10 independently checked stance intervals. Half a second at rate 0 produces exactly zero elapsed gait time, travel and vertex change; repeated explicit seeks produce identical vertices. Immutable v3 hash is asserted.

**C1 continuity gate: PASS / KEEP for this isolated fix. S overall: REVISE.** This numeric gate does not approve visual gait or production use. C2 (continuous acceleration/deceleration profiles, speed/velocity evidence, four-view videos and PC/mobile before/after) starts only after this checkpoint is published. Rolling toe-off, force transfer, flight/extension naturalness and inherited appearance issues remain separate work.
