# Motion First S Phase B v2 Review — 2026-09-26

Status: **FAIL — Phase B remains open**

Evidence reviewed:

- dedicated gait page: `public/preview-motion-first-gait/`
- CI build / motion capture from PR #29 and PR #30
- continuous SIDE → LOW video artifact
- current main baseline: `8fb89748cf1ece7353d42db553e779fd946609b5`
- reference standard: `docs/motion-first-creature-standard-v0.1.md`

## What v2 solved

- stance and swing are now separate;
- gait cadence is tied to world speed and stride length;
- S limbs use a three-joint planar IK solve;
- foot target movement during stance is coupled to runner forward travel;
- automated checks reject unreachable IK and excessive stance slip;
- SIDE / LOW can be reviewed in continuous motion instead of only still images.

Those are necessary corrections, but they are not enough.

## Blocking visual defects

### 1. Body is still too rigid

The torso translates through space, but the animal does not visibly load, compress, extend, and release strongly enough.

Observed:

- shoulder and pelvis rotation exists but reads as small mechanical oscillation;
- chest-to-pelvis distance is nearly constant;
- the back line remains too rigid through the stride;
- suspension phases do not clearly separate from loading phases.

Required correction:

- explicit longitudinal spine extension/compression;
- visible shoulder and pelvis root travel;
- stronger but controlled vertical load/rebound;
- body pitch tied to contact phase, not only a generic sine wave.

### 2. Recovery legs still look mechanically folded

The foot path is smoother than the old sine swing, but recovery legs can still read as hinged sticks.

Required correction:

- faster early fold after toe-off;
- compact mid-swing;
- progressive extension before touchdown;
- root motion at shoulder / hip so the leg does not do all of the work alone.

### 3. Head / neck follow-through is not inertial enough

The head remains readable, but its motion is still driven directly from phase.

Required correction:

- use damped follow-through from torso pitch / vertical load;
- head should stabilize while neck absorbs body movement;
- avoid excessive bobbing.

### 4. Tail is still phase-driven rather than physically delayed

The tail no longer whips excessively, but it still follows an obvious procedural rhythm.

Required correction:

- per-segment damped target angles;
- delay increases toward the tail tip;
- turning influence remains stronger than vertical wag.

## Decision

Do not derive P / E / A yet.

The next pass remains **S locomotion only**.

Phase B passes only when SIDE and LOW show:

- clear load → drive → suspension → recovery;
- no obvious foot skating;
- no IK snapping;
- a visibly deforming / articulating body rather than a rigid hull with moving legs;
- restrained head stabilization and delayed tail response.
