#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np
import trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000/S-trellis2-clean-seed0000.glb"
OUT = ROOT / "art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-weld"
OUT.mkdir(parents=True, exist_ok=True)


def face_component_labels(mesh):
    fa = np.asarray(mesh.face_adjacency, dtype=np.int32)
    n = len(mesh.faces)
    if len(fa) == 0:
        return n, np.arange(n, dtype=np.int32)
    rows = np.r_[fa[:, 0], fa[:, 1]]
    cols = np.r_[fa[:, 1], fa[:, 0]]
    data = np.ones(len(rows), dtype=np.uint8)
    graph = coo_matrix((data, (rows, cols)), shape=(n, n)).tocsr()
    return connected_components(graph, directed=False, return_labels=True)


def edge_stats(mesh):
    edges = np.sort(np.asarray(mesh.edges), axis=1)
    _, counts = np.unique(edges, axis=0, return_counts=True)
    return {
        "boundary_edges": int(np.sum(counts == 1)),
        "nonmanifold_edges_gt2_faces": int(np.sum(counts > 2)),
        "edge_face_count_histogram": {
            str(int(k)): int(v)
            for k, v in zip(*np.unique(counts, return_counts=True))
        },
    }


def audit(mesh, label):
    components, labels = face_component_labels(mesh)
    sizes = np.bincount(labels) if len(labels) else np.array([], dtype=np.int64)
    result = {
        "label": label,
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "connected_components": int(components),
        "component_face_counts_desc": [int(x) for x in np.sort(sizes)[::-1][:32]],
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "is_volume": bool(mesh.is_volume),
        "euler_number": int(mesh.euler_number),
        "bounds": np.asarray(mesh.bounds).tolist(),
        "extents": np.asarray(mesh.extents).tolist(),
    }
    result.update(edge_stats(mesh))
    return result, labels, sizes


scene = trimesh.load(SRC, force="scene")
raw = scene.to_geometry()

v = np.asarray(raw.vertices)
f = np.asarray(raw.faces)

# Exact-position weld: no vertex coordinates are moved. 8 decimals matches
# the duplicate-position audit used in T1 and only merges coincident positions.
rounded = np.round(v, 8)
unique_v, inverse = np.unique(rounded, axis=0, return_inverse=True)
wf = inverse[f]

nondeg = (
    (wf[:, 0] != wf[:, 1])
    & (wf[:, 1] != wf[:, 2])
    & (wf[:, 0] != wf[:, 2])
)
degenerate_removed = int(np.sum(~nondeg))
wf = wf[nondeg]

# Remove duplicate triangles independent of winding.
sorted_faces = np.sort(wf, axis=1)
_, first = np.unique(sorted_faces, axis=0, return_index=True)
keep = np.sort(first)
duplicate_faces_removed = int(len(wf) - len(keep))
wf = wf[keep]

welded = trimesh.Trimesh(vertices=unique_v, faces=wf, process=False)
welded_audit, labels, sizes = audit(welded, "exact_position_weld_all_components")

largest_label = int(np.argmax(sizes))
largest_faces = np.flatnonzero(labels == largest_label)
main = welded.submesh([largest_faces], append=True, repair=False)
main_audit, _, _ = audit(main, "largest_connected_component_after_weld")

welded_path = OUT / "S-trellis2-clean-seed0000-welded.glb"
main_path = OUT / "S-trellis2-clean-seed0000-maincomponent.glb"
welded.export(welded_path)
main.export(main_path)

result = {
    "source": str(SRC.relative_to(ROOT)),
    "operation": {
        "position_round_digits": 8,
        "coordinates_moved": False,
        "degenerate_faces_removed": degenerate_removed,
        "duplicate_faces_removed": duplicate_faces_removed,
        "small_components_removed_from_maincomponent": int(welded_audit["connected_components"] - 1),
        "largest_component_face_fraction": float(len(main.faces) / len(welded.faces)),
    },
    "welded_all": welded_audit,
    "maincomponent": main_audit,
}
(OUT / "T2_WELD_AUDIT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

decision = f"""# T2 exact-weld bench

This step does not retopologize, decimate, smooth, or move any retained vertex.

- source vertices: {len(v):,}
- exact-weld vertices: {len(welded.vertices):,}
- exact-weld faces: {len(welded.faces):,}
- exact-weld connected components: {welded_audit['connected_components']}
- exact-weld boundary edges: {welded_audit['boundary_edges']}
- exact-weld non-manifold edges (>2 faces): {welded_audit['nonmanifold_edges_gt2_faces']}

Largest connected component:

- vertices: {len(main.vertices):,}
- faces: {len(main.faces):,}
- share of welded faces: {len(main.faces)/len(welded.faces):.4%}
- boundary edges: {main_audit['boundary_edges']}
- non-manifold edges (>2 faces): {main_audit['nonmanifold_edges_gt2_faces']}
- watertight: {main_audit['watertight']}
- volume: {main_audit['is_volume']}

Interpretation: exact welding is topology recovery, not morphology editing. The largest
component is retained as the next repair input only if it removes detached fragments
without moving the S candidate surface.
"""
(OUT / "T2_WELD_RESULT.md").write_text(decision, encoding="utf-8")

print(json.dumps(result, indent=2))
