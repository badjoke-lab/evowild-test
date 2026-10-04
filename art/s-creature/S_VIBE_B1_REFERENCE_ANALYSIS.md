# S Vibe Lane — Gate B1 Shoulder / Chest Analysis

Status: LOCKED FOR B1a
Lane: exp/s-creature-vibe-modeling
Source: output/S-vibe-b0-v025.blend

## Reference

Primary:
- references/01_s_body_primary.png
- references/02_s_silhouette.png
- S_MODELING_IMAGE_LOCK.md

Target read:
- shoulder mass is readable but not oversized
- neck, thorax and forelimb root belong to one continuous anatomical mass
- no pasted-on cone
- no hanging sternum pouch
- chest remains athletic/narrow rather than barrel-shaped

## B0-v025 result

Continuity method is accepted:
- one manifold core+limb surface
- non-manifold edges 0
- Gate-A silhouette retained
- crest/toes unchanged

Remaining local B1 problem:
- voxel-scale waviness around shoulder/chest
- shoulder-root transition is continuous but still lumpy
- local planar read is weak

## B1 subdivision

Do not sculpt the whole body.

### B1a — local shoulder/chest surface cleanup

Single hypothesis:
Remove voxel-scale waviness and local shoulder-root bumps without changing the accepted silhouette or inventing new anatomy.

Editable continuous-body region:
- Y: -0.12 to 0.22
- Z: 0.74 to 1.14
- all X within that region

Hard fixed:
- every continuous-body vertex outside that region
- crest
- all toes
- topology / vertex count

Method:
- boundary-tapered local Taubin-style relax
- two lambda/mu cycles
- positive pass lambda = 0.22
- negative pass mu = -0.23
- edit weights fade to zero near Y/Z region boundaries

Why:
- local relax removes remesh noise while the negative pass reduces smoothing shrinkage
- fixed outside vertices anchor neck, torso, distal forelimbs and accepted silhouette

B1a is NOT:
- shoulder enlargement
- chest proportion change
- global smoothing
- limb repositioning
- final sculpt

Acceptance:
- FRONT34 shoulder root looks continuous, not melted
- SIDE chest/shoulder contour remains essentially unchanged
- no barrel widening
- no neck or distal-limb drift
- fixed vertices exact-match source
- max edited displacement stays small and is reported

Stop after five-view render.
Do not proceed to B1b anatomical plane shaping automatically.

## B1a-v1 result

Decision: REVISE / effect insufficient.

Safety:
- 916 editable vertices
- 4742 fixed body vertices exact
- crest/toes exact
- topology exact
- max displacement 0.0016187
- mean displacement 0.0001115

Visual result:
- SIDE and FRONT34 are effectively indistinguishable from B0-v025 at review scale
- no damage, but no meaningful voxel-waviness cleanup either

B1a-v2 locked change:
- restart from B0-v025, not from B1a-v1
- same spatial region and boundary taper
- lambda 0.32
- mu -0.33
- 4 cycles
- reject if max displacement exceeds 0.010 object-space units
- all other scope rules unchanged

## B1a-v2 / v3 / v4 outcome

B1a-v2: REVISE.
- max displacement 0.0058322
- visual cleanup still insufficient

B1a-v3: REVISE.
- cycles 8
- max displacement 0.0096156
- visual cleanup still insufficient
- cycle escalation exhausted

B1a-v4: HARD FAIL.
- same 8 cycles, narrower boundary taper
- max displacement 0.0127102 > 0.010
- stopped before render

### B1a method closure

The isotropic Taubin-relax family is closed. No B1a candidate is accepted.
B0-v025 remains the source.

The dominant residual is now classified as a lateral shoulder-root / chest-side plane problem rather than only voxel-scale noise.

### B1b-v1 locked hypothesis

Use X-only local fairing from B0-v025:
- target Y [-0.12, 0.18]
- target Z [0.80, 1.12]
- |X| >= 0.055
- Y/Z exact fixed
- X-only adjacency fairing
- cumulative |delta X| <= 0.006
- crest/toes/topology fixed
- SIDE profile invariant by construction

B1b is explicitly unblocked by this method decision. It was not started automatically from B1a-v2/v3.
