# T1 TRELLIS.2 Decision — clean input seed 0

Decision: **T1_KEEP**

Source generation:
- Run: `37458478227`
- Engine: `microsoft/TRELLIS.2`
- Input: `primary_clean_v1.png`
- Resolution: 1024
- Seed: 0
- Persisted candidate commit: `7372a3210e3d63beae5326bb34002c2574ac9144`

Baseline:
- `S-vibe-b1a-v2.blend`
- Decision in its own lane: REVISE

## T1 morphology comparison

The TRELLIS.2 candidate is kept because it is visibly closer to the locked S reference than B1a-v2 on enough of the T1-only morphology criteria to justify mesh validation.

| Criterion | B1a-v2 | TRELLIS.2 seed 0 | T1 result |
|---|---|---|---|
| small wedge head | very simplified blunt wedge | clearer small tapered head | TRELLIS closer |
| skull-integrated rear-swept crest | separate/simple blade masses | more integrated layered rear-swept crest | TRELLIS closer, but too long |
| long non-tubular neck | strongly tube-like | more shaped transition into shoulder/chest | TRELLIS closer |
| compact athletic thorax | flat/simple trunk | clearer thorax, abdomen and hip mass | TRELLIS closer |
| shoulder/chest transition | abrupt blockout transition | more continuous organic transition | TRELLIS closer |
| fore/hind limb differentiation | crude stick-like segmentation | clearer different fore/hind structure and joint rhythm | TRELLIS closer |
| overall S silhouette | recognizable but highly schematic | more reference-like organic sprint morph | TRELLIS closer overall |

## T1 defects that do not invalidate T1_KEEP

- crest is too long/exaggerated
- tail/body rear geometry is not clean
- detached shard-like geometry is visible
- feet and distal limbs still need scrutiny
- exact proportions are not approved final morphology

T1 intentionally does not approve topology, watertightness, UVs, rigging or animation.

## Raw mesh result

The raw GLB is **not** acceptable as a game/deformation mesh.

`mesh-audit.json`:
- vertices: 209,427
- faces: 298,794
- connected components: 5,807
- watertight: false
- is_volume: false
- boundary edges: 114,128
- non-manifold edges with >2 faces: 0
- duplicate vertex positions (rounded 1e-8): 60,123

Therefore:

- morphology candidate: **KEEP**
- raw mesh for T2: **REJECT_RAW / repair required**
- motion/rig gate: **DO NOT ENTER**
- next operation: test topology-preserving weld / component consolidation before any decimation or retopology claim

The S mainline is unchanged.
