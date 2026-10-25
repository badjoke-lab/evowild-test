# EvoWild Run repository agent rules

These rules apply to every creature implementation lane in this repository, including 2.5D, Motion First, 3D, sprite generation, asset regeneration, and visual experiments.

## Canonical creature design

The repository-wide canonical visual reference is:

- `docs/references/evowild-creature-reference-sheet-20260921.jpg`
- `docs/creature-reference-index-v0.1.md`

S / P / E / A are not free design prompts. They are locked morphological variants of the same species.

Before creating, regenerating, editing, rigging, animating, or promoting any creature asset, read the canonical reference and the relevant lock document.

## Hard rules

- Do not redesign S / P / E / A.
- Do not replace a morph with a different creature merely because it is easier to animate.
- Do not add armor, horns, plates, proportions, head shapes, tails, palettes, or anatomy that are not supported by the canonical reference.
- Do not turn a morph into a recognizable existing animal or unrelated monster.
- Motion donors may contribute pose, gait, timing, contact, recovery, body motion, or phase structure only.
- A donor's visual appearance must never become the target creature appearance unless it already matches the canonical reference.
- Image interpolation, optical flow, or raster deformation cannot justify shape drift.
- A technically smoother animation is a failure if the creature identity drifts from the canonical reference.
- S remains S, P remains P, E remains E, and A remains A in silhouette, body proportions, head family, limbs, tail, and species language.
- Cue Band compatibility remains part of the shared species design.

## Promotion gate

No creature asset may be promoted to production without all of the following:

1. canonical-reference comparison;
2. same-morph identity check;
3. silhouette check at race size;
4. motion / gait check;
5. PC and mobile runtime check where relevant;
6. explicit KEEP decision recorded in the repository.

If visual identity and animation quality conflict, preserve identity and revise the animation. Do not solve animation problems by inventing a different creature.

## 2.5D

For 2.5D specifically, also read:

- `docs/2p5d-creature-reference-lock.md`

P/E/A animation work may use Motion First direct gait states as motion donors, but the final sprite artwork must remain the canonical P/E/A designs.


## 2.5D game-first Codex handoff (2026-10-25)

For any Codex/AI task changing 2.5D racing, courses, Race Agents, UI, stable, training, results or genetics, **first** read the following **before code changes**:

- `docs/2p5d/CODEX_HANDOFF_20261025.md`
- `docs/2p5d/MOCKUP_INDEX_20261025.md`
- `docs/2p5d/CODEX_EXECUTION_ORDER_20261025.md`
- `docs/2p5d/mockups/manifest.json`
- `docs/design-spec-v0.1.md`
- `docs/race-agent-spec-v0.1.md`

The 11 user-supplied screen mocks have fixed SHA-256 checksums. **They are visual references, not new gameplay rules or canonical Creature art.** Verify with `python3 scripts/verify_2p5d_mockups.py` before changing UI visuals. If missing, report the exact blocker and import the authentic images; never fabricate replacements.

Do not introduce countries, real-world racecourses, wilderness course defaults, in-race user commands, currency/levels/ownership/breeding odds invented by an image, or new Creature silhouettes. Work game-first, with visible real browser evidence. Do not merge to `main` or declare visual KEEP without explicit acceptance.

### Anti-drift / anti-tampering policy

- The hashes in `docs/2p5d/mockups/manifest.json` refer to **exact user-submitted files**. Never change hashes, filenames or the verifier/importer logic to make a substituted image pass.
- Do not quietly rewrite `docs/design-spec-v0.1.md`, `docs/race-agent-spec-v0.1.md`, Creature reference locks, the mock register or handoff policy to rationalize an implementation. A correction to a reference requires explicit user authority, and a reviewed, isolated change.
- Every new UI implementation PR must map its modified view to an **existing mock ID** and explicitly label illustrative data as `TBD`, with true real-game desktop/mobile evidence.
- Maintain distinct evidence: **(a)** a verified original mock, **(b)** live runtime screenshot, **(c)** test results, **(d)** user approval. None substitutes for the others.
- If verified original mock PNGs are missing, do not pretend they are present or create replicas. Explicitly report `REFERENCE_IMAGE_MISSING` and use the provided original ZIP import path.

## Codex usage-limit resilience: mandatory checkpoints
**A long uninterrupted job is unsafe: Codex can hit hourly/session limits without an opportunity for a final push.**

Read `docs/2p5d/CODEX_QUOTA_RECOVERY_PROTOCOL.md` and `docs/2p5d/HANDOFF_STATE.json` before editing. This applies to **every** task even if the user prompt omits the instructions.

1. Prefer a bounded unit that can be completed, tested and pushed independently, not a long chain of speculative edits.
2. After **each meaningful edit/working unit or at most 15 minutes of actual work**, whichever happens first, immediately **commit AND push** to the active child branch; save checkpoint state to `docs/2p5d/HANDOFF_STATE.json` on that branch and push that as well. Do not save only locally or rely on an unpushed commit.
3. If limits are nearing, the task is getting long, or remaining tool calls are uncertain: **stop new work**, record the current done/unfinished state, the latest confirmed remote SHA, the failed tests, the exact next operation, and push the checkpoint. Never wait for quota exhaustion.
4. If quota unexpectedly interrupts before a checkpoint, work after the last **verified remote** checkpoint may be lost. On restart, fetch remote and recover actual files before any changes. Never describe unpushed work as saved.
5. For resumption, read the saved checkpoint, inspect `git status`, `git log -5` and `git branch -vv`, confirm origin SHA; continue **the unfinished unit**, do not repeat completed tasks, wipe branches, regenerate mocks or start 3D.
6. Unit completion ≠ global completion. Report blockers/REVISE and partial progress accurately. Do not merge main or run paid services.

The 15-minute value is a *maximum checkpoint interval*, **not** a promise that the tool will remain available for 15 minutes or that it can sense account quota precisely.

