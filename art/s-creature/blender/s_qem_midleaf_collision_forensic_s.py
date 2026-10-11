"""Real Blender QEM mid-left feather: forensic collision coordinates and structure.

Loads pre-existing, repeatable Q MID_LEFT evaluated .blend from repo; no
geometry edited, only writes immutable data describing the five actual BVH
collisions with triangle coordinates and closest original-M reference.
"""
import bpy,numpy as np,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"midleaf-forensic-s-v1";OUT.mkdir(parents=True,exist_ok=True)
ref=ROOT/"references/00_s_type_modeling_image_v1.png"
donor=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
rh="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
dh="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
assert hashlib.sha256(ref.read_bytes()).hexdigest()==rh
assert hashlib.sha256(donor.read_bytes()).hexdigest()==dh
src=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
core=bpy.data.objects["S_REAL_QEM_UNIFORM_ANGULAR_TAIL_M_NOT_APPROVED"]
leaf=bpy.data.objects["S_QEM_Q_SINGLE_SEWN_LEAF_MID_LEFT_NOT_APPROVED"]
assert (len(src.data.vertices),len(src.data.polygons))==(29948,59932)
assert (len(core.data.vertices),len(core.data.polygons))==(31948,63932)
assert (len(leaf.data.vertices),len(leaf.data.polygons))==(32232,64500)
def actual(o):
    bpy.context.view_layer.update()
    x=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=x.to_mesh()
    try:return np.asarray([x.matrix_world@v.co for v in me.vertices],dtype=float)
    finally:x.to_mesh_clear()

orig=actual(src);m=actual(core);v=actual(leaf)
t=np.asarray([list(f.vertices) for f in leaf.data.polygons],dtype=np.int32)
a=v[t]
cent=a.mean(axis=1)
roi=np.flatnonzero((cent[:,1]>1.50)&(cent[:,2]>.94)&(abs(cent[:,0])<.7))
ft=[tuple(map(int,t[i])) for i in roi]
bvh=BVHTree.FromPolygons([Vector(p) for p in v],ft,all_triangles=True,epsilon=1.e-7)
pairs=[]
for i,j in bvh.overlap(bvh):
    if i>=j:continue
    if set(ft[i])&set(ft[j]):continue
    pairs.append((int(roi[i]),int(roi[j])))
pairs=sorted(pairs)
assert len(pairs)==5,(len(pairs),pairs)
tree=KDTree(len(m))
for i,x in enumerate(m):tree.insert(Vector(x),i)
tree.balance()
distance=np.asarray([tree.find(Vector(p))[2] for p in v])
face_ids=sorted(set(i for q in pairs for i in q))
faces=[]
for fi in face_ids:
    tri=t[fi]
    pp=v[tri]
    norm=np.cross(pp[1]-pp[0],pp[2]-pp[0])
    length=np.linalg.norm(norm)
    dirs=(norm/length).tolist() if length>1e-15 else None
    faces.append({
      "face_id":int(fi),"vertex_indices":list(map(int,tri)),
      "vertex_world":pp.tolist(),"vertex_nearest_M_dist":distance[tri].tolist(),
      "new_leaf_vertex_gt_0_025":list(map(bool,distance[tri]>.025)),
      "centroid_world":cent[fi].tolist(),"normal":dirs,
      "face_twice_area":float(length),
      "bounding_box_min":pp.min(axis=0).tolist(),
      "bounding_box_max":pp.max(axis=0).tolist()
    })
details=[]
for i,j in pairs:
    ci,cj=cent[i],cent[j]
    details.append({"face_i":i,"face_j":j,
                    "centroids_world":[ci.tolist(),cj.tolist()],
                    "centroid_delta_magnitude":float(np.linalg.norm(ci-cj)),
                    "both_appear_original_M":bool((distance[t[i]]<=.025).all() and
                                                  (distance[t[j]]<=.025).all())})
digest=hashlib.sha256(np.round(v,6).tobytes()).hexdigest()
report={
 "authoritative_S_sha256":rh,
 "original_QEM_GLb_sha256":dh,
 "source_and_M_intact":True,"real_midleaf_model":True,
 "midleaf_mesh_sha256_6dp":digest,
 "expected_previous_Q_digest":"__FILL_FROM_Q_QA__",
 "roi_polygon_count":len(roi),"collision_count":len(pairs),"pairs":details,
 "offending_faces":faces,
 "new_leaf_vertices_gt_0_025_from_M":int((distance>.025).sum()),
 "technical_rejection_reason":"FIVE_BVH_COLLISIONS_BEFORE_CORRECTION",
 "design_S_match":"NOT_APPROVED",
 "changes_to_geometry":False
}
(OUT/"ACTUAL_QEM_MIDLEAF_FIVE_FACE_FORENSIC.json").write_text(json.dumps(report,indent=2)+"\n")
print("S_MIDLEAF_FIVE_COLLISIONS",json.dumps(details,indent=2))
print("S_MIDLEAF_3D_OFFENDERS",json.dumps(faces,indent=2))
