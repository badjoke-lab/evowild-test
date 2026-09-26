# EvoWild Run — Motion First Creature Standard v0.1

Status: **development reference / required for Motion First work**

This document is the visual and motion contract for the isolated Motion First experiment.

The current primitive runners in `public/preview-motion-first/` are **technical placeholders only**. They prove that multiple articulated 3D runners and multiple camera modes can coexist. They are not an accepted visual baseline and must not be treated as one.

## 1. Canonical creature references

Use the repository concept assets below before changing creature geometry, gait proportions, head structure, tail structure, or Cue Band placement.

- [S — Sprint morph](../public/concept/S.webp)
- [P — Power morph](../public/concept/P.webp)
- [E — Endurance morph](../public/concept/E.webp)
- [A — Agility morph](../public/concept/A.webp)
- [S running reference sheet](../public/concept/s-run-sheet.svg)

These assets define the intended species language. Implementation convenience must not silently replace that language.

### Reference hierarchy

When references conflict, use this order:

1. the latest explicit user direction;
2. the creature concept assets listed above;
3. this document;
4. implementation convenience.

Do not promote a temporary implementation artifact into the design specification.

## 2. Species-level visual rules

EvoWild runners are one species with morph variation, not four unrelated animals.

Required common traits:

- small, restrained head relative to body;
- non-mascot proportions;
- long forward/backward directional silhouette;
- clearly non-real-world leg/foot anatomy;
- integrated crest / horn structure rather than accessories attached at random;
- tail designed as part of balance and locomotion;
- race Cue Band present on every runner;
- body plan readable from side, front, rear, and 3/4 views;
- morphs remain recognizably related even when proportions differ.

Avoid:

- horse, deer, dog, llama, dinosaur, or goat silhouettes by accident;
- long vertical necks that dominate the body;
- round toy-like torsos;
- oversized eyes;
- chibi proportions;
- disconnected spikes or decorative parts with no structural logic;
- generic quadruped primitives whose only difference is scale.

## 3. Rendering direction for Motion First

The Motion First lane uses **simplified 3D**, not 2D sprites.

Why:

- CHASE, LOW, PACK, SIDE, and FRONT cameras must all work;
- the camera may interpolate between angles;
- foot contact, limb overlap, and body banking must remain spatially coherent;
- 18 runners must coexist without requiring a separate sprite set for every angle.

Simplified 3D means:

- low or moderate geometric complexity;
- strong silhouette;
- large readable planes;
- restrained toon / graphic shading;
- limited material count;
- selective emissive accents;
- no dependence on expensive surface detail.

Simplified 3D does **not** mean simplified motion.

## 4. Morph definitions

### S — Sprint

Reference: `public/concept/S.webp`

Visual:

- narrow torso;
- long legs;
- small head;
- long, rearward-flowing head / crest line;
- light rear body;
- long tail;
- strongest forward directional silhouette.

Motion:

- high cadence;
- long effective stride;
- short ground-contact phase;
- low unnecessary vertical bounce;
- stronger forward pitch during acceleration;
- rapid recovery of limbs.

### P — Power

Reference: `public/concept/P.webp`

Visual:

- thick chest and rear body;
- heavier limbs;
- broader structural mass;
- shorter, stronger-looking neck transition;
- compact, forceful silhouette.

Motion:

- lower cadence than S;
- longer force application during stance;
- stronger compression / extension;
- visibly heavier body transfer;
- slower lane-change response than A.

### E — Endurance

Reference: `public/concept/E.webp`

Visual:

- longer trunk;
- balanced limb thickness;
- stable back line;
- moderate head / neck profile;
- neither S-thin nor P-heavy.

Motion:

- stable cadence;
- efficient stride;
- low wasted vertical movement;
- consistent body attitude;
- reduced dramatic acceleration/deceleration.

### A — Agility

Reference: `public/concept/A.webp`

Visual:

- lower center of mass;
- compact trunk;
- flexible-looking body line;
- strong fore/aft balance;
- tail and body should visually support turning.

