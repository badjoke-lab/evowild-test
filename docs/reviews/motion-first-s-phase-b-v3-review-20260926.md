# Motion First S Phase B v3 Review — 2026-09-26

Status: **FAIL — Phase B remains open**

Evidence:

- PR #31 CI run `36210478405`
- continuous gait video artifact
- 1-second SIDE contact sheet sampled at 12 fps
- LOW multi-frame review
- automated IK / planted-stance / body-stretch gates all passed

## Improvements over Phase B v2

- the torso now has measurable longitudinal articulation;
- shoulder and hip roots participate in the stride;
- head and tail are damped rather than directly phase-locked;
- swing recovery is asymmetric rather than a simple mirrored arc;
- foot-plant math remains stable under the new body motion.

## Blocking visual defects

### 1. Left/right limb pairs still read too synchronously

At full speed, the hind pair and fore pair spend too much of the cycle in nearly matching poses.

Result:

- the gait can read as bounding / paired-leg motion instead of a fast asymmetric gallop;
- the silhouette repeats too mechanically;
- SIDE does not yet have the desired continuous sequence of trailing hind → leading hind → trailing fore → leading fore.

Required correction:

- shorter stance fraction;
- wider intra-pair phase separation;
- stronger distinction between leading and trailing limb recovery.

### 2. Spine deformation remains visually too subtle

The numeric body-stretch gate passes, but SIDE still reads as a long rigid top line in many frames.

Required correction:

- increase chest/pelvis longitudinal separation range;
- scale / reposition the central waist and underside bridge so stronger flex does not create gaps;
- increase contact compression and suspension rebound without turning it into vertical bouncing.

### 3. Fore and hind joint solutions look too similar

The current planar solve uses essentially the same bend topology for both limb families.

Required correction:

- differentiate fore vs hind bend solution;
- fore recovery should read as elbow/wrist folding;
- hind recovery should read as hip/stifle/hock drive;
- preserve the non-real-animal foot design.

## Decision

Do not start Phase C yet.

Phase B v4 will target gait silhouette and joint sequencing only. Camera director, P/E/A, 18-runner expansion, and environment work remain blocked.
