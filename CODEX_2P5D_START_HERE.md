# Codex: 2.5D GAME FIRST — START HERE

Use this repository as the source of truth. **Do not start a new model-generation lane or make any new image mock.**

**Work base:** `origin/feat/2p5d-autonomous-agent-orbs-20261024` (Draft PR [#131](https://github.com/badjoke-lab/evowild-test/pull/131), visual status REVISE). Main is NOT the working branch. Do not merge #130 or #131 without user approval.

1. Read [AGENTS.md](AGENTS.md) then [Codex full handoff](docs/2p5d/CODEX_HANDOFF_20261025.md), [execution order](docs/2p5d/CODEX_EXECUTION_ORDER_20261025.md), [mock register](docs/2p5d/MOCKUP_INDEX_20261025.md) and existing [game spec](docs/design-spec-v0.1.md) / [Race Agent spec](docs/race-agent-spec-v0.1.md).
2. **11 actual user-shared PNGs were not uploaded into GitHub by this handoff.** Use the independently supplied `evowild-2p5d-codex-mockups-originals.zip` attachment, which preserves exact original bytes. Import by running `python3 scripts/import_2p5d_mockups.py /path/to/the.zip`, then `python3 scripts/verify_2p5d_mockups.py`. When it passes, commit these exact PNG files in the Codex branch.
3. If ZIP is inaccessible, report `REFERENCE_IMAGE_MISSING` and do not redesign based on invented screenshots. Logic/testing work independent of images may proceed.
4. No countries, real-world racetracks, wilderness presets, live player Agent commands, new Creature designs, NFT Creature issuance, pay-to-win, or invented numeric training/genetic rules.
5. Implement and test the **whole** existing 2.5D playable loop, not isolated art: Home → oval Course → select runner → 7-field autonomous Race Agent → full 18-entrant race → actual result → local history. Correct incorrect data/GUI behavior. Then work on other game systems only with documented spec status.
6. Keep all proposed work on an independent child branch + DRAFT PR; record build/Playwright (desktop and Android) and real screenshots, KEEP/REVISE. Do not automatically merge.

Copy-ready prompt: [CODEX_START_PROMPT_20261025.txt](docs/2p5d/CODEX_START_PROMPT_20261025.txt).

**Handoff status**: instructions and checksum-verified mock manifest are committed; binary images are an explicit handoff attachment, not falsely claimed as committed. 
