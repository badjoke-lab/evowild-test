# Motion First S v3 Visual Review — 2026-09-25

Status: **FAIL — Phase A remains open**

Evidence:

- PR: #27
- CI run: `36160088517`
- isolated captures: SIDE / LOW / CHASE / FRONT
- compared against `public/concept/S.webp`, the repository reference sheet, and the Motion First creature standard

## What v3 fixed

- the visible head / neck gap from v2 is closed;
- the head now reads as part of the same organism;
- FRONT structure is stronger;
- forelimb root spacing is improved;
- split-toe contact shape is clearer;
- v2 torso proportions remain intact.

## Remaining blocking defect

### Tail root is visibly detached in SIDE

SIDE shows a clear empty gap between the rear body and the first tail segment.

LOW makes the root relationship easier to read and confirms that this is geometry placement, not only a camera artifact.

This violates the same-species structural continuity rule and is too visible to defer.

## v4 correction

Keep v3 head, neck, torso, limbs, Cue Band, and camera inspection positions unchanged.

Only:

- move the S tail root forward into the rear-body surface;
- preserve the lower tail angle;
- keep the shorter v2/v3 tail length;
- confirm SIDE and LOW have no visible separation.

## Decision

Do not start Phase B gait work yet.

Phase A stays open until the tail root passes multi-view inspection.
