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
