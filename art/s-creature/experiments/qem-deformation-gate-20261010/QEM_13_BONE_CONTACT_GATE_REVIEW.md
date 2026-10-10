# EvoWild S — original QEM 13-bone chain and grounding review (2026-10-10)

**Local geometry and restricted multi-joint armature: PASS.**
**Actual quadruped gait and ground contact: FAIL / NOT IMPLEMENTED.**
**Production creature: NOT APPROVED.**

## Authority & protected geometry

Authoritative S design is `art/s-creature/references/00_s_type_modeling_image_v1.png`, SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
The only donor input is `art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb`, SHA-256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`, 29,948 vertices/59,932 faces; nonmanifold edges 0. The GLB and original mesh object are not modified. R0 simplification and R1 donor remain rejected.

## New verifiable results

### Actual joint anatomy candidate survey
- Actions [38017170103](https://github.com/badjoke-lab/evowild-test/actions/runs/38017170103) SUCCESS.
- `joint-anatomy-survey-v2/JOINT_CANDIDATE_SURVEY.json` contains 12 vertex-derived candidate positions (bilateral shoulder/elbow/wrist/hip/stifle/hock), each with original vertex index and point count.
- `joint-anatomy-survey-v2/QEM_REAL_12_joint_candidates_fiveview.jpg` maps these to genuine 5-view Blender source geometry. **Candidate landmarks, not artist or anatomist-approved joints**.

### Real 13-bone armature
- Actions [38017380321](https://github.com/badjoke-lab/evowild-test/actions/runs/38017380321) SUCCESS.
- `three-segment-armature-v1/S-QEM-real-13-bone-joint-chain-test.blend` is editable Blender source containing preserved original QEM plus a separate identically triangulated weighted copy.
- **13 actual deform bones**: body root + 4 limbs x (UPPER/MIDDLE/LOWER), parented into 3-segment joint chains. Skinning is via real Armature modifier and vertex groups. Native keyframes 1,8,16; 16-frame playback.
- `three-segment-armature-v1/review/QEM_13_bone_joint_before_after_real_fiveview.jpg`: matched five-view source and frame-8.
- Scan of strength factors 1.0/0.85/0.7/0.55: full proposed bend yielded 7 triangles below half area and 3 above twice area; **0.55 was the first passing factor**, with 16,246 deformed vertices, max displacement 0.0500873 normalized world units; zero flipped/collapsed/half/double faces. Rest-pose maximum coordinate error 2.38e-7.
- Actual upper/mid/lower per-link local angles at frame 8: fore left (+5.5,-9.35,+6.05)°, fore right signs reversed; hind left (-4.4,+8.25,-6.05)°, hind right reversed. **No claim of anatomically correct run dynamics.**

### Contact truth from real frame-by-frame evaluated geometry
- Actions [38017566860](https://github.com/badjoke-lab/evowild-test/actions/runs/38017566860) SUCCESS.
- `three-segment-armature-v1/contact-motion-review/REAL_FOOT_CONTACT_AUDIT.json` measures the **same mesh contact-patch vertices** for all 16 evaluated keyed frames, four feet separately. Original feet have min-Z ≈0, with root stationary.
- Max horizontal contact-patch drift in normalized world units: **FORE_L 0.02324, FORE_R 0.01745, HIND_L 0.04373, HIND_R 0.02708**.
- Max change in lowest-Z: FORE_L 0.01963, FORE_R 0.01483, HIND_L 0.01533, HIND_R 0.01425.
- At frame 8, FORE_R min-Z **−0.00950** and HIND_R **−0.01087** (below the z=0 ground plane), while FORE_L min-Z **+0.02202** and HIND_L **+0.01533** (hovering above it).
- Therefore **no validated planted feet or gait**; the current 16-frame sample must not be described as running or race-ready.
- `three-segment-armature-v1/contact-motion-review/QEM_13BONE_true_skeletal_test_16frame.gif` is compiled from **16 actual Blender renders of existing keyed pose**. No synthetic artwork or video generator involved.

## Decision and next concrete gate

1. **Keep** the 13-bone source as a demonstrably working technical foundation and preserve QEM body/crests/armor/tail geometry.
2. **Do not merge** into `main`, `feat/s-creature-model`, Motion First, or gameplay. The current asset lacks full anatomical approvals and shows measured foot penetration and slip.
3. Next task: build a real 4-foot ground-contact/IK stance controller driving the same bone chains. Demand each planted foot has min-Z >=−0.002 and ≤+0.006 normalized units, horizontal patch drift <=0.01 normalized units during stance, per-foot and per-frame; all skin triangles noninverting and area ratio between 0.5 and 2.0.
4. Separate stance/recovery phase and root motion only after actual planted feet pass; **do not artificially paint poses or switch to simplified R0**. Later validate multi-angle running game camera and design resemblance against the authoritative art.

**Production-complete S count remains 0.**
