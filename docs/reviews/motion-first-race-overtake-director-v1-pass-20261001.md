# Motion First Simplified Race Overtake Director v1 Review — 2026-10-01

Status: **PASS**

Scope:
- simplified Motion First 18-runner race
- Phase F AUTO director
- explicit overtake-attempt storytelling
- no gait, contact, morph, LOD, speed-cue, Sakura, sprite, 2.5D, or Lane 5 changes

## Problem

AUTO previously had lane-change and lead-change events, but no event that represented a runner actually closing on the runner immediately ahead.

A lane change alone is not treated as an overtake.

## Detection

Within the top eight, adjacent ranking pairs are reviewed for:
- gap between `0.65 m` and `4.8 m`
- challenger closing speed at least `0.35 m/s`
- same / adjacent-lane proximity within `1.35` lane widths

When all conditions are true:
- focus = challenger
- camera = SIDE
- reason = `OVERTAKE_ATTEMPT`
- hold = `2.6 s`

Immediate repeated `OVERTAKE_ATTEMPT:SIDE` shots are blocked by the persistent-shot regression rule.

## Deterministic-race validation

The first ~12 s review window correctly produced no false overtake event.

The same deterministic race was therefore allowed to continue to ~28 s rather than weakening the thresholds.

Observed extended director history:

`ACCELERATION:LOW, PACK_COMPRESSION:PACK, BREAKAWAY:LOW, RACE_FLOW:CHASE, BREAKAWAY:LOW, OVERTAKE_ATTEMPT:SIDE, LANE_MOVE:LOW, OVERTAKE_ATTEMPT:SIDE, BREAKAWAY:LOW, OVERTAKE_ATTEMPT:SIDE, BREAKAWAY:LOW`

This confirms:
- a real closing pair is required
- overtake attempts are not fired during the opening pack without evidence
- repeated attempts are separated by other race events
- the director does not lock on SIDE

## Visual result

Artifact review of the first overtake interval shows:
- Runner 08 (A), rank 7, selected as challenger focus
- SIDE composition keeps the challenger and nearby pack visible together
- race context is preserved rather than isolating only the leader
- the shot reads as a mid-pack contest, which was missing from the previous director

## Performance / regression evidence

Final CI:
- standard E2E: PASS
- Motion First capture: PASS
- Sakura NPR capture: PASS

Performance sample:
- observed average FPS: `21.51`
- p95 frame time: `50.1 ms`
- average EvoWild JS frame work: `1.83 ms`
- p95 EvoWild JS frame work: `2.5 ms`
- render calls: `29`
- triangles: `36,724`
- proxy runners: `18`
- render pixel ratio: `0.75`

## Decision

**PASS — explicit OVERTAKE_ATTEMPT event accepted.**

The next director review should address another race-storytelling gap rather than broadening this detector into generic lane movement.
