"""EvoWild S real original-QEM tail H self-intersection localization.
Separates baseline A collisions from the new, surface-connected H feather
collisions, records exactly which 3D regions/triangles are involved. No mesh
mutations, no substitute standard, no screenshots presented as game assets.
"""
import bpy, numpy as np, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
HBASE=BASE/"tail-authority-blades-h-v1"
OUT=BASE/"tail-intersection-audit-i-v1"
OUT.mkdir(parents=True,exist_ok=True)
ref=ROOT/"references/00_s_type_modeling_image_v1.png"
glb=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
assert hashlib.sha256(ref.read_bytes()).hexdigest()=="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
assert hashlib.sha256(glb.read_bytes()).hexdigest()=="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
src=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
a=bpy.data.objects["S_QEM_TAIL_MORPH_TEST_A_NOT_APPROVED"]
h=bpy.data.objects["S_QEM_REAL_TAIL_SWEPT_BLADES_H_DESIGN_TRIAL"]
assert len(src.data.vertices)==len(a.data.vertices)==29948
assert len(h.data.vertices)==30540
def coordinates(o):
    bpy.context.view_layer.update()
    ob=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=ob.to_mesh()
    try:return np.asarray([ob.matrix_world@v.co for v in me.vertices],dtype=np.float64)
    finally:ob.to_mesh_clear()
orig=coordinates(src)
a_xyz=coordinates(a)
h_xyz=coordinates(h)
origin_hash=hashlib.sha256(orig.tobytes()).hexdigest()
original_a_hash=hashlib.sha256(a_xyz.tobytes()).hexdigest()
original_h_hash=hashlib.sha256(h_xyz.tobytes()).hexdigest()
verts_ref=KDTree(len(a_xyz))
for i,v in enumerate(a_xyz):verts_ref.insert(Vector(v),i)
verts_ref.balance()
# The new integrated lofts have vertices away from original A skin.
distance_from_a=np.array([verts_ref.find(Vector(v))[2] for v in h_xyz])
new_surface_vertex=(distance_from_a>.012)
assert new_surface_vertex.sum()>60
def audit(obj,xyz):
    tris=np.asarray([tuple(f.vertices) for f in obj.data.polygons],dtype=np.int32)
    centroid=xyz[tris].mean(axis=1)
    face_ids=np.flatnonzero((centroid[:,1]>1.55)&(centroid[:,2]>1.28)&(abs(centroid[:,0])<.55))
    faces=[tuple(int(z) for z in tris[i]) for i in face_ids]
    tree=BVHTree.FromPolygons([Vector(z) for z in xyz],faces,all_triangles=True,epsilon=1.e-7)
    results=[]
    for ai,bi in tree.overlap(tree):
        if ai>=bi:continue
        va=faces[ai];vb=faces[bi]
        if set(va)&set(vb):continue
        results.append((int(face_ids[ai]),int(face_ids[bi])))
    return tris,centroid,results,face_ids
tri_a,cen_a,overlap_a,roi_a=audit(a,a_xyz)
tri_h,cen_h,overlap_h,roi_h=audit(h,h_xyz)
hist={}
examples=[]
classify={"new_to_new":0,"new_to_original":0,"original_to_original":0}
for aa,bb in overlap_h:
    a_new=bool(np.any(new_surface_vertex[tri_h[aa]]))
    b_new=bool(np.any(new_surface_vertex[tri_h[bb]]))
    label="new_to_new" if a_new and b_new else ("new_to_original" if a_new or b_new else "original_to_original")
    classify[label]+=1
    c=(cen_h[aa]+cen_h[bb])*.5
    by_y=("BASE" if c[1]<1.96 else ("MID" if c[1]<2.30 else "DISTAL"))
    key=label+":"+by_y
    hist[key]=hist.get(key,0)+1
    if len(examples)<150:
        examples.append({
            "face_a":aa,"face_b":bb,
            "new_a":a_new,"new_b":b_new,"collision_type":label,
            "3d_midpoint_world":c.tolist(),
            "triangle_a_world":h_xyz[tri_h[aa]].tolist(),
            "triangle_b_world":h_xyz[tri_h[bb]].tolist(),
            "face_a_vertex_ids":list(map(int,tri_h[aa])),
            "face_b_vertex_ids":list(map(int,tri_h[bb]))
        })
report={
  "ref_png_sha256":"93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6",
  "source_glb_sha256":"e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f",
  "source_preserved":True,
  "donor_source_vertices":len(orig),
  "A_existing_original_QEM_vertices":len(a_xyz),
  "H_derived_connected_QEM_vertices":len(h_xyz),
  "A_source_sha256_world_vertex_array":original_a_hash,
  "H_derived_sha256_world_vertex_array":original_h_hash,
  "A_baseline_self_intersections":len(overlap_a),
  "H_total_self_intersections":len(overlap_h),
  "H_surface_vertices_more_than_0_012_from_A":int(new_surface_vertex.sum()),
  "H_intersection_type_counts":classify,
  "H_intersection_type_region_histogram":hist,
  "H_example_polygons_and_exact_3D_coordinates":examples,
  "A_first_50_baseline_face_pairs":[[int(aa),int(bb)] for aa,bb in overlap_a[:50]],
  "is_H_visual_S_approved":False,
  "is_H_mesh_repair_complete":False,
  "production_approved":False
}
(OUT/"QEM_H_TAIL_COLLISION_LOCATION_QA.json").write_text(json.dumps(report,indent=2)+"\n")
print("REAL_QEM_H_INTERSECTION_AUDIT",json.dumps({
  "baseline_A":len(overlap_a),
  "new_H":len(overlap_h),
  "classification":classify,
  "zones":hist,
  "added_vertex_count":int(new_surface_vertex.sum())
},indent=2))
assert hashlib.sha256(coordinates(src).tobytes()).hexdigest()==origin_hash
