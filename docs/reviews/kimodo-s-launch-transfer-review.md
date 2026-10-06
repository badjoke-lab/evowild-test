# Kimodo S Launch Transfer Review

Branch: `exp/kimodo-s-launch-transfer-20261006`

## Source

Real Kimodo SOMA sprint generated previously from NVIDIA's official public Kimodo Space.

Transfer rule remains descriptor/timing only. No humanoid joint rotation or human foot contact is mapped to the S quadruped.

## V1 — raw establishment envelope -> S root lean

Evidence: Actions run `37498323217`.

The A/B was aligned at exact simulation times after the initial wall-clock review was found invalid.

At `t=0.5 s`:
- baseline root lean target: `0.0238`
- Kimodo V1 target: `0.9553`
- Kimodo envelope: `0.2039`

At `t=1.6 s`:
- baseline root lean target: `0.0975`
- Kimodo V1 target: `0.3357`
- Kimodo envelope: `0.7203`

At `t=4.2 s`:
- baseline root lean target: `0.0779`
- Kimodo V1 target: `0.0000`
- Kimodo envelope: `1.0000`

Decision: **REVISE**.

Reason: using `(1 - Kimodo speed envelope)` directly as S root-lean amplitude confuses establishment progress with posture magnitude. It overdrives early S root pitch by an order of magnitude relative to the accepted baseline, yet still produces only a modest visible gain because the existing root rotation scale is deliberately small.

## V2 — Kimodo acceleration timing -> non-contact creature follow-through

Status: **RUNNING**

V2 changes the transfer meaning:

- S root lean remains the accepted baseline;
- S gait playback remains the accepted baseline;
- race physics remains unchanged;
- Kimodo contributes only an early launch-drive timing curve derived from the slope of the speed-establishment envelope;
- the drive is applied only to `neck`, `head`, and `tail` local pitch after the baked V5 mixer update;
- these bones are not ancestors of any S foot, so the overlay cannot move the four foot chains;
- the drive is faded out before 2.5 s to prevent the source curve's later rise from creating a second launch cue.

V2 maximum local offsets at full drive:

- neck: `+7.0°`
- head counter-pitch: `-3.5°`
- tail: `-5.0°`

Required decision after exact-time SIDE / LOW A/B review:

- `KEEP` only if acceleration intent becomes visibly clearer without species distortion;
- `REVISE` if the cue is useful but amplitude/sign/timing is wrong;
- `REJECT` if the difference is negligible or looks artificial.

No production merge before visual review.


V2 status marker: `EXACT_TIME_REVIEW_READY`

The review harness now uses two model loads total, pauses at exact simulation times (0.5 / 1.6 / 4.2 s), and captures both SIDE and LOW while paused. This removes the wall-clock/FPS timing ambiguity and the previous four-pass timeout.
