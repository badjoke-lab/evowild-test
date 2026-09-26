# EvoWild Run — Astra S Modeling Handoff v1

Status: **ACTIVE / S ONLY**

This is the modeling handoff for the first production-candidate S creature.

## Absolute rule

Do **not** continue P / E / A modeling from the current procedural Motion First bodies.

The existing procedural S/P/E bodies are motion/camera test fixtures only.

The next accepted creature model must start with **S** and must be modeled against the repository references below.

## Canonical references

Use these in this order:

1. `docs/references/evowild-creature-reference-sheet-20260921.jpg`
2. `public/concept/S.webp`
3. `public/concept/s-run-sheet.svg`
4. `docs/motion-first-creature-standard-v0.1.md`

Do not use the current procedural S mesh as a shape reference.

## S target

The S candidate must read as the repository Sprint morph:

- narrow athletic torso
- long legs
- small restrained head
- long rearward directional crest line
- light rear body
- long balancing tail
- clearly non-real-world quadruped anatomy
- Cue Band integrated into the head
- same species language as future P/E/A variants

The model must not read primarily as:
- shrimp / crustacean
- deer
- horse
- goat
- dog
- dinosaur
- insect
- toy / mascot

## Required modeling deliverable

Create one complete S creature as a standalone 3D model.

Preferred output:

- `public/models/astra/s-v1.glb`

If GLB export is not possible at the modeling stage, provide the highest-fidelity source asset available and record the format in the manifest.

Required state:

- full body
- neutral standing pose
- four clearly separated limbs
- no rider
- no saddle
- no environment
- no pedestal
- no extra accessories beyond Cue Band
- no animation required in the first modeling pass
- no P/E/A variants in this task

## Required viewpoints before acceptance

The same model must survive:

- SIDE
- FRONT
- REAR
- 3/4 FRONT
- 3/4 REAR
- LOW 3/4

A model that looks acceptable only from SIDE fails.

## Visual acceptance checklist

Before integration, compare directly against the references and answer yes/no for each:

- [ ] overall S silhouette materially matches the reference
- [ ] head is small enough
- [ ] head is not a recognizable existing-animal face
- [ ] crest is integrated into the head/neck line
- [ ] torso is narrow and athletic
- [ ] chest/pelvis are one organism, not disconnected lumps
- [ ] legs are long but not stick/insect-like
- [ ] feet have the intended non-real-animal structure
- [ ] tail is integrated into the rear body
- [ ] Cue Band is fitted to the head and does not dominate it
- [ ] FRONT view preserves species identity
- [ ] LOW view does not expose disconnected geometry

If any item is no, revise S before handoff.

## Technical constraints for integration

The Motion First runtime already supports:
- multi-camera inspection
- distance-coupled gait
- IK / planted stance checks
- SIDE / LOW / CHASE / FRONT review

The model should therefore favor:
- clean separated limb chains
- clear shoulder / hip attachment points
- predictable forward axis
- clean neutral transform
- no baked camera
- no giant scene scale
- no hidden geometry used only to fake one view

## Handoff metadata

When the model is ready, add/update:

`public/models/astra/s-v1.manifest.json`

with:

- source
- format
- scale
- forward axis
- up axis
- polygon count
- material count
- texture list
- rigged: true/false
- animated: true/false
- reference version
- notes

## Integration gate

Do not wire the Astra S into Motion First until the model itself passes the visual checklist.

After it passes, the next step is:

Astra S model
→ Motion First rig adapter
→ SIDE / LOW / CHASE / FRONT
→ gait validation
→ only then P/E/A derivation.
