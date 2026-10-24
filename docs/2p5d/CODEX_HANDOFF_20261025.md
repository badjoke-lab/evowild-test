# EvoWild Run — Codex handoff: 2.5D GAME FIRST

**Snapshot:** 2026-10-25 (JST)
**Required repo:** `badjoke-lab/evowild-test`
**Start from:** `origin/feat/2p5d-autonomous-agent-orbs-20261024`
**Working PR:** [#131](https://github.com/badjoke-lab/evowild-test/pull/131) — DRAFT / REVISE, not approved.
**Main branch at handoff:** `cde1bd7c8a26637d587aafd6d1d8cc4da8fb0315` (verify live on entry; do not infer it never changes).
**Separate unapproved PR:** [#130](https://github.com/badjoke-lab/evowild-test/pull/130), course presets and builder proposal. Do NOT merge/cherry-pick it as accepted spec.
**Source-of-truth hierarchy:** `AGENTS.md` / `docs/2p5d-creature-reference-lock.md` / `docs/design-spec-v0.1.md` / `docs/race-agent-spec-v0.1.md` > *approved visual purpose of* mockups in `MOCKUP_INDEX_20261025.md` > current experimental code / PR opinions. No document here grants permission to override an explicit earlier FIXED constraint.

## Mission and current limits

The user explicitly asked to stop endless Creature-only work and build the **entire game** on the 2.5D lane while 3D remains blocked. No new image mocks. Visual look is based on 11 supplied examples, but **not all numbers and speculative systems drawn in them are agreed requirements**.

Main functionality to close next: Home -> oval Course choice -> Creature entry -> **pre-race seven-field Agent** -> autonomous observed race with visible orbs -> actual finish classification -> saved real results/Agent history -> home/history. Then extend stable, training, genetics, retirement, breeding, user Course Builder **only once their rules are based on approved spec, not invented from mock captions**.

## Must-read order (Codex, before edits)

1. `AGENTS.md`
2. `docs/2p5d/CODEX_HANDOFF_20261025.md` (this file)
3. `docs/2p5d/MOCKUP_INDEX_20261025.md` and `docs/2p5d/mockups/manifest.json`; validate available PNGs with `python3 scripts/verify_2p5d_mockups.py`
4. `docs/design-spec-v0.1.md`
5. `docs/race-agent-spec-v0.1.md`
6. `docs/2p5d-creature-reference-lock.md`
7. `docs/2p5d/CODEX_EXECUTION_ORDER_20261025.md`
8. Git/CI and source code named below.

## Verified implementation map — no blanket "complete"

| File | What it actually does | Limitations |
|---|---|---|
| `game-2p5d.html`, `src/game_shell_2p5d.{js,css}` | Connected home, one oval Course selection, 18 demo runner list, local race history | Not production ownership/stable; no breeding/training |
| `race-stadium.html`, `src/race_stadium.{js,css}` | Reuses existing fixed-step 18-runner simulator; pre-race selection, autonomous Agents, orbs, finish view | 3/4 view has side-facing sprite billboards; visual REVISE |
| `src/oval_course_2p5d.js`, `src/oval_render_2p5d.js` | 1600m closed oval positions, track/rail geometry, camera, minimap | Simplified stands; multiple visuals overlap; look not approved |
| `src/race_agent_v1.js`, `src/race_agent_profile_store.js` | Common 7 fields / validator / strategy presets / JSON import-export and local profile storage | Prototype schema and command tuning; not finalized external Agent File contract |
| `src/game_progress_2p5d.js` | Local demo participant selection, versioned 18-runner finished race archive, actual Agent decision history | LocalStorage, no remote authority, no async competition |
| `race-quality.html`, `src/race_quality.js` | Existing independent side-race demo on main, unchanged | Historical manual command test UI; not the desired player-facing Agent workflow |
| `docs/references/evowild-creature-reference-sheet-20260921.jpg`, `public/concept/` | Canonical Creature visual authority | Never replace with mock-derived character pictures |

## Last known test evidence

- GitHub Actions [run 40110098267](https://github.com/badjoke-lab/evowild-test/actions/runs/40110098267) at handoff: **64 passed, 3 failed, 81 skipped**, overall **FAILURE**. Failing tests: both desktop and Android historical `tests/race-quality.spec.js:47` Agent PUSH comparison, and desktop `tests/motion-first.spec.js:3146` agility threshold. These should be independently confirmed: do not simply delete tests or pretend full CI is green.
- New `tests/game-shell-2p5d.spec.js`, `tests/race-stadium-agent.spec.js`, and `tests/oval-course-2p5d.spec.js` verify local journey/Agent/camera/geometry and run on desktop + Android. A previous Android navigation overlay obstruction was corrected by `#preRacePanel .setup-back-link`.
- Real screenshots exist in GitHub Actions artifacts (`motion-first-race-visuals`), including 2.5D game screens, oval screenshots, and failure traces. **Review screenshots, not only green PASS numbers.** They were judged REVISE: side sprites overlap; no approved 3/4 gallop; simplified stadium. No doctored renders.
- Final known PR head when preparing this handoff: `ad59b2216816cf22b020fc3a254164b4643f5ba7` (recheck after this documentation commit).

## Hard constraints (violations => REJECT)

- Do NOT merge/push to `main`, reset/destroy branches, force-update, delete prior experiments, incur paid compute/API costs, or substitute new Creature art. Codex works in a **new child feature branch** off PR #131, creates its own DRAFT PR, preserving #131 for comparison (unless explicit approval to extend it).
- Do NOT render arbitrary wilderness courses, countries, real racing circuits, championships, costs, wallets, currencies, ownership limits, training increments, breeding odds, or user rankings simply because a mock shows them.
- Do NOT add manual in-race PUSH/SHIFT controls to player flow. Every entrant gets a common Race Agent, running after start without user input. The existing separate manual test page is a legacy review harness, not authority for a gameplay redesign.
- Do NOT claim 3D/3/4 animation is ready because the 2.5D camera follows an oval; current sprites show their side. No frozen cutouts, raster warps, missing foot contact, identity drift or unverified generated images may be promoted as final.
- Do NOT choose exact inherited genetics, Creature age/lifespan, training costs, asynchronous fairness or economics without a written SPEC FIXED/CURRENT basis and explicit review; implement isolated prototypes if needed and label them.
- Do NOT write a success statement without commit SHA, CI URLs, real screenshots/recordings, and honest KEEP/REVISE status.
- Do NOT assume screenshot mock text, example statistics, arbitrary logos, invented property rights or Agent orb color legend is a gameplay contract.

## Known engineering checks that merit investigation

1. Verify the **recorded Agent result** is the real Creature-resolved outcome (see `resolveAgentCommand` and `runAutonomousAgent`); pending/expired decision classifications must not be silently marked success.
2. Validate final rank uses real `finishPlace` rather than sorting all finishers on capped distance 1600m.
3. Confirm a completed race saves exactly once and only if 18 genuinely finish; review/instant-finish/paused/reset navigation must not produce history.
4. `game-2p5d.html` is localStorage demo with 18 created participant identities; do not represent them as actual user-owned Creatures.
5. Ensure per-Creature Agent File upload is validated identically to UI file, cannot execute JS, and preserves a strategy after reload.
6. Check mobile overlay/controls; mock's HUD is not a license to cover game action with panels.
7. Verify path `/evowild-test/` in Playwright/Vite. This test branch is not deployed by main GitHub Pages automatically. Never claim a live Pages URL without actual deployment verification.
8. Confirm user mock images exist **on the Codex checkout**. If absent, the manifest SHA register and user-attached ZIP are the recovery procedure. Do not reconstruct.

## Exit criteria for an individual Codex session

Report: `base SHA` / `head SHA` / changed files / PR / build and targeted E2E status / count and nature of unrelated failures / real desktop & mobile visual evidence / gameplay paths tested / unresolved blockers. Finish with KEEP or REVISE per feature, not an unjustified one-word overall success.
