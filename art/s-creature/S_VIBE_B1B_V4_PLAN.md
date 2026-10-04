# S Vibe B1b-v4 Compact 3D Root Fairing Plan

Status: LOCKED FOR EXECUTION
Lane: exp/s-creature-vibe-modeling
Source: output/S-vibe-b0-v025.blend

## Single hypothesis

The remaining shoulder-root defect is a coupled 3D connection problem.
A compact residual-gated XYZ fairing over the proximal root only can soften
both the SIDE upper-edge step and the FRONT34 triangular boundary without
altering the wider thorax/neck/limb morphology.

## Editable source-coordinate mask

- |X|: 0.080 to 0.165
- Y: -0.075 to 0.085
- Z: 0.925 to 1.085

Boundary taper:
- X margin: 0.018
- Y margin: 0.025
- Z margin: 0.030

## Exact edit

- same-side neighbors only
- residual-gated XYZ Laplacian fairing
- positive pass only
- lambda: 0.20
- passes: 3
- residual threshold: 0.0020
- cumulative full 3D displacement clamp: 0.006

This is narrower than B1a and more compact than B1b-v2/v3.
It targets only the proximal attachment zone.

## Keep fixed

- all body vertices outside the compact mask
- crest
- all toes
- topology
- vertex count
- B0-v025 remains recoverable

## Expected visual change

SIDE:
- shoulder top step becomes a continuous slope
- triangular root silhouette softens
- no neck/thorax/distal-limb drift

FRONT34:
- root reads less like a faceted triangular wedge
- shoulder remains present, not collapsed

FRONT/BACK:
- no material width change

## Hard limits

- max cumulative XYZ displacement <= 0.006
- whole-body X/Y/Z min/max drift <= 0.004 per axis
- all non-mask vertices exact
- crest/toes exact
- topology/count exact

## Stop

Render SIDE / FRONT / FRONT34 / REAR34 / BACK and stop for actual-image review.
Do not start B2 automatically.
