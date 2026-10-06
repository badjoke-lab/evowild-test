# Kimodo S Launch Transfer v0.1

Status: **isolated C1 comparison / not production approved**

Branch: `exp/kimodo-s-launch-transfer-20261006`

Base: `main@d40ab7cb0a3d62bb3ae2598c1eeff9345de5e3ca`

## Purpose

Use the already-generated real Kimodo SOMA sprint only as an acceleration-posture timing reference for EvoWild S.

This lane exists because the BlendCap S hybrid closed as `KEEP_AS_REFERENCE`: direct human-derived body layering did not justify its contact/root side effects.

Kimodo is tested more narrowly here.

## Hard constraints

The Kimodo curve may change only the timing of the existing S launch lean in review mode.

It must not change:

- race distance or root travel;
- `runner.speed` or `runner.targetSpeed`;
- the S V5 baked quadruped limb cycle;
- animation playback rate;
- foot locking/contact logic;
- P/E/A motion;
- production behavior when the review query is absent.

No humanoid joint is retargeted to S.

## Source

The source curve is copied from the verified real official-Space sprint artifact on:

`exp/kimodo-ardy-motion-feasibility-20261004`

Real source generation:

- NVIDIA official Kimodo Hugging Face Space;
- model: `Kimodo-SOMA-RP-v1`;
- prompt: `A person sprints forward quickly at a steady pace.`;
- 180 frames at 30 fps;
- extracted motion duration: 5.9667 s.

The useful observation is shape-only: Kimodo reaches 80% of its normalized launch envelope substantially earlier than the existing EvoWild launch envelope.

## Hypothesis

Current S launch lean is driven directly by instantaneous speed error. It remains forward-pitched for relatively long.

For the isolated test, keep the same maximum lean scale but drive its decay with the normalized Kimodo launch envelope:

`leanTarget = (1 - kimodoEnvelope) * 1.2`

This tests whether a faster establishment/return-to-running-attitude curve makes S acceleration more readable without touching gait/contact/physics.

## Gate

Required before any integration decision:

1. baseline SIDE continuous review;
2. Kimodo-timed SIDE continuous review;
3. baseline LOW continuous review;
4. Kimodo-timed LOW continuous review;
5. confirm same S V5 asset and same animation playback rule;
6. confirm review mode does not alter physics;
7. visual decision: `KEEP`, `REVISE`, or `REJECT`.

A technical pass is not a visual pass.
