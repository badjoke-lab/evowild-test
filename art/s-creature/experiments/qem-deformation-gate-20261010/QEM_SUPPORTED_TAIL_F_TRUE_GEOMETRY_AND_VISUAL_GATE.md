# EvoWild S — actual connected supported QEM tail F review (2026-10-11)

**Result:** PASS for connected-manifold topology and constrained finite real-mesh deformation; **REJECT for canonical S visual morphology**. No rig motion after geometry modification. Production S remains 0.

## Immutable source and intended authority

- Official top-priority design `art/s-creature/references/00_s_type_modeling_image_v1.png`, SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
- Actual original TRELLIS2 repaired QEM GLB SHA256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`.
- Original QEM source unchanged, with 29,948 vertices/59,932 faces; real 13-bone/IK successful experiments remain separate, **not retested on F**.
- Derived A/C input retained without edits. This is a **topology-changing** derivative of sewn C. The F mesh has 30,514 vertices / 61,064 triangle faces.

## Executed Blender 4.3.2 topology and deformation inspection

| Test | Actual result | Technical gate |
| --- | --- | --- |
| Connected components | 1 | PASS |
| Boundary and nonmanifold edges | 0 | PASS |
| Supported local edge refinement | Applied to 3 integrated real tail plate regions | Done |
| Requested plate-sweep magnitude | 0.130 normalized world model units | Attempted |
| Adaptive projected displacement retained | **51.13%** | Recorded, not full target |
| Maximum actual vertex movement | ~0.09981 normalized world units | Nonzero |
| Constraint solver iterations | **15** (0–14), originally 67 violating faces | Verified |
| Face flips / area <0.5x / area >2x | **0 / 0 / 0** | PASS |
| Smallest and largest triangle area ratio after support-topology rest | **0.50316 / 1.98929** | PASS but close to both limits |
| Body, legs, 13-bone skinning or gait on F | **NOT EXECUTED** | NOT APPROVED |
| Self-intersection or thickness clearance | **NOT EXECUTED** | NOT APPROVED |

Blender run [38065686701](https://github.com/badjoke-lab/evowild-test/actions/runs/38065686701) completed; preserve exact full solver logs, every iteration, affected face IDs and per-face gates in `tail-supported-f-v1/F_CONSTRAINED_TAIL_QA.json`. Full editable model: `tail-supported-f-v1/S-QEM-actual-supported-tail-F-TRIAL.blend`.

## Real visual comparison checked

- Full five-view 10-image comparison: `tail-supported-f-v1/review/REAL_QEM_CONSTRAINED_F_FIVE_VIEW_COMPARE.jpg`.
- Magnified real geometric SIDE / REAR34 tail inspection: `tail-supported-f-v1/review/REAL_QEM_CONSTRAINED_F_TAIL_DETAIL.jpg`.

The F variant preserves one coherent tail and improves controlled sweep without local face inversion. **But the plates continue to look like large upright rectangular tabs, not the S authority's long swept layered feather/laminae**. Its body and leg silhouette remain the original rejected donor. Geometry checks cannot correct design mismatch. **Visual gate = REJECT.**

The previous E first attempt (subdivided but unconstrained) gave one connected manifold 30,514/61,064 mesh but many flipped/underhalf/overdouble faces even at 0.010. The F adaptive actual-face solver finds a constrained numerical PASS but no corresponding morphologically adequate final asset. Do not claim the production S tail is solved.

## Mandatory next intervention

**Stop automatic scaling/tweaking of rectangular C cap regions.** The failure is fundamentally in their 3D contour, edge flow and blade shape, not merely contact, area, or numerical deformation. Construct a genuinely new tail authored against authority: narrow swept tapered blades with longitudinal supporting edge loops and actual overlaps, attached through source-skin patch replacement rather than detached proxy fins. Re-render the same SIDE/FRONT/FRONT34/REAR34/BACK and zoomed SIDE/REAR34, check manifoldness AND self-intersections, then obtain explicit S-design visual pass. Until then, keep C and F only as failure/feasibility evidence. Re-rig and 97-sample gait contact validation must be rerun after any changed topology.

Torso independent face-localization is in `exp/s-qem-torso-face-audit-20261011`: problematic polygon **20958** (vertices 12566/13507/12944), limited original-topology adjustment PASS at offset 0.050. Still not visual S approval.

**No main merge. No S-type production approval.**
