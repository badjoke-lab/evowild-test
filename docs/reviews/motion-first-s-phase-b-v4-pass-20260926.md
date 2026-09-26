# Motion First S Phase B v4 Review — 2026-09-26

Status: **PASS — Phase B locomotion gate passed; Phase C remains open**

Evidence:

- PR #31
- CI run `36210793284`
- continuous SIDE → LOW motion video
- SIDE 1-second sequence sampled at 12 fps
- LOW 1-second sequence sampled at 12 fps
- automated gates:
  - IK reach clipping: none
  - planted-stance slip: below configured threshold
  - longitudinal body articulation: above strengthened threshold

## What changed enough to pass Phase B

- high-speed stance is shorter and reads as contact rather than a prolonged walk cycle;
- trailing / leading limbs are more separated in phase;
- fore and hind chains use different bend topology;
- recovery folds earlier and extends before touchdown;
- chest and pelvis visibly separate / compress through the stride;
- central waist / underside bridge follows that deformation rather than opening gaps;
- shoulder / hip roots contribute to forward / recovery motion;
- head remains more stable than the torso;
- tail response is delayed per segment rather than directly copied from gait phase;
- SIDE and LOW no longer depend on the old rigid-body + sine-leg motion.

## Important limitation

This is a **Phase B pass**, not a statement that the animation is final-production quality.

The gait still needs Phase C validation from CHASE / FRONT / transitions, where overlap, symmetry, clipping, tail behavior, and camera-relative readability can expose defects not visible in SIDE / LOW.

## Decision

Proceed to **Phase C — multi-camera S validation**.

Still blocked:

- P / E / A derivation;
- 18-runner creature replacement;
- AUTO race director;
- environment polish;
- Race Agent UI expansion.

Phase C must validate the same moving S runner from SIDE / CHASE / LOW / FRONT and through actual camera transitions.
