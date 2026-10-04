# EvoWild Run — S Vibe Gate B1a-v3 Review

Status: REVISE
Lane: exp/s-creature-vibe-modeling
Candidate: output/S-vibe-b1a-v3.blend
Source: output/S-vibe-b0-v025.blend

## Validation

PASS.

- lambda: 0.32
- mu: -0.33
- cycles: 8
- changed vertices: 914
- max displacement: 0.009615554795231405
- mean displacement: 0.0006631121090316585
- fixed geometry unchanged: true
- crest/toes unchanged: true
- topology unchanged: true
- five-view render completed

The candidate remains inside the hard limit of 0.010, but only narrowly.

## Visual review

Actual SIDE / FRONT / FRONT34 / REAR34 / BACK renders were inspected and compared with B0-v025, B1a-v1 and B1a-v2.

Result:
- the shoulder/chest transition is incrementally smoother
- the visible shoulder-root bump remains
- lateral chest unevenness remains visible in FRONT34
- the improvement from v2 to v3 is small relative to the increased displacement
- no justification exists for increasing cycles further

## Decision

**REVISE**

B1a-v3 is not a KEEP candidate.

B1b remains blocked.

## Method conclusion

The simple strategy of increasing Taubin relax cycles has reached diminishing returns:
- v1 max displacement: 0.0016187
- v2 max displacement: 0.0058322
- v3 max displacement: 0.0096156

The hard limit is almost exhausted while the target visual artifact remains.

Do not try 12 / 16 cycles.

## B1a-v4 — next single hypothesis

Source:
- output/S-vibe-b0-v025.blend

Keep:
- same Y/Z edit bounds
- lambda 0.32
- mu -0.33
- cycles 8
- all hard-scope locks
- max displacement <= 0.010

Change only:
- boundary taper width
- Y margin: 0.060 -> 0.030
- Z margin: 0.070 -> 0.035

Hypothesis:
The current wide boundary fade suppresses the relax too strongly near the shoulder-root / lateral-chest residual. A narrower taper will allow more of the already-approved eight-cycle relax to reach that residual while preserving exact zero movement at the region boundary.

Additional fail rule:
- SIDE / FRONT bounding silhouette drift in the B1a body region must remain <= 0.003 object-space units per axis.

Stop after five-view render and validation.
Do not start B1b automatically.
