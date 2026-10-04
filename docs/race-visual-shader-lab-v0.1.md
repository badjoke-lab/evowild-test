# EvoWild Run — Race Visual Shader Lab v0.1

Status: **isolated experiment / not production-approved**

Branch: `exp/race-visual-shader-lab-20261003`

Base branch: `main`

Base commit: `d25553169e4406f5af660fc5559e075163aac6ff`

## Purpose

Improve race-screen environmental quality without touching Creature morphology, motion generation, Race Agent logic, or the accepted race runtime.

This lab tests visual techniques in isolation before any production integration.

## Scope lock

Allowed:

- terrain / ground shading;
- atmospheric haze;
- grass/wind presentation;
- dust / contact particles;
- race-lighting presentation;
- speed-reactive environmental effects;
- performance measurement.

Forbidden in this lane:

- Creature geometry edits;
- Creature rig edits;
- gait changes;
- Race Engine rules;
- Agent behavior;
- camera-director logic changes;
- 2.5D changes.

## Gate order

### V0 — ground material + atmospheric baseline

Build an isolated Three.js preview with:

- procedural ground ShaderMaterial;
- existing-style dirt track;
- fog / haze baseline;
- moving camera;
- shader ON/OFF comparison;
- live FPS readout.

No grass field, dust system, post-processing stack, or Creature changes in V0.

Review:

- depth readability;
- ground scale / repetition;
- track separation;
- horizon quality;
- shimmer / aliasing;
- mobile-safe visual stability;
- FPS delta against shader OFF.

Decision:

- `KEEP`
- `REVISE`
- `REJECT`

### V1 — wind grass

Blocked until V0 review.

### V2 — dust / contact particles

Blocked until V1 review.

### V3 — race lighting

Blocked until V2 review.

### V4 — speed-reactive effects

Blocked until V3 review.

## Acceptance rule

Visual novelty does not justify a feature.

Each gate must preserve race readability and remain suitable for the project's free-hosted browser runtime. Any effect that requires a large performance sacrifice must be rejected or reduced.

## Preview

Entry page:

`visual-shader-lab.html`

The V0 page intentionally contains no race Creature. It is an environment-only benchmark so environment quality can be judged without motion/model confounds.


## V0 v1 real-render review

Decision: `REVISE`

Evidence source: GitHub Actions run `37129601880`, artifact `visual-shader-lab-v0`.

Observed:

- shader ON/OFF screenshots were generated successfully;
- the dirt track was not readable in either screenshot;
- shader ON vs OFF difference was too weak to justify the custom material;
- the first implementation used `fog: true` on a custom ShaderMaterial without the required Three.js fog uniforms/chunks, producing repeated `refreshFogUniforms` runtime errors;
- captured desktop FPS was approximately mid-50s, but the visual result was not acceptable enough for a performance conclusion.

Exact V0 v2 correction:

- remove Three.js automatic fog handling from the custom ground ShaderMaterial and keep manual ground horizon haze;
- reduce geometric ground relief;
- make the track double-sided and lift it above the ground;
- add explicit track-edge lines;
- move the camera closer/lower so the track occupies the review frame;
- increase low-frequency ground color variation while retaining a flat-color OFF baseline.

V1 remains blocked.

Next action: render V0 v2 shader ON/OFF through CI, inspect the actual images, and decide `KEEP / REVISE / REJECT`.


## V0 v2 real-render review

Decision: `REVISE`

Evidence source: GitHub Actions run `37129980162`, artifact `visual-shader-lab-v0`.

Observed:

- runtime fog error was eliminated and the full E2E suite passed;
- dirt track and edge lines became clearly readable;
- shader ON produced visible terrain variation;
- the first variation pattern read as coarse tiled/checkered patches and was not acceptable as final V0 ground treatment;
- headless capture FPS read roughly 20–23 in both modes, so this environment is useful only for relative regression checks, not a production FPS claim.

Exact correction: replace cell-stepped variation with smoothly interpolated value noise; keep the accepted track/camera/haze correction unchanged.

## V0 v3 real-render review

Decision: `KEEP`

Evidence source: GitHub Actions run `37130200719`, artifact `visual-shader-lab-v0`.

Observed:

- E2E passed with no shader runtime error;
- track/ground separation remains clear;
- shader ON now adds broad, smooth low-frequency terrain variation without the v2 checker pattern;
- shader OFF remains a useful flat-color baseline;
- horizon remains intentionally simple because grass, dust and production lighting are outside V0;
- headless screenshot readout was approximately 20 FPS in both ON and OFF captures, showing no obvious ON/OFF regression in this CI run but not establishing device performance.

V0 decision: `KEEP`

V1 status: `READY`

Next action: add wind grass in V1 without changing the V0 ground, track, camera or Creature/race logic.


## V1 implementation

Status: `REVIEW_PENDING`

V0 locks preserved:

- V0 ground shader retained;
- V0 dirt track retained;
- V0 camera path retained;
- V0 haze retained;
- no Creature, gait, Race Engine, Agent or 2.5D edits.

V1 exact change:

- add one instanced grass field outside the dirt track;
- desktop target: up to 4,200 blades;
- mobile target: up to 1,500 blades;
- deterministic placement so comparisons are repeatable;
- reject placements within 8.5 world units of the sampled track centerline;
- vertex-shader wind sway only; no CPU per-blade animation;
- explicit GRASS ON/OFF control for review;
- no dust, post-processing or lighting expansion yet.

V1 review gate:

- grass must read as environmental depth, not vertical noise;
- dirt track must remain unobstructed;
- wind movement must not create obvious synchronized waving;
- no runtime/WebGL errors;
- compare GRASS ON vs OFF in the same moving-camera scene;
- CI FPS is relative-only and must not be treated as device performance.

Allowed decision: `KEEP / REVISE / REJECT`.

V2 dust remains blocked until V1 is reviewed from real captures.
