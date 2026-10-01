# EvoWild Run — S-rebuild-v2 Gate A Task

Status: READY
Scope: S only
Input: output/S-rebuild-v1.blend
Output: output/S-rebuild-v2.blend
Primary lock: S_MODELING_IMAGE_LOCK.md

## Gate A v1 decision

REVISE.

The fresh rebuild direction is correct, but the silhouette still misses the locked S target.

## Keep from v1

- Fresh-rebuild approach; do not use v12 morphology.
- Small wedge-head intent.
- Multi-plate crest concept.
- Narrow-waist intent.
- Separate fore/hind limb chains.
- Multi-toe foot intent.
- Low-complexity Gate A cage.

## Required v2 silhouette corrections

### 1. Head / crest — highest priority

Current failure:
- SIDE: plates are too large and read as separate flat fins.
- FRONT/BACK: the two tallest plates become a pair of upright horns.
- FRONT34: crest mass is too vertical and too far above the skull.

Required:
- Keep six total plate elements if useful, but reorganize them into 3 visual layers per side/root region.
- Lower the crest root and sweep all major plate tips rearward.
- No plate may read as a vertical spike in FRONT or BACK.
- Primary plates should overlap in SIDE, with their long axes approximately 25–40 degrees above the skull-to-tail direction, not near vertical.
- Shorten the two tallest plates by about 20–30% relative to v1.
- Increase root overlap with the posterior skull so the crest reads as skull-integrated.
- Keep head small; slightly broaden the posterior cranium while keeping the muzzle wedge narrow.

### 2. Neck proportion

Current failure:
- Too long, thin, and tube-like.

Required:
- Shorten effective skull-to-shoulder neck length by about 12–18%.
- Increase base depth/width near the shoulder by about 15–20%.
- Keep the upper neck light.
- Lower the head/neck carriage slightly so SIDE reads forward-racing rather than giraffe/deer upright.
- Dorsal and ventral lines must both flare into the thorax; no straight pipe section.

### 3. Torso / shoulder / waist / pelvis

Current failure:
- Torso too long/flat.
- Shoulder mass too weak.
- Pelvis and thorax do not create enough athletic rhythm.

Required:
- Shorten shoulder-to-hip torso length by about 8–12%.
- Increase anterior thorax depth/mass modestly while keeping a narrow waist.
- Raise the ventral abdomen toward the waist.
- Keep pelvis light and slightly elevated.
- SIDE silhouette should show: shoulder mass -> rising waist -> light elevated pelvis.
- FRONT should not become barrel-chested.

### 4. Limb joint rhythm

Current failure:
- Limbs read as rods and fore/hind chains are too similar.

Required:
- Forelimb: readable upper-arm/forearm break with a compact elbow; distal segment long and light.
- Hindlimb: stronger hip/thigh mass, forward knee, rearward hock, then narrow distal segment.
- Preserve overall long-legged sprint proportion.
- Do not add muscle detail; only silhouette joint massing.
- Feet remain small multi-toed, not hooves.

### 5. Tail

Current failure:
- Too long and blunt.

Required:
- Shorten total tail length by about 12–18%.
- Taper continuously from pelvis.
- Keep a restrained terminal blade/feather-like flare.
- Do not make a heavy club.

## Forbidden

- single central horn
- paired upright horn silhouette
- antler structure
- deer/gazelle/horse body read
- tube neck
- barrel chest
- rod limbs
- hoof feet
- Cue Band
- eyes/details
- textures/colors
- animation
- final retopology

## Stop condition

After the v2 edits:
- save output/S-rebuild-v2.blend
- render exactly SIDE / FRONT / FRONT34 / REAR34 / BACK
- update CHECKPOINT.md and HANDOFF_STATE.json
- commit and push to feat/s-creature-model
- STOP for Gate A review

Do not proceed to Gate B.
