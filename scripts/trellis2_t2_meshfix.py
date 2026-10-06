#!/usr/bin/env python3
import inspect
import json
from pathlib import Path

import numpy as np
import trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
from pymeshfix import MeshFix

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-weld/S-trellis2-clean-seed0000-maincomponent.glb"
OUT = ROOT / "art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-meshfix"
OUT.mkdir(parents=True, exist_ok=True)


def load_mesh(path):
    obj = trimesh.load(path, force="scene")
    return obj.to_geometry()


def face_components(mesh):
    fa = np.asarray(mesh.face_adjacency, dtype=np.int32)
    n = len(mesh.faces)
    if n == 0:
        return 0, np.array([], dtype=np.int32)
    if len(fa) == 0:
        return n, np.arange(n, dtype=np.int32)
    rows = np.r_[fa[:, 0], fa[:, 1]]
    cols = np.r_[fa[:, 1], fa[:, 0]]
    graph = coo_matrix(
        (np.ones(len(rows), dtype=np.uint8), (rows, cols)),
        shape=(n, n),
    ).tocsr()
    return connected_components(graph, directed=False, return_labels=True)


def audit(mesh, label):
    edges = np.sort(np.asarray(mesh.edges), axis=1)
    _, counts = np.unique(edges, axis=0, return_counts=True)
    ncomp, labels = face_components(mesh)
    sizes = np.bincount(labels) if len(labels) else np.array([], dtype=np.int64)
    return {
        "label": label,
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "connected_components": int(ncomp),
        "component_face_counts_desc": [int(x) for x in np.sort(sizes)[::-1][:16]],
        "boundary_edges": int(np.sum(counts == 1)),
        "nonmanifold_edges_gt2_faces": int(np.sum(counts > 2)),
        "edge_face_count_histogram": {
            str(int(k)): int(v)
            for k, v in zip(*np.unique(counts, return_counts=True))
        },
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "is_volume": bool(mesh.is_volume),
        "euler_number": int(mesh.euler_number),
        "area": float(mesh.area),
        "bounds": np.asarray(mesh.bounds).tolist(),
        "extents": np.asarray(mesh.extents).tolist(),
    }


def drift_metrics(a, b, samples=20000):
    np.random.seed(0)
    pa, _ = trimesh.sample.sample_surface(a, samples)
    np.random.seed(1)
    pb, _ = trimesh.sample.sample_surface(b, samples)
    ta = cKDTree(pa)
    tb = cKDTree(pb)
    d_ab = tb.query(pa, k=1, workers=-1)[0]
    d_ba = ta.query(pb, k=1, workers=-1)[0]
    diag = float(np.linalg.norm(a.extents))

    def stats(x):
        return {
            "mean": float(np.mean(x)),
            "p50": float(np.quantile(x, 0.50)),
            "p95": float(np.quantile(x, 0.95)),
            "p99": float(np.quantile(x, 0.99)),
            "max": float(np.max(x)),
            "mean_over_source_bbox_diagonal": float(np.mean(x) / diag),
            "p95_over_source_bbox_diagonal": float(np.quantile(x, 0.95) / diag),
            "p99_over_source_bbox_diagonal": float(np.quantile(x, 0.99) / diag),
            "max_over_source_bbox_diagonal": float(np.max(x) / diag),
        }

    return {
        "samples_per_direction": samples,
        "source_bbox_diagonal": diag,
        "source_to_repaired_nn": stats(d_ab),
        "repaired_to_source_nn": stats(d_ba),
        "symmetric_mean_over_diagonal": float((np.mean(d_ab) + np.mean(d_ba)) / 2 / diag),
        "symmetric_p95_over_diagonal": float((np.quantile(d_ab, .95) + np.quantile(d_ba, .95)) / 2 / diag),
    }


source = load_mesh(SRC)
source_audit = audit(source, "welded_largest_component")

mf = MeshFix(np.asarray(source.vertices), np.asarray(source.faces))
sig = inspect.signature(mf.repair)
kwargs = {}
if "verbose" in sig.parameters:
    kwargs["verbose"] = False
if "joincomp" in sig.parameters:
    kwargs["joincomp"] = False
if "remove_smallest_components" in sig.parameters:
    kwargs["remove_smallest_components"] = False
mf.repair(**kwargs)

repaired = trimesh.Trimesh(
    vertices=np.asarray(mf.points),
    faces=np.asarray(mf.faces),
    process=False,
)
repaired.remove_unreferenced_vertices()

repaired_audit = audit(repaired, "pymeshfix_repaired")
drift = drift_metrics(source, repaired)

dst = OUT / "S-trellis2-clean-seed0000-maincomponent-meshfix.glb"
repaired.export(dst)

result = {
    "source": str(SRC.relative_to(ROOT)),
    "method": "pymeshfix.MeshFix.repair",
    "repair_kwargs": kwargs,
    "source_audit": source_audit,
    "repaired_audit": repaired_audit,
    "drift": drift,
    "automatic_gate": {
        "topology_pass": bool(
            repaired_audit["connected_components"] == 1
            and repaired_audit["boundary_edges"] == 0
            and repaired_audit["nonmanifold_edges_gt2_faces"] == 0
            and repaired_audit["watertight"]
        ),
        "low_drift_candidate": bool(
            drift["symmetric_p95_over_diagonal"] <= 0.01
        ),
        "note": "Automatic metrics are not visual morphology approval."
    }
}
(OUT / "T2_MESHFIX_AUDIT.json").write_text(
    json.dumps(result, indent=2) + "\n",
    encoding="utf-8",
)

md = f"""# T2 MeshFix repair bench

Source: exact-weld largest connected component.

## Topology

Before:
- vertices: {source_audit['vertices']:,}
- faces: {source_audit['faces']:,}
- boundary edges: {source_audit['boundary_edges']}
- non-manifold edges (>2 faces): {source_audit['nonmanifold_edges_gt2_faces']}
- watertight: {source_audit['watertight']}

After MeshFix:
- vertices: {repaired_audit['vertices']:,}
- faces: {repaired_audit['faces']:,}
- connected components: {repaired_audit['connected_components']}
- boundary edges: {repaired_audit['boundary_edges']}
- non-manifold edges (>2 faces): {repaired_audit['nonmanifold_edges_gt2_faces']}
- watertight: {repaired_audit['watertight']}
- volume: {repaired_audit['is_volume']}

## Approximate morphology drift

- symmetric mean / source bbox diagonal: {drift['symmetric_mean_over_diagonal']:.6f}
- symmetric p95 / source bbox diagonal: {drift['symmetric_p95_over_diagonal']:.6f}
- source→repair p99 / diagonal: {drift['source_to_repaired_nn']['p99_over_source_bbox_diagonal']:.6f}
- repair→source p99 / diagonal: {drift['repaired_to_source_nn']['p99_over_source_bbox_diagonal']:.6f}

Automatic topology pass: {result['automatic_gate']['topology_pass']}
Automatic low-drift candidate: {result['automatic_gate']['low_drift_candidate']}

These metrics do not authorize rig/motion. A visual review is still required.
"""
(OUT / "T2_MESHFIX_RESULT.md").write_text(md, encoding="utf-8")

print(json.dumps(result, indent=2))
