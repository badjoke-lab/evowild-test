# S full-body zero rebuild — preserved source and review

This lane continues the saved 2026-10-17 model. The three original Blender files
are immutable inputs; no earlier model geometry is imported and no rebuild is run.

**Current decision: REVISE.** Five-view review and a focused shoulder/hip sculpt
are complete. See [quality review](QUALITY_REVIEW.md),
[reference comparison](comparisons/REFERENCE_COMPARISON.png), and
[revised working model](S_ZERO_CANDIDATE_REVISED_R1.blend).

- Original lane: `exp/s-fullbody-zero-rebuild-20261017`
- Preservation/review branch: `exp/s-fullbody-zero-verify-20261017`
- Base commit: `cde1bd7c8a26637d587aafd6d1d8cc4da8fb0315`
- Primary modeling PNG: `../references/00_s_type_modeling_image_v1.png`
- Repository species lock: `docs/creature-reference-index-v0.1.md` and the canonical sheet.
- Source models are experimental; preservation is not a production KEEP.

## Preserved files

| File | Bytes | SHA256 |
| --- | ---: | --- |
| S_ZERO_BLOCKOUT.blend | 1171877 | eb1b959264916d7512893c6c419ae2a056333b49b4165145b2b88f7ae518e502 |
| S_ZERO_REFINED.blend | 1178832 | 24f1b61d23c6eda67e3d9dbb39ce96c99ac11b6dbf375fffb9fc782dff4dcba5 |
| S_ZERO_CANDIDATE.blend | 1224567 | fac25ffe586cacd294c4d0b9f7ab4ae71f93595a3f70fcfa9354c5b44cbef29d |

All three files opened in Blender 4.3.2, build `32f5fdce0a0a`, without saving.
Their hashes matched before and after opening. All twelve existing PNG renders /
viewport captures plus the reference PNG passed decoding verification.

Evidence:

- `evidence/ORIGINAL_ARTIFACTS.json`: all 26 pre-existing files, sizes and SHA256.
- `evidence/VERIFY_SAVED_ORIGINALS.json`: load checks and per-mesh topology.
- `evidence/VERIFY_SAVED_ORIGINALS_UNSANDBOXED.log`: successful Blender run.
- `evidence/VERIFY_SAVED_ORIGINALS.log`: sandbox startup failure, before file loading.

The sandboxed Blender attempt crashed in Metal device initialization. The same
Blender executable completed outside that restriction. This was not a .blend
corruption. No external image dependencies, armatures or actions were present.

Each original mesh has no boundary/nonmanifold edges, loose vertices or
zero-area faces under the audit threshold. This does not prove that the entire
assembled creature is fused, that surfaces do not intersect, or that it is ready
to rig. The CANDIDATE collection contains 150 meshes plus one root empty.

Further review and corrections must use separate filenames. Main and all prior
branch tips must remain unchanged. Production promotion requires the complete
repository gates, including motion and PC/mobile runtime checks.
