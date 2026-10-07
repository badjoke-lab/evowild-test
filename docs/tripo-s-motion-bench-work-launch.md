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


## Repository review automation already prepared

Before external Tripo execution, the branch already contains:

- `tripo-motion-review.html`
- `src/tripo_motion_review.js`
- `tests/tripo-motion-review.spec.js`

The test intentionally skips while `public/experiments/tripo-s/t1-steady-run.glb` is absent. Once Work commits that real T1 GLB, the same branch CI will render the four required views and continuous review video automatically.


## WebGL-blocked fallback — use documented API for T0

The authenticated Work browser has already failed T0 because its Chromium surface reports WebGL disabled. Do not keep retrying the same Studio preview.

Use the repository fallback documented in:

- `docs/tripo-t0-api-fallback.md`
- `scripts/tripo-t0-api.mjs`
- `.github/workflows/tripo-t0-api.yml`

One-time requirement: GitHub Actions repository secret `TRIPO_API_KEY`.

Execution order:

1. dispatch `tripo-t0-api` with `mode=check`;
2. inspect the returned rig-check result;
3. only if `riggable=true` and `rig_type=quadruped`, dispatch `mode=rig`;
4. the rig workflow downloads and commits `public/experiments/tripo-s/t0-rigged-lod2.glb` directly to this branch;
5. resume the normal bench from the committed T0 GLB.

Do not spend rig credits if rig-check recommends another body type.

This fallback does not solve T1. The public Tripo v3 docs currently document rig-check, rig and retarget, but not the new Studio Text to Motion / Multi-stage Motion flow. T1 therefore still requires a WebGL-capable Studio execution surface unless a documented API appears.


## 2026-10-07 execution route update

Primary execution route is now **desktop-local Work**, not the cloud browser.

Reason:

- the authenticated cloud Work browser reproduced a hard WebGL-context failure in Tripo Studio;
- ChatGPT desktop Work can operate locally with user-approved local files/apps;
- the desktop built-in browser runs on the user's machine;
- when an existing Chrome profile/session is preferable, use the supported Chrome path from the desktop app.

### Preferred route

1. Open the ChatGPT desktop app on the user's Mac.
2. Open this project in **Work**.
3. Use local Work, not Cloud Work, for the Tripo browser step.
4. Open the desktop built-in browser (`Command+Shift+B`) and navigate to Tripo Studio.
5. Sign in in the browser if needed; never put credentials in chat.
6. Open/clone the repository locally and checkout:
   `exp/tripo-s-motion-bench-20261003`
7. Read this file and the bench/review specs.
8. Run T0 in Tripo Studio with:
   - `public/models/evowild-s/source-lod2.glb`
   - model/version `v2.5-20260210`
   - rig type `quadruped`
9. If T0 passes, run exactly one T1 steady-run Text to Motion generation.
10. Export the real results locally and let Work place them in the repository paths, commit, and push.
11. Stop after T1 and wait for repository/Actions review.

### Fallback route

If the local desktop browser still cannot render Tripo:

- T0 falls back to the existing GitHub Actions API route in `docs/tripo-t0-api-fallback.md`.
- T1 remains blocked until a WebGL-capable local browser/Chrome path is available or Tripo exposes Text to Motion via API.

Do not retry the known-broken cloud browser path.
