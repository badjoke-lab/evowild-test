# Motion First E Phase D v1 Body Review — 2026-09-26

Status: **FAIL — E body gate remains open**

Evidence:

- PR #36
- CI run `36214719598`
- isolated E SIDE / CHASE / LOW / FRONT captures
- repository reference: `public/concept/E.webp`
- shared species standard: `docs/motion-first-creature-standard-v0.1.md`

## What v1 established

- E is no longer the old generic placeholder;
- it shares the S/P head-family, Cue Band, two-mass torso, central bridge, segmented tail, three-stage limbs, and split feet;
- the long-distance silhouette is visibly distinct from S and P.

## Blocking defects

### 1. Limbs read as stilts

The first E limb set is too long and too thin relative to the torso.

In CHASE / LOW / FRONT this makes E look insect-like rather than like the same EvoWild species.

Required correction:

- shorten upper / lower / cannon segments;
- add a small amount of limb thickness;
- retain E as the lightest / longest-limbed morph without breaking family resemblance.

### 2. Torso is too needle-like

SIDE exaggerates length so far that the body becomes a narrow horizontal beam.

Required correction:

- slightly widen / deepen chest and pelvis;
- reduce longitudinal stretch;
- keep the back line long and stable.

### 3. Head / muzzle line is too extreme

The head is overly long and narrow compared with the reference family.

Required correction:

- slightly broaden head;
- shorten muzzle;
- shorten the thin crest while preserving the E directional line.

### 4. Tail presentation is wrong

CHASE / LOW show an elevated segmented tail that dominates the rear silhouette.

Part of this is caused by the old generic non-S/P placeholder motion being applied during inspection.

Required correction:

- shorten and lower E tail geometry;
- body inspection must use a neutral E pose rather than the obsolete generic race animation.

## Decision

E v1 fails.

E v2 remains a **body / silhouette** correction. E locomotion stays blocked until the corrected body passes SIDE / CHASE / LOW / FRONT.
