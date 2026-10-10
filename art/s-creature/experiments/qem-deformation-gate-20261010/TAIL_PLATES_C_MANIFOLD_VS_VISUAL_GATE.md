# EvoWild Run S — QEM sewn tail plates C (2026-10-10)

## Actual executed status

**PASS on mesh connectivity/watertight manifold QA. REJECT on S tail appearance.**

Canonical S image is `art/s-creature/references/00_s_type_modeling_image_v1.png` (SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`). Original QEM donor is SHA-256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`.

### What physically changed

The source QEM still has **29,948 vertices and 59,932 faces**, unchanged. B's naive BMesh extrude caused 81 nonmanifold/boundary edges and visible low-value bumps. C replaces three existing original-tail skin face patches with elevated caps and individually sewn sidewalls on **one connected derived 3D mesh**. It does not paste three disconnected fins. This is a topology-changing derivative, *not* a source-QEM vertex-preserving deformation claim.

| Item | Trial B (FAIL) | Trial C (topology PASS) |
| --- | ---: | ---: |
| Result vertices | 30,088 | **30,029** |
| Result triangles | 60,287 | **60,094** |
| Connected components | 1 | **1** |
| Nonmanifold or boundary edges | 81 | **0** |
| Zero-area faces | 0 | **0** |
| Original source object unchanged | Yes | **Yes** |

C plate source-region triangle counts = 52, 60 and 81; sewn region perimeter quads = 24, 24 and 33. Geometry is real Blender 4.3.2 output, not a painted overlay. Saved in `tail-integrated-plates-c-v1/S-QEM-tail-sewn-plates-C-TRIAL.blend`. Full audit `tail-integrated-plates-c-v1/SEWN_TAIL_PLATES_C_QA.json`. Workflow [38036326179](https://github.com/badjoke-lab/evowild-test/actions/runs/38036326179) succeeded.

## Actual five-view visual assessment

Opened `tail-integrated-plates-c-v1/review/REAL_QEM_TAIL_A_VS_SEWN_PLATES_C_FIVE_VIEW.jpg` displaying 15 actual SOURCE / extended TAIL_A / SEWN_PLATES_C Blender views across SIDE, FRONT, FRONT34, REAR34, BACK.

The topology is now attached and watertight, but the three new appendages look like small rectangular tabs sitting atop a straight single-spur tail. They do **not** match the authority's elongated swept, layered, feather/blade-like armor tail. The head/crest, torso profile and foot anatomy are still not approved. The repeated comparable views are gray Workbench; coloration is **not evaluated**. New mesh self-intersection and post-retopology rig/weight/foot contact have **not been tested**.

**DESIGN: REJECT. MOTION ON DERIVED MESH: NOT TESTED. PROD MERGE: FORBIDDEN. FINISHED S: 0.**

### Next corrective principle

Redesign plate **profile and attachment** as a tapered swept lamina, not merely upward translation of existing same-width triangle patches. Preserve exact original/QEM & full C result separately. Topology correctness is necessary, not sufficient; run both manifold QA and actual five-direction appearance review before re-rigging and race QA.
