# S Vibe Lane — Gate B Method Lock

Status: ACTIVE METHOD LOCK
Lane: exp/s-creature-vibe-modeling
Gate A source: output/S-vibe-a4-v2.blend

## Why Gate B changes representation

Gate A intentionally used overlapping low-complexity cages to solve silhouette.

Gate B must solve continuous anatomical massing. Continuing to move the same coarse rings indefinitely would polish the blockout representation rather than solve the surface.

## External method evidence

Blender Manual, Remesh / Sculpt:
https://docs.blender.org/manual/en/4.3/sculpt_paint/sculpting/tool_settings/remesh.html

Blender Manual, Adaptive Resolution:
https://docs.blender.org/manual/en/4.3/sculpt_paint/sculpting/introduction/adaptive.html

Blender Manual, Retopology:
https://docs.blender.org/manual/en/4.0/modeling/meshes/retopology.html

Blender Studio, Creature Factory 2 / Retopology:
https://studio.blender.org/training/creature-factory-2/chapter/5604151f044a2a00caa7b053/

Relevant process:
- voxel remesh is suitable for turning overlapping blockout volumes into a continuous manifold sculpting surface
- remesh resolution controls retained detail
- generated/sculpt topology is not the final deformation topology
- animation-ready topology requires a later retopology stage

## B0 — continuity feasibility test

B0 is a disposable technical test, not morphology acceptance.

Source:
- output/S-vibe-a4-v2.blend

Duplicate/merge candidate only:
- S_rebuild_core_head_crest_neck_torso_tail
- S_forelimb_L
- S_forelimb_R
- S_hindlimb_L
- S_hindlimb_R

Exclude / preserve exactly:
- S_reference_crest_v11
- all fore toe objects
- all hind toe objects
- cameras/review objects

Method:
1. Join the five body/limb blockout meshes into one temporary source object.
2. Voxel-remesh the joined volume at a controlled test resolution.
3. Do NOT remesh crest or toes.
4. Render five review views.
5. Compare against accepted Gate A silhouette.

Initial voxel-size candidate:
- 0.025 object-space units

Acceptance for B0:
- overlapping shoulder/hip roots become one continuous surface
- gross Gate A silhouette remains recognizable
- no limb is lost or fused to another limb
- neck/tail remain intact
- no unacceptable erosion of thin distal limbs
- crest and toes remain exact-coordinate unchanged

B0 failure means:
- reject B0 candidate
- keep Gate A model unchanged
- test a finer voxel size or a different continuity method

## Gate B1 and later

Only after B0 proves a safe continuity method:
- B1 shoulder/chest massing
- B2 fore/hind joint-root massing
- B3 crest-root/skull integration
- B4 feet
- B5 tail root/tip

Final deformation topology is a later retopology stage, not the B0/B1 sculpt topology.
