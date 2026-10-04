# S Vibe B1b-v3 Shoulder-Root Connection Hypothesis

Status: LOCKED FOR EXECUTION
Lane: exp/s-creature-vibe-modeling
Source: output/S-vibe-b0-v025.blend

## Why v3 is separate from v2

B1b-v2 reduced some lateral X-direction irregularity, but actual SIDE and FRONT34 review still shows:
- a raised/stepped shoulder upper edge
- a triangular proximal forelimb/root connection
- insufficient integration of the shoulder root into the thorax

Those residuals exist in the Y/Z connection shape and cannot be solved by increasing X-only fairing.

B1b-v2 is REVISE and is not used as the cumulative source.
B0-v025 remains the immutable recovery source.

## Single hypothesis

A small residual-gated **Y/Z-only shoulder-root fairing** can soften the stepped/triangular root connection while leaving lateral width and FRONT/BACK body width unchanged.

## Editable region

Source-coordinate mask:
- |X|: 0.070 to 0.180
- Y: -0.10 to 0.10
- Z: 0.90 to 1.12

Boundary taper:
- X margin: 0.020
- Y margin: 0.030
- Z margin: 0.035

## Exact edit

- X coordinate of every body vertex remains exact.
- Only Y/Z coordinates inside the mask may move.
- same-side mesh neighbors only
- residual-gated Laplacian fairing in the Y/Z plane
- positive fairing only
- lambda: 0.24
- passes: 3
- residual threshold: 0.0015 object units
- cumulative per-vertex Y/Z displacement clamp: 0.006

This is not global smoothing and not a repeat of B1a:
- B1a used a much broader shoulder/chest region and moved the full 3D coordinate.
- B1b-v3 locks X and targets only the proximal root connection.

## Keep fixed

- every body vertex outside the B1b-v3 mask
- X coordinate of every body vertex
- crest
- all toes
- topology
- vertex count
- B0-v025 source remains recoverable

## Expected visual change

SIDE:
- shoulder upper edge loses the abrupt step
- triangular root reads more like a continuous shoulder-to-upper-limb connection
- no gross thorax/neck/limb silhouette drift

FRONT34:
- root boundary becomes less triangular/plate-like
- lateral shoulder width stays unchanged because X is exact-fixed

FRONT/BACK:
- body width should remain effectively unchanged

## Hard limits

- max cumulative Y/Z displacement <= 0.006
- X delta = 0 for every body vertex
- whole-body Y min/max drift <= 0.004
- whole-body Z min/max drift <= 0.004
- all non-mask vertices exact
- crest/toes exact
- topology/count exact

## Stop

Render:
- SIDE
- FRONT
- FRONT34
- REAR34
- BACK

Then stop for actual-image review.
Do not combine this pass with B1b-v2.
Do not start B2 automatically.
