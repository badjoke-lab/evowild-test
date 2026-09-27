# EvoWild Run — S-type / Sprint morph modeling task

## Scope lock
- Model **one S-type / Sprint morph only**.
- Do **not** start P, E, or A.
- Do not use the old procedural creature as a morphology reference.
- The supplied reference sheet is the morphology source of truth.
- First objective is a credible **S-blockout**, not animation, texturing, or production rigging.

## Reference facts to preserve
From the supplied sheet:
- S = Sprint type.
- Slender body and long legs.
- Optimized for maximum speed.
- Small head and restrained eyes are intentional species-level traits.
- Do not make the face read as a collage of familiar real animals.
- Limb, joint, and body construction should have a distinct species logic.
- The creature must read as one coherent organism, not assembled parts.
- Head/crest/tail/leg/surface variants are intraspecies variation. They are not separate species.
- All race individuals eventually wear the race Cue Band; leave plausible head clearance, but do not spend the first blockout pass detailing the device.

## Primary morphology target for S
Prioritize these proportions before detail:
1. Small, narrow head mass.
2. Long rear-swept horn/crest silhouette.
3. Long, light neck-to-shoulder transition.
4. Narrow thorax/abdomen with readable ribcage vs pelvis masses.
5. Long limbs with explicit joint rhythm; no stick legs.
6. Light distal limbs/feet suitable for a sprint morphology.
7. Overall forward, fast silhouette rather than heavy or power-oriented massing.

Do not copy the exact colors as if they define anatomy. Shape takes priority.

## Work order
### Stage A — scene/bootstrap
1. Work in a dedicated branch/worktree if repository access is available.
2. Run `blender/setup_scene.py` inside Blender to create review cameras/collections.
3. Create a new mesh from scratch inside the `S_MODEL` collection.

### Stage B — S-blockout-v1
Block only:
- head
- neck
- thorax
- abdomen
- pelvis
- forelimbs
- hindlimbs
- tail
- major crest/horn mass

Do not add micro detail, texture, fur, decorative surface geometry, or animation.

### Stage C — self-review
Before doing another detail pass, render only these four views:
- front
- side
- front 3/4
- rear 3/4

Use `blender/render_review.py` after adjusting camera scale/target if needed.

Review against `references/01_s_body_primary.png` and `references/02_s_silhouette.png` first. Consult the head/crest/leg/tail crops only when that region is being corrected.

## Hard failure conditions
Do not advance to detail if any of these remain:
- head looks split down the middle
- front/rear views do not describe the same creature as side view
- front/back orientation becomes ambiguous
- torso is a tube
- limbs are rods
- joints are unreadable
- crest looks pasted on rather than structurally connected
- model drifts toward an obvious horse/deer/dog/dinosaur copy
- smoothing is hiding bad underlying form

## Review gates
### Gate 1 — S-blockout-v1
Required artifacts:
- editable `.blend`
- exported `.glb` if export is already stable
- 4 review renders
- updated `CHECKPOINT.md`

Gate 1 is only about silhouette, proportion, and multi-view coherence.

### Gate 2 — S-blockout-v2
Only after Gate 1 issues are corrected. Improve:
- head integration
- shoulder/chest volume
- pelvis/hindlimb rhythm
- joint structure
- crest root
- tail root

### Gate 3 — S-model-v1
Only after blockout is accepted. Secondary form/topology cleanup may begin.

## Context/capacity conservation
- Do not repeatedly re-describe the whole task.
- Do not generate large contact sheets every iteration.
- Default review output is exactly 4 views at each gate.
- Load the full reference only when necessary; use the cropped references for focused work.
- After every meaningful saved milestone, update `CHECKPOINT.md` so another agent can resume without reading conversation history.
- If tool/model/session limits are approaching, stop after saving the current `.blend`, renders if available, and checkpoint. Do not spend remaining budget on a prose summary.

## Stop rule
If interrupted for any reason, leave the project in a resumable state and update `CHECKPOINT.md`. The next agent should be able to continue from `next_action` without reconstructing prior reasoning.
