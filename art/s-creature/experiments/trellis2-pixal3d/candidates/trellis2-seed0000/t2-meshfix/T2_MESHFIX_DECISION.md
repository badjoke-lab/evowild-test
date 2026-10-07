# T2 MeshFix visual decision

Decision: **KEEP_AS_WATERTIGHT_SOURCE**

This is an intermediate T2 decision, not final `T2_KEEP` and not authorization for rig/motion.

## Evidence

Source: exact-weld largest component.

Repair:
- method: `pymeshfix.MeshFix.repair`
- vertices: 132,330 -> 131,752
- faces: 264,856 -> 263,544
- connected components: 1 -> 1
- boundary edges: 0 -> 0
- non-manifold edges (>2 faces): 56 -> 0
- watertight: false -> true
- volume: false -> true
- symmetric p95 surface drift / source bbox diagonal: 0.004592

Five-view review:
- SIDE: no visible silhouette loss from repair.
- FRONT: shoulder/chest width and limb spacing remain visually unchanged.
- FRONT34: crest, neck, thorax, limbs and tail remain visually unchanged.
- REAR34: hindquarter, rear-leg proportions and crest silhouette remain visually unchanged.
- BACK: bilateral width and rear silhouette remain visually unchanged.

No repair-induced morphology regression is visible at the review resolution.

## Why this is not final T2 approval

The repaired mesh is still about 263k triangular faces and does not yet establish game deformation suitability or useful edge flow.

## Next

Run the **actual LODTailor Blender worker used by the PixelArtistry game-ready workflow**, pinned to upstream commit
`3d25b7d4aa382fa5dac210eb5d8d0eadc4a4f183`, against this repaired mesh.

First target: 60,000 triangles, no voxel rebuild. Preserve the watertight source as much as possible, then audit topology/drift and render the same five views.
