# D3-B recovery diagnosis — before runtime edits

Source `ca1c41daef98d5565ca892a5927d08aeda57b84f`, preserved D2-D push-v3 vs failed D3-B push-v5. DraftPR132 verified open/draft/unmerged. Local Playwright exactly reproduces the previous guard failure: .07352899508547898m/s vs unchanged<.02. [Failure](reproduced-failure.log), [fourteen full actual-mesh/body traces and summary](diagnosis-summary.json).

The first assertion hides a larger companion failure. At abrupt-hind t=.120833333s, cycle phase=.405060966544:
- fore_L: .073528995m/s; limb phase.765060967, swing u.716940924, EXTENSION.
- fore_R: .100112122m/s; limb phase.685060967, swing u.620555381, EXTENSION.
- Both airborne, no active support anchor, IK reach error0. Not swing/contact transition, toe-roll support, or unreachable IK.

`additionalReach = E(swing) * (.045 + .035*effectiveRate)` directly follows C1's bounded-rate ramp. The command changes effectiveRate's derivative from0 to4/s. Thus the added foot velocity jumps by `E*.035*4`: predicted .073680663/.100223377m/s. Actual10us mesh probes differ by ordinary finite-step acceleration. Shrinking epsilon from100us to1us makes right-fore residual converge .09913→.10021, rather than vanish: this is a real velocity corner, not Float32/sample noise. D2-D baseline residual converges toward0. [Actual sole and protected body probe arrays](failed-speed-probes.json).

Broader scan: failed continuous acceleration/deceleration maxima .109383/.109690m/s; abrupt-fore .109457m/s. Baseline maximum across all seven profiles .005987m/s. Stance targets remain anchored, zero-time foot position is invariant; it is the new speed-dependent visual trajectory derivative that is broken.

Chest has the same issue independently: at phase.75 the actual protected body-mesh velocity residual approaches .08331m/s under .5→1.5; baseline approaches0. `foreLoad` uses the same instantaneous effectiveRate coefficient. Both need a shared continuous-velocity posture response, not removal of fore reach or an altered contact threshold.

Planned bounded correction: an opt-in second-order, critically damped posture-rate state, advanced only by elapsed simulation time, initialized explicitly on diagnostic seek and frozen at speed0. Feed it only to push-v5 reach and chest amplitudes. Keep C1 travel/cadence/rate, anchors, swing replanning, toe paths, all push-v3/D2-D source behavior and steady-speed reach magnitudes intact. No global bob or GLB change. Verify the exact failure AND chest/endpoint responses, then full existing guards and actual four-view evidence.

Canonical PNG is absent from this branch and main. Read-only retrieval from `exp/s-creature-vibe-modeling` at `48b39d8b64aa5146dc2028876b448c3e884295e6`, path `art/s-creature/references/00_s_type_modeling_image_v1.png`, gives SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6` exactly. Viewed that image, without editing or importing it into this branch. No other-lane modification. It shows a narrow athletic body, directional crest/small head, species-specific jointed limbs and long tail; current review GLB remains an inherited visual REVISE candidate.

Diagnosis completed before correction; videos and passing corrected tests are still pending at this checkpoint. No new Actions manually queued. Diagnostic-only save uses skip-ci to avoid a redundant known-failing full run.
