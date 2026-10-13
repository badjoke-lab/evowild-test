# EvoWild Run — S original Hunyuan real Blender editing proof

**Scope:** Technical editability verification only. **This is NOT approved S-creature sculpting or a shape-quality review.**

- Branch: `exp/s-hunyuan-shoulder-sculpt-20261013`
- Test workflow commit: `c64382a04620241be9ac7c905ed0245ef5699714`
- Workflow: `.github/workflows/s-original-hunyuan-blender-edit-proof.yml`
- GitHub Actions run: https://github.com/badjoke-lab/evowild-test/actions/runs/38410981636
- Job: https://github.com/badjoke-lab/evowild-test/actions/runs/38410981636/job/115342920735
- Result: **SUCCESS**, including actual file edit, save, reopen, original SHA check and artifact upload.
- Artifact: https://github.com/badjoke-lab/evowild-test/actions/runs/38410981636/artifacts/11821276841 (GitHub Actions artifact; expires 2026-10-27)
- Blender version: 4.3.2

## Measured real mesh data

- Mesh datablock: `geometry_0`
- Vertices: **38,802**
- Faces: **77,684**
- Modified vertex: **0** (only that vertex was modified)
- Coordinate before: `[-0.34407034516334534, 0.6818781495094299, 0.025634517893195152]`
- Coordinate after edit and after save/reload: `[-0.3430703580379486, 0.6818781495094299, 0.025634517893195152]`
- Measured delta: `[0.0009999871253967285, 0.0, 0.0]`
- Saved proof `.blend` size: **2,764,116 bytes**
- Modified meshes / vertices after reload: `[{"mesh":"geometry_0","vertex":0}]`

## Original files protected

- Base `.blend` SHA256 (before and after): `1f26bbd4485721a69d74c0c4c4da917dacf9341c15932785e42ba478c3f71c37`
- Highest authority reference PNG SHA256 (before and after): `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`
- The only edited file is a separate test `.blend` saved under `/tmp/evowild-s-vertex-proof/` in the Actions runner and uploaded as an artifact.
- Original geometry and the reference PNG in the repository were not changed.
- No render was produced in this test, and no shoulder/chest/upper-arm art-directed sculpting was attempted.

## Interpretation and next gate

1. **TECHNICAL EDITABILITY: PASS** — The actual Hunyuan mesh can be modified via Blender 4.3.2 `bpy`, saved to `.blend` and verified after reopening without changing the originals.
2. **ARTISTIC SHAPE GATE: NOT STARTED** — Still must sculpt shoulder/chest/upper arm in a fresh named working file, render SIDE/FRONT/FRONT34/REAR34/BACK, and compare against canonical PNG. Do not count this proof as sculpt progress.
3. **Codex Cloud E2E: NOT PROVEN** — The confirmed execution above took place in GitHub Actions, not in Codex Cloud.
4. Do not merge the test proof model into the game or treat the single-vertex displacement as an art improvement.
