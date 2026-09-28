# Motion First Simplified Race Animated Proxy LOD v2 Review — 2026-09-28

Status: **PASS — LOD/performance gate accepted for the simplified race lane**

Scope:
- simplified Motion First 18-runner race only
- S / P / E / A procedural EvoWild morphs
- no Hunyuan / high-detail S asset in this lane
- latest-main carry-forward branch: `feat/simplified-race-lod-v3-20260928`
- PR #65

## Evidence

Final latest-main CI:
- run `36439818048`
- build: PASS
- standard E2E: PASS
- Motion First capture: PASS
- Sakura NPR capture: PASS

Final race performance sample:
- render pixel ratio: `0.75`
- observed average FPS: `22.99`
- observed p95 frame time: `50.1 ms`
- average EvoWild JS frame work: `1.739 ms`
- p95 EvoWild JS frame work: `2.5 ms`
- render calls: `27`
- rendered triangles: `35,164`
- full high-draw runners: `0`
- animated proxy runners: `18`

A previous identical source implementation sample on PR #61 reached:
- average FPS: `35.73`
- p95 frame time: `33.4 ms`
- average JS frame work: `1.49 ms`

Headless Chromium cadence is variable, so the final gate combines a conservative observed FPS floor with direct per-frame work and draw-call budgets.

## Motion result

The proxy representation does not use a static sprite, sine-only leg swing, or reduced gait path.

Each proxy keeps the canonical S / P / E / A pose solver for:
- articulated leg motion
- planted stance logic
- torso compression / extension
- chest / pelvis motion
- banking
- head / neck follow-through
- tail response

Continuous AUTO and SIDE captures show changing limb and body poses rather than frozen or rocking-only runners.

## Morph readability

The dedicated SIDE / LOW artifacts retain visible shape differences:
- S: long, narrow sprint silhouette and long rear line
- P: heavier chest / pelvis mass and shorter, thicker power build
- E: longer, lighter endurance silhouette
- A: compact low body and shorter agility silhouette

Differences are structural, not color-only.

## Camera / speed result

Phase F remains event-driven:
- START
- lead / duel / pack / lane-move events
- breakaway
- final chase
- finish views

The race keeps roadside speed cues, close CHASE / LOW framing, speed-linked FOV / vibration and broadcast-style cuts.

## Separation result

The simplified race still reports the procedural simplified lane and makes no request for `/models/evowild-s/` high-detail assets.

The latest-main carry-forward also passes the Sakura capture job, so this change does not replace or break the parallel Sakura lane.

## Decision

**PASS for the animated proxy LOD/performance gate.**

This does not mean the overall simplified race is visually finished. The representation is intentionally simplified and close focus shots remain low-detail compared with the high-quality 3D lane.

Next priority returns to the project order:
1. motion
2. camera
3. speed impression
4. morph readability
5. further LOD/performance only if a measured regression appears
