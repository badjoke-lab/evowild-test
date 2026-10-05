# Tripo T0 API fallback

The Work cloud browser cannot create a WebGL context, so Tripo Studio cannot currently complete the T0 import/preview path there.

The documented Tripo v3 API can perform the T0 operations without WebGL:

1. upload `source-lod2.glb` via `POST /v3/files`;
2. run `POST /v3/animations/rig-check`;
3. if riggable and the recommended type is `quadruped`, run `POST /v3/animations/rig` with model `v2.5-20260210`;
4. download the resulting GLB directly into `public/experiments/tripo-s/t0-rigged-lod2.glb`;
5. preserve machine-readable evidence in `art/motion/tripo-s/review/t0-api-session.json`.

Workflow:

`.github/workflows/tripo-t0-api.yml`

Script:

`scripts/tripo-t0-api.mjs`

## One-time secret setup

Create a Tripo API key from the signed-in Tripo Console API Keys page.

Store it as a GitHub Actions repository secret named:

`TRIPO_API_KEY`

Never paste the API key into repository files, issues, PR text, chat messages, or logs.

## Run order

First dispatch the workflow with:

`mode=check`

This performs upload + rig-check only. The official rig-check endpoint reports `credits_consumed: 0`.

If and only if the result is riggable and recommends `quadruped`, dispatch:

`mode=rig`

The rig call uses:

- model `v2.5-20260210`
- rig type `quadruped`
- spec `tripo`
- output `glb`

The official Auto Rig example currently shows 30 credits consumed by a rig task. Treat the actual returned `credits_consumed` and account balance as authoritative.

## Scope

This fallback solves T0 only.

The public Tripo v3 documentation currently exposes rig-check, rig and retarget animation endpoints, but does not list the new Studio Text to Motion / Multi-stage Motion workflow as a documented public endpoint. Therefore T1 remains a Studio execution task unless/until a documented API endpoint is available.

Do not substitute a preset quadruped walk for the T1 Text to Motion gate; that would answer a different question.
