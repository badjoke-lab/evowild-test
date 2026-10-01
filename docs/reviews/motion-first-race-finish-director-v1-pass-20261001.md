# Motion First Simplified Race Finish Director v1 Review — 2026-10-01

Status: **PASS**

Scope:
- simplified Motion First 18-runner race
- Phase F AUTO director finish sequence
- FINAL_CHASE / FINISH_SIDE / FINISH_FRONT
- no gait, contact, morph, LOD, speed-cue, Sakura, sprite, 2.5D, or Lane 5 changes

## Review method

The finish sequence is reviewed through the dedicated deterministic URL mode:

`preview-motion-first-race/index.html?finishReview=1`

The test waits for each real director reason instead of capturing at fixed wall-clock times.

Required order:
1. `FINAL_CHASE:CHASE`
2. `FINISH_SIDE:SIDE`
3. `FINISH_FRONT:FRONT`

For every stage:
- director focus id must match the selected runner
- the expected camera reason must be active before capture
- the finish-front profile must report `leader-centered`

## Visual result

FINAL_CHASE:
- leader remains identifiable in race context
- field depth and closing race structure remain visible
- the shot does not collapse into a single isolated runner

FINISH_SIDE:
- leader and pursuing field remain readable together
- SIDE composition preserves the relative gap and finish approach
- no major foreground occlusion blocks the leader

FINISH_FRONT:
- leader remains full-body readable in the foreground
- pack remains behind as finish context
- camera is centered on the active leader rather than a stale focus
- composition reads as an approach/finish shot rather than an accidental close-up

## Performance / regression evidence

Final PR CI:
- standard E2E: PASS
- Motion First capture: PASS
- Sakura NPR capture: PASS

Representative performance sample:
- observed average FPS: `24.12`
- p95 frame time: `50.1 ms`
- average EvoWild JS frame work: `1.38 ms`
- p95 EvoWild JS frame work: `1.8 ms`
- render calls: `29`
- triangles: `36,724`
- proxy runners: `18`
- render pixel ratio: `0.75`

## Decision

**PASS — three-stage AUTO finish sequence accepted.**

The next Motion First task should be an end-to-end full-race director review, then environment/readability work. Do not add more director event types unless that full-race review exposes a specific storytelling gap.
