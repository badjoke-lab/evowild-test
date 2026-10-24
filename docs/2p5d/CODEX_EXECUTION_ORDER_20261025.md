# 2.5D Codex work order — execution, not more mock production

**Stop rewriting plans endlessly. Execute a bounded unit of work, test it, commit/push it on a child branch, and leave meaningful evidence.** Do not automatically merge.

## Gate 0 — Fix the reference handoff first
- `git fetch origin`; inspect live main, PR #131, PR #130 and CI status. Create `codex/2p5d-game-integration-20261025` from `origin/feat/2p5d-autonomous-agent-orbs-20261024` (or another non-colliding child branch).
- Run `python3 scripts/verify_2p5d_mockups.py`. If images missing, import the user-provided ZIP `evowild-2p5d-codex-mockups-originals.zip` preserving file names, then verify hashes. If ZIP inaccessible, report asset-transfer blocker accurately; **do not fabricate a different mock**.
- Read `AGENTS.md`, `docs/design-spec-v0.1.md`, `docs/race-agent-spec-v0.1.md`, reference locks and mock register. No material UI art changes until verified images are present; pure logic/test work may continue.
- Run build and relevant tests and check if baseline failures are pre-existing. Do not rewrite tests just to get a green status.

## Gate 1 — Make vertical slice truthful and robust (first code priority)
- Prove in an actual browser: Home -> 1600m oval -> choose Creature -> 7 setting Race Agent -> race starts automatically -> 18 true finish positions -> saved history -> view result after reload.
- Fix incorrect winner/ranking/elapsed times, reset/pause edge cases, hidden/overlapping mobile navigation, Agent decision vs Creature execution result mismatch. User view must not claim a result that simulation did not produce.
- Add Playwright tests for real 18-runner race completion, persistence, strategy loading, invalid JSON, no unwanted saved result on debug/partial finish, and no manual controls.
- Screenshots/short screen recording for desktop + mobile. KEEP only for mechanics that actually work; visual scene remains REVISE until reviewed.

## Gate 2 — Course is a real oval racetrack, not wild geography
- Keep grandstand, run surfaces, rails, start/finish and corner/lane positions physically tied to oval world coordinates. Follow camera track-turn, no teleportation, bounded gaps.
- Implement actual Course data-to-engine effects only when formula behavior and its assumptions are explicitly documented. `#130` weather/course presets were never approved; do not include automatically.
- Never assume that a visual oval alone resolves race positioning, collisions, congestion, camera or anatomy. Keep existing 18-runner logical data stable.

## Gate 3 — Race Agent orb and readable result (one shared contract)
- `docs/race-agent-spec-v0.1.md` decides semantics: autonomous preconfigured Agent per entrant; orb follows above/behind each Creature. Commands and Creature-resolved results are distinct.
- The mock #01/#02 is the visual comparison. Render orb in screen-space with world/object tracking, line of sight and size constraints on mobile. Command-dependent color, pulse, direction warning and brief result notification must be visible, not just a data-attribute test.
- Exact colors and fancy overlays are aesthetic examples; no ability to manually command during race, no privileged external AI live-control. AI-generated Agent File must pass the same validator.

## Gate 4 — Visual quality & camera (independent blocker)
- **Already REVISE:** side-facing 6-frame sheets become paper-like side billboards under 3/4 chase. Do not promote this as acceptable animation; do not solve by changing S/P/E/A or drawing a fake creature.
- Check existing project-approved references/donors and work on a single candidate in separate visual lane with real foot plant/push/recovery, actual speed, correct angle and silhouettes. Only apply after visual KEEP review in PC+mobile. No new mock generation.

## Gate 5 — Broader game, only as spec becomes authoritative
- Next loop: stable -> training -> breed/parents -> lineage -> retirement -> next generation -> competition histories. Separate proven data contracts from screens.
- Training gain numbers, Creature inventory limits, parent gender restrictions, precise genetics and lifespan remain TBD. Implement no permanent rules based on the illustration.
- Course Builder requires genuine segment/track continuity, on-track race equivalence, local draft import/export and rollback; inspect spec status before implementation.

## Evidence required at every gate
- Branch/commit and PR; steps actually performed; screenshots/recordings produced **by the running game**; desktop & Android; runnable commands; failure triage; explicitly REVISE when criteria unmet.
- Do not merge to main automatically. No spend / paid third-party services. Stop expanding scope once a gate is done, instead of generating more mockups.
