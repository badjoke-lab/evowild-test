# Motion First Simplified Race Acceleration Director v1 Review — 2026-10-01

Status: **PASS**

Scope:
- simplified Motion First 18-runner race only
- Phase F AUTO director
- launch / acceleration storytelling
- no gait, stance/contact, morph geometry, LOD, Sakura, sprite, 2.5D, or Lane 5 changes

## Problem

Phase F listed acceleration as a race event, but AUTO previously moved from the opening START/PACK shot directly into generic race events.

The first acceleration implementation correctly emitted `ACCELERATION:LOW`, but visual review rejected several camera placements:
- rear LOW allowed the focus runner / nearby runner to dominate the foreground
- outward front-quarter placement could push an edge-lane leader shot toward the grass
- too-close lead framing could crop the long S silhouette

CI success alone was not accepted as a visual pass.

## Accepted event behavior

After the opening START shot, AUTO may emit exactly one acceleration shot when:
- race time is below `7.2 s`
- leader speed is above `7.0 m/s`
- `targetSpeed - speed > 0.75 m/s`

Accepted shot:
- camera: `LOW`
- reason: `ACCELERATION`
- hold: `2.0 s`
- one-shot per race reset

The shot uses the already-approved speed cues and speed-linked FOV. It does not exaggerate gait or add stronger shake.

## Accepted camera composition

Final AUTO LOW profile:
- `lead-front-quarter-inboard`
- camera remains ahead of the leader
- lateral position is moved toward track center rather than farther outside the leader lane
- camera X is clamped inside the track
- full S silhouette remains visible through the acceleration interval
- surrounding runners remain race context rather than foreground occluders

AUTO camera-mode changes continue to use clean broadcast cuts instead of long free-camera travel.

## Visual evidence

Final AUTO sequence was reviewed at approximately:
- 4.0 s — START / PACK
- 4.5 s — cut into acceleration lead shot
- 4.8–6.3 s — ACCELERATION / LOW
- 6.5 s — return to PACK / normal race flow

Final evidence:
- no off-track grass-side acceleration composition
- no focus-runner self-occlusion
- no other runner blocks the focus subject
- focus S remains full-body readable
- launch pack remains visible
- event exits normally into subsequent race direction

## Performance / regression evidence

Final pre-review CI Motion First sample:
- observed average FPS: `21.75`
- p95 frame time: `50.1 ms`
- average EvoWild JS work: `1.54 ms`
- p95 EvoWild JS work: `3.3 ms`
- render calls: `29`
- triangles: `36,724`
- proxy runners: `18`
- render pixel ratio: `0.75`

The accepted change adds no new render representation and no additional gait work.

## Decision

**PASS — ACCELERATION event and final inboard AUTO LOW composition accepted.**

Next camera-director work should target a different race-storytelling gap rather than revisiting launch gait or LOD.
