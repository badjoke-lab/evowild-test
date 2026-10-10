# EvoWild S — original QEM IK and moving-root contact gate (2026-10-10)

## Authority and non-negotiable source lock

- Authoritative design: `art/s-creature/references/00_s_type_modeling_image_v1.png` (SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`).
- Original TRELLIS2 QEM source: `art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb` (SHA-256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`).
- Preserve the 29,948-vertex/59,932-face source mesh and genuine 13-bone Blender armature, plus an independently weighted copy. Do not import R1 as a substitute.
- Production S approved: **NO**. Main and gameplay branches untouched.

## Executed tests with actual Blender-depsgraph geometry

| Test | Body displacement | Real Blender frames | Stance contacts | Triangle QA | Verdict |
| --- | ---: | ---: | --- | --- | --- |
| IK V1 (stationary root) | 0 | 16 | PASS | PASS | **LIMITED PASS** |
| Root V2 | 0.048 | 17 | PASS | 4 frames outside area bound (13/14/15/17) | **FAIL** |
| Root V2b | 0.032 | 17 | PASS | 1 frame outside area bound (14) | **FAIL** |
| Root V2c | 0.024 | 17 | PASS | PASS, zero flips, collapse, half-/double-area faces | **LIMITED PASS** |

The geometry criteria above are strict: zero flipped or collapsed faces, no triangle with evaluated area <0.5x or >2.0x rest, and 0.01 maximum stance-patch world-space drift with minimum foot Z in [-0.002,+0.006]. V2c moved up to 15,766 real mesh vertices relative to source (max 3D displacement 0.09466 normalized units). Original source geometry is hash checked and retained.

Measured maximum V2c stance-patch XY drift:
- FORE_L: 0.000000239
- FORE_R: 0.000001815
- HIND_L: 0.000000410
- HIND_R: 0.000000390

Actual swing foot ground clearances (peak minimum vertex Z): FORE_L 0.02839, FORE_R 0.03132, HIND_L 0.02700, HIND_R 0.02891. These are procedural test targets, **not measured race stride or speed**.

### Review-ready evidence

- `ik-contact-v1/S-QEM-real-13bone-IK-contact-v1.blend` + `ik-contact-v1/REAL_IK_CONTACT_QA.json` + `ik-contact-v1/review/QEM_IK_REAL_16_frame_motion.gif`.
- `rootmotion-contact-v2/ROOT_MOTION_CONTACT_QA.json` and its Blender/17-frame original renders — FAIL preserved.
- `rootmotion-contact-v2b/ROOT_MOTION_CONTACT_QA.json` and its Blender/17-frame original renders — FAIL preserved.
- `rootmotion-contact-v2c/S-QEM-real-13bone-rootmotion-v2c.blend` + `rootmotion-contact-v2c/ROOT_MOTION_CONTACT_QA.json` + `rootmotion-contact-v2c/review/QEM_ROOT_IK_REAL_17frame.gif` — LIMITED PASS.
- V1 GitHub Actions run: 38027750123. V2: 38028017917. V2b archival rerun: 38028230794. V2c: 38028254484.

## Exact scope of success

V2c demonstrates short-distance root translation of 0.024 world units (~0.94% of height 2.55) alongside two-foot stance lock, alternating diagonal swing, real evaluated Blender skinned-geometry validation, and keyed-frame replay. **It is NOT a validated walk/gallop**, continuous cyclic locomotion, contact dynamics, race acceleration or a shipping character.

The upper feasible displacement remains unknown. With this timing/weight configuration, 0.024 was observed to pass and 0.032 observed to fail; the boundary has not been measured.

## Next required gates

1. Design continuous multiple cycles with pose/velocity continuity at all swing-to-stance boundaries. Audit the 17th-to-next-frame seam and detect target/mesh pops; separate planted and swinging gait phase explicitly.
2. Improve articulation/deformation around joint surfaces and **retest larger stride** without altering authoritative visible QEM geometry. If needed, create a new independently versioned deformation-topology/weight variant, preserving the original donor and comparative renders.
3. Explicit anatomy and silhouette gate against the locked S image, SIDE / FRONT / FRONT34 / REAR34 / BACK. Candidate 12 joints are vertex-derived hints, not anatomy-validated.
4. Only after safe multi-cycle run at meaningful relative travel: full race camera and 18-creature stress test, ground/slip metrics, actual game-frame FPS. Do not merge into main before evidence-based approval.

No mass production, race-ready or approved S claim is authorized at this checkpoint.
