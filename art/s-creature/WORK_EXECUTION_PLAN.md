# Work execution plan — EvoWild Run S-model

## Model routing
Use models in this order. Do not restart the project from scratch when switching.

### 1. GPT-6 Astra — morphology-critical passes
Use Astra for:
- interpreting the S references
- creating the initial S-blockout-v1
- correcting silhouette/proportion problems
- fixing head/neck/torso/limb/crest integration
- any pass where visual judgment materially changes the mesh

Astra should spend its budget on editing the model, not on long reports, repository archaeology, or repeated full-sheet analysis.

### 2. GPT-6 Sol (or GPT-5.6 Sol if that is the Sol option shown in the Work model picker) — continuation/fallback
Switch to Sol when Astra is unavailable or its allowance is exhausted.
Continue the SAME task from the current files and `CHECKPOINT.md`.
Use Sol for:
- continuing an already-started modeling pass
- Blender Python fixes
- exports
- review renders
- topology/cleanup work that is already specified
- Git/file organization
- checkpoint updates

Do not ask Sol to re-research the project or reconstruct old conversation history.

### 3. Luna/Terra — housekeeping only
If available, use lighter models only for deterministic work such as:
- file moves/renames
- manifest/checksum updates
- basic export automation
- non-judgmental script edits

Do not use them for final morphology decisions unless no stronger model is available.

## Work start prompt
Open this package and continue the EvoWild Run S-type modeling task.
Read, in order:
1. `CHECKPOINT.md`
2. `ASTRA_TASK.md`
3. `references/01_s_body_primary.png`
4. `references/02_s_silhouette.png`

Do not audit old chat history. Do not work on P/E/A.
Run `blender/setup_scene.py`, create the S mesh from scratch, and work toward the current `next_action`.
Use the old procedural creature only for technical integration later, never as morphology reference.
Save the `.blend` frequently.
Before model/session limits interrupt the task, save the current `.blend` and update `CHECKPOINT.md`.

## Astra -> Sol switch prompt
Continue this exact Work task with the current files. Do not restart or re-audit.
Read `CHECKPOINT.md`, then continue `next_action` from the saved `.blend`.
Treat existing Astra work as the current source state, while the supplied S reference images remain the morphology source of truth.
S only. No P/E/A. Update `CHECKPOINT.md` after the next saved milestone.

## Work -> Chat / another Work session handoff
Transfer only:
- latest `.blend`
- latest `.glb` if present
- latest 4 review renders if present
- `CHECKPOINT.md`
- `HANDOFF_STATE.json`
- the reference package (only if the next environment does not already have it)

Do not transfer old conversation logs unless a concrete unresolved decision is missing from the checkpoint.

## Stop protocol
When near a limit, stop optional work and do this in order:
1. save current `.blend`
2. save any currently useful render(s)
3. update `CHECKPOINT.md`
4. update `HANDOFF_STATE.json` if stage/next_action changed
5. stop

A prose progress report is lower priority than the saved model and checkpoint.
