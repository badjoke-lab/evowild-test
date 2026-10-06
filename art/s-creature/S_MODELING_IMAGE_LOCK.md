# EvoWild Run — S-type Modeling Image Lock v1.0

Status: APPROVED MODELING TARGET
Scope: S / Sprint type only
Branch: feat/s-creature-model

## Source-of-truth order

1. The approved **S-type Modeling Image v1.0** shown in the current review thread is the primary global morphology target.
2. Repository references `references/00_full_reference.png`, `references/01_s_body_primary.png`, and `references/02_s_silhouette.png` remain species/design constraints.
3. `S-blockout-v12.blend` is a technical donor/checkpoint only. It is **not** a morphology source and must not be patched into the final silhouette if it conflicts with this lock.
4. Older v1-v11 renders/scripts are historical only.

## Global read to lock before detail

The S creature must read as a purpose-bred alien racing organism: slim, fast, long-limbed, forward-balanced, and unmistakably non-deer/non-horse/non-dog.

The first acceptance test is silhouette, not surface quality.

### Head / crest

- Small wedge-shaped head with restrained eye mass.
- No deer/horse muzzle, no beak-like bird head.
- **No single sagittal horn, spear, unicorn horn, or vertical central spike.**
- Crest is a group of **backward-swept laminar plates/blades integrated into the skull**.
- Main plates flow rearward from the cranium and overlap in silhouette.
- Crest must visually belong to the skull, not read as attached antlers/horns.
- Front view should show a narrow head with layered crest width, not one central needle.

### Neck

- Long but not tubular.
- Tapers toward the head and broadens smoothly into the shoulder girdle.
- Ventral and dorsal neck lines must transition into the thorax without a hanging pouch or hard shelf.
- Keep the sprint silhouette forward and light; do not make a swan/deer neck.

### Torso / shoulder / pelvis

- Compact athletic thorax; no barrel body.
- Shoulder mass is readable but not oversized.
- Chest-to-abdomen transition rises toward a narrow waist.
- Pelvis is elevated and athletic, not heavy.
- Dorsal line should be continuous with a mild shoulder-to-hip rhythm, not separate humps.
- Side silhouette must feel fast before any texture/material is added.

### Limbs

- Long limbs, but not rods.
- Forelimb and hindlimb must have different joint rhythm.
- Shoulder/elbow/wrist and hip/knee/hock must be readable in silhouette.
- Distal limbs are light and narrow.
- Feet are small multi-toed racing feet, not hooves and not paws.
- Do not use familiar horse/deer anatomy as the default proportion template.

### Tail

- Long, tapered, aerodynamic tail integrated into the pelvis.
- Terminal shape may broaden into a restrained blade/feather-like silhouette.
- No heavy club tail.

## Approximate normalized proportion targets

These are modeling guides, not millimeter constraints. Normalize shoulder-to-ground height to 1.00.

- head length: ~0.27–0.32
- skull width: ~0.16–0.20
- neck base-to-skull length: ~0.55–0.65
- torso shoulder-to-hip length: ~0.85–0.95
- thorax maximum depth: ~0.36–0.43
- waist depth: ~0.22–0.28
- crest rearward reach from skull root: ~0.45–0.60
- pelvis width/depth must remain lighter than a power-type body

The target is the approved image; these ranges only prevent drift.

## Hard fails

Reject immediately if any of these appear:

- single central horn/spike
- antler-like crest
- deer/gazelle/horse silhouette
- tube neck
- barrel torso
- hanging sternum pouch
- rod limbs
- identical fore/hind limb structure
- hoof-like feet
- pasted-on shoulder/crest/tail pieces
- morphology that only works from one camera angle

## Rebuild policy

Do **not** continue incremental v12 chest polishing.

Create a new morphology rebuild from the approved target while reusing only technical pieces that still match it.

### Gate A — silhouette cage

Build a low-complexity S silhouette cage first:
- head
- layered swept crest
- neck
- thorax
- waist
- pelvis
- four limbs with explicit joints
- tail

No eyes, Cue Band, textures, surface pattern, color, micro-detail, or final topology.

Required renders:
- SIDE
- FRONT
- FRONT 3/4
- REAR 3/4
- BACK

Gate A is accepted only if the creature matches the approved modeling image in global silhouette and no hard-fail trait is present.

### Gate B — anatomical massing

Only after Gate A:
- shoulder/chest planes
- head/crest root integration
- fore/hind joint massing
- feet
- tail root

### Gate C — production refinement

Only after Gate B:
- final topology/retopology
- rig preparation
- materials/color
- Cue Band
- animation

## Working rule

At every modeling step, ask: “Does this move the silhouette toward S-type Modeling Image v1.0?”

If not, do not keep the edit.


## v2.0 authority override — exact repository image

The highest authority is now the exact repository file:

`art/s-creature/references/00_s_type_modeling_image_v1.png`

Verified identity:

- 1448 × 1086 PNG
- 1,982,782 bytes
- SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`

If anything earlier in this file conflicts with that image, ignore the older sentence and follow the image.

Visible anchors that must be preserved:

- two dominant elongated blade-like head crests, separated in FRONT/BACK;
- narrow wedge-like head;
- long dark neck;
- strong shoulder/chest mass followed by a deep waist tuck;
- streamlined pelvis / upper hindquarter;
- very long light limbs with distinct fore/hind chains;
- compact split racing feet;
- long layered blade/feather tail.

Therefore the following older interpretations are explicitly superseded:

- “paired tall crest blades are a hard fail” — false for the approved image;
- “generic multi-toed feet” as the target — too vague / wrong;
- “short S tail” — wrong for the approved image.

Review must still use SIDE / FRONT / FRONT34 / REAR34 / BACK, but the exact approved image is the deciding authority.
