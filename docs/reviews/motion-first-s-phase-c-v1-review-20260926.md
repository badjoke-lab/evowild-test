# Motion First S Phase C v1 Review — 2026-09-26

Status: **FAIL — Phase C remains open**

Evidence:

- PR #33
- CI run `36212025299`
- continuous SIDE → CHASE → LOW → FRONT → SIDE video
- stabilized screenshots from each camera
- reference: `docs/motion-first-creature-standard-v0.1.md`

## Result

The S gait itself remained stable through the camera changes and the CI gait gates stayed green, but the camera presentation failed Phase C.

### SIDE

Usable. Full S silhouette remains readable and the gait can be judged.

### CHASE

The runner is too small and too far from the camera for useful gait / body-overlap inspection.

### LOW

The low rear 3/4 angle is technically usable, but the runner is still framed too loosely for the intended close speed / contact inspection.

### FRONT

Blocking failure.

The previous strong lateral camera offset produces an extreme 3/4 crop. The long S body is pushed against / beyond the right side of the frame, so FRONT cannot be used to judge head/chest/leg crossing correctly.

## Correction

Phase C v2 changes only the isolated-review camera geometry:

- CHASE moves closer and reduces lateral offset;
- LOW moves closer and lower while keeping the whole runner visible;
- FRONT becomes a much shallower 3/4 front angle with extra longitudinal distance and a slightly wider FOV;
- SIDE stays unchanged as the working baseline.

No S body or gait geometry is changed in this correction.

## Decision

Phase C remains open until the same continuous S run passes SIDE / CHASE / LOW / FRONT without camera framing hiding or cropping the creature.
