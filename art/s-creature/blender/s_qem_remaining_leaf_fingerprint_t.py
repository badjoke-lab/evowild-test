"""Forensic source-QEM 3D collision mapping for remaining S tail root & tip.

Includes only original approved SHA locked image and donor; no mesh edits.
Use exact deterministic, previously-archived separate Q Blender candidates.
"""
import bpy,numpy as np,os,json,hashlib,collections
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

PANEL=os.environ.get("TAIL_PANEL")
assert PANEL in ("PROXIMAL_RIGHT","DISTAL_RIGHT"),PANEL
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/("tail-remaining-forensic-t-"+PANEL.lower())
OUT.mkdir(parents=True,exist_ok=True)
R="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
G="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
ref=ROOT/"references/00_s_type_modeling_image_v1.png"
donor=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
assert hashlib.sha256(ref.read_bytes()).hexdigest()==R
assert hashlib.sha256(donor.read_bytes()).hexdigest()==G
src=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
m=bpy.data.objects["S_REAL_QEM_UNIFORM_ANGULAR_TAIL_M_NOT_APPROVED"]
q=bpy.data.objects["S_QEM_Q_SINGLE_SEWN_LEAF_"+PANEL+"_NOT_APPROVED"]
assert (len(src.data.vertices),len(src.data.polygons))==(29948,59932)
assert (len(m.data.vertices),len(m.data.polygons))==(31948,63932)
expected={"PROXIMAL_RIGHT":(32117,64270,34,1.85030174),
          "DISTAL_RIGHT":(32147,64330,152,2.69752693)}
nverts,nfaces,prior_count,root_y=expected[PANEL]
assert (len(q.data.vertices),len(q.data.polygons))==(nverts,nfaces)
def xyz(o):
    bpy.context.view_layer.update()
    ob=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=ob.to_mesh()
    try:return np.asarray([ob.matrix_world@v.co for v in mesh.vertices],dtype=np.float64)
    finally:ob.to_mesh_clear()
v=xyz(q);mxyz=xyz(m)
source_digest=hashlib.sha256(xyz(src).tobytes()).hexdigest()
origQdigest=hashlib.sha256(np.round(v,6).tobytes()).hexdigest()
tris=np.asarray([tuple(p.vertices) for p in q.data.polygons],dtype=np.int32)
x=v[tris];c=x.mean(axis=1)
ROI=np.flatnonzero((c[:,1]>1.50)&(c[:,2]>.94)&(abs(c[:,0])<.7))
rt=[tuple(int(t) for t in tris[i]) for i in ROI]
tree=BVHTree.FromPolygons([Vector(i) for i in v],rt,all_triangles=True,epsilon=1e-7)
pairs=[]
for ia,ib in tree.overlap(tree):
    if ia>=ib:continue
    if set(rt[ia])&set(rt[ib]):continue
    pairs.append((int(ROI[ia]),int(ROI[ib])))
pairs.sort()
assert len(pairs)==prior_count,(PANEL,len(pairs),prior_count)
treeM=KDTree(len(mxyz))
for i,x in enumerate(mxyz):treeM.insert(Vector(x),i)
treeM.balance()
dist=np.array([treeM.find(Vector(pt))[2] for pt in v])
detailed=[]
affected=collections.Counter()
roots={}
for i,j in pairs:
    cc=(c[i]+c[j])/2.
    band="ROOT_FIRST_RING" if cc[1]<root_y+.17 else (
         "MID_SPAN" if cc[1]<root_y+.40 else "TIP_END")
    roots[band]=roots.get(band,0)+1
    new_ids=[int(a) for z in (i,j) for a in tris[z] if int(a)>=31948]
    affected.update(new_ids)
    if len(detailed)<160:
        detailed.append({
          "faces":[i,j],"world_midpoint":cc.tolist(),
          "Y_dist_from_attachment_center":float(cc[1]-root_y),
          "section":band,"face_vertices":[tris[i].tolist(),tris[j].tolist()],
          "new_ring_vertex_ids":sorted(set(new_ids)),
          "face_normals":[[
             float(t) for t in np.cross(x[k,1]-x[k,0],x[k,2]-x[k,0])/
             max(np.linalg.norm(np.cross(x[k,1]-x[k,0],x[k,2]-x[k,0])),1e-12)
          ] for k in (i,j)]
        })
top=[]
for i,freq in affected.most_common(40):
    top.append({"vertex_id":i,"involved_pair_count":freq,
                "XYZ_world":v[i].tolist(),
                "nearest_M_vertex_distance":float(dist[i])})
out={
  "canonical_ref_SHA256":R,"original_QEM_GLb_SHA256":G,
  "target":PANEL,"original_QEM_and_M_untouched":True,
  "source_QEM_29948_vertices":True,
  "real_Q_derived_vertex_digest_6dp":origQdigest,
  "vertex_count":nverts,"triangle_count":nfaces,
  "baseline_actual_collision_pairs":len(pairs),"correctly_reproduces_previous_Q":True,
  "collisions_by_root_mid_tip":roots,
  "new_ring_vertex_frequency":top,
  "all_intersecting_pair_geometry":detailed,
  "original_source_SHA256_evaluated_array":source_digest,
  "target_morphology_approved":False,
  "mesh_modifications":False,
  "game_ready":False
}
(OUT/"REAL_QEM_T_REMAINING_LEAF_COLLISION_MAP.json").write_text(json.dumps(out,indent=2)+"\n")
print("S_T_REMAINING_BVH_ROOT_MAP",PANEL,roots,"critical",top[:12])
