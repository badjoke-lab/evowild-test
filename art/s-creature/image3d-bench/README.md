# S-type image-to-3D benchmark — ISOLATED / NOT AN APPROVAL

**Branch:** `exp/s-image3d-benchmark-20261008` (created from `exp/s-creature-vibe-modeling`).

**Safety:** No changes to `feat/s-creature-model`, no replacement of S references, no Actions/workflows, no paid GPU provisioning, and no automatic merge.

## Verified existing baseline

- Single authoritative image: `art/s-creature/references/00_s_type_modeling_image_v1.png` — use the exact original PNG.
- R0 morphological reference: `art/s-creature/output/S-authority-r0-a5-v2.blend`.
- Approval record: `art/s-creature/S_AUTHORITY_R0_A6_REVIEW.md` — only **R0 morphology** accepted, *not* a production-ready animated model.
- Next modeling gate: **R1-A1**, surface and junction continuity of shoulder/proximal forelimb and pelvis/proximal hindlimb.

## Experiment A / B

A: **Pixal3D** with the locked original PNG, one unmodified GLB output.

B: **TRELLIS.2** with the **same PNG**, one unmodified GLB output.

Record for each: official model or Space URL, exact revision (if available), input PNG SHA-256, parameters, seed (if available), upload visibility/privacy, pricing/quota, inference success/failure, queue and generation time, downloaded GLB SHA-256, and original texture files.

**Do not assume that third-party hosted demos keep input private.** Before uploading the authoritative PNG to any public hosted Space, verify its visibility/data rules and that upload is permitted.

Multi-view conditioning, if available, is experiment C, tested separately; only actual approved existing view images may be used. Do not synthesize new S design material.

## Audit & acceptance

First run the advisory geometry audit on downloaded raw GLBs (requires Python, numpy, trimesh):

```bash
python -m pip install 'numpy>=1.24' 'trimesh>=4.0'
python art/s-creature/image3d-bench/audit_glb.py pixal3d-original.glb -o pixal3d-audit.json
python art/s-creature/image3d-bench/audit_glb.py trellis2-original.glb -o trellis2-audit.json
```

The audit reports mesh count, triangle count, bounds, boundary/nonmanifold edges, and degeneracy. It **does not** approve a model or establish reference-image fidelity, riggability, commercial licensing, or animation readiness.

Then import both GLBs and the R0 source into Blender. Normalize world scale and consistent anatomical direction (head/foot/tail), and render SIDE / FRONT / FRONT34 / REAR34 / BACK with the same orthographic camera framing and lighting. Compare against **original locked S image**, not an imagined variant.

### Hard visual checks

- Paired dominant rear-swept crest blades, not generic horns, rabbit ears, or a single horn.
- Long forward head/neck, broad athletic shoulder/thorax, deep abdominal tuck, supported pelvis/hindquarter.
- Long slender limbs with distinct angular joints, not fused/limbless or generic dog/deer legs.
- Specialized split racing feet, not undifferentiated blobs.
- Long layered blade/feather trailing tail, not short blunt tube.
- Coherent shoulder + upper forelimb, and pelvis + upper hindlimb junction surfaces.
- Five-view consistency, silhouette and mesh continuity.
- Measure time *including* needed cleanup, retopology, and rig preparation. A quick raw GLB alone does not prove an overall speed gain.

**Disposition:** `REJECT` if authority morphology materially differs; `REVISE` if recoverable with bounded labor; `CONSIDER` only with five-view evidence, quality and time measurements. Nothing here can automatically mark a new model `KEEP`.

## Status — 2026-10-08

| Check | Result |
|---|---|
| Authoritative PNG exists | VERIFIED via GitHub |
| R0 morphology approved | VERIFIED by repo review |
| Isolated benchmark branch | CREATED |
| GLB audit code | COMMITTED; tested with synthetic cube |
| Pixal3D actual S inference | NOT RUN |
| TRELLIS.2 actual S inference | NOT RUN |
| Real generated GLB / five views | NOT AVAILABLE |
| Comparative performance/time result | UNKNOWN |
| Existing S production changes | NONE |

This lane records real measurements; it does not substitute planning documents for actual 3D generation.
