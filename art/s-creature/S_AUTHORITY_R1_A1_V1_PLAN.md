# S Authority R1-A1 v1 Plan

Status: **LOCKED FOR EXECUTION**

Source: `output/S-authority-r0-a5-v2.blend`

R0 status: **ACCEPTED_R0_MORPHOLOGY**

## Scope

Surface continuity only at:

1. shoulder / proximal forelimb junction;
2. pelvis / proximal hindlimb junction.

Do not change the authority morphology.

## Method

Localized weighted Taubin smoothing on the continuous body mesh.

Fore outer support:

- Y -0.18 .. 0.26
- Z 0.70 .. 1.12
- |X| 0.06 .. 0.235

Fore full-weight core:

- Y -0.10 .. 0.14
- Z 0.78 .. 1.04
- |X| 0.085 .. 0.20

Hind outer support:

- Y 0.58 .. 0.98
- Z 0.70 .. 1.12
- |X| 0.06 .. 0.235

Hind full-weight core:

- Y 0.66 .. 0.88
- Z 0.78 .. 1.04
- |X| 0.085 .. 0.20

Run four Taubin cycles:

- lambda +0.38
- mu -0.40
- boundary taper applied every pass
- per-vertex total displacement cap 0.025

## Hard locks

Exact:

- all body vertices outside the two supports;
- head / neck;
- central thorax / waist outside support;
- tail support;
- distal limbs below Z 0.70;
- all separate crest meshes;
- all split-foot meshes;
- all tail-blade meshes;
- body topology / vertex count;
- cameras.

## Hard limits

- non-manifold edges: 0;
- bbox min/max drift per axis <= 0.015;
- max body displacement <= 0.025;
- support roughness mean must decrease;
- render five views and stop.

No R1-A2 work before review.
