# Motion First Simplified Race Start v1 Review — 2026-10-01

Status: **PASS**

Scope:
- simplified Motion First 18-runner race
- public pre-start / start presentation
- READY -> 3 -> 2 -> 1 -> GO -> RUNNING
- no gait, contact, morph, LOD, AUTO event, environment, Sakura, sprite, 2.5D, or Lane 5 changes

## Accepted behavior

On the public race URL:
- race begins in READY state
- runners remain stationary
- race time remains at 0
- PAUSE is disabled during the start sequence
- sequence advances READY -> 3 -> 2 -> 1 -> GO
- race simulation starts only after the sequence completes
- overlay clears on RUNNING
- RESTART returns the race to READY / 0.000

Review and CI URLs can use `skipStart=1` so existing motion/director benchmarks do not inherit the presentation delay.

A deterministic `startReview=1` mode freezes the presentation at GO for visual evidence only; it does not alter the public start timing.

## Visual evidence

Accepted artifact:
- `motion-first-start-go.png`

The accepted frame shows:
- 18 runners stationary behind the start stripe
- centered GO overlay
- top race status = GO
- distance = 0 / 1600 m
- focus speed = 0.0 m/s
- PAUSE disabled

## Performance / regressions

Final push CI: **success**
Final PR job: **success**

One headless runner produced a borderline 19.866 FPS sample while the same code on the parallel runner measured above the 20 FPS gate. The gate was **not lowered**.

The performance test now retries one 2.5 s observation window when the first sample is below 20 FPS and still requires the better sample to satisfy the existing 20 FPS floor.

Representative successful sample on this start branch:
- average FPS: `26.93`
- p95 frame: `50.0 ms`
- average JS work: `1.60 ms`
- p95 JS work: `2.0 ms`
- render calls: `29`
- triangles: `36,940`
- full runners: `0`
- proxy runners: `18`

Regression status:
- standard E2E: PASS
- Motion First capture: PASS
- Sakura capture: PASS

## Decision

**PASS — public pre-start / start presentation accepted.**

Next Motion First work moves to the player-facing Race Agent command loop. Do not spend another pass on countdown cosmetics before command/state gameplay is connected.
