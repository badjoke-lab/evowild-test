# Game Studio evaluation — existing 2.5D survivor race

Evaluation date: 2026-10-10 (Asia/Tokyo). Branch: `exp/gamestudio-2p5d-20261010`.
Base: `610d42800180ed31f174a097fc2eb96c27ecd0ab` from `main`.
Target: `race-quality.html`, using the existing Canvas 2D/Vite implementation.

Game Studio improved the validation and UI workflow. It did not improve or replace
the creature artwork, source poses, or race simulation. This is an evaluation
branch, with no merge or promotion decision.

## Findings and outcomes

| Finding | Before | After / remaining limitation |
| --- | --- | --- |
| Mobile command controls were difficult to touch | Target selector 24px high; commands 25px high; Pause/Reset 26px high | All buttons and selector at least 44×44 CSS px; mobile Agent panel still below the existing 140px height limit |
| Command target could be confused with camera subject | Only name and morph in selector | Runner code and `YOU` identify the target; changing target still leaves the camera on the existing selected runner |
| Nonessential feedback pulse ignored reduced-motion preference | Animated under `prefers-reduced-motion: reduce` | Pulse disabled under that preference; race still advances |
| Strict console-error tests caught missing favicon | Browser requested `/favicon.ico`, which returned 404 | Target page explicitly uses an empty data favicon; console-error assertions remain enabled |
| Agent test compared unlike creature conditions | Raw S PUSH ≈0.613, E PUSH ≈0.746; S was under opening-pack pressure | Test compares compatibility after accounting for measured stamina, fatigue and pressure; still requires positive response, fatigue and stamina effects and S/E differentiation |
| Dense pack silhouettes remain crowded | Existing sprites can overlap while labels prioritize YOU, rival and leaders | Unchanged rendering. Zero label intersections in the captured normal and battle-review scenes; no claim that source-pose quality improved |
| Source sheets have rough motion and source artifacts | P/E/A quality limitations already documented by the canonical lock; A uses a 2×3 layout | All 24 source slots are distinct and retain transparency. Preview strips expose source artifacts and pose differences. No art generation, cleanup, re-anchoring or promotion was performed |

The default scene includes all 18 runners and four morphs. Camera framing remains
`selected-plus-nearby` with at most six relevant runners; it does not promise every
runner is always on screen. In the controlled normal captures, 18 runners are
visible, with three labels and zero label collisions on both projects. In the
battle-review captures, 14 Android / 17 desktop runners are visible, with two
labels and zero collisions.

## Game Studio capabilities actually used

- **Game Studio routing:** kept the existing engine and lane; routed the requested
  work to UI, sprite review and browser QA instead of adopting the default Phaser
  scaffold.
- **Sprite Pipeline:** applied the existing-frame identity, transparency,
  consistent preview scale, bottom-center slot anchor and in-engine review gates.
  Generated inspection strips from the shipped sheets and audited hashes, alpha
  bounds, source slot layouts and all six live phases for **S/P/E/A**. The common
  scale/anchor applies only to inspection strips, not production assets. No image
  generation or bundled strip-normalization script was used.
- **Game Playtest:** Playwright automation of boot, normal race, dense pack,
  target selection, PUSH/CLEAR, pause/resume, reset and reduced-motion behavior;
  desktop and Pixel 7 emulation screenshots, telemetry, WebM video and JSON test
  outcomes. Existing traffic, lane choice, fair start and 18-runner classification
  checks were retained.
- **Game UI:** larger touch targets, visible keyboard focus, stronger secondary
  label contrast, clearer runner targeting and header, semantic pressed states,
  and reduced nonessential UI motion. Preserved the existing HUD arrangement;
  mobile result text shares the action row to keep the panel compact.

## Validation

| Run | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Initial onboarding subset (primary race, 2.5D, quality, selection) | 22 | 7 | 1 |
| New evaluation tests against unchanged application | 8 | 4 | 0 |
| Evaluation + existing quality/selection tests after changes | 36 | 0 | 0 |

The initial failures were five missing-favicon console failures across pages and
two raw S/E response comparisons. The four evaluation baseline failures identify
small control targets and missing reduced-motion support on both projects.
The after run covers 12 new checks and 24 existing checks. It does **not** rerun
the primary 3D page or `race-2_5d.html`; those files were not changed, and their
favicon issue remains outside this target.

`npm run build` passed. The existing main Three.js bundle size warning remains.
`git diff --check` passed. SHA-256 comparisons verify that all four canonical
concept images, all four shipped run sheets, the canonical reference image,
reference index and 2.5D lock are unchanged.

Tested runtime: Node 24.19.0, npm 11.9.0, Vite 7.3.7, Three.js 0.181.2,
Playwright 1.64.0, system Chromium 151.0.7922.173, FFmpeg 7.1.5.
No dependencies were added and no lockfile was created.

## Evidence

Reviewed evidence is committed under
[`docs/evidence/gamestudio-2p5d-20261010/`](evidence/gamestudio-2p5d-20261010/).

- [`summary.json`](evidence/gamestudio-2p5d-20261010/summary.json): before/after
  test outcomes, control dimensions, captured race telemetry and protected hashes.
