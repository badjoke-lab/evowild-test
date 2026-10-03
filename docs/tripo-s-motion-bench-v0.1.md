# EvoWild Run — Tripo S Motion Bench v0.1

Status: **isolated experiment / not production-approved**

Branch: `exp/tripo-s-motion-bench-20261003`

Base branch: `main`

Base commit: `d25553169e4406f5af660fc5559e075163aac6ff`

## Purpose

Determine whether Tripo-generated animation can materially improve the current Motion First S runner without weakening the existing contact, cadence, race-state, or camera work.

This lane is isolated. It must not modify:

- `exp/s-creature-vibe-modeling`
- `feat/s-creature-model`
- the accepted Motion First / Simplified Race runtime
- the UniMate bench
- 2.5D, Sakura, Sprite, or Hunyuan experiments

## Input lock

Use:

`public/models/evowild-s/focus-rigged-v5.glb`

Do **not** use the current Vibe Modeling B1a-v2 asset. That morphology lane is still review-pending and has no approval to become a motion-test input.

The purpose of this bench is motion quality, not geometry quality.

## Execution gates

### T0 — import / rig compatibility

Upload the locked S GLB to Tripo and confirm:

- model imports intact;
- all four limbs remain distinct;
- head / neck / tail are present;
- rig or animation preprocessing completes;
- no destructive topology or orientation change prevents comparison.

If T0 fails, stop and record `REJECT_IMPORT`.

### T1 — one sprint only

Generate **one** maximum-effort forward sprint clip first.

Prompt must describe motion only. Use this semantic target:

`maximum-effort forward quadrupedal sprint, explosive long stride, strong shoulder and pelvis drive, stable forward travel`

Do not describe appearance, camera, environment, lore, UI, lighting, or race strategy.

Export the animated result in the most reusable supported 3D format available. Preserve the original export without post-processing.

T1 exists to avoid spending credits/time on twelve clips before basic usefulness is proven.

### T1 review

Compare the single Tripo sprint against the current Motion First v5 S baseline.

Required views:

- SIDE
- LOW
- CHASE
- FRONT

Required checks:

- stance foot skating;
- foot penetration / floating;
- fore/hind phase coherence;
- stride direction;
- root travel vs leg cadence;
- shoulder/chest contribution;
- pelvis drive;
- spinal compression / extension;
- neck/head follow-through;
- tail behavior;
- high-speed readability;
- export / replay stability.

T1 decision:

- `EXPAND` — materially useful enough to justify the full bench;
- `KEEP_AS_REFERENCE` — useful motion ideas but not suitable as a runtime clip;
- `REJECT` — no material improvement or severe contact/rig/export failure.

Do not expand unless T1 is `EXPAND`.

### T2 — full comparison set

Only after T1 = `EXPAND`, generate three repetitions for each motion:

- steady forward run;
- fast gallop / bound;
- maximum-effort sprint;
- explosive acceleration from a low start.

Total: 12 generated clips.

Use motion-only prompts and keep semantic wording as consistent as possible across repetitions.

## Comparison baseline

Compare:

1. current Motion First v5;
2. UniMate bench outputs, when real outputs exist;
3. Tripo bench outputs.

Use the same S input family and the same review cameras wherever technically possible.

No system wins by visual novelty alone. Runtime usefulness is the criterion.

## Runtime acceptance criteria

A Tripo result is not accepted merely because the generated video or viewport looks plausible.

A production candidate must survive:

- deterministic 3D export;
- replay inside the EvoWild Three.js runtime;
- speed-to-cadence remapping;
- race-state blending;
- foot-contact correction / locking as needed;
- multi-view review.

If useful, the intended hybrid architecture is:

`Tripo motion clip -> EvoWild contact correction -> speed/cadence matching -> race-state blending -> Three.js runtime`

Tripo does not replace Race Engine movement, camera direction, Agent decisions, or Creature morphology.

## Artifact layout

Store only real outputs.

Suggested layout:

`art/motion/tripo-s/`

- `input/` — input manifest only; do not duplicate large repo assets unnecessarily
- `raw/` — untouched Tripo exports
- `normalized/` — runtime-normalized exports, if needed
- `review/` — rendered SIDE / LOW / CHASE / FRONT evidence
- `TRIPO_S_MOTION_BENCH_RESULTS.md` — result ledger

No mock render or placeholder may be presented as a generated result.

## Stop rule

After every gate:

`generate/export -> inspect real artifact -> compare -> decision -> next gate`

Do not start T2 before T1 is explicitly reviewed.
