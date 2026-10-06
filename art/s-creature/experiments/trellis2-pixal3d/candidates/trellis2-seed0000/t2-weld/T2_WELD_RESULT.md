# T2 exact-weld bench

This step does not retopologize, decimate, smooth, or move any retained vertex.

- source vertices: 209,427
- exact-weld vertices: 149,304
- exact-weld faces: 298,783
- exact-weld connected components: 27
- exact-weld boundary edges: 17
- exact-weld non-manifold edges (>2 faces): 90

Largest connected component:

- vertices: 132,330
- faces: 264,856
- share of welded faces: 88.6449%
- boundary edges: 0
- non-manifold edges (>2 faces): 56
- watertight: False
- volume: False

Interpretation: exact welding is topology recovery, not morphology editing. The largest
component is retained as the next repair input only if it removes detached fragments
without moving the S candidate surface.
