# S Vibe B1c-v1 Local Shoulder-Root Resurface Plan

Status: LOCKED FOR EXECUTION
Lane: exp/s-creature-vibe-modeling
Source: output/S-vibe-b0-v025.blend

## Why representation changes

B1b-v1 through v4 show that the root wedge is not removable within the current
fixed-topology displacement budget. The local remesh surface has insufficient
degrees of freedom to become a rounded anatomical bridge without consuming the
entire displacement budget.

Gate B sculpt topology is not final deformation topology.
A local topology refinement is therefore allowed as a controlled B1 test.

## Single hypothesis

Subdivide only the fully-contained proximal shoulder-root faces once, then
perform a small boundary-anchored fairing on that refined patch.

This should round the triangular connection while preserving the rest of the
B0-v025 surface exactly.

## Support region

Source coordinates:
- |X|: 0.070 to 0.180
- Y: -0.090 to 0.105
- Z: 0.900 to 1.105

Only edges whose adjacent source faces are completely inside this support box
may be subdivided.

## Smoothing region / weights

Same support box with taper:
- X margin 0.025
- Y margin 0.035
- Z margin 0.040

Method after one local subdivision:
- same-side XYZ Laplacian fairing
- lambda 0.18
- 3 passes
- residual threshold 0.0015
- cumulative displacement of every original or newly-created local vertex <= 0.004

## Keep fixed

- every original body vertex outside support
- crest
- toes
- all other objects
- global body extents
- all topology outside faces fully contained in support

## Topology rule

Topology change is allowed ONLY inside the support region:
- one subdivision cut
- no object-wide remesh
- no subdivision of an edge if any linked source face contains a vertex outside support
- resulting body must remain manifold

## Hard limits

- original outside-support vertex coordinates exact
- local original/new vertex displacement <= 0.004 from their pre-fairing positions
- whole-body extent drift <= 0.003 per axis
- non-manifold edges = 0
- crest/toes exact

## Expected visual change

SIDE:
- shoulder-root wedge becomes rounder and the abrupt upper edge is reduced

FRONT34:
- triangular attachment boundary becomes a softer continuous bridge

FRONT/BACK:
- no material width change

## Stop

Render five standard views and stop for actual-image review.
B2 remains blocked.
