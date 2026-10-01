# Motion First Simplified Race Results v1 Review — 2026-10-01

Status: **PASS**

Scope:
- simplified Motion First 18-runner race
- final 1600 m classification and result presentation
- no gait, contact, morph, LOD, AUTO event, environment geometry, Sakura, sprite, 2.5D, or Lane 5 changes

## Problem

The race previously stopped as soon as the leader crossed 1600 m and only changed the status to `FINISHED`.

That left no real race-result loop:
- no recorded finish time
- no 1–18 classification
- no winner continuity
- no field-complete state
- a completed race could be resumed through PAUSE

## Accepted finish model

Each runner records its own `finishTime` when crossing 1600 m.

The crossing time is interpolated within the fixed 60 Hz simulation step rather than using the coarse end-of-step time.

After a runner finishes:
- its race target speed becomes zero
- it decelerates
- its distance is capped just beyond the finish

The first finisher becomes the declared winner and remains the director focus while the remaining runners complete the race.

The race reaches final `FINISHED` state only after all 18 runners have recorded a finish time.

## Final classification

The result order is sorted by:
1. finish time
2. runner id as deterministic tie-break

The final result panel shows:
- winner runner / morph
- winning time
- field-complete time
- 1–18 classification
- each runner's morph and finish time

Result data is also exposed through:
- `data-result-ready`
- `data-winner-declared`
- `data-winner-id`
- `data-winning-time`
- `data-final-classification`

## Interaction

On completed race:
- PAUSE is disabled
- completed race cannot be resumed accidentally
- RESTART clears result data and hides the panel
- normal running state is restored

## Visual evidence

Accepted result artifact:
- winner: Runner 03 / E / ENDURE
- winning time: `0:14.478` in deterministic finish-review mode
- classification panel remains readable without covering the entire race view
- leader / field remain visible behind the result panel
- 18 result rows are available through the scrollable classification
- finish stripe and finish environment remain readable behind the result UI

## Validation

Automated result gates verify:
- result state reaches `FINISHED`
- result panel becomes visible
- exactly 18 classification rows exist
- winner id matches classification row 1
- winning time matches classification row 1
- classification ranks run from 1 through 18
- finish times are monotonic
- RESTART hides/clears the result state
- PAUSE is enabled again after restart

## Performance / regression evidence

Final code CI:
- standard E2E: PASS — 6 tests
- Motion First capture: PASS — 2 tests
- Sakura regression: PASS — 1 test

Representative performance:
- observed average FPS: `26.06`
- p95 frame time: `50.0 ms`
- average EvoWild JS work: `1.69 ms`
- p95 EvoWild JS work: `2.5 ms`
- render calls: `29`
- triangles: `36,940`
- full runners: `0`
- proxy runners: `18`
- render pixel ratio: `0.75`

## Decision

**PASS — final 18-runner race classification and result presentation accepted.**

Next work should move to pre-start / start presentation and then the actual player-facing Race Agent command loop. Do not spend another pass on result cosmetics before command/state gameplay is connected.
