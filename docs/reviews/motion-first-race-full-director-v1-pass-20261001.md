# Motion First Simplified Race Full AUTO Director v1 Review — 2026-10-01

Status: **PASS**

Scope:
- simplified Motion First 18-runner race
- one continuous 1600 m AUTO race from START to FINISHED
- camera balance / shot duration / focus churn / late-race framing
- no gait, stance/contact, morph geometry, LOD, Sakura, sprite, 2.5D, or Lane 5 changes

## Review method

The dedicated review mode records every director shot as:
- race time
- camera
- reason
- focus runner

A continuous 1280x720 video is recorded from race start through finish, with additional early / mid / late / finish stills.

The diagnostic is isolated behind `fullDirectorReview=1` and `MOTION_FIRST_FULL_RACE_REVIEW=1`; normal CI does not inherit the ~70 s capture.

## First full-race result — FAIL

Initial full-race metrics:
- race time: `69.733 s`
- shot count: `24`
- focus switches: `10`
- LOW coverage: `30.466 s / 43.7%`

Problems found:
1. repeated `BREAKAWAY:LOW` shots made LOW effectively dominant even though identical persistent shots were not adjacent
2. long AUTO LOW tracking let the camera close too far on a 23–25 m/s leader, producing oversized/cropped late-race framing
3. at 1200m+ low-angle views, the long track plane and ground plane were separated by only 3 cm; depth precision allowed grass to visually overwrite the track while lane lines remained visible

CI success was not treated as visual acceptance.

## Accepted fixes

### BREAKAWAY frequency

Added an 8 s cooldown between `BREAKAWAY` shots.

This keeps BREAKAWAY available as a race event while preventing LOW from returning every other shot.

### Long AUTO LOW framing

The previously accepted short `ACCELERATION:LOW` composition stays unchanged.

For other AUTO LOW shots:
- camera lateral position is biased strongly toward track center
- lead distance increases from `10.5 m` to `16.0 m`
- this compensates for damped tracking lag at racing speed and keeps the focus runner inside a readable full-body composition

### Late-track depth stability

Simplified-race ground Y:
- old: `-0.03`
- accepted: `-0.12`

Track and creature contact remain at `y = 0`.

This removes late-race grass/track depth bleed without changing gait/contact geometry.

## Final full-race result

Final deterministic race:
- race time: `69.733 s`
- shot count: `24`
- focus switches: `10`
- shortest shot: `1.967 s`
- longest shot: `3.867 s`

Camera coverage:
- PACK: `7.233 s` — `10.4%`
- LOW: `22.283 s` — `32.0%`
- CHASE: `14.617 s` — `21.0%`
- SIDE: `23.267 s` — `33.4%`
- FRONT: `2.333 s` — `3.3%`

Final sequence remains:
- `FINAL_CHASE:CHASE`
- `FINISH_SIDE:SIDE`
- `FINISH_FRONT:FRONT`

Required event coverage also includes:
- START
- ACCELERATION
- OVERTAKE_ATTEMPT
- BREAKAWAY
- LANE_MOVE
- RACE_FLOW

## Visual result

Final continuous-video/still review:
- no late-race grass replacing the racing surface
- long LOW shots keep the leader readable rather than filling/cropping the frame
- SIDE remains available for pack/overtake context
- CHASE remains meaningful rather than being displaced by LOW
- finish FRONT remains track-centered and readable
- no rapid-cut sequence below 1.5 s
- focus changes remain limited rather than occurring every shot

## Regression gates

The full-race test now requires:
- LOW share < `35%`
- any single camera share < `40%`
- shortest shot > `1.5 s`
- focus switches <= `12`
- all five camera modes appear
- final finish sequence order is preserved
- no adjacent identical `reason:camera` entries

## Decision

**PASS — full-race AUTO director integration accepted.**

Next Motion First work should leave director event logic alone unless a new full-race artifact proves a specific defect. The next quality pass is environment / race-space readability, followed by player-facing race UI/Agent presentation.
