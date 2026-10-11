"""Real original-QEM S-type attached armor P: classify O intersections and
scan NON-DESTRUCTIVE clearance shape keys on the same connected topo.

No fake improvement: all face area and BVH collision results re-evaluated by
Blender. Preserve original donor, actual manifold M and O unaltered. Failed
candidate evidence persisted; visual design never auto-approved.
"""
import bpy,numpy as np,hashlib,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"tail-lamina-clearance-p-v1"
REV=OUT/"review"
REV.mkdir(parents=True,exist_ok=True)
REF=ROOT/"references/00_s_type_modeling_image_v1.png"
GLB=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
RS="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
GS="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
assert hashlib.sha256(REF.read_bytes()).hexdigest()==RS
assert hashlib.sha256(GLB.read_bytes()).hexdigest()==GS
src=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
m=bpy.data.objects["S_REAL_QEM_UNIFORM_ANGULAR_TAIL_M_NOT_APPROVED"]
o=bpy.data.objects["S_QEM_O_SKIN_CONNECTED_TAPERED_ARMOR_TRIAL_NOT_APPROVED"]
assert len(src.data.vertices)==29948 and len(src.data.polygons)==59932
assert len(m.data.vertices)==31948 and len(m.data.polygons)==63932
assert len(o.data.vertices)==32600 and len(o.data.polygons)==65236

def xyz(obj):
    bpy.context.view_layer.update()
    a=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=a.to_mesh()
    try:return np.array([a.matrix_world@v.co for v in mesh.vertices],dtype=np.float64)
    finally:a.to_mesh_clear()

src_xyz=xyz(src);m_xyz=xyz(m);o_xyz=xyz(o)
sha_original=hashlib.sha256(src_xyz.tobytes()).hexdigest()
sha_m=hashlib.sha256(m_xyz.tobytes()).hexdigest()
sha_o=hashlib.sha256(o_xyz.tobytes()).hexdigest()
tris=np.array([tuple(f.vertices) for f in o.data.polygons],dtype=np.int32)
T=o_xyz[tris]
area_normal=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0])
area_ref=np.linalg.norm(area_normal,axis=1)
assert np.count_nonzero(area_ref<1e-10)==0
face_centers=T.mean(axis=1)
# Use exactly O test ROI so 185 baseline stays comparable.
ids=np.flatnonzero((face_centers[:,1]>1.5)&
                   (face_centers[:,2]>.94)&
                   (np.abs(face_centers[:,0])<.7))
assert 7000<len(ids)<8000

base_tree=KDTree(len(m_xyz))
for i,v in enumerate(m_xyz):base_tree.insert(Vector(v),i)
base_tree.balance()
dist=np.array([base_tree.find(Vector(v))[2] for v in o_xyz],dtype=np.float64)
# No changes to original M donor or untouched limb geometry.
new_leaf=(dist>.025)
assert 150<new_leaf.sum()<1200,("leaf identification failed",new_leaf.sum())
def smooth(v):
    w=np.maximum(0.,np.minimum(1.,v))
    return w*w*(3.-2.*w)
weight=smooth((dist-.004)/.080)
weight*=smooth((o_xyz[:,1]-1.76)/.11)
weight*=(o_xyz[:,2]>1.10).astype(float)
assert 180<np.count_nonzero(weight>.30)<1500

def face_test(actual):
    x=actual[tris]
    n=np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0])
    len2=np.linalg.norm(n,axis=1)
    ratio=len2/area_ref
    wrong={
      "inverted":int(np.count_nonzero(np.sum(n*area_normal,axis=1)<0)),
      "collapsed":int(np.count_nonzero(len2<1e-10)),
      "area_lt_half":int(np.count_nonzero(ratio<.5)),
      "area_gt_double":int(np.count_nonzero(ratio>2.0)),
      "min_area_ratio":float(ratio.min()),
      "max_area_ratio":float(ratio.max())
    }
    return wrong

