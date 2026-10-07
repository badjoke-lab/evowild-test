#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np
import trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000"
SRC = BASE / "t2-meshfix/S-trellis2-clean-seed0000-maincomponent-meshfix.glb"
DST = BASE / "t2-lodtailor60k/S-trellis2-clean-seed0000-maincomponent-meshfix-lod60k.glb"
OUT = BASE / "t2-lodtailor60k"
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
    rows = np.r_[fa[:,0], fa[:,1]]
    cols = np.r_[fa[:,1], fa[:,0]]
    graph = coo_matrix((np.ones(len(rows), dtype=np.uint8),(rows,cols)),shape=(n,n)).tocsr()
    return connected_components(graph, directed=False, return_labels=True)

def audit(mesh,label):
    edges=np.sort(np.asarray(mesh.edges),axis=1)
    _,counts=np.unique(edges,axis=0,return_counts=True)
    ncomp,labels=face_components(mesh)
    sizes=np.bincount(labels) if len(labels) else np.array([],dtype=np.int64)
    return {
        "label":label,
        "vertices":int(len(mesh.vertices)),
        "faces":int(len(mesh.faces)),
        "connected_components":int(ncomp),
        "component_face_counts_desc":[int(x) for x in np.sort(sizes)[::-1][:16]],
        "boundary_edges":int(np.sum(counts==1)),
        "nonmanifold_edges_gt2_faces":int(np.sum(counts>2)),
        "watertight":bool(mesh.is_watertight),
        "winding_consistent":bool(mesh.is_winding_consistent),
        "is_volume":bool(mesh.is_volume),
        "euler_number":int(mesh.euler_number),
        "area":float(mesh.area),
        "bounds":np.asarray(mesh.bounds).tolist(),
        "extents":np.asarray(mesh.extents).tolist(),
    }

def drift_metrics(a,b,samples=20000):
    np.random.seed(20)
    pa,_=trimesh.sample.sample_surface(a,samples)
    np.random.seed(21)
    pb,_=trimesh.sample.sample_surface(b,samples)
    ta=cKDTree(pa); tb=cKDTree(pb)
    d_ab=tb.query(pa,k=1,workers=-1)[0]
    d_ba=ta.query(pb,k=1,workers=-1)[0]
    diag=float(np.linalg.norm(a.extents))
    def stats(x):
        return {
            "mean":float(np.mean(x)),
            "p95":float(np.quantile(x,.95)),
            "p99":float(np.quantile(x,.99)),
            "max":float(np.max(x)),
            "mean_over_source_bbox_diagonal":float(np.mean(x)/diag),
            "p95_over_source_bbox_diagonal":float(np.quantile(x,.95)/diag),
            "p99_over_source_bbox_diagonal":float(np.quantile(x,.99)/diag),
            "max_over_source_bbox_diagonal":float(np.max(x)/diag),
        }
    return {
        "samples_per_direction":samples,
        "source_bbox_diagonal":diag,
        "source_to_lod":stats(d_ab),
        "lod_to_source":stats(d_ba),
        "symmetric_mean_over_diagonal":float((np.mean(d_ab)+np.mean(d_ba))/2/diag),
        "symmetric_p95_over_diagonal":float((np.quantile(d_ab,.95)+np.quantile(d_ba,.95))/2/diag),
    }

def exact_position_weld(mesh, digits=8):
    v=np.asarray(mesh.vertices)
    f=np.asarray(mesh.faces)
    rounded=np.round(v,digits)
    unique_v,inverse=np.unique(rounded,axis=0,return_inverse=True)
    wf=inverse[f]
    nondeg=(
        (wf[:,0]!=wf[:,1])
        & (wf[:,1]!=wf[:,2])
        & (wf[:,0]!=wf[:,2])
    )
    degenerate_removed=int(np.sum(~nondeg))
    wf=wf[nondeg]
    sorted_faces=np.sort(wf,axis=1)
    _,first=np.unique(sorted_faces,axis=0,return_index=True)
    keep=np.sort(first)
    duplicate_faces_removed=int(len(wf)-len(keep))
    wf=wf[keep]
    welded=trimesh.Trimesh(vertices=unique_v,faces=wf,process=False)
    return welded,{
        "position_round_digits":digits,
        "coordinates_moved":False,
        "degenerate_faces_removed":degenerate_removed,
        "duplicate_faces_removed":duplicate_faces_removed,
    }

source=load_mesh(SRC)
lod_raw=load_mesh(DST)
lod,lod_weld_operation=exact_position_weld(lod_raw,8)
sa=audit(source,"meshfix_source")
lra=audit(lod_raw,"lodtailor_60k_export_raw")
la=audit(lod,"lodtailor_60k_exact_position_weld")
drift=drift_metrics(source,lod)

result={
    "source":str(SRC.relative_to(ROOT)),
    "output":str(DST.relative_to(ROOT)),
    "upstream_component":"LODTailor-The-Mesh-Trimmer-ComfyuiNode/decimate_only.py",
    "upstream_commit":"3d25b7d4aa382fa5dac210eb5d8d0eadc4a4f183",
    "settings":{
        "target_tris":60000,
        "passes":3,
        "tolerance":1.05,
        "voxel_rebuild":False,
        "triangulate":True,
        "seal_distance":0.0001,
        "seal_keep_trying":True,
    },
    "source_audit":sa,
    "lod_export_raw_audit":lra,
    "lod_export_exact_weld_operation":lod_weld_operation,
    "lod_audit":la,
    "drift":drift,
    "automatic_gate":{
        "topology_pass":bool(la["connected_components"]==1 and la["boundary_edges"]==0 and la["nonmanifold_edges_gt2_faces"]==0 and la["watertight"]),
        "target_count_pass":bool(la["faces"]<=63000),
        "low_drift_candidate":bool(drift["symmetric_p95_over_diagonal"]<=0.01),
        "note":"Automatic metrics are not visual morphology or deformation approval."
    }
}
(OUT/"T2_LODTAILOR60K_AUDIT.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
md=f"""# T2 PixelArtistry LODTailor 60k bench

Upstream worker pinned at `3d25b7d4aa382fa5dac210eb5d8d0eadc4a4f183`.

- source faces: {sa['faces']:,}
- GLB export raw faces: {lra['faces']:,}
- GLB export raw vertices: {lra['vertices']:,}
- exact-position-weld faces: {la['faces']:,}
- exact-position-weld vertices: {la['vertices']:,}
- exact-position-weld connected components: {la['connected_components']}
- boundary edges: {la['boundary_edges']}
- non-manifold edges (>2 faces): {la['nonmanifold_edges_gt2_faces']}
- watertight: {la['watertight']}
- volume: {la['is_volume']}
- symmetric p95 drift / source bbox diagonal: {drift['symmetric_p95_over_diagonal']:.6f}

The GLB is audited after an exact-position weld because flat-normal/attribute seams can split identical positions on export. This weld moves no coordinates.

Automatic topology pass: {result['automatic_gate']['topology_pass']}
Automatic target-count pass: {result['automatic_gate']['target_count_pass']}
Automatic low-drift candidate: {result['automatic_gate']['low_drift_candidate']}

A five-view visual comparison is required before any deformation test.
"""
(OUT/"T2_LODTAILOR60K_RESULT.md").write_text(md,encoding="utf-8")
print(json.dumps(result,indent=2))
