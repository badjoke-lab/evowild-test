# S-type TRELLIS.2 / Pixal3D Bench

Status: ACTIVE / EXPERIMENT ONLY

## Isolation

- Branch: `exp/trellis2-pixal3d-s-bench-20261004`
- Parent checkpoint: `exp/s-creature-vibe-modeling@07d87340345031d68834552f10561107a1560b88`
- Do not modify or merge into `feat/s-creature-model`.
- Do not modify the Vibe B1a/B1b sequence from this lane.
- No manual Blender morphology edits are allowed before Gate T1 is decided.

## Purpose

Test whether single-image 3D generation from the locked S reference can produce a morphology candidate that is visibly closer to the approved S-type than the current Vibe B1a-v2 baseline.

This lane does **not** assume that watertight mesh, retopology, rigging, or animation quality is acceptable. Those are later gates.

## Locked input

Primary image:

`art/s-creature/references/01_s_body_primary.png`

Supporting review references only:

- `art/s-creature/references/00_full_reference.png`
- `art/s-creature/references/02_s_silhouette.png`
- `art/s-creature/references/04_crest_structure.png`
- `art/s-creature/references/06_leg_foot_variants.png`

Baseline comparison:

- `art/s-creature/output/S-vibe-b1a-v2.blend`
- `art/s-creature/output/review/vibe-b1a-v2/S_vibe_b1a_v2_side.png`
- `art/s-creature/output/review/vibe-b1a-v2/S_vibe_b1a_v2_front.png`
- `art/s-creature/output/review/vibe-b1a-v2/S_vibe_b1a_v2_front34.png`
- `art/s-creature/output/review/vibe-b1a-v2/S_vibe_b1a_v2_rear34.png`
- `art/s-creature/output/review/vibe-b1a-v2/S_vibe_b1a_v2_back.png`

B1a-v2 remains REVISE in its own lane.

## Gate T0 — endpoint smoke test

Try one generation from each official public Space first:

1. Microsoft TRELLIS.2
2. TencentARC Pixal3D

Use only free/public execution. No paid GPU job or local GPU setup is authorized.

If an endpoint requires a Hugging Face token, the runner may use an already-configured `HF_TOKEN` secret if present; absence of that secret must fall back to anonymous access rather than creating a paid resource.

Outputs:

`art/s-creature/experiments/trellis2-pixal3d/raw/<engine>/<candidate>/`

Record endpoint schema, generation settings, seed if exposed, output filename, and failure reason.

## Gate T1 — morphology

After endpoint smoke test succeeds, produce up to three candidates per engine using the same locked input. Do not tune the source image separately per engine.

Render every candidate with the same neutral orthographic review cameras:

- SIDE
- FRONT
- FRONT34
- REAR34
- BACK

Evaluate only:

1. small wedge head
2. skull-integrated backward-swept layered crest
3. long but non-tubular neck
4. compact athletic thorax
5. shoulder/chest transition
6. forelimb vs hindlimb proportion and joint rhythm
7. overall S silhouette

Ignore at T1:

- texture quality
- watertightness
- face count
- UVs
- materials
- animation
- final deformation topology

### T1 stop rule

If every generated candidate is equal to or worse than B1a-v2 in the locked morphology criteria, STOP this lane. Do not install or run PixelArtistry watertight/game-ready processing.

If at least one candidate is visibly closer to the locked S references, keep only the best morphology candidate(s) and proceed to T2.

## Gate T2 — mesh viability

Only after T1 PASS:

- non-manifold edges / holes
- disconnected or internal geometry
- duplicate vertices
- face count
- decimation tolerance
- deformation topology around neck, shoulder, elbow, hip, knee/hock and tail root
- rig suitability

PixelArtistry / WTiVo / game-ready processing belongs here, not before T1.

## Gate T3 — motion viability

Only a T2-passing candidate may enter a separate rig/motion bench. Existing Tripo and BlendCap motion lanes remain independent comparisons.

## Decision vocabulary

- `T0_BLOCKED`: endpoint cannot be executed in the free path
- `T1_REJECT`: morphology does not beat the baseline
- `T1_KEEP`: morphology candidate merits mesh validation
- `T2_REJECT`: mesh is unsuitable for game deformation
- `T2_KEEP`: candidate merits motion test
- `T3_KEEP`: candidate can be considered for later integration

No result from this experimental branch changes the S mainline automatically.
