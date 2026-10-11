# EvoWild Run / S TYPE — Original-QEM sewn armor O→R, authoritative visual and geometry gate (2026-10-11)

## Canonical design and immutable geometry (do not change)

The **only user-confirmed highest-authority S design image** is `art/s-creature/references/00_s_type_modeling_image_v1.png`, SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`. This exact file is checked by each Blender workflow; no substitute generated image or approval assumption is permitted.

Original TRELLIS2 QEM donor GLB, SHA256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`: **29,948 vertices / 59,932 triangles, unchanged**. Technical core-tail M is also immutable, with **31,948 vertices / 63,932 triangles** and zero measured self-intersections in the defined tail ROI. **M is not an approved S design**.

## Real Blender 4.3.2 mesh deliverables

| Stage | Actual physical action | Topology result | Tail BVH intersecting polygon pairs | Decision |
| --- | --- | --- | ---: | --- |
| **O** | Carve 3 disjoint ACTUAL M surface patches and connect each hole to 10 longitudinal oval loft rings and an integrated tapered tip; three real thick S-like leaves on one actual mesh, not detached cards | **32,600 vertices / 65,236 triangles, one connected component, 0 nonmanifold/boundary, 0 degenerate** | **185** | FAIL collision; visual S not approved |
| **P** | O derivative non-destructive feather-surface displacement, 15 radial/longitudinal candidate trials | Identical connected source topology | Best **179**, but every candidate fails triangle quality gate | REJECT |
| **Q / proximal right alone** | Build only first leaf directly on the same immutable M core | 32,117 vertices / 64,270 triangles, manifold 1 component | **34** | FAIL |
| **Q / middle left alone** | Build only second leaf, no other new leaves present | 32,232 vertices / 64,500 triangles, manifold 1 component | **5** | FAIL |
| **Q / distal right alone** | Build only third leaf, no other new leaves present | 32,147 vertices / 64,330 triangles, manifold 1 component | **152** | FAIL |
| **R / independent cross-run root repeat** | Regenerate exact proximal Q from same real original M blend on fresh GitHub Actions runner with deterministic boundary selection | Vertex-position SHA-256 (quantized to six decimals) **identical across runs**: `ee349175201deb205800dc1b19eaebe38001295beb3a2ae373d9776c5cd7d104` | **34 reproduced** | **PASS reproducibility**, FAIL mesh collision |

The numerical self-intersection tests are actual Blender BVHTree overlaps on a documented posterior tail polygon-centroid ROI, excluding triangle pairs sharing a vertex. They are **not** a whole-body self-intersection or collision clearance certificate. 0 boundary/degenerate are **full derived-mesh** checks. Running an Actions job successfully is **not a geometry or design PASS**.

### Actual inspected visual evidence

- O editable authentic-QEM model: `tail-integrated-lamina-o-v1/S-QEM-original-connected-armor-laminae-O-TRIAL.blend`
- O real tail close-up (M vs O): `tail-integrated-lamina-o-v1/review/REAL_QEM_O_ARMOR_CLOSE_COMPARE.jpg`
- Exact reference and O/M side-by-side: `tail-integrated-lamina-o-v1/review/CANONICAL_S_VS_REAL_QEM_ARMOR_O.jpg`
- O 5 real views: `tail-integrated-lamina-o-v1/review/REAL_QEM_O_FIVE_VIEW_COMPARE.jpg`
- P actual 15 mesh scans: `tail-lamina-clearance-p-v1/REAL_QEM_P_CLEARANCE_QA.json`
- Q side-by-side all three single-plate actual Blender views: `tail-panel-isolation-q-summary/REAL_QEM_ISOLATED_THREE_LEAVES_Q.jpg`
- Q all three independent geometry numbers: `tail-panel-isolation-q-summary/THREE_REAL_TAIL_LEAVES_Q_REPORT.json`
- R full fresh independent Blender: `tail-panel-isolation-r-proximal-verified/S-QEM-single-panel-Q-PROXIMAL_RIGHT.blend`
- R cross-run SHA/collision proof: `tail-panel-isolation-r-proximal-verified/CROSS_RUN_REPRODUCIBILITY_GATE.json`
- R Actions [38113067192](https://github.com/badjoke-lab/evowild-test/actions/runs/38113067192) successfully ran and committed the uniquely named output.

### Corrected audit reproducibility

The initial O and early Q versions used Python set iteration / face selection ordering to start skin-hole boundary loops; *the same* one-leaf trial could previously yield different face intersection counts across Actions. **Do not cite those earlier Q numerical values as stable audited QA**. Q's script was corrected to choose the minimum original BMesh boundary vertex index and sorted component/edit order. R then independently confirmed the exact six-decimal vertex digest and the **34** same baseline self-intersections across Actions.

A later repeat-Actions build [38112827949](https://github.com/badjoke-lab/evowild-test/actions/runs/38112827949) passed in-run deterministic validation but failed **file push/rebase** because two concurrent workflows wrote the same artifact paths. This was a packaging conflict, not geometry acceptance. The R isolated branch and unique output path resolves this conflict; it completed and persisted new proof without overwriting Q.

### Design authority comparison and unavoidable next engineering change

Actual side/3/4/back render of O: distinct swept feather-like structures are now visible rather than M's sawtooth humps. However **these three leaves are not the canonical S tail**: too few/short/poorly overlapped and the donor full body, head crest, shoulders and leg-hoof geometry still differ materially from the original S TYPE / SPRINT MORPH art. Only technical topology connectivity was validated; neither visual morphology nor whole-body performance is accepted.

**O/P/Q/R have no approved in-game S asset. Do NOT import into main.**

**Stop shifting whole feathers or simply duplicating the 3 O root patches**. Each isolated patch collides. For next iteration, start with the least-bad **middle-left individual plate (5 collisions)**, examine its exact offending polygon IDs/3D triangles, then re-author **the root-to-first-loop transition and cap winding/orientation**; do not add more plates until an individually connected new blade has (a) full model one-component manifold 0 bad edges/faces (b) **zero** measured tail-ROI BVH overlaps (c) genuine 5-view visual correspondence. Once multiple safe leaves are assembled, test new plates against *each other*, not just core. Only after shape APPROVED should retarget weights and redo 13-bone / multi-cycle IK and actual race scene checks.

No game or production main changes. Complete **S type count remains zero**.
