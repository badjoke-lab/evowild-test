# EvoWild Run — S Vibe Modeling Work Handoff

Status: ACTIVE
Lane: exp/s-creature-vibe-modeling
Do not modify: feat/s-creature-model
Authoritative remote checkpoint commit at handoff creation: 6417f827b76855c437e3a8250769d04e37b34c60

## Purpose

This file exists so ChatGPT Work can resume the experimental S-type modeling lane from the exact current remote state without replaying old steps or guessing from chat history.

## First actions in Work

1. Pull/fetch the latest remote state of `exp/s-creature-vibe-modeling`.
2. Read:
   - `art/s-creature/S_VIBE_WORK_HANDOFF.md`
   - `art/s-creature/CHECKPOINT.md`
   - `art/s-creature/HANDOFF_STATE.json`
   - `art/s-creature/S_VIBE_GATE_B_METHOD.md`
   - `art/s-creature/S_VIBE_B1_REFERENCE_ANALYSIS.md`
3. Inspect the latest Actions for this branch.
4. Do not trust older chat summaries over the current remote files.
5. Do not modify `feat/s-creature-model`.

## Current exact stage

Latest completed model:
- `art/s-creature/output/S-vibe-b1b-v1.blend`

Latest completed action:
- workflow: `S creature Vibe lane Gate B1b v1 shoulder plane`
- run id: `37184095417`
- result: SUCCESS

Latest result commit:
- `6417f827b76855c437e3a8250769d04e37b34c60`
- message: `art: save Vibe B1b-v1 shoulder plane review`

Current stage:
- **B1b-v1 = REVIEW_PENDING**
- modeling is STOPPED for actual-image review
- do not start a new edit before the review decision

## Why B1b exists

B1a isotropic Taubin relax was exhausted:

- B1a-v1: safe but visually negligible
- B1a-v2: REVISE; visual improvement too small
- B1a-v3: REVISE; max displacement 0.0096155548 near the 0.010 hard limit, residual remained
- B1a-v4: HARD_FAIL before render; max displacement 0.0127101907 > 0.010

Conclusion:
- do not increase relax cycles further
- do not narrow the B1a taper further
- B0-v025 remains the recovery/source baseline
- remaining issue was reclassified as a lateral shoulder-root / chest-side plane problem, not only voxel noise

## B1b-v1 method

Source:
- `output/S-vibe-b0-v025.blend`

Target:
- lateral shoulder-root / chest-side protrusion visible in FRONT34

Method:
- X-axis-only local fairing
- body Y/Z coordinates exact fixed
- topology and vertex count fixed
- symmetric same-side adjacency fairing
- crest and toes fixed

Editable mask:
- Y: -0.12 to 0.18
- Z: 0.80 to 1.12
- |X| >= 0.055

Hard limit:
- max |delta X| <= 0.006

## B1b-v1 validation result

PASS.

- editable vertices: 529
- changed vertices: 527
- max |delta X|: 0.004377767443656921
- mean |delta X|: 0.0003738141986620674
- whole-body X extent drift: 0
- all body Y/Z unchanged: true
- fixed geometry unchanged: true
- crest/toes unchanged: true
- topology unchanged: true
- render hard-scope validation: true

## B1b-v1 review renders

Inspect the actual images, not filenames or metadata:

- `output/review/vibe-b1b-v1/S_vibe_b1b_v1_side.png`
- `output/review/vibe-b1b-v1/S_vibe_b1b_v1_front.png`
- `output/review/vibe-b1b-v1/S_vibe_b1b_v1_front34.png`
- `output/review/vibe-b1b-v1/S_vibe_b1b_v1_rear34.png`
- `output/review/vibe-b1b-v1/S_vibe_b1b_v1_back.png`

Compare primarily against:
- `output/review/vibe-b0-v025/`
- approved repository S references:
  - `references/00_full_reference.png`
  - `references/01_s_body_primary.png`
  - `references/02_s_silhouette.png`

Do not claim to have inspected any separately named "Modeling Image v1.0" unless that file is actually present and opened.

## Required next decision

Work's immediate task is only:

**Review B1b-v1 actual five-view renders and decide KEEP or REVISE.**

Review questions:
- Did FRONT34 shoulder-root protrusion become a cleaner lateral plane?
- Did FRONT/BACK remain narrow enough?
- Did shoulder mass remain readable rather than collapse?
- Did the chest avoid barrel widening?
- SIDE should remain effectively invariant because Y/Z were hard-fixed.
- Is the visual improvement large enough to justify keeping B1b-v1?

## If KEEP

1. Record the KEEP decision in a dedicated review markdown.
2. Update CHECKPOINT and HANDOFF_STATE.
3. Close B1 shoulder/chest shaping only if the reference comparison supports it.
4. Define the next Gate B subtask from the method lock before editing.
5. Use one hypothesis only.

## If REVISE

1. Record the reason with actual-image evidence.
2. Do not accumulate blindly on top of B1b-v1 unless the review explicitly justifies it.
3. Prefer B0-v025 as recovery source unless there is a documented reason to use B1b-v1 as base.
4. Define exactly one next hypothesis with:
   - source
   - target
   - keep_fixed
   - exact_edit
   - expected_visual_change
   - hard_limit
5. Execute only after those fields are locked.
6. Stop after validation + five-view render for another actual-image review.

## Permanent rules

- Experimental lane only: `exp/s-creature-vibe-modeling`
- Never change `feat/s-creature-model` from this workflow.
- Reference -> hypothesis -> edit -> validation -> render -> actual-image review.
- One morphological/anatomical hypothesis per revision.
- No automatic progression across review gates.
- Never mark KEEP from validation alone.
- Never claim to have reviewed an image that was not actually opened.
- B0-v025 is the recovery baseline for B1 unless a later accepted candidate explicitly replaces it.
