# Motion First S Phase C v1 Review — 2026-09-26

Status: **FAIL — Phase C remains open**

Evidence:

- PR #32
- CI run `36211064196`
- moving multi-camera video: SIDE → CHASE → LOW → FRONT → SIDE
- steady screenshots after each camera hold

## SIDE

Usable as an inspection view.

- full body remains visible;
- gait silhouette is readable;
- no obvious clipping.

No blocking SIDE camera defect found in this pass.

## CHASE — fail

The current CHASE endpoint is too high, too diagonal, and too distant.

Result:

- the runner occupies too little of the frame;
- rear limb / pelvis motion is difficult to judge;
- the view reads more like a loose 3/4 overview than a pursuit camera;
- speed impression is weak.

Required correction:

- move closer;
- lower the camera;
- reduce lateral offset;
- look slightly ahead of the torso rather than far down-track.

## LOW — fail

LOW is technically low, but still too distant for its intended role.

Result:

- foot contact is not prominent enough;
- runner is small relative to the road;
- low-angle speed impression is weaker than it should be.

Required correction:

- move closer behind the runner;
- lower camera slightly;
- keep enough forward look-ahead to preserve track flow;
- widen FOV moderately, without using extreme distortion.

## FRONT — fail

FRONT is the main blocker.

The current endpoint is too close and too laterally offset. The runner is heavily cropped and the view does not function as a readable front / 3Q-front camera.

Required correction:

- move substantially farther ahead;
- reduce lateral offset;
- center the chest / head structure;
- keep all four limbs inside frame through the gait;
- preserve a slight 3Q angle only to avoid complete limb overlap.

## Transitions

The interpolation itself is continuous, but smooth movement into a bad endpoint is not sufficient.

The next pass must fix the camera endpoints first, then re-check transition timing.

## Decision

Do not pass Phase C.

Do not begin P/E/A.

Next pass: camera framing only. Creature geometry and Phase B gait stay unchanged.
