# EvoWild Run — original-QEM integrated-tail D lamina experiment, 2026-10-10

**Verdict: REJECT — both geometric quality and S authority morphology.**

Canonical S design `art/s-creature/references/00_s_type_modeling_image_v1.png` SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`. Immutable QEM donor GLB SHA256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`.

Input is the real one-component, closed manifold C derived QEM mesh: 30,029 vertices and 60,094 triangle faces (original donor 29,948 / 59,932 kept separately). D bends only the tops of three C sewn patches using a shape key; retains C connectivity and topology, but **topology preservation does not imply acceptable evaluated triangle quality**.

## Real Blender mesh deformation gate (D)

| Plate tip growth | Flipped faces | Smaller than 0.5x source C area | More than 2.0x source C area | Verdict |
| ---: | ---: | ---: | ---: | --- |
| 0.22 | 3 | 2 | 78 | FAIL |
| 0.17 | 3 | 3 | 26 | FAIL |
| 0.13 | 3 | 5 | 7 | FAIL |
| 0.09 | 0 | 7 | 4 | FAIL |
| 0.05 | 0 | 6 | 1 | FAIL |

At the smallest listed trial, measured min/max face area ratios were **0.346 / 5.031** relative to C. Report includes *all* candidates and their exact deformation values at `tail-tapered-d-v1/QEM_TAIL_TAPERED_D_QA.json`.

Blender 4.3.2 GitHub Actions: [38036811687](https://github.com/badjoke-lab/evowild-test/actions/runs/38036811687). The Action completes successfully because failure evidence is intentionally persisted; the **actual mesh quality gate is FAIL**.

## Actual visual evidence examined

- Five real original C vs tapered D view pairs: `tail-tapered-d-v1/review/REAL_QEM_SWEPT_D_FIVE_VIEW_COMPARE.jpg`.
- Real geometric **tail-only SIDE and REAR34 close-ups**: `tail-tapered-d-v1/review/REAL_QEM_SWEPT_D_TAIL_DETAIL.jpg`.
- Editable Blender: `tail-tapered-d-v1/S-QEM-tail-tapered-laminae-D-TRIAL.blend`.

At close scale the top pieces remain broad, visibly polygonal rectangular tabs instead of the canonical layered swept feather/laminae. Simple pulling of C's top vertices does not resolve this silhouette and creates large local triangle stretch. **No quality pass and no S-design pass.**

## Implementer next action and stop condition

**Stop varying the same C cap vertices.** Keep source, C manifold variant and D failure snapshots unchanged. Real next step is independent custom topological re-authoring of the tail with narrow longitudinal edge flow / sufficient support loops and manifold attachments, conforming to the canonical S design. New laminae need controlled taper and sweep in genuine 3D, not gray pasted polygons or texture tricks. Require: one connected closed mesh, zero nonmanifold edges, zero face area violations, no self-intersections, five real canonical-comparable views and preferably real shaded/material preview. Only AFTER visual acceptance transfer skin weights/re-rig and rerun true multi-cycle contacts. Same general principle for torso: original QEM topology is too sensitive to broad shape-key refits and requires localized patch repair.

**Production S type: 0. Main untouched. Game import forbidden.** No proxy replacement of the donor is allowed.
