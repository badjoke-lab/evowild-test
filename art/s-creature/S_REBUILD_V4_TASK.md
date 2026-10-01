# EvoWild Run — S-type Gate A v4 execution task

Status: READY TO EXECUTE
Branch: `feat/s-creature-model`
Input model: `art/s-creature/output/S-rebuild-v3.blend`
Output model: `art/s-creature/output/S-rebuild-v4.blend`

## Read first

- `art/s-creature/S_MODELING_IMAGE_LOCK.md`
- `art/s-creature/S_MORPHOLOGY_RESET_PLAN.md`
- `art/s-creature/CHECKPOINT.md`
- `art/s-creature/HANDOFF_STATE.json`
- `art/s-creature/references/00_full_reference.png`
- `art/s-creature/references/01_s_body_primary.png`
- `art/s-creature/references/02_s_silhouette.png`

Always pull the latest remote `feat/s-creature-model` before opening Blender.

## Decision being executed

Gate A v3 = **REVISE**.

v3 is a meaningful improvement and the following are KEEP:

- fresh rebuild basis; do not return to v12 morphology
- small wedge-head direction
- low rearward multi-plate crest envelope
- shorter flared neck direction
- compact torso / narrow waist direction
- distinct fore/hind joint rhythm direction
- shorter tapered tail
- S-only scope

Gate A still fails because:

- crest plates still read as flat/pasted-on fins in FRONT / FRONT34
- distal limb segments still read as rods
- shoulder/pelvis-to-limb transitions are abrupt and geometric
- overall stance still reads too much like a generic ungulate instead of the approved alien racing organism

## v4 — one structural silhouette pass only

This is **still Gate A**. Do not perform Gate B surface refinement.

### 1. Crest root integration

Keep the current low, rearward crest envelope.

Modify only the skull/crest-root relationship enough that the plates emerge from and overlap the posterior cranium as one anatomical structure.

Required read:
- skull-integrated layered plates
- rearward flow
- no upright horn pair
- no single central spike
- no antler read
- no floating/pasted-on fins

Do not add eyes, facial detail, Cue Band, texture, color, or ornamental micro-detail.

### 2. Limb structural massing

Keep the established fore/hind chain topology and overall long-limbed sprint proportions.

Replace the visibly uniform rod read with low-complexity segment masses:
- shoulder / upper forelimb / elbow / distal forelimb must be distinguishable
- thigh / knee / lower hindlimb / hock must be distinguishable
- distal limbs remain light and narrow, but not constant-width cylinders
- fore and hind chains must remain visibly different

This is silhouette massing, not final anatomy.

### 3. Racing posture

Without changing the creature into a horse/deer/dog template, lower and compact the whole read toward the approved S silhouette:
- forward-balanced
- fast
- light
- compact athletic thorax
- narrow rising waist
- elevated but light pelvis

Do not make the thorax deeper/heavier than v3.

## Locked / forbidden

Do not:
- reuse v12 geometry as morphology input
- enter Gate B
- add surface polish, final topology, retopology, rigging, materials, color, texture, animation or Cue Band
- create a new branch
- modify P / E / A types
- turn the crest back into horns
- make feet hoof-like or paw-like
- make fore/hind limbs identical
- deepen the chest into a barrel body

## Required outputs

Save:
- `art/s-creature/output/S-rebuild-v4.blend`

Render exactly:
- `art/s-creature/output/review/rebuild-v4/S_rebuild_side.png`
- `art/s-creature/output/review/rebuild-v4/S_rebuild_front.png`
- `art/s-creature/output/review/rebuild-v4/S_rebuild_front34.png`
- `art/s-creature/output/review/rebuild-v4/S_rebuild_rear34.png`
- `art/s-creature/output/review/rebuild-v4/S_rebuild_back.png`

Update:
- `art/s-creature/CHECKPOINT.md`
- `art/s-creature/HANDOFF_STATE.json`

Then commit and push to the existing branch.

## Stop condition

After push:
- report the commit SHA
- report the five render paths
- **STOP**
- do not claim Gate A PASS
- do not enter Gate B

The review side will retrieve the five PNGs directly from GitHub by commit SHA. The user must not be asked to download and re-upload them.
