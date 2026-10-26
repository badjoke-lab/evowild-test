# Unit A — S hind joint fit v2 (2026-10-26 JST), REVISE

Input: immutable `review/focus-bind-repair-v1.glb`. Output: separate `review/focus-hind-fit-v2.glb`, SHA-256 `efa804ea4c3e2a2d272918e6982da12a365f1759140f50fa6d3f586c5fd2bede`. Open `s-run-review.html?rig=hind-v2`. Rebuild with `python3 scripts/repair_s_hind_candidate.py` (NumPy). Canonical source GLBs, v1 and production manifest are unchanged.

Formal S.webp / full reference sheet were compared with the existing sculpt: retain the slender thigh, forward knee, rear hock and distal foot of this S mesh. No borrowed animal geometry or silhouette change. Mesh slices gave distal shank center Z≈-0.75..-0.79 (Y=-0.6..-0.8), whereas v1's ground-level joint was at Z=-0.371, well in front of the mesh. [Fitted landmarks, offsets and affected vertices](asset-report.json) and [nearest-surface distances](landmark-measurements.json) are in original GLB model units; surface distance alone is not anatomical approval.

| Landmark | Fit (Y,Z) | Former nearest surface distance → fitted, left/right |
| --- | --- | --- |
| Hip | .035, -.500 | .068/.069 → .029/.030 |
| Knee | -.285, -.515 | .158/.154 → .050/.047 |
| Hock | -.490, -.735 | .358/.360 → .023/.023 |
| Toe | -.825, -.780 | Newly separated distal articulation |

The existing hind upper/lower/foot nodes now represent hip/knee/hock. Two appended toe joints make explicit four-joint chains (21 bones total). Only hind-node translations and their translation tracks are retargeted; native rotations and non-hind animation tracks stay unchanged. 7,685 vertices near the ipsilateral hind chains are reweighted, with proximal blending. Outside that region weight bytes are untouched. Lower-left hind vertices' ipsilateral weight share changes from .9803 to 1.0. POSITION, NORMAL and index bytes are unchanged; no remeshing or shape edits.

## Actual movement and comparison

[Before: v1 four-view sequences](../20261026-s-bind-repair/frames) / [After: SIDE](frames/SIDE), [CHASE](frames/CHASE), [LOW](frames/LOW), [REAR 3/4](frames/REAR_3_4): same 12 native phases, camera, ground and speed. [Rear-quarter video](rear-quarter.mp4) encodes those actual frames without interpolation. [PC](desktop-hind-v2.png) / [Pixel 7 emulation](android-hind-v2.png) screenshots; physical device not tested.

Improved: hock bends inside the distal-leg mesh; toe motion is separated; rear leg no longer hinges around a point in front of the mesh. Side and rear-quarter silhouette stays the same S. Torso, neck and foreleg motion remains visually consistent; the targeted test compares 81 protected mesh probes over four phases (<0.00001 world-unit displacement between v1/v2). 17,670 vertices have no hind influence and lie outside the modified region.

Worse/unresolved: native ankle rotations now act on a shorter fitted distal chain; toe-group recovery is lower (about .12m vs v1 group's .27m), and minimum diagnostic centroid Y remains about -.125m. These are **different weight groups**, not a sole-to-sole comparison. Visible penetration/sliding persists. No contact success is claimed in Unit A; actual mesh sole vertices and stance slip belong to Unit B. A fitted joint alone does not produce a valid sprint.

Validation: production build PASS; [targeted PC/Pixel 7 test log](tests.log) checks protected body motion, articulated toe chains and browser errors. [Build log](build.log). Baseline supplied by user: Actions 40275890477, 108 pass / 3 known fail / 81 skipped, no S-specific failure. No full 54-case journey rerun.

**REVISE, no production promotion or 2.5D export.** Save this unit separately before starting Unit B. Next: identify actual sole vertex patches, measure them through the cycle, implement contact-aware IK and stride/cadence, compare .5×/1×/1.5× with ground/cameras unchanged.
