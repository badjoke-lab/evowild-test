# 2026-10-25 2.5D playable-loop evidence

Child branch: `feat/2p5d-flow-persistence-20261025` (Draft PR #132, based on #131 at `dcd3f56d0d3187b972ac3919141889a2933b0c9d`). No merge or deployment.

## Original references

Both user-attached split ZIPs were downloaded successfully (19,899,200 and 16,622,054 bytes). The eleven PNG byte streams were combined in a temporary ZIP so the unchanged repository importer could validate all eleven atomically. `python3 scripts/verify_2p5d_mockups.py` passes all eleven SHA-256 values. No reference, hash, importer or verifier was changed. Original PNGs were pushed in `f904fd95a210d21c978d49320f60df7e90810a17`; GitHub contents API confirmed all eleven filenames and sizes.

## Recovery and final results

Resumed from remote checkpoint `c040191fc19fbc0eb0925e4231fe9d4dc5e61675` by fast-forward, preserving that externally saved interruption record. The pending local suite had already completed: **54 passed (2.9m)**. Its log and latest PNGs were recovered without rerunning imports, fixes or completed races. Screenshots now correspond to source `ad0756349d707945da71588be2e93cdfd912ca7c` (same game source as `c0acb5f`).

- [Combined local suite](final-targeted.log): 54/54 PASS across desktop and Android emulation.
- [Latest verified Actions](https://github.com/badjoke-lab/evowild-test/actions/runs/40153976228) at `ad07563`: build PASS; **84 passed / 3 failed / 81 skipped**, overall FAILURE. [Extracted log](actions-summary.log). All new tests passed; remaining failures are the original three legacy assertions. The extra parent-head pressure assertion passed in this run.
- [Agent outcomes](agent-outcome.log): 10/10 PASS, including actual lane request → PENDING → arrival → SUCCESS on both browser projects. The lane integration test advances the browser clock; the full race journey below does not.
- No existing tests, balances, canonical art or specification/hash files were modified. This recovery only archives existing evidence and updates checkpoint/PR documentation.

## Actual browser journey

`tests/game-loop-2p5d.spec.js` operates home → course → entrant #4 → seven-field CLOSER Agent → normal 1600m race → all 18 finish → history → reload. The full journey uses real runtime frames, no finishReview, no injected result, no accelerated clock and no manual race commands. The pause assertion also confirms that no record is created while the race is incomplete. Displayed IDs/times are compared to the saved record; the record is unchanged after repeated reloads. Agent JSON export/import/reload, malformed/unknown-field/oversized input rejection, reset and navigation aborts are covered separately.

Desktop uses Chromium at 1280×720. Android uses Playwright Pixel 7 Chromium emulation (touch/mobile/device scale), not physical-device hardware. PNGs are direct, unedited browser screenshots. Local Chromium is `/usr/bin/chromium`; bundled Playwright Chromium was absent and its download domain was blocked. The temporary local config changes only the executable path and test/output paths; CI uses the repository config.

| Stage | Original mock | Desktop evidence | Android emulation evidence |
|---|---|---|---|
| Home | [03](../../mockups/03-home.png) | [home](game-home-desktop-chromium.png) | [home](game-home-android-chromium.png) |
| Course | [04](../../mockups/04-course-selection.png) | [course](game-course-desktop-chromium.png) | [course](game-course-android-chromium.png) |
| Entrant selection | [05](../../mockups/05-race-entry.png), [09](../../mockups/09-creature-stable.png) | [entrants](game-creatures-desktop-chromium.png) | [entrants](game-creatures-android-chromium.png) |
| Pre-race settings | [02](../../mockups/02-race-agent-settings.png), [05](../../mockups/05-race-entry.png) | [setup](loop-setup-desktop-chromium.png) | [setup](loop-setup-android-chromium.png) |
| Running on the oval | [01](../../mockups/01-race-agent-orb-race.png) | [race](loop-race-desktop-chromium.png) | [race](loop-race-android-chromium.png) |
| Real classification | [07](../../mockups/07-race-results.png) | [results](loop-results-desktop-chromium.png) | [results](loop-results-android-chromium.png) |
| Reloaded local history | [07](../../mockups/07-race-results.png), [08](../../mockups/08-pedigree-history.png) | [history](loop-history-desktop-chromium.png) | [history](loop-history-android-chromium.png) |

Illustrative mock names, race distances/laps, ages, training numbers, economy and breeding rules remain TBD. They were not adopted. The existing prototype keeps its single 1600m oval and 18 demo entrants.

## Findings and quality gate

- **KEEP (tested mechanics only):** interpolated within-step finish order, actual stored times/ranks, full player journey, repeated reload/deduplication, Agent File roundtrip/validation, pause and aborted-run exclusion. Agent lane requests remain pending until actual lane arrival; popup, live log and history share the observed result. A same-tick crossing previously gave the first array entry the better place; regression coverage now proves a later array entry crossing earlier gets the better rank.
- **REVISE (visuals):** the six-frame side sprites remain side billboards in the rear camera; overlapping bodies make each runner/foot contact difficult to read. These screenshots do not prove an acceptable contact/push/recovery/flight/reach cycle. Proper same-morph rear-angle locomotion still needs a separate reviewed candidate. No asset was promoted or redesigned.
- **REVISE (stadium):** oval world geometry, rails and start/finish stripe exist, but stands are sparse primitives and not consistently in view; the runtime is far below the approved stadium detail. The course diagram/marker alignment and full-lap scenery merit a follow-up visual pass.
- **REVISE (history readability):** the real mobile history screenshot exposes concatenated time/command/result/reason text in `.agent-history-list`; this requires a small layout fix, not a replay of the already-tested race flow.
- **Follow-up logic audit:** `targetSpeedFor` can initiate an opportunistic lane change separately from `runAutonomousAgent`. A live screenshot shows COMPLETE SHIFT alongside a failed Agent request. The resolved request result is now truthful, but provenance of these separate engine lane changes still needs one shared logging path and focused coverage. This path predates this PR; no final claim that every movement is explained by its Agent log.
- **REVISE (UI):** every rendered runner receives an orb and the browser asserts orb count equals visible-runner count; pack occlusion limits readability. The full field is not always simultaneously in camera. Result analysis lacks the mock's real stamina graph/replay, and the desktop result panel requires scrolling. Mobile navigation is operable, but panels remain visually heavy.
- **Unimplemented/TBD:** actual stable ownership, training, inheritance, breeding/economy rules, remote history/sync, replay and production-quality locomotion. No example mock values were used as final rules.

## Baseline and failure separation

Parent-head Actions [40152147602](https://github.com/badjoke-lab/evowild-test/actions/runs/40152147602) at `dcd3f56`: build passed, **63 passed / 4 failed / 81 skipped**. The handoff's three known failures remain (desktop and Android `race-quality.spec.js:47` PUSH comparison; desktop `motion-first.spec.js:3146` agility threshold). The additional Android `race-quality.spec.js:125` pressure assertion also failed on the parent before these changes. Reference-only checkpoint Actions [40153348139](https://github.com/badjoke-lab/evowild-test/actions/runs/40153348139) reproduced the same four failures.

Local pre-change targeted run: 33 passed; one desktop screenshot teardown failed because a second local Playwright invocation overlapped and cleared the shared artifact directory. The final combined suite ran sequentially and all 54 tests passed, including that screenshot test. The first new full-journey test incorrectly selected a diagnostic `data-agent-command` on the stage as an input; the selector was corrected to actual buttons, and both full journeys passed. See `initial-tests.log` and `full-journey.log`. Existing tests were not deleted or relaxed.

Full-game visual acceptance and physical Android testing remain outstanding. A passing build or test does not grant visual KEEP.

## Next bounded work

1. Fix mobile history log column/spacing/wrapping for time, command, result and reason (mock 07/08); reuse the saved evidence and isolate validation to this view. Then reconcile the separate engine lane-planning path with Agent logging without inventing new command semantics.
2. Improve spectator readability of the existing oval: validate stands/start-finish/rails over a full lap and reduce runner/orb overlap at race size on PC and mobile. Preserve the existing course and canonical creature identity; compare mocks 01/06.
3. Track the three legacy failing tests in their own follow-up; do not change command balance or a test threshold merely to turn CI green.
4. Proper rear-angle gait needs a separately reviewed canonical-morph candidate; the current side sheets remain REVISE. Training/genetics/economy continue to require approved rules.
