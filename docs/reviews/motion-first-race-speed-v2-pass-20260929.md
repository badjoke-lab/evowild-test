# Motion First Simplified Race Speed Impression v2 Review — 2026-09-29

Status: **PASS**

Scope:
- `public/preview-motion-first-race/`
- simplified Motion First 18-runner race only
- LOW / CHASE speed impression
- no gait, IK, contact, morph body, or LOD representation changes

## Changes reviewed

- existing roadside speed cue spacing remains `7.25 m`
- added low near-field inner-shoulder markers at `4.8 m` spacing
- markers use two InstancedMesh draws and do not add per-frame pose work
- CHASE gets speed-linked FOV boost up to `+2.4°`
- LOW gets speed-linked FOV boost up to `+3.4°`
- LOW was revised twice after visual review to remove foreground runner occlusion
- final LOW sits inside the trailing-row gap and uses a wider low-angle field of view

## Visual result

Dedicated final artifacts:
- `motion-first-speed-chase.png`
- `motion-first-speed-low.png`
- `motion-first-phase-f-auto-director.webm`

CHASE:
- focus runner remains readable
- near-field and roadside references move through the frame more aggressively
- pack remains visible enough to preserve race context

LOW:
- initial implementation failed because another runner dominated the foreground
- second implementation still allowed pack occlusion
- final implementation keeps the focus runner centered and fully readable
- edge runners may enter the frame, but no longer cover the focus subject
- low camera remains distinct from CHASE rather than becoming a duplicate angle

AUTO:
- Phase F event-driven camera behavior remains intact
- AUTO artifact continues to cut among SIDE / PACK / LOW and other event shots
- previous persistent-state camera-lock fix remains intact

## Performance evidence

Final PR #67 CI sample:
- average observed FPS: `21.62`
- p95 frame time: `50.1 ms`
- average EvoWild JS frame work: `1.69 ms`
- p95 EvoWild JS frame work: `2.0 ms`
- render calls: `29`
- rendered triangles: `36,724`
- render pixel ratio: `0.75`
- proxy runners: `18`
- full high-draw runners: `0`

A prior sample from the same change set reached `26.88 FPS` with `29` render calls. Headless Chromium cadence remains variable, while direct JS work stays well inside the existing budget.

## Separation / regression result

PASS:
- standard E2E
- Motion First capture
- Sakura NPR capture
- simplified S/P/E/A canonical gait remains unchanged
- no Hunyuan asset is introduced into the simplified race lane
- no Sakura / sprite / 2.5D / Lane 5 implementation is replaced

## Decision

**PASS — speed impression v2 accepted.**

Next priority returns to:
1. motion quality under live pack traffic
2. camera composition / race storytelling
3. morph readability at racing distance

Further environment decoration is not the next priority.