def collision_pairs(actual):
    t=actual[tris[ids]]
    bvh=BVHTree.FromPolygons([Vector(v) for v in actual],
               [tuple(map(int,tris[j])) for j in ids],all_triangles=True,epsilon=1.e-7)
    result=[]
    for i,j in bvh.overlap(bvh):
        if i>=j:continue
        a,b=map(int,tris[ids[i]]),map(int,tris[ids[j]])
        if set(a)&set(b):continue
        result.append((int(ids[i]),int(ids[j])))
    return sorted(result)

basepairs=collision_pairs(o_xyz)
assert len(basepairs)==185,("different O baseline than actual CI",len(basepairs))
# Exact failing pairs enriched with per-face center coords and new-versus-M
# classification, rather than inventing a root-cause from image appearance.
classification={"new_new":0,"new_core":0,"core_core":0}
bands={"root":0,"middle":0,"distal":0}
example=[]
for i,j in basepairs:
    flag_i=bool(np.any(new_leaf[tris[i]]))
    flag_j=bool(np.any(new_leaf[tris[j]]))
    cat=("new_new" if flag_i and flag_j else "new_core" if flag_i or flag_j else "core_core")
    classification[cat]+=1
    cen=((face_centers[i]+face_centers[j])*.5)
    bands["root" if cen[1]<2.02 else "middle" if cen[1]<2.57 else "distal"]+=1
    if len(example)<100:
        example.append({
         "polygons":[int(i),int(j)],"type":cat,
         "center_world":cen.tolist(),
         "tri_a_world":o_xyz[tris[i]].tolist(),
         "tri_b_world":o_xyz[tris[j]].tolist()})
root=1.64;L=1.97
t=np.clip((o_xyz[:,1]-root)/L,0.,1.)
core_x=.008617273531+.032*np.sin(np.pi*t)
core_z=1.599118232727+.065*np.sin(np.pi*t)-.33*t-.12*t*t
radial=np.column_stack([o_xyz[:,0]-core_x,np.zeros(len(t)),o_xyz[:,2]-core_z])
norm=np.linalg.norm(radial,axis=1)
radial=radial/np.maximum(norm[:,None],1e-6)
copy=o.copy()
copy.data=o.data.copy()
copy.name="S_QEM_P_SEWN_ARMOR_CLEARANCE_SAFETY_EXPERIMENT"
bpy.context.scene.collection.objects.link(copy)
copy.matrix_world=o.matrix_world.copy()
copy.shape_key_add(name="O_BASE_GEOMETRY",from_mix=False)
key=copy.shape_key_add(name="P_SURFACE_CLEARANCE_DEFORMATION",from_mix=False)
key.value=1.0
inv=copy.matrix_world.inverted()
def assign(v):
    for i,p in enumerate(v):key.data[i].co=inv@Vector(p)

candidates=[]
winner=None;chosen=None
# Candidate search: small *outward radial* offsets which do not flatten
# feather shape; do not move root rim or intact source.
for radial_push in (.035,.060,.090,.125,.16):
    for aft_shift in (0.,.03,.065):
        requested=o_xyz+radial*(weight*radial_push)[:,None]
        requested[:,1]+=aft_shift*weight
        assign(requested)
        measured=xyz(copy)
        face=face_test(measured)
        collisions=collision_pairs(measured)
        face_ok=all(face[k]==0 for k in ("inverted","collapsed","area_lt_half","area_gt_double"))
        row={
         "radial_push":radial_push,"aft_shift":aft_shift,
         "self_intersection_pairs":len(collisions),
         "change_from_O":len(collisions)-185,
         "face_quality":face,"face_quality_PASS":face_ok,
         "technical_PASS":face_ok and len(collisions)==0,
         "max_vertex_displacement":float(np.max(np.linalg.norm(measured-o_xyz,axis=1))),
         "first_40_intersections":collisions[:40]
        }
        candidates.append(row)
        print("O_TO_P_REAL_CLEARANCE",radial_push,aft_shift,row["self_intersection_pairs"],
              face_ok,face["inverted"],face["area_lt_half"],face["area_gt_double"])
        metric=(0 if face_ok else 1,len(collisions))
        if winner is None or metric<(0 if winner["face_quality_PASS"] else 1,winner["self_intersection_pairs"]):
            winner=row;chosen=measured.copy()
        if row["technical_PASS"]:break
    if winner and winner["technical_PASS"]:break

