# EvoWild Run — 2.5D Creature Reference Lock

Status: **ACTIVE / REPOSITORY CANONICAL / 2.5D HARD GATE**

This file exists to prevent 2.5D animation work from drifting into creature redesign.

## Canonical source

Primary:

- `docs/references/evowild-creature-reference-sheet-20260921.jpg`

Supporting per-morph assets:

- `public/concept/S.webp`
- `public/concept/P.webp`
- `public/concept/E.webp`
- `public/concept/A.webp`

Reference index:

- `docs/creature-reference-index-v0.1.md`

The reference sheet defines the species and the S/P/E/A morphology. It outranks generated candidates, donor models, animation convenience, stylistic preference, and prior failed experiments.

## S / P / E / A identity lock

### S — Sprint

Locked identity:

- slender;
- long-legged;
- small head;
- sprint-specialized;
- light athletic body;
- same species head / limb / tail language as the other morphs.

### P — Power

Locked identity:

- thick torso;
- muscular / powerful build;
- stronger shoulder / chest and limbs;
- visibly heavier than S/E/A;
- still the same species;
- not a plated dragon, dinosaur, wolf, rhino, or unrelated armored monster.

### E — Endurance

Locked identity:

- long, light body;
- stable sustained-running proportions;
- narrower / more efficient than P;
- same species head and limb language;
- not a horse, deer, antelope, or other borrowed animal.

### A — Agility

Locked identity:

- low center of mass;
- flexible compact body;
- corner / poor-surface specialization;
- same species anatomy;
- not a feline, lizard, or unrelated crouching monster.

## What animation work is allowed to change

Animation work may change:

- limb pose;
- gait phase;
- foot contact;
- stride extension;
- recovery position;
- body vertical motion;
- small pitch / roll / compression needed for locomotion;
- timing;
- cadence.

Animation work must not freely change:

- species;
- body proportions;
- head family;
- crest / horn family;
- tail family;
- armor / surface structure;
- palette;
- markings;
- limb count;
- limb architecture;
- overall silhouette category.

## Motion donor rule

Motion First P/E/A direct-gait captures are **motion donors only**.

They may define:

- CONTACT;
- intermediate contact-to-push;
- PUSH;
- intermediate push-to-lift;
- LIFT;
- intermediate lift-to-flight;
- FLIGHT;
- intermediate flight-to-reach;
- REACH;
- intermediate reach-to-land;
- LAND;
- intermediate land-to-contact.

They do not define final 2.5D creature appearance.

Low-poly donor geometry is explicitly forbidden as a production appearance substitute.

## Forbidden shortcuts

Reject any candidate that improves animation by doing any of the following:

- inventing a new creature;
- adding dramatic armor or spikes not present in the reference;
- changing P/E/A into visually unrelated species;
- replacing canonical anatomy with donor anatomy;
- preserving motion while losing morph identity;
- using smooth interpolation that creates double limbs / heads / ghosts;
- using raster warping that cuts torso / joints or creates duplicate limbs;
- changing color scheme to make a new design easier to recognize.

## Required comparison before KEEP

Every P/E/A regenerated candidate must be reviewed against:

1. the canonical full reference sheet;
2. that morph's `public/concept/<MORPH>.webp`;
3. current production run sheet;
4. approved motion donor phase sequence;
5. race-size runtime.

The candidate must pass both:

- **identity gate** — unmistakably the canonical morph;
- **motion gate** — phase / contact / recovery visibly improved.

Passing only one is not sufficient.

## Current P/E/A animation status

Known conclusions:

- current production six-frame P/E/A animation is visually rough;
- timing and runtime plumbing improvements do not solve source-pose quality;
- optical-flow interpolation is rejected;
- raster phase-transfer v1 is rejected;
- distal-limb raster phase-transfer v2 is rejected;
- Motion First mf12 direct-gait sequence is KEEP as a motion donor;
- Motion First low-poly appearance is REJECT as final art.

Therefore the next valid route is:

**canonical high-detail P/E/A identity + approved mf12 motion specification**

not:

**generate a new creature that happens to animate better**.

## Promotion order

Do not regenerate all three morphs blindly.

1. P candidate only;
2. isolated identity review;
3. isolated 12-frame motion review;
4. race-size runtime review;
5. only if P passes, repeat for E;
6. only if E passes, repeat for A;
7. production switch only after all three individually pass.

S remains untouched during this work unless separately authorized.
