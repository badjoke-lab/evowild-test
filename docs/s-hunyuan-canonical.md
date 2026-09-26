# EvoWild Run — Canonical S Asset: Hunyuan2MV

Status: **ACTIVE**

The active S visual baseline is now the Hunyuan-derived model family already proven in the 3D lane.

The procedural Motion First S and the locally generated Sol/Astra experiments are not active shape baselines.

## Canonical files

- Shape/edit source: `public/models/evowild-s/source-lod2.glb`
- Near/focus animated model: `public/models/evowild-s/focus-rigged-v31.glb`
- Multi-runner animated model: `public/models/evowild-s/race-lod4-rigged-v31.glb`
- Far/static LOD: `public/models/evowild-s/race-lod4.glb`
- Machine-readable mapping: `public/models/evowild-s/manifest.json`

These canonical files point to the same Git blob contents already validated in the earlier 3D / rig lanes; they are not newly regenerated meshes.

## Usage

### Shape work

Start from `source-lod2.glb`.

Do not use:
- procedural Motion First S geometry;
- rigged-v31 as the shape-edit master;
- LOD4 as the shape-edit master.

### Motion / close camera

Use `focus-rigged-v31.glb`.

It is the current stable near-camera animated candidate. v4 remains an IK experiment; an unverified v5 must not silently replace v31.

### Race population

Use `race-lod4-rigged-v31.glb` for animated S runners when several are on screen.

The static `race-lod4.glb` is reserved for future far-distance LOD switching; it must not replace animation for a visible racing creature just to save performance.

## Motion First integration

Motion First must now load the Hunyuan asset instead of drawing the procedural S.

- `?inspect=1&morph=S`: rigless LOD2 shape baseline.
- dedicated gait page / `?motion=1&morph=S`: high-detail rigged v31.
- normal 18-runner race: LOD4 rigged v31 for S entries.

The procedural S code may remain temporarily as a fallback implementation, but it must not be visible when the canonical Hunyuan asset loads successfully.

## Acceptance

The replacement is not complete merely because the GLB loads.

The integration must verify:
- the canonical GLB is actually visible;
- no procedural S remains visible behind it;
- gait mode has at least one animation clip or is otherwise driven by the validated v31 rig path;
- SIDE / LOW / CHASE / FRONT cameras keep the Hunyuan model in frame;
- replacing the visual does not degrade race speed or camera transitions.
