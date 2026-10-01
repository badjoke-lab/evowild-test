# EvoWild Run — S Creature Modeling Workflow

Status: ACTIVE PROCESS LOCK
Scope: S / Sprint type only
Branch: exp/s-creature-vibe-modeling
Primary morphology lock: S_MODELING_IMAGE_LOCK.md

## Purpose

This document exists to stop free-form AI modeling.

The AI must not invent its own creature-modeling workflow. Every Blender edit must follow the staged reference-driven process below. Visual plausibility is not enough; each stage must be checked against the approved S-type reference before the next region is touched.

## Core rule

Reference first. Landmarks second. Geometry third.

Before editing geometry, define:
- target region
- keep_fixed regions
- reference landmarks to match
- exact intended silhouette change
- forbidden changes
- review cameras

If these are not explicit, do not edit.

## Reference hierarchy

1. Approved S-type Modeling Image v1.0
2. references/00_full_reference.png
3. references/01_s_body_primary.png
4. references/02_s_silhouette.png
5. S_MODELING_IMAGE_LOCK.md
6. Current accepted checkpoint geometry

S-blockout-v12 is never a morphology reference.

## Overlay rule

For SIDE and FRONT validation, compare the creature against the reference in the same camera space whenever practical.

Use either:
- Blender camera-background reference image with wire/transparent model overlay, or
- deterministic render overlay generated from locked camera renders.

Do not rely only on looking back and forth between two separate images.

## Landmark rule

Before a sub-gate edit, identify the relevant 2D/normalized landmarks from the approved reference.

Required landmark families:
- head: nose tip, skull center, skull rear, crest root, crest rear extent
- neck: dorsal neck root, ventral neck root, skull-neck junction
- torso: shoulder high point, anterior thorax, sternum low point, waist low point, pelvis high point
- forelimb: shoulder, elbow, wrist, foot contact
- hindlimb: hip, knee, hock, foot contact
- tail: tail root, major bend, terminal extent

The goal is not millimeter reconstruction. The landmarks prevent semantic prompt words such as "compact", "athletic", or "swept" from being interpreted arbitrarily.

## Gate A subdivision

Gate A is no longer one full-body correction pass.

### Gate A1 — head / crest / neck

Editable:
- head
- crest
- neck

Keep fixed:
- thorax
- waist
- pelvis
- all four limbs
- feet
- tail

Acceptance:
- no single horn or paired horn reading from FRONT/BACK
- crest reads as skull-integrated, layered and rear-swept
- head remains small and wedge-like
- neck is shorter/thicker than rebuild-v1 and does not read as a tube
- skull-to-neck and neck-to-thorax flow are coherent in SIDE and FRONT34

Required review:
- SIDE
- FRONT
- FRONT34
- BACK

Stop after render and review.

### Gate A2 — thorax / waist / pelvis

Only after A1 is accepted.

Editable:
- thorax
- shoulder mass
- waist
- pelvis

Keep fixed:
- accepted A1 head/crest/neck
- limbs below their roots
- feet
- tail

Acceptance:
- torso reads compact rather than long/flat
- shoulder mass is visible but not bulky
- waist rises clearly from thorax
- pelvis remains light and athletic
- dorsal and ventral silhouettes are continuous

### Gate A3 — limb joint rhythm

Only after A2 is accepted.

Editable:
- forelimb and hindlimb primary masses and joint positions
- feet only as required for contact/readability

Acceptance:
- forelimb and hindlimb do not share the same rod construction
- shoulder/elbow/wrist and hip/knee/hock are legible in silhouette
- distal segments are lighter
- feet remain small and non-hoof/non-paw

### Gate A4 — tail

Only after A3 is accepted.

Editable:
- tail only

Acceptance:
- aerodynamic
- integrated at pelvis
- shorter and cleaner than rebuild-v1 if required by reference
- restrained terminal blade/feather shape
- no club tail

### Gate A5 — global silhouette review

No free remodeling.

Render:
- SIDE
- FRONT
- FRONT34
- REAR34
- BACK

Review the whole creature against the approved reference. If one region fails, reopen only that sub-gate.

## One-change discipline

Within a sub-gate, prefer one morphological hypothesis per revision.

Do not simultaneously change unrelated regions just because they also look wrong.

For each revision record:
- target
- keep_fixed
- actual vertices/objects changed
- expected effect
- observed effect
- KEEP / REVISE / REJECT

## Forbidden until Gate A is accepted

- eyes
- facial detail
- Cue Band
- materials
- texture/color design
- final retopology
- rigging
- animation
- decorative anatomy
- generic deer/horse/dog anatomy substitution
- smoothing modifiers that alter non-target geometry

## Production sequence after Gate A

Only after global silhouette acceptance:

Gate B:
- anatomical massing
- shoulder/chest planes
- crest-root integration
- joint massing
- foot construction
- tail-root integration

Gate C:
- sculpt cleanup / production surface
- retopology for deformation
- rig preparation
- materials
- Cue Band
- animation

## Failure rule

If a result technically satisfies prompt words but visually misses the approved reference, it fails.

Do not explain the mismatch away as style, interpretation, low-poly abstraction, or future refinement. Correct the morphology before proceeding.
