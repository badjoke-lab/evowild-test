# EvoWild Run — Original S authority / authentic QEM collar V–W actual-mesh review
Date: 2026-10-11 UTC. Trial branch: `exp/s-qem-root-aperture-w-20261011`.

## Absolute authority / preserved source

- **Only highest modeling authority**: `art/s-creature/references/00_s_type_modeling_image_v1.png`; verified SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
- Real source donor: `art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb`; verified SHA-256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`. Immutable original **29,948 vertices / 59,932 triangles**.
- V and W **physically reconstruct M-QEM tail patch holes + first two new collar support loops** using genuine Blender BMesh geometry, not a flat image or simulated placeholder. The M source is preserved. No `main` changes, no production import.

## Prior correct benchmark (independent physical 3D models)

- Single corrected **MID_LEFT S**: actual ROI BVH non-vertex-sharing triangle collision pairs **5→0**, full mesh shared-edge opposite winding PASS and face deformation threshold PASS. **Not a complete S type**.
- **PROXIMAL_RIGHT U**: 34→24 overlaps; 0 new triangle inversions/degenerates/area extreme; **FAIL due to 24 remaining overlaps**.
- **DISTAL_RIGHT U**: 152→119 overlaps; **FAIL due to 119 remaining overlaps**.

## New actual source-mesh topology V

Root seam of authentic M trimmed and re-sewn with **13 swept support rings**, including two first-root collar loops absent from Q. **24 independent true Blender mesh candidates per blade**, original source SHA enforced. Both geometry winners have **one component, 0 open/nonmanifold edges, 0 winding conflicts, 0 degenerate triangles**. However neither passes actual tail-ROI BVH non-vertex-sharing triangle intersection test:

| Blade | Previous U best | New V best | Patch faces / perimeter edges | Measured V geometry | Result |
|---|---:|---:|---|---|---|
| PROXIMAL_RIGHT | 24 | **56** | 40 / 18 | 32,171 vertices / 64,378 faces | FAIL (worse) |
| DISTAL_RIGHT | 119 | **108** | 79 / 35 | 32,381 vertices / 64,798 faces | FAIL (partial improvement) |

Actual `.blend`:
- `tail-integrated-collar-v-proximal_right/S-QEM-real-PROXIMAL_RIGHT-collar-retopo-V-TRIAL.blend`
- `tail-integrated-collar-v-distal_right/S-QEM-real-DISTAL_RIGHT-collar-retopo-V-TRIAL.blend`

QA:
- `tail-integrated-collar-v-proximal_right/REAL_QEM_V_NEW_ROOT_TOPOLOGY_QA.json`
- `tail-integrated-collar-v-distal_right/REAL_QEM_V_NEW_ROOT_TOPOLOGY_QA.json`

Actual Blender 5-view screenshots:
- `tail-integrated-collar-v-proximal_right/review/REAL_QEM_PROXIMAL_RIGHT_V_FIVE_VIEW_COMPARE.jpg`
- `tail-integrated-collar-v-distal_right/review/REAL_QEM_DISTAL_RIGHT_V_FIVE_VIEW_COMPARE.jpg`

Run [38142818986](https://github.com/badjoke-lab/evowild-test/actions/runs/38142818986) SUCCESS. Earlier run [38142788896](https://github.com/badjoke-lab/evowild-test/actions/runs/38142788896) encountered a Blender Python unsupported face-loop access, corrected before successful execution.

## Expanded but bounded source tail cut aperture W

Physically reconstruct from M with **24 additional candidate cut apertures per blade**. Instead of mere positional offsets, change original source-hole Y length and angular aperture; preserve actual QEM donor and one-root connected mesh. **Hard bound: remove at most 260 M tail patch faces** so whole posterior M cannot be erased to game the test.

| Blade | Previous best across Q/U/V | W best | Patch faces / perimeter edges | Measured W geometry | Result |
|---|---:|---:|---|---|---|
| PROXIMAL_RIGHT | U: **24** | **184** | 155 / 53 | 32,586 vertices / 65,208 faces | FAIL, much worse |
| DISTAL_RIGHT | V: **108** | **226** | 137 / 43 | 32,460 vertices / 64,956 faces | FAIL, much worse |

Both W winners **one connected manifold, boundary edges=0, nonmanifold edges=0, winding conflicts=0, degenerate triangles=0**, but many physical self-intersections remain. Run [38143148240](https://github.com/badjoke-lab/evowild-test/actions/runs/38143148240) SUCCESS, confirming execution and persistence, **not technical or canonical visual acceptance**.

Actual W geometry / QA:
- `tail-integrated-aperture-w-proximal_right/S-QEM-real-PROXIMAL_RIGHT-expanded-aperture-W-TRIAL.blend`
- `tail-integrated-aperture-w-distal_right/S-QEM-real-DISTAL_RIGHT-expanded-aperture-W-TRIAL.blend`
- Each contains `REAL_QEM_W_APERTURE_TOPOLOGY_QA.json`, original M vs new W same-angle five-view rendered PNGs, and composite actual photo.
- `tail-integrated-aperture-w-summary/ACTUAL_QEM_TWO_ROOT_APERTURE_W_COMPARE.json`

**Technical note**: BVH intersection counts are evaluated on the specified posterior tail ROI (triangle centroid Y>1.5, Z>.94, abs(X)<.7) and exclude pairs sharing vertices. This is *not* whole-body global collision clearance. Manifold, degeneracy and winding checks cover the entire derived mesh.

## Decision: no more numerical-only patch/collar search

- **REJECT V and W** for actual production and modeling authority visual gate.
- Latest W failure shows that simply broadening the skin removal aperture or inserting additional collar loops is not a reliable solution.
- M technical donor base, S corrected single middle-left blade, and all failed variants remain only auditable prototypes. No previous 13-bone IK/gait results may be promoted to this new topology. **Approved complete S = 0.**
- More importantly, reviewing actual five-view Blender shots against the original user-authorized image shows whole-body morphology mismatches: antelope-like thin horns, trunk/chest/haunch silhouette and limb/hoof proportions, plus little bumpy dorsal leaves instead of long separately layered armored feathers. Tail micro-polishing cannot yield canonical full S.

### Next actual construction strategy (change architecture, don't resweep same parameters)

1. Start from **exact canonical approved PNG** and explicitly trace/reference *geometric controls* for SIDE and other drawn views: S head-and-crest, shoulder/haunch mass, fore/hind feet, tail core, and lamina root/outer edge/tip. Do **not** invent a new master reference.
2. **Visual-authority shape first**. Rebuild dorsal and lateral armor from separately controllable 3D blade mesh elements positioned with real 3D clearance from parent skin. One connected manifold is a convenient engineering property, **not a reason to force visibly wrong single-tube armor**. Separate mesh subobjects can be valid once their attachment/rigging/appearance and intersections are proved; disallow unattached floating objects and fake sprites.
3. Validate each individual mesh and mutual relationships in 5 Blender viewpoints against source reference; require zero unintended 3D body/plate intersection, correct layered side/rear34 silhouette, material and coloring gates; only then optimize/merge/rerig.
4. Validate full-head/body/feet at the same time, then rig all actual plate transforms and 13-bone/foot contact/gallop in race scene. Do not infer pass from unaltered donor, Blender job success, or numerical tail contact.
5. Work in isolated experiment branch, preserve best technical sources and full original QA, **main untouched**.

**Game-ready S creature: ZERO. User must not be told that this constitutes accepted S modeling.**
