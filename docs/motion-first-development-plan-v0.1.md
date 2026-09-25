# EvoWild Run — Motion First Development Plan v0.1

Status: **active execution plan**

This plan controls the isolated Motion First lane at `public/preview-motion-first/`.

The purpose is to determine whether EvoWild Run can use a simplified visual style while preserving high-quality motion, speed, camera work, and race readability.

The creature standard is mandatory:

- [Motion First Creature Standard v0.1](./motion-first-creature-standard-v0.1.md)

## 1. Isolation rule

Motion First remains separate from:

- `race-2_5d.html`
- `race-lane5.html`
- `public/preview-3d/`
- `public/preview-3d-gait-v2/`
- `public/preview-3d-rig-v3/`

Changes in this lane must not overwrite or silently redefine those experiments.

The current Motion First implementation is a technology proof, not a quality benchmark.

## 2. Current state

Already proven:

- a separate Motion First page can run;
- 18 simplified articulated 3D runners can be displayed;
- S/P/E/A parameter families can coexist;
- CHASE / LOW / PACK / SIDE / FRONT cameras can operate;
- camera position, target, and FOV can transition smoothly;
- a focused runner can be changed;
- lane changes and body lean can be represented.

Not proven:

- concept-faithful creature geometry;
- high-quality gait;
- reliable foot locking;
- good motion from every camera;
- acceptable speed sensation;
- convincing S/P/E/A derivation from one species;
- acceptable 18-runner quality after creature replacement.

## 3. Execution order

Do not skip ahead because a later item is easier.

### Phase A — Canonical S body

Build one S runner from the repository creature references.

Required work:

- replace the current generic primitive body;
- match the S silhouette first;
- reduce vertical neck impression;
- reduce head mass;
- establish the long directional crest / head line;
- redesign chest / pelvis connection;
- redesign fore and hind limb proportions;
- redesign feet;
- redesign tail;
- fit the Cue Band to the head.

Deliverable:

- one S runner visible in the existing Motion First page.

Gate A:

- S silhouette is recognizable before animation quality is judged.

### Phase B — S locomotion

Replace the current generic limb swing with a gait that respects stance and recovery.

Required work:

- explicit stance vs swing phase;
- planted-foot compensation to reduce sliding;
- coordinated fore/hind timing;
- shoulder/chest motion;
- pelvis drive;
- controlled body compression / extension;
- neck/head follow-through;
- tail inertia;
- acceleration posture;
- lane-change lean.

Deliverable:

- S can run continuously without obvious foot skating or rigid-stick motion.

Gate B:

- motion must pass SIDE and LOW before any P/E/A geometry work.

### Phase C — Multi-camera S validation

Validate the same S creature in every camera.

Required views:

- SIDE;
- CHASE;
- LOW;
- FRONT;
- 3/4 transition between camera modes.

Check:

- silhouette;
- limb crossing;
- head proportions;
- tail behavior;
- Cue Band;
- contact;
- camera clipping;
- apparent speed.

Gate C:

- no camera may depend on hiding major geometry or motion defects.

### Phase D — Derive P / E / A

Only after S passes A-C, create the remaining morphs from the same species structure.

P:

- heavier chest/rear body;
- thicker limbs;
- stronger stance;
- heavier transfer.

E:

- longer balanced trunk;
- stable back line;
- efficient gait;
- reduced wasted motion.

A:

- lower compact body;
- stronger flex;
- faster lateral response;
- strongest banking.

Gate D:

- all four must look related;
- differences must remain visible in silhouette without relying on color.

### Phase E — 18-runner deployment

Expand from four canonical morphs to the 18-runner race.

Add individual variation only here:

- color;
- markings;
- approved head variants;
- approved crest variants;
- approved tail variants;
- small proportion variance.

Do not create 18 unrelated body plans.

Gate E:

- 18 runners remain readable;
- no significant frame-rate collapse;
- animation quality is not reduced to rescue performance.

### Phase F — Camera director

Manual cameras stay available permanently for inspection.

Replace the current time-loop AUTO logic with race-event-driven logic.

Events to detect:

- start;
- acceleration;
- overtake attempt;
- side-by-side contest;
- leader change;
- dense pack;
- breakaway;
- final straight;
- finish approach.

Camera roles:

- CHASE — default focus / pursuit;
- LOW — short acceleration and speed emphasis;
- PACK — tactical group relationship;
- SIDE — overtakes and gait-readable racing;
- FRONT — brief approach shot, never dominant.

AUTO must choose a camera because of a race event, not because a timer elapsed.

Gate F:

- automatic camera changes explain the race rather than interrupt it.

## 4. Speed-impression work

After creature motion is credible, improve perceived speed.

Use:

- closer trackside reference objects;
- denser fence posts / markers;
- near-field ground texture or markings;
- controlled FOV increase for LOW / CHASE;
- relative motion between runners;
- short camera lag under acceleration;
- restrained dust / contact effects.

Do not fake speed primarily with strong camera shake, blur, or excessive speed lines.

## 5. Environment work

Environment remains subordinate to creature and motion quality.

Initial environment goals:

- enough geometry to expose motion and speed;
- clear near / middle / far depth;
- trackside objects that create optical flow;
- no large empty zones that make 20+ m/s look slow.

Large art-production work starts only after creature gates A-E.

## 6. UI / Agent work

Until the creature gates are passed, UI is diagnostic only.

Keep:

- camera buttons;
- focus runner selection;
- speed;
- position;
- FPS.

Defer:

- polished Race Agent panels;
- deep strategy UI;
- history panels;
- compatibility panels;
- cosmetic overlays.

The page should first be judged as a race, not as a dashboard.

## 7. Review protocol

Every important creature change must be reviewed against the repository references before expanding scope.

For S body changes:

1. compare SIDE silhouette;
2. compare head-to-body ratio;
3. compare leg length and foot form;
4. compare back line and chest/pelvis relation;
5. compare tail direction;
6. compare Cue Band placement;
7. run SIDE;
8. run LOW;
9. run CHASE;
10. run FRONT.

If any step exposes a major defect, fix S before propagating the change.

## 8. No-self-certification rule

Do not call a phase complete merely because:

- it builds;
- CI passes;
- it reaches 60 FPS;
- the model is more detailed than the previous one;
- one camera looks acceptable.

Technical correctness and visual acceptance are separate.

CI can verify regressions and runtime behavior. It cannot certify creature quality by itself.

## 9. Next concrete implementation task

The next coding task is:

**replace the current S primitive creature with a reference-driven S body, while leaving P/E/A and the rest of the race infrastructure untouched.**

The first implementation pass should concentrate on:

- head;
- crest;
- neck line;
- chest;
- pelvis;
- long limbs;
- feet;
- tail;
- Cue Band.

Do not redesign AUTO camera, HUD, or environment in the same pass.

After that pass, inspect S in SIDE / CHASE / LOW / FRONT before proceeding.
