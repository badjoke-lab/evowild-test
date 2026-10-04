# S Vibe B1b-v4 actual-image review

Decision: REVISE.
B1 shoulder/chest remains OPEN.
B2 and later remain BLOCKED.

Actions run: 37212977784 — SUCCESS.

## Validation

PASS.

- editable vertices: 103
- changed vertices: 53
- max displacement: 0.005999985421544982
- mean displacement: 0.0009400964332546556
- whole-body X/Y/Z extent drift: 0 / 0 / 0
- fixed geometry unchanged: true
- crest/toes unchanged: true
- topology unchanged: true
- five-view render hard-scope validation: true

## Actual-image review

Opened SIDE / FRONT / FRONT34 / REAR34 / BACK.

Compared directly with B1b-v2 and B1b-v3 crops as well as the repository S reference used for this lane.

SIDE:
- top shoulder transition is slightly softer
- triangular proximal-root silhouette remains obvious
- root still reads as a wedge/plate instead of continuous shoulder mass

FRONT34:
- small local softening
- raised cap and triangular root boundary remain clearly visible
- improvement is not large enough for KEEP

FRONT / REAR34 / BACK:
- no material gross regression
- no evidence that the core root-shape defect is solved

## Method conclusion

B1b fixed-topology local fairing is exhausted.

Evidence:
- X-only v1/v2 could reduce lateral irregularity but could not solve SIDE connection shape
- Y/Z-only v3 could not solve it
- compact XYZ v4 reaches essentially the full 0.006 displacement budget and still retains the triangular root

Do not:
- increase the displacement budget
- add more passes
- accumulate v2/v3/v4
- continue fixed-topology smoothing variants

B0-v025 remains the recovery source.

The next test must change local surface resolution/representation while remaining strictly local to B1 shoulder root.
