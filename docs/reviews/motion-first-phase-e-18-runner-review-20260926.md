# Motion First Phase E — 18-runner Deployment Review — 2026-09-26

Status: **DEPLOYMENT PASS / PRESENTATION QUALITY OPEN**

Evidence:

- PR #49
- successful CI run `36250641118`
- artifact `10909600285`
- screenshot: `motion-first-phase-e-18-runner-race.png`
- CI screenshot readout: 18 runners, 29 FPS, Runner 04 · A, PACK camera

## What Phase E proves

The isolated simplified lane can now render the full field rather than a single test creature.

Verified:

- 18 runners coexist;
- S / P / E / A are all present;
- all four use the simplified procedural lane, not the Hunyuan S asset pipeline;
- the four dedicated gait systems remain active;
- deterministic individual variation is applied;
- CHASE / SIDE / LOW / FRONT / PACK all remain switchable;
- no high-detail S asset request is made from the simplified race page;
- CI render stayed above the explicit 20 FPS gate and showed 29 FPS in the captured PACK frame.

## What is **not** accepted yet

The Phase E screenshot is still visibly below the intended presentation quality.

### Speed impression is weak

The track is long and visually sparse. Most near-field reference objects are too far from the runner pack, so 20+ m/s does not read strongly enough.

### PACK is too loose

The full field is visible, but the runners occupy too little of the frame. This is useful diagnostically, not yet strong race presentation.

### Environment is generic

Rails, trees, stands, and flat ground prove depth, but do not yet provide the dense optical flow of the target direction.

### Individual variation is secondary

Morph silhouette and color are readable. The narrow per-runner head / crest / tail / proportion variation is intentionally subtle and is not yet enough to make every one of 18 runners memorable at a glance.

## Decision

Phase E passes as an **18-runner deployment / performance gate**.

It does **not** certify the page as finished or visually marketable.

Immediate order:

1. Phase F — replace timer AUTO camera with race-event direction.
2. Speed/presentation pass — increase near-field optical flow, tighten PACK / CHASE framing, and improve the sense of velocity without reducing gait quality.
3. Re-review the 18-runner page as a race presentation, not only as a technical deployment.