assert winner is not None
assign(chosen)
final=xyz(copy)
gate_f=face_test(final)
pairs_f=collision_pairs(final)
winner["replay_intersections"]=len(pairs_f)
winner["replay_face_gate"]=gate_f
winner["replay_PASS"]=(len(pairs_f)==0 and all(gate_f[k]==0 for k in
                                   ("inverted","collapsed","area_lt_half","area_gt_double")))
assert hashlib.sha256(xyz(src).tobytes()).hexdigest()==sha_original
assert hashlib.sha256(xyz(m).tobytes()).hexdigest()==sha_m
assert hashlib.sha256(xyz(o).tobytes()).hexdigest()==sha_o

report={
 "authoritative_S_SHA256":RS,"original_QEM_donor_SHA256":GS,
 "all_sources_preserved":True,
 "source_original_QEM_counts":[29948,59932],
 "base_M_counts":[31948,63932],
 "input_O_counts":[32600,65236],
 "output_P_counts":[len(copy.data.vertices),len(copy.data.polygons)],
 "source_M_nearest_dist_leaf_vertices_over_0_025":int(new_leaf.sum()),
 "weighted_vertices_over_0_30":int(np.count_nonzero(weight>.30)),
 "O_baseline_nonshared_collision_pairs":len(basepairs),
 "baseline_collision_classification":classification,
 "baseline_collision_y_bands":bands,
 "baseline_collision_exact_3D_examples":example,
 "tested_candidates":candidates,
 "selected":winner,
 "geometry_gate":"PASS_NO_COLLISIONS" if winner["replay_PASS"] else "FAIL",
 "canonical_S_visual_match":"UNAPPROVED_NOT_AUTOMATIC",
 "global_body_collision_check":"NOT_TESTED",
 "skin_weights_for_added_topology":"NOT_TESTED",
 "race_gait_97_sample_check":"NOT_TESTED",
 "production_game_ready":False
}
(OUT/"REAL_QEM_P_CLEARANCE_QA.json").write_text(json.dumps(report,indent=2)+"\n")
scene=bpy.context.scene
cam=scene.camera
assert cam and cam.type=="CAMERA"
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.render.resolution_x=1030;scene.render.resolution_y=772
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
cam.data.type="ORTHO"
views={
 "SIDE":Vector((1,0,0)),"FRONT":Vector((0,-1,0)),
 "FRONT34":Vector((1,-1,0)).normalized(),
 "REAR34":Vector((1,1,0)).normalized(),
 "BACK":Vector((0,1,0))
}
for v,vec in views.items():
    target=Vector((0,.20,1.25))
    cam.data.ortho_scale=6.5
    cam.location=target+vec*9
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    for tag,ob in (("O_BASE",o),("P_CLEARANCE",copy)):
        for obj in (src,m,o,copy):obj.hide_render=(obj!=ob)
        bpy.data.objects["S_QEM_TAIL_MORPH_TEST_A_NOT_APPROVED"].hide_render=True
        scene.render.filepath=str(REV/f"REAL_QEM_{tag}_{v}.png")
        bpy.ops.render.render(write_still=True)
for v,vec in (("SIDE",Vector((1,0,0))),("FRONT34",Vector((1,-1,0)).normalized())):
    target=Vector((0,2.34,1.36))
    cam.data.ortho_scale=2.9
    cam.location=target+vec*6
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    for tag,ob in (("O_BASE",o),("P_CLEARANCE",copy)):
        for obj in (src,m,o,copy):obj.hide_render=(obj!=ob)
        scene.render.filepath=str(REV/f"REAL_QEM_CLOSE_{tag}_{v}.png")
        bpy.ops.render.render(write_still=True)
for obj in (src,m,o):obj.hide_render=True
copy.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-real-sewn-leaf-clearance-P-TRIAL.blend"),compress=True)
print("P_REAL_MESH_QA",report["geometry_gate"],"O",185,"P",len(pairs_f),
      "best",winner["radial_push"],winner["aft_shift"],"categories",classification)
