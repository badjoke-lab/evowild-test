# Tripo S Motion Bench — Work launch handoff

Date: 2026-10-05

Repository: `badjoke-lab/evowild-test`

Branch: `exp/tripo-s-motion-bench-20261003`

## ChatGPT execution configuration

Recommended execution environment:

- Mode: **Work**
- Model: **GPT-6 Astra**
- Reasoning / thinking level: **High**

Reason:

This task combines authenticated browser interaction, file download/export, Git repository mutation, animation-quality inspection, and multi-step stop gates. Use the strongest Work configuration available rather than an Instant session.

Fallback if GPT-6 Astra Work is not available in the UI:

- GPT-5.6 Sol
- High thinking

Do not use a low/instant reasoning setting for T0/T1 decisions.

## Tripo rig configuration

For the primary T0 test:

- input geometry: `public/models/evowild-s/source-lod2.glb`
- geometry LOD: `LOD2`
- current repository role: canonical unrigged S shape/edit source
- Tripo rig model/version, when selectable/API-equivalent: `v2.5-20260210`
- rig type: `quadruped`
- output preference: `GLB`
- rig spec: prefer Tripo-native for the first compatibility test unless Studio only exposes another supported path

The existing EvoWild `focus-rigged-v5.glb` is the comparison reference only. It is not the primary Auto Rig input.

## Exact task

1. Fetch/pull latest remote branch.
2. Read:
   - `docs/tripo-s-motion-bench-v0.1.md`
   - `docs/tripo-s-motion-bench-work-instructions.md`
   - `docs/reviews/tripo-s-motion-bench-review.md`
   - `art/motion/tripo-s/bench-manifest.json`
3. Run only T0 first.
4. If T0 passes, run exactly one T1 steady-run generation.
5. Commit real outputs and metadata to the repository paths defined in the spec.
6. Push the branch.
7. Wait for GitHub Actions to produce `tripo-s-motion-review`.
8. Stop after T1. Do not start T2 until the external reviewer has inspected the repository/CI evidence and recorded `PASS_TO_T2`.

## No manual handoff

Do not ask the user to download Tripo files and re-upload them into chat.

Do not use chat attachments as the canonical handoff.

Canonical handoff is:

`Tripo -> exported file -> repository branch -> GitHub Actions review artifact -> reviewer`

## Completion report format

Report only:

- T0 decision
- input geometry path + LOD
- Tripo rig model/version and rig type actually used
- T1 decision state (`REVIEW_PENDING` until external review)
- committed artifact paths
- commit SHA
- Actions run ID
- CI artifact name
- credits consumed / paid credits used if visible
- any conversion/normalization performed

Do not claim PASS from the Tripo viewport.
