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

Current phase: **HUNYUAN S INTEGRATION / S ONLY**

The procedural S remains rejected as a visual baseline.

The active S geometry baseline is now the existing Hunyuan-derived model family. The rigless LOD2 mesh is the shape/edit source; rigged v31 variants are runtime motion assets. This does not mean the Hunyuan model is final art — it means further S work starts from the best existing geometry instead of rebuilding another weak procedural creature.

What is actually proven:

- isolated Motion First page exists;
- dedicated gait page exists at `public/preview-motion-first-gait/`;
- 18 simplified articulated 3D runners can be displayed;
- CHASE / LOW / PACK / SIDE / FRONT cameras can operate;
- camera position, target, and FOV can transition smoothly;
- distance-coupled gait / IK / planted-stance checks can be implemented.

What is **not** accepted:

- the procedural Motion First S body as a shape source;
- the abandoned local Sol/Astra S candidates;
- current P / E bodies as production-quality morphs;
- any A derivation;
- propagation to 18 production-quality creatures.

### S source rule

Use the canonical Hunyuan mapping in `public/models/evowild-s/manifest.json`:

- `source-lod2.glb` — shape/edit baseline;
- `focus-rigged-v31.glb` — near/focus motion;
- `race-lod4-rigged-v31.glb` — multi-runner race;
- `race-lod4.glb` — far/static LOD only.

Do not restart the S shape from procedural primitives or the abandoned Astra placeholder.

Do not continue P / E / A production modeling until the Hunyuan S replacement is integrated and reviewed in Motion First.

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

- the visible S must use the canonical Hunyuan family rather than procedural geometry;
- the rigless LOD2 mesh is the current shape baseline, not a claim of final-art completion;
- "builds", "runs", or "loads a GLB" are not sufficient — the model must remain readable from SIDE / LOW / CHASE / FRONT;
- the close-camera gait must use the rigged v31 asset without degrading movement quality;
- no P/E/A production derivation is allowed until this replacement survives visual runtime review.

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

The current task is the Hunyuan S replacement.

Next:

1. load rigless LOD2 for S shape inspection;
2. load high-detail rigged v31 for isolated/focus gait;
3. load LOD4 rigged v31 for visible S runners in the race;
4. verify that no procedural S remains visible when the GLB load succeeds;
5. re-run SIDE / LOW / CHASE / FRONT review;
6. verify animation clips and frame-rate behavior;
7. only then decide whether S geometry needs further editing from LOD2.

Until that passes:

- no A production modeling;
- no further E production modeling;
- no 18-creature production expansion;
- no return to a newly generated procedural S.
