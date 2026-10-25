# 2026-10-25 2.5D playable-loop evidence

Child branch: `feat/2p5d-flow-persistence-20261025` (Draft PR #132, based on #131 at `dcd3f56d0d3187b972ac3919141889a2933b0c9d`). No merge or deployment.

## Original references

Both user-attached split ZIPs were downloaded successfully (19,899,200 and 16,622,054 bytes). The eleven PNG byte streams were combined in a temporary ZIP so the unchanged repository importer could validate all eleven atomically. `python3 scripts/verify_2p5d_mockups.py` passes all eleven SHA-256 values. No reference, hash, importer or verifier was changed. Original PNGs were pushed in `f904fd95a210d21c978d49320f60df7e90810a17`; GitHub contents API confirmed all eleven filenames and sizes.

## Actual browser journey

`tests/game-loop-2p5d.spec.js` operates home → course → entrant #4 → seven-field CLOSER Agent → normal 1600m race → all 18 finish → history → reload. The full journey uses real runtime frames, no finishReview, no injected result, no accelerated clock and no manual race commands. The pause assertion also confirms that no record is created while the race is incomplete. Displayed IDs/times are compared to the saved record; the record is unchanged after repeated reloads. Agent JSON export/import/reload, malformed/unknown-field/oversized input rejection, reset and navigation aborts are covered separately.

Desktop uses Chromium at 1280×720. Android uses Playwright Pixel 7 Chromium emulation (touch/mobile/device scale), not physical-device hardware. PNGs are direct, unedited browser screenshots. Local Chromium is `/usr/bin/chromium`; bundled Playwright Chromium was absent and its download domain was blocked. The temporary local config changes only the executable path and test/output paths; CI uses the repository config.

| Stage | Original mock | Desktop evidence | Android emulation evidence |
|---|---|---|---|
| Pre-race settings | [02](../../mockups/02-race-agent-settings.png), [05](../../mockups/05-race-entry.png) | [setup](loop-setup-desktop-chromium.png) | [setup](loop-setup-android-chromium.png) |
| Running on the oval | [01](../../mockups/01-race-agent-orb-race.png) | [race](loop-race-desktop-chromium.png) | [race](loop-race-android-chromium.png) |
| Real classification | [07](../../mockups/07-race-results.png) | [results](loop-results-desktop-chromium.png) | [results](loop-results-android-chromium.png) |
| Reloaded local history | [07](../../mockups/07-race-results.png), [08](../../mockups/08-pedigree-history.png) | [history](loop-history-desktop-chromium.png) | [history](loop-history-android-chromium.png) |

Illustrative mock names, race distances/laps, ages, training numbers, economy and breeding rules remain TBD. They were not adopted. The existing prototype keeps its single 1600m oval and 18 demo entrants.

## Findings and quality gate

- **KEEP (tested mechanics only):** interpolated within-step finish order, actual stored times/ranks, full player journey, repeated reload/deduplication, Agent File roundtrip/validation, pause and aborted-run exclusion. A same-tick crossing previously gave the first array entry the better place; regression coverage now proves a later array entry crossing earlier gets the better rank.
- **REVISE (visuals):** the six-frame side sprites remain side billboards in the rear camera; overlapping bodies make each runner/foot contact difficult to read. These screenshots do not prove an acceptable contact/push/recovery/flight/reach cycle. Proper same-morph rear-angle locomotion still needs a separate reviewed candidate. No asset was promoted or redesigned.
- **REVISE (stadium):** oval world geometry, rails and start/finish stripe exist, but stands are sparse primitives and not consistently in view; the runtime is far below the approved stadium detail. The course diagram/marker alignment and full-lap scenery merit a follow-up visual pass.
- **REVISE (UI):** every rendered runner receives an orb and the browser asserts orb count equals visible-runner count; pack occlusion limits readability. The full field is not always simultaneously in camera. Result analysis lacks the mock's real stamina graph/replay, and the desktop result panel requires scrolling. Mobile navigation is operable, but panels remain visually heavy.
- **Unimplemented/TBD:** actual stable ownership, training, inheritance, breeding/economy rules, remote history/sync, replay and production-quality locomotion. No example mock values were used as final rules.

## Baseline and failure separation

Parent-head Actions [40152147602](https://github.com/badjoke-lab/evowild-test/actions/runs/40152147602) at `dcd3f56`: build passed, **63 passed / 4 failed / 81 skipped**. The handoff's three known failures remain (desktop and Android `race-quality.spec.js:47` PUSH comparison; desktop `motion-first.spec.js:3146` agility threshold). The additional Android `race-quality.spec.js:125` pressure assertion also failed on the parent before these changes. Reference-only checkpoint Actions [40153348139](https://github.com/badjoke-lab/evowild-test/actions/runs/40153348139) reproduced the same four failures.

Local pre-change targeted run: 33 passed; one desktop screenshot teardown failed because a second local Playwright invocation overlapped and cleared the shared artifact directory. Subsequent suites run sequentially. The first new full-journey test incorrectly selected a diagnostic `data-agent-command` on the stage as an input; the selector was corrected to actual buttons, and both full journeys passed. See `initial-tests.log` and `full-journey.log`. Existing tests were not deleted or relaxed.

Full-game visual acceptance and physical Android testing remain outstanding. A passing build or test does not grant visual KEEP.
