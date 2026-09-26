# EvoWild Run — S Modeling Continuation Checkpoint

Status: **WIP / NOT ACCEPTED / S ONLY**

This checkpoint exists because the Work/Astra session hit its usage cap before it pushed its local modeling branch or model files.

## Source situation

Work reported a local branch named `art/astra-s-v1-20260926`, but no such remote branch existed when checked. The branch has now been created remotely from the then-current main so the work has a durable continuation point.

The attached creature reference remains the highest-priority visual source:

1. `docs/references/evowild-creature-reference-sheet-20260921.jpg`
2. `public/concept/S.webp`
3. `public/concept/s-run-sheet.svg`
4. `docs/motion-first-creature-standard-v0.1.md`

Do not use the old procedural Motion First S as a shape reference.

## What Work established before the cap

- S only; no P/E/A.
- small head;
- rear-flowing crest;
- chest-to-waist taper;
- pelvis-to-tail continuity;
- pale blue/white dorsal body with dark underside;
- long legs with actual joint mass rather than thin sticks;
- small separated toes;
- save candidates under `public/models/astra/`.

## Continuation work completed after the cap

A deterministic fallback WIP model was built directly from the attached S reference to avoid losing the session.

Current local high-resolution candidate:

- `/mnt/data/evowild_s_v7/s-v1.glb`
- ~221,496 triangles
- 28 geometry objects
- no rig
- no animation
- no texture atlas; color is geometry/face-color based

Low-resolution review candidate:

- `/mnt/data/evowild_s_v7/s-v1-lite4.glb`
- ~25,359 triangles

Six review views were rendered:

- SIDE
- FRONT
- REAR
- 3/4 FRONT
- 3/4 REAR
- LOW 3/4

A turnaround montage and side/reference comparison were also produced.

## Current visual verdict

**FAIL / WIP. Do not integrate as the accepted S yet.**

What is improved versus the rejected shrimp-like procedural S:

- one continuous torso/neck/head/tail body surface;
- smaller head;
- twin rear-flowing crest structure;
- longer athletic legs with visible joint mass;
- separate small toes;
- pale body / dark structural underside;
- compact Cue Band;
- short integrated tail instead of a long segmented appendage.

Remaining blockers:

- head/neck still reads too generic compared with the concept;
- armor/surface transitions need more authored shape language;
- FRONT and 3/4 views need stronger EvoWild-specific identity;
- limb attachment and foot design need another visual pass;
- no rig;
- no animation;
- current model was produced as a continuity fallback, **not by Astra**.

## Continuation rule

When Work/Astra becomes available again:

1. open this branch;
2. read this checkpoint and `docs/astra-s-modeling-handoff-v1.md`;
3. inspect the reference image first;
4. inspect the current WIP only as a continuation artifact, not as the design authority;
5. either refine it or replace it;
6. keep work limited to S;
7. do not start P/E/A;
8. do not wire it into Motion First until the six-view visual gate passes.

## CHECKPOINT

- current_step: Step 2/3 — S WIP model exists; six-view review started
- done: reference read; remote continuation branch created; deterministic WIP candidate built; six-view renders generated; manifest updated
- next: refine head/neck/crest/armor/feet against the reference, then repeat six-view review
- files_created: local `s-v1.glb`, local `s-v1-lite4.glb`, six review renders, turnaround, side comparison
- files_updated: `public/models/astra/s-v1.manifest.json`
- blockers: Work/Astra usage cap; GLB binary not yet committed to GitHub
- resume_note: S ONLY. Continue from this branch and reference sheet. Current WIP is not accepted and not Astra-generated. Fix the visual blockers before rigging or Motion First integration.
