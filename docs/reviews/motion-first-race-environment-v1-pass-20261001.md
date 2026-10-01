# Motion First Simplified Race Environment Pass 1 Review — 2026-10-01

Status: **PASS**

Scope:
- simplified Motion First 18-runner race
- race-space distance / finish readability
- low-cost environment structure only
- no gait, contact, morph, LOD representation, or new AUTO director event changes
- no Hunyuan/high-quality, Sakura, sprite, 2.5D, or Lane 5 changes

## Problem

The race motion and AUTO director were already validated through a full 1600 m race, but the world remained visually weak:
- the end of the 1600 m race was not visibly anchored
- long straight sections had weak distance segmentation
- course-side structure was too sparse to support speed/distance perception

The first environment implementation added a full overhead START/FINISH gate. Artifact review rejected that version because the white crossbar dominated the FINISH_FRONT composition.

The first FINISH_FRONT placement was also rejected because the camera remained before the 1600 m line, leaving the finish structure behind the camera.

CI success alone was not accepted as visual PASS.

## Accepted environment structure

### Distance structure

Existing 100 m markers remain.

Added larger mirrored landmarks at:
- 400 m
- 800 m
- 1200 m

These reuse the existing marker InstancedMesh draw.

### START / FINISH

Accepted structure:
- two side pylons
- one ground stripe
- no overhead crossbar

START is at 0 m.
FINISH is at 1600 m.

The finish-line structure also reuses the existing marker InstancedMesh; it does not add a new draw call.

### Mid / far race-space massing

Course-side stand instances were increased and redistributed, with larger structures toward the late-race region.

This retains a single stand InstancedMesh draw.

### FINISH_FRONT composition

For the real FINISH_FRONT event:
- camera is placed beyond the 1600 m line
- accepted profile: `leader-centered-through-line`
- camera looks back across the finish stripe toward the leader
- FINISH stripe remains visible while the leader / field stay readable

This is a targeted correction exposed by the environment artifact, not a new director event.

## Visual result

Accepted artifacts show:
- PACK view has stronger side/reference structure and 400 m scale landmarks
- the racing surface continues to read clearly at distance
- FINISH_FRONT visibly includes the 1600 m stripe instead of hiding the finish behind the camera
- the rejected oversized crossbar is gone
- finish pylons do not block the racing field
- environment remains deliberately simplified rather than pretending to be the high-quality visual lane

## Performance / regression evidence

Final CI:
- standard E2E: PASS — 6 tests
- Motion First capture: PASS — 2 tests
- Sakura regression: PASS — 1 test

Representative simplified-race performance:
- observed average FPS: `21.51`
- p95 frame time: `50.1 ms`
- average EvoWild JS work: `1.70 ms`
- p95 EvoWild JS work: `3.0 ms`
- render calls: `29`
- triangles: `36,940`
- render pixel ratio: `0.75`
- full runners: `0`
- proxy runners: `18`
- pose mode: `canonical-instanced-all`

Render calls remain at the pre-environment level because the new structure reuses existing InstancedMesh draws.

## Decision

**PASS — Environment Pass 1 accepted.**

Next Motion First work should move to player-facing race presentation:
- clear pre-start / running / finish / result states
- final 1–18 order and race time presentation
- focus/winner continuity after finish

Do not expand environmental decoration indiscriminately before the race-result loop is complete.