- [`before/tests.json`](evidence/gamestudio-2p5d-20261010/before/tests.json) and
  [`after/tests.json`](evidence/gamestudio-2p5d-20261010/after/tests.json): original
  Playwright output, including failures and attachment paths from the actual run.
- Each `before/` and `after/` project folder contains normal and dense-pack
  screenshots, Agent PUSH and reduced-motion screenshots, four FLIGHT runtime
  samples, `motion-review.webm`, `controls-playtest.webm`, UI/scene telemetry and
  sprite audits. The after folders also contain keyboard-focus screenshots and
  four full six-phase source inspection strips.

| View | Before | After |
| --- | --- | --- |
| Android normal race | [Screenshot](evidence/gamestudio-2p5d-20261010/before/android-chromium/race-4600ms.png) | [Screenshot](evidence/gamestudio-2p5d-20261010/after/android-chromium/race-4600ms.png) |
| Desktop normal race | [Screenshot](evidence/gamestudio-2p5d-20261010/before/desktop-chromium/race-4600ms.png) | [Screenshot](evidence/gamestudio-2p5d-20261010/after/desktop-chromium/race-4600ms.png) |
| Android battle review | [Screenshot](evidence/gamestudio-2p5d-20261010/before/android-chromium/dense-pack-4600ms.png) | [Screenshot](evidence/gamestudio-2p5d-20261010/after/android-chromium/dense-pack-4600ms.png) |
| Desktop battle review | [Screenshot](evidence/gamestudio-2p5d-20261010/before/desktop-chromium/dense-pack-4600ms.png) | [Screenshot](evidence/gamestudio-2p5d-20261010/after/desktop-chromium/dense-pack-4600ms.png) |

The complete generated evidence remains at
`artifacts/gamestudio-2p5d/{before,after}/` in the evaluation workspace. This includes
all 24 pinned poses per project per run, per-morph phase telemetry, pause/reset
images, every test's video and failure traces. These bulky generated directories
are ignored; the committed selection above is reviewable after checkout.
Original JSON attachment paths refer to these generated directories, not the
renamed curated video files. Initial onboarding traces are retained at
`/workspace/.cloud-setup/evowild-test/baseline/test-results/`.

## Repeat the workflow

Use the existing isolated checkout; do not create a worktree unless explicitly
requested. From the repository root:

```bash
npm install --package-lock=false
npx playwright install --with-deps chromium
GAMESTUDIO_EVIDENCE_DIR=artifacts/gamestudio-2p5d/latest \
  npx playwright test --config playwright.gamestudio.config.js \
  tests/gamestudio-2p5d.spec.js tests/race-quality.spec.js tests/2p5d-selection.spec.js
npm run build
```

In this cloud environment, use installed system Chromium and the prepared FFmpeg
cache instead of downloading browser artifacts:

```bash
PLAYWRIGHT_BROWSERS_PATH=/workspace/.cache/ms-playwright \
GAMESTUDIO_CHROMIUM_PATH=/usr/bin/chromium \
GAMESTUDIO_EVIDENCE_DIR=artifacts/gamestudio-2p5d/latest \
  npx playwright test --config playwright.gamestudio.config.js \
  tests/gamestudio-2p5d.spec.js tests/race-quality.spec.js tests/2p5d-selection.spec.js

node scripts/gamestudio-2p5d-summary.mjs \
  artifacts/gamestudio-2p5d/before artifacts/gamestudio-2p5d/after \
  artifacts/gamestudio-2p5d/summary
```

The server must not already occupy port 4173; Playwright starts its own server.
Use a new evidence directory for a fresh run so recorded before/after results are
not overwritten. The summary command exits with an error if protected art hashes
change. For a fresh before/after comparison, capture the before run on the base
application with this same evaluation harness, before applying UI changes.

## Limits and unchanged behavior

- S/P/E/A designs, canonical references and all production sprites are untouched.
- The 18-runner field, four morphs, course, race distance, fixed-step simulation,
  acceleration, stamina, traffic, lane choices, camera, frame extraction, cadence,
  runtime anchor/transform logic and classification are unchanged.
- No rejected lane, new race format, new preview lane, new engine, asset-generation
  service or LLM call was introduced. No asset receives a new KEEP decision.
- Android means Pixel 7 Chromium emulation (412×839 CSS px, DPR 2.625); desktop is
  1280×720. Physical Android, portrait/landscape rotation and other browsers remain
  unvalidated. System Chromium uses software WebGL flags; this is not a GPU
  performance benchmark.
- The 4600ms scenes use controlled browser-clock advancement. Initial RAF
  scheduling can shift one simulation step; telemetry records the actual state.
  They are paired review images, not pixel-identical simulation assertions.
- Source sheet previews are raw source slots, with one scale per morph and no
  bbox-based recentering. Runtime shots use the existing connected-body cleanup
  and ground/center correction. Pinned pose screenshots include the existing
  countdown; live-phase loops and videos provide running-motion evidence.
- Browser-artifact downloads were denied by the existing network policy. The
  tests successfully used preinstalled Chromium and system FFmpeg via a local
  Playwright cache link; TLS verification and network policy were not weakened.
- The work is committed and pushed only to the experiment branch. Main is not
  modified or merged by this task. Cloud configuration drafts are separate from
  publication and are not proof of fresh-task restoration.
