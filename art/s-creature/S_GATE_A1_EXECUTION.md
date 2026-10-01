# EvoWild Run — S Gate A1 Execution Brief

Status: READY TO EXECUTE
Branch: exp/s-creature-vibe-modeling
Input model: art/s-creature/output/S-rebuild-v1.blend
Output model: art/s-creature/output/S-rebuild-v2-a1.blend

## Objective

Correct only the head / crest / neck silhouette of the S-type creature.

Do not perform a full-body revision.

## Read first

1. art/s-creature/S_MODELING_IMAGE_LOCK.md
2. art/s-creature/S_CREATURE_MODELING_WORKFLOW.md
3. art/s-creature/S_MORPHOLOGY_RESET_PLAN.md
4. art/s-creature/CHECKPOINT.md
5. art/s-creature/HANDOFF_STATE.json

Reference images:
- art/s-creature/references/00_full_reference.png
- art/s-creature/references/01_s_body_primary.png
- art/s-creature/references/02_s_silhouette.png

## Hard scope lock

Editable:
- head
- crest
- neck

Must remain fixed:
- thorax
- waist
- pelvis
- forelimbs
- hindlimbs
- feet
- tail

Forbidden:
- full-body reshaping
- chest edits
- limb edits
- tail edits
- materials
- textures
- Cue Band
- facial detail
- rigging
- animation
- final retopology
- global smoothing that changes non-target geometry

## Before editing

Record:
- target landmarks
- keep-fixed regions
- exact intended silhouette changes
- review cameras

Use SIDE and FRONT reference comparison. Prefer an in-camera/background reference overlay or equivalent deterministic overlay.

Required A1 landmarks:
- nose tip
- skull center
- skull rear
- crest root
- crest rear extent
- skull-neck junction
- dorsal neck root
- ventral neck root

## Required morphology change

Head:
- keep small wedge-head intent
- do not enlarge into horse/deer head

Crest:
- eliminate any paired-horn or vertical-prong reading in FRONT/BACK
- keep multiple layered elements
- integrate the roots into the skull
- sweep the visible mass rearward
- avoid antler, unicorn, or sagittal-spike language

Neck:
- reduce the long, thin, tube-like read
- shorten and thicken relative to rebuild-v1
- preserve a light sprint profile
- make skull-to-neck and neck-to-thorax transitions coherent
- do not convert it into a deer/horse neck

## Save

Save as:
art/s-creature/output/S-rebuild-v2-a1.blend

Never overwrite S-rebuild-v1.blend.

## Required renders

- art/s-creature/output/review/rebuild-v2-a1/S_rebuild_side.png
- art/s-creature/output/review/rebuild-v2-a1/S_rebuild_front.png
- art/s-creature/output/review/rebuild-v2-a1/S_rebuild_front34.png
- art/s-creature/output/review/rebuild-v2-a1/S_rebuild_back.png

## Validation before stopping

Confirm:
- non-target body geometry is unchanged
- no horn-like read from FRONT/BACK
- crest mass flows rearward
- neck no longer reads as a long tube
- head remains small
- no materials/detail/rig/animation were added

## Stop condition

After saving and rendering the four required views:

STOP.

Update CHECKPOINT.md and HANDOFF_STATE.json with:
- actual geometry changed
- validation result
- render paths
- decision status = REVIEW_PENDING

Do not start Gate A2.