Motion:

- fast response;
- strongest lateral lean;
- compact recovery phase;
- active body flex;
- lane changes should visibly differ from S/P/E.

## 5. Head / crest / tail / limb variation

The concept sheet establishes that individual variation exists inside the same species.

Permitted variation axes include:

- head length and breadth;
- head pitch / carriage;
- crest length and direction;
- branched, plate-like, or reduced crest structures;
- short / standard / long / bifurcated / plate-like / flowing tails;
- limb thickness and foot construction;
- large graphic body markings;
- non-natural colors and emissive accents.

Rules:

- variation must not destroy species identity;
- variation is subordinate to the S/P/E/A body type;
- do not use variation as a substitute for getting the base body correct;
- first pass is one canonical S body, then P/E/A, then individual variation.

## 6. Cue Band

Every race creature wears a Cue Band.

The Cue Band must:

- be visible from side, front, rear, and 3/4 angles;
- follow the head structure rather than float around it;
- read as a race device, not a fantasy horn;
- include a restrained status / signal light;
- remain identifiable at medium camera distance;
- preserve the underlying head silhouette.

Do not use the Cue Band to hide an incorrect head shape.

## 7. Motion fidelity requirements

The following are mandatory even for low-poly geometry:

- foot plant must not visibly slide during the stance phase;
- fore and hind limb cycles must be coordinated rather than independent sine swings;
- shoulder / chest and pelvis movement must support the limb cycle;
- acceleration must change body attitude;
- deceleration must return the center of mass;
- head and neck have delayed follow-through;
- tail has inertial follow-through;
- lateral movement must produce body lean;
- speed must affect cadence / stride in a controlled way;
- runner motion must remain smooth at normal display refresh rates.

A "still image that shakes", a rigid body with swinging sticks, or a few pose swaps is not acceptable for this lane.

## 8. Multi-camera acceptance

A creature is not approved from SIDE view alone.

Before a morph can be propagated to 18 runners, it must survive:

- SIDE — silhouette and gait;
- CHASE — rear structure, stride, tail behavior;
- LOW — contact, underside, speed impression;
- FRONT — head, chest, leg crossing, symmetry;
- 3/4 transition — no sudden visual collapse during camera interpolation.

If a model only works from one angle, it fails this lane.

## 9. Performance strategy

The visual target is achieved by allocating complexity where it is visible.

Near / focus runner:

- full articulation;
- complete head / crest / Cue Band silhouette;
- full tail chain;
- full material accents.

Mid-distance runners:

- same species geometry with reduced detail where safe;
- preserve silhouette and major joints.

Far runners:

- simplified geometry / reduced secondary detail;
- preserve movement, morph silhouette, and identification.

Do not solve performance by reducing animation quality first.

## 10. Immediate S-morph gate

**Current status: NOT PASSED.**

The current procedural / primitive S is a motion-test fixture only. It must not be treated as the accepted creature model.

The accepted S candidate is to come from the dedicated **Astra modeling lane**. No further P/E/A creature-model expansion is allowed until that candidate meets all of the following:

- recognizably matches the S concept silhouette;
- no accidental real-world-animal silhouette dominates;
- head is small and directional;
- torso is narrow and athletic;
- legs are long and structurally coherent;
- Cue Band sits correctly on the head;
- foot contact reads correctly at SIDE and LOW;
- CHASE, SIDE, LOW, FRONT all remain visually coherent;
- motion remains smooth;
- no reliance on camera distance to hide defects.

Only after this gate passes should P/E/A be derived.

A previous internal decision incorrectly marked the primitive S as passed because it survived multi-camera and motion checks. That decision is revoked: multi-camera stability is necessary, not sufficient, for visual acceptance.

## 11. What is deliberately deferred

Until the S gate passes, do not spend development time on:

- Race Agent HUD refinement;
- cosmetic UI polish;
- breeding UI;
- large-scale environment art;
- detailed markings for 18 individuals;
- complex race cinematics;
- decorative VFX.

The creature and its motion are the first quality gate.
