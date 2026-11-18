# Agent history readability — 2026-10-25

PR #132, task 1. These are real browser captures of the game history screen using an **isolated UI fixture**, named 「表示検証サンプル」. They are not evidence of another completed race. The fixture exists only in tests; production does not load it. Genuine completed-race evidence remains in `../20261025-flow/`.

| Browser | Before | After |
| --- | --- | --- |
| Desktop Chromium, 1280×720 viewport | [Before](before-desktop.png) | [After](after-desktop.png) |
| Pixel 7 Chromium emulation | [Before](before-android.png) | [After](after-android.png) |

Before: time/command/result/reason run together. An unbroken long reason expands the card beyond the viewport on both projects. After: labeled definition-list fields, bordered execution badges, and a separate wrapping reason row. The same layout regression fails before the fix and passes after. Mobile additionally checks a 320px viewport; no horizontal overflow or overlapping value boxes. The archive data remains unchanged after display. Physical Android hardware was not tested.

## Reference comparison

- Mock 07 (`../../mockups/07-race-results.png`): preserves the readable separation of decision time, command, result and reason, adapted to compact history cards. Execution results retain the existing recorded values, without adopting mock example numbers as rules.
- Mock 08 (`../../mockups/08-pedigree-history.png`): keeps the dark navy panels, cyan hierarchy, and grouped history information. This task does not implement pedigree, breeding, or unknown numerical rules.
- **Readability behavior validated; overall graphics remain REVISE. No visual approval is implied.** Full mock composition, stadium, rear-view sprites, gait, and orb readability are not approved by these UI tests.

Validation: focused Playwright test passes on desktop and Android (2/2); Vite production build passes. The old 54-test suite and full 18-runner race were not repeated. System `/usr/bin/chromium` used through the local Playwright config because the bundled browser download is unavailable in this environment.
