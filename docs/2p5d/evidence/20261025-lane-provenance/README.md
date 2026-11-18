# Lane decision provenance — 2026-10-25

PR #132, task 2. Task 1 was committed/pushed at `8499c74` and its checkpoint verified at `e6b27d5` **before** this unit began.

## Behavior

- `runAutonomousAgent` records Agent SHIFT_LINE requests, including rejected requests. `targetSpeedFor` independently records ENGINE lane adjustments. Existing lane choice, safety checks, cooldowns, movement speed and Agent strategy are preserved.
- Each lane event keeps its decision source, starting lane, requested target (or no available target), observed lane, observation time and result. Movement remains PENDING until physical arrival. On interruption/expiry/finish, the result becomes PARTIAL or FAILED. A new owner freezes the earlier event **before** moving; reaching the same target later cannot turn the earlier request into SUCCESS.
- Engine events have a separate expandable live log and a separate saved history section. The upper status panel is labeled as engine running state. Agent results, orb feedback and popup remain tied to Agent decisions.
- Live and saved views use the same observation formatter. UI lane numbers are 1–4; fractional values show position between lanes. The time beside the observation identifies the snapshot, not the runner's position forever afterward.
- Storage adds optional `engineLaneChanges` and Agent lane metadata. Existing v1 histories still load without invented lane observations. Validation rejects invalid sources, lane ranges, observation times and success without arrival. Each source retains up to 30 events; the live view shows the latest five for each source.

## Browser evidence

| Screen | Desktop Chromium | Pixel 7 Chromium emulation |
| --- | --- | --- |
| Real Agent lane request, actual arrival | [Live](lane-live-desktop.png) | [Live](lane-live-android.png) |
| Normal race: rejected Agent request plus separate successful engine movement | [Live](lane-engine-desktop.png) | [Live](lane-engine-android.png) |
| Separate persisted execution logs | [History fixture](lane-history-desktop.png) | [History fixture](lane-history-android.png) |

Live captures use the actual renderer/engine with a controlled browser clock over only the start of a race. The first uses the existing lane-review setup; the engine case uses the normal race start with entrant 4. Neither is presented as a completed race. History captures use an isolated test-only record explicitly named 「表示検証サンプル」. Synthetic results are never included in the game or normal history. Physical Android hardware is untested.

## Validation and limitations

Targeted tests cover rejected Agent → engine success, ownership takeover (including equal targets), pending/partial/failed engine movement, exact record/store/load roundtrip, legacy compatibility, invalid observation rejection, physical lane versus live HUD, history rendering and mobile overflow. Existing Agent outcome and history-layout regressions are included because these paths changed. The completed 54-test suite and full 18-runner race were not manually repeated.

An intermediate local run was invalidated by Vite reloading during an edit. Another new test initially expected a three-lane move within 1.2s; the actual existing 1.9 lanes/s requires about 1.58s. The test now checks PENDING first, then advances 2s and requires actual arrival and SUCCESS; assertions were not removed or weakened. Final result: **26/26 passed** (1.3m); production build **PASS**. Logs are `targeted-tests.log` and `build.log`.

Mock mapping: 06 spectator HUD distinguishes command from execution; 07 separates result/time/command/reason; 08 groups saved history. This is functional log work, not acceptance of mock visual fidelity. Overall graphics remain **REVISE**, including stadium, rear-angle gait, sprite/orb overlap and panel coverage. Original PNGs, hashes, creature assets and specifications are unchanged.
