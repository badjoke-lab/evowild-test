# T2 MeshFix repair bench

Source: exact-weld largest connected component.

## Topology

Before:
- vertices: 132,330
- faces: 264,856
- boundary edges: 0
- non-manifold edges (>2 faces): 56
- watertight: False

After MeshFix:
- vertices: 131,752
- faces: 263,544
- connected components: 1
- boundary edges: 0
- non-manifold edges (>2 faces): 0
- watertight: True
- volume: True

## Approximate morphology drift

- symmetric mean / source bbox diagonal: 0.002641
- symmetric p95 / source bbox diagonal: 0.004592
- source→repair p99 / diagonal: 0.005547
- repair→source p99 / diagonal: 0.005650

Automatic topology pass: True
Automatic low-drift candidate: True

These metrics do not authorize rig/motion. A visual review is still required.
