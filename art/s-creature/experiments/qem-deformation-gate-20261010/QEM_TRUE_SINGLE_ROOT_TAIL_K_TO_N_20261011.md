# EvoWild Run / S Type — Canonical-authority tail core rebuilt from true QEM, K–N (2026-10-11)

## Sole authoritative S design

**User-confirmed highest priority S TYPE / SPRINT MORPH modeling image:**
`art/s-creature/references/00_s_type_modeling_image_v1.png`
SHA-256 **`93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`**.
The pictured SIDE / FRONT / BACK / 3/4, HEAD & CREST, FOOT STRUCTURE and TAIL sections define the visual target; **no generated or substitute reference may supersede this file**.
Git blob `34e92e5f56e12f611b59c62381f7bc1f1ff015bc`.

Immutable donor real-QEM GLB: `art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb`; SHA-256 **`e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`**. Original **29,948 vertices / 59,932 triangles** protected and re-verified via code. **No R0/R1 proxy substitution. No main merge.**

## Actual Blender experiments (real 4.3.2 Actions, not flat images)

| Iteration | Actual change | Connected manifold / zero boundary / zero degenerates | Tail ROI BVH intersecting triangle pairs (excluding vertex-sharing triangles) | Visual authority |
| --- | --- | --- | ---: | --- |
| K | Test 64 real-QEM posterior cut sections | Identified actual original tail root **one 24-edge closed loop** at Y>1.58 / Z>1.32 / abs(X)<.30 | Not applicable; no mesh altered | No shape approval |
| L | **Replace 632 donor-tail triangles** from real open skin root with one 96-ring longitudinal tail, 5 molded ridges | PASS on **31,948 vertices / 63,932 tris** | **333 → FAIL** | REJECT (sawtooth dorsal edges, wrong feathers) |
| M | Fix 24-edge boundary angular order, eliminate downstream ring twist; change ridge continuity | PASS on **31,948 vertices / 63,932 tris** | **0 → PASS** | REJECT (small dorsal hump fins rather than stacked long laminae) |
| N | Increase dorsal thickness and include six upper/lower 3-D radial armor ridges | PASS on **31,948 vertices / 63,932 tris** | **0 → PASS** | REJECT (bulky slab/paddle instead of tapered, overlapping S feather blades) |

Exact measured QA:
- `tail-core-rebuild-k-v1/REAL_QEM_TAIL_BASE_SECTION_SCAN.json`
- `tail-core-rebuild-l-v1/REAL_QEM_TAIL_CORE_L_QA.json`
- `tail-core-regularized-m-v1/REAL_QEM_TAIL_CORE_M_QA.json`
- `tail-core-canopy-n-v1/REAL_QEM_TAIL_CANOPY_N_QA.json`

The 96 new longitudinal rings on **one continuous tube** avoid colliding appended pieces. The BVH result covers a **defined posterior tail ROI** (M/N each 6,083 triangle candidates), not a whole-body/global self-intersection certificate. All topology/edge/degenerate metrics cover the actual full evaluated derived mesh. They do not imply correct visual design.

### Actual Blender artifacts

- M **best technical geometry base**: `tail-core-regularized-m-v1/S-QEM-true-one-piece-tail-core-M-TRIAL.blend`.
- N broader-canopy variant **unapproved**: `tail-core-canopy-n-v1/S-QEM-true-one-piece-tail-canopy-N-TRIAL.blend`.
- Both have SIDE, FRONT, FRONT34, REAR34, BACK real original/variant comparisons, and an actual canonical-S source crop beside SIDE views.
- L comparison: `tail-core-rebuild-l-v1/review/CANONICAL_S_VS_ACTUAL_REBUILT_L.jpg`.
- M comparison: `tail-core-regularized-m-v1/review/CANONICAL_S_VS_ACTUAL_REBUILT_M.jpg`.
- N comparison: `tail-core-canopy-n-v1/review/CANONICAL_S_VS_ACTUAL_REBUILT_N.jpg`.

All original images are SHA checked by each workflow before Blender. Side comparisons preserve the *actual canonical image crop*, not a regenerated stand-in.

Actions runs: K [38103522030](https://github.com/badjoke-lab/evowild-test/actions/runs/38103522030), L [38103672755](https://github.com/badjoke-lab/evowild-test/actions/runs/38103672755), M [38103833700](https://github.com/badjoke-lab/evowild-test/actions/runs/38103833700), N [38103962187](https://github.com/badjoke-lab/evowild-test/actions/runs/38103962187). All workflow runs completed SUCCESS, but this is **NOT S morphology PASS**.

## Real visual review and hard engineering stop

Actual M and N five-view images were opened and inspected side-by-side with the canonical image.

The canonical tail extends from a strong hindquarter attachment as **several long rear-swept, overlapping, tapered armor/feather blades with differing lateral and vertical articulation**, blue/navy/white color/plate segmentation, and a recognizable sculpted tail profile. The donor's thin twig and M's small dorsal hummocks are nowhere close. N broadens the rear tail into an unarticulated paddle/slab, also incorrect. Gray Workbench cannot assess materials.

**Stop changing only sine/gaussian bump amplitudes on the common one-tube radial shell.** A closed single-valued radial shell is adequate for a connected technical base, not a faithful overlapping plate design. Further same-method tweaks waste iterations without resolving the visual goal.

Next necessary construction gate:

1. **Separate true laminae surface from core trunk topology in an ORIGINAL-QEM-connected derived mesh**, with deliberately authored overlap geometry, controlled longitudinal supporting edge loops, and contact-safe spacing. Do not use G–J's independently intersecting roots or detached generic fins.
2. Reference **SIDE + actual TAIL close-up + BACK + 3/4** simultaneously to place plate roots/tips/widths. Ensure sustained volume and taper; reject paddles, sawteeth and twigs.
3. Require **whole derived mesh** 1 connected component, 0 nonmanifold/boundary, 0 degenerates. Require independent tail ROI BVH self-intersections=0, plus global collisions where appropriate.
4. Design review must confirm **canonical morph proportions, head/crest, shoulder, abdomen, fore/hind leg and feet** separately. These remain REJECT/NOT APPROVED on current donor, irrespective of tail improvements.
5. **13-bone weights and 97-sample multi-cycle contact/deformation have not been transferred to M/N**. No assumption old gait PASS survives the new topology. Re-skin and re-run contact/gait only after visual shape is sufficiently faithful.

## Gate

- **K: PASS structural feasibility**
- **L: FAIL collision + visual**
- **M: PASS technical tail topology/intersections; REJECT S design**
- **N: PASS technical tail topology/intersections; REJECT S design**
- **Entire S production candidate: REJECT; approved S count = 0.**
- No production `main` changes, no game import, no performance claim.

This is an executed artifact review, not a project specification or a substitute standard.
