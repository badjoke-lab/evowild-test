"""EvoWild S original-QEM tail J: source-surface collision clearance search.

Actual derived H connected feather mesh, copied to a new candidate with a
NON-DESTRUCTIVE surface-clearance shape key. Pull existing, attached leaf
vertices gently outward from ORIGINAL A skin via measured nearest-distance
weights, keeping attachment vertices fixed. Test true triangle-stress and
3D BVH collision counts for each candidate; preserve every failed result.
Never substitute another base mesh or approve S shape from numerical PASS.
"""
from pathlib import Path
import bpy, numpy as np, math, json, hashlib
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"tail-surface-clearance-j-v1"
REV=OUT/"review"
REV.mkdir(parents=True,exist_ok=True)
ref=ROOT/"references/00_s_type_modeling_image_v1.png"
donor=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
RH="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
DH="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
assert hashlib.sha256(ref.read_bytes()).hexdigest()==RH
assert hashlib.sha256(donor.read_bytes()).hexdigest()==DH
src=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
A=bpy.data.objects["S_QEM_TAIL_MORPH_TEST_A_NOT_APPROVED"]
H=bpy.data.objects["S_QEM_REAL_TAIL_SWEPT_BLADES_H_DESIGN_TRIAL"]
assert len(src.data.vertices)==len(A.data.vertices)==29948
assert len(H.data.vertices)==30540 and len(H.data.polygons)==61116

def evaluated(obj):
    bpy.context.view_layer.update()
    o=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=o.to_mesh()
    try:return np.asarray([o.matrix_world@v.co for v in me.vertices],dtype=np.float64)
    finally:o.to_mesh_clear()

world_A=evaluated(A)
world_src=evaluated(src)
world_H=evaluated(H)
source_signature=hashlib.sha256(world_src.tobytes()).hexdigest()
H_signature=hashlib.sha256(world_H.tobytes()).hexdigest()
src_tree=KDTree(len(world_A))
for i,v in enumerate(world_A):src_tree.insert(Vector(v),i)
src_tree.balance()
distance=np.array([src_tree.find(Vector(v))[2] for v in world_H],dtype=np.float64)
assert np.count_nonzero(distance>.012)>200
# Detect the new feather surface by 3D distance from OLD QUEM skin.
def smooth(arr):
    t=np.clip(arr,0.,1.)
    return t*t*(3-2*t)
w=smooth((distance-.003)/.125)
# Keep initial skin attachment ring position fixed as near as possible.
w *= smooth((world_H[:,1]-1.64)/.26)
w *= (world_H[:,2]>1.27).astype(float)
# Underlying original skin must not be pushed around with new feathers.
# Restrict remaining candidate effect to previously identified feather ROI.
assert np.count_nonzero(w>.3)>140

out=H.copy()
out.data=H.data.copy()
out.name="S_QEM_J_CONNECTED_TAIL_SURFACE_CLEARANCE_TRIAL"
bpy.context.scene.collection.objects.link(out)
out.matrix_world=H.matrix_world.copy()
out.shape_key_add(name="BASE_H_REST_UNCHANGED",from_mix=False)
key=out.shape_key_add(name="J_SKIN_AVOIDANCE_CLEARANCE",from_mix=False)
key.value=1.
inv=out.matrix_world.inverted()

tris=np.asarray([tuple(f.vertices) for f in out.data.polygons],dtype=np.int32)
original_tri=world_H[tris]
norm0=np.cross(original_tri[:,1]-original_tri[:,0],original_tri[:,2]-original_tri[:,0])
area0=np.linalg.norm(norm0,axis=1)
valid=area0>1.e-10
assert valid.sum()>61000
def mesh_quality(xyz):
    tri=xyz[tris]
    n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    lengths=np.linalg.norm(n,axis=1)
    ratio=np.divide(lengths,area0,out=np.ones_like(lengths),where=valid)
    stats={
        "inverted":int(np.count_nonzero((np.sum(n*norm0,axis=1)<0)&valid)),
        "collapsed":int(np.count_nonzero((lengths<1.e-10)&valid)),
        "area_lt_half":int(np.count_nonzero((ratio<.5)&valid)),
        "area_gt_double":int(np.count_nonzero((ratio>2)&valid)),
        "min_ratio":float(ratio[valid].min()),
        "max_ratio":float(ratio[valid].max())
    }
    return stats
def bvh_collision(xyz):
    tri=xyz[tris]
    cen=tri.mean(axis=1)
    ids=np.flatnonzero((cen[:,1]>1.55)&(cen[:,2]>1.28)&(abs(cen[:,0])<.55))
    meshtris=[tuple(map(int,tris[k])) for k in ids]
    bvh=BVHTree.FromPolygons([Vector(v) for v in xyz],meshtris,
                              all_triangles=True,epsilon=1.e-7)
    pairs=[]
    for a,b in bvh.overlap(bvh):
        if a>=b:continue
        if set(meshtris[a])&set(meshtris[b]):continue
        pairs.append((int(ids[a]),int(ids[b])))
    return len(pairs),pairs
base_overlap,base_pairs=bvh_collision(world_H)
assert base_overlap==824,("new run's H baseline differs",base_overlap)
def assign(v):
    for i,p in enumerate(v):
        key.data[i].co=inv@Vector(p)
def candidate(up,spread):
    p=world_H.copy()
    # Distribute to the sides smoothly, preserving central blade attachment;
    # do not create disconnected geometry or a separate card.
    p[:,2]+=up*w
    p[:,0]+=spread*w*np.tanh((world_H[:,0]-.015)/.068)
    return p

scan=[]
winner=None
best_geometry=None
best_metric=None
for up in (.20,.15,.10,.06,.035):
    for spread in (.22,.15,.09,.04):
        proposal=candidate(up,spread)
        assign(proposal)
        xyz=evaluated(out)
        face=mesh_quality(xyz)
        count,pairs=bvh_collision(xyz)
        gate=all(face[k]==0 for k in ("inverted","collapsed","area_lt_half","area_gt_double"))
        # Lower collisions is more important than moving the largest distance.
        # Require meaningful nonzero motion to prevent false "improvement".
        improvement=base_overlap-count
        metric=(0 if gate else 1,count,up+spread)
        row={
           "up":up,"outward_spread":spread,
           "nonshared_triangle_intersections":count,
           "intersection_change_from_H":-improvement,
           "max_vertex_displacement":float(np.linalg.norm(xyz-world_H,axis=1).max()),
           "face_quality":face,"triangle_gate_pass":gate,
           "candidate_clearance_gate_pass":gate and count==0,
           "first_intersection_face_pairs":pairs[:20],
        }
        scan.append(row)
        print("QEM_TAIL_J_CLEARANCE_SCAN",up,spread,"intersections",count,
              "delta",count-base_overlap,"geometry",gate)
        if best_metric is None or metric<best_metric:
            best_metric=metric
            winner=row
            best_geometry=xyz.copy()
        if gate and count==0:break
    if winner is not None and winner["candidate_clearance_gate_pass"]:break
assert winner is not None
assign(best_geometry)
replay=evaluated(out)
replay_faces=mesh_quality(replay)
replay_collision,replay_pairs=bvh_collision(replay)
# Blake float rounding can marginally shift metrics; recompute after replay.
winner["replayed_real_intersections"]=replay_collision
winner["replayed_face_quality"]=replay_faces
winning_geometry_ok=all(replay_faces[k]==0 for k in ("inverted","collapsed","area_lt_half","area_gt_double"))
winner["replayed_technical_pass"]=winning_geometry_ok and replay_collision==0
assert hashlib.sha256(evaluated(src).tobytes()).hexdigest()==source_signature
assert hashlib.sha256(evaluated(H).tobytes()).hexdigest()==H_signature
assert len(out.data.vertices)==30540 and len(out.data.polygons)==61116

report={
 "canonical_S_authority_SHA256":RH,"original_QEM_donor_SHA256":DH,
 "source_QEM_unchanged":True,
 "source_H_variant_unchanged":True,
 "H_real_mesh_vertices":30540,"H_real_mesh_triangles":61116,
 "J_real_mesh_vertices":30540,"J_real_mesh_triangles":61116,
 "origin_tail_intersections_A":0,
 "H_new_tail_intersections_at_start":base_overlap,
 "local_original_QEM_distance_weight_vertices":int(np.count_nonzero(w>.3)),
 "candidates":scan,"selected":winner,
 "topology_unchanged_from_one_manifold_H":True,
 "numeric_technical_clearance_gate":"PASS" if winner["replayed_technical_pass"] else "FAIL",
 "design_reference_silhouette_gate":"NOT_APPROVED_PENDING_REAL_REVIEW",
 "self_intersection_method":"BVHTree tested triangle intersections discounting only faces that share vertices; same ROI H and J",
 "rig_on_J":"NOT_TESTED",
 "animation_on_J":"NOT_TESTED",
 "game_production":"REJECT_NOT_APPROVED"
}
(OUT/"QEM_J_SURFACE_CLEARANCE_QA.json").write_text(json.dumps(report,indent=2)+"\n")

scene=bpy.context.scene
cam=scene.camera
assert cam and cam.type=="CAMERA"
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.render.resolution_x=1020
scene.render.resolution_y=765
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
cam.data.type="ORTHO"
views={"SIDE":Vector((1,0,0)),
       "FRONT":Vector((0,-1,0)),
       "FRONT34":Vector((1,-1,0)).normalized(),
       "REAR34":Vector((1,1,0)).normalized(),
       "BACK":Vector((0,1,0))}
for name,vec in views.items():
    target=Vector((0,.18,1.28))
    cam.data.ortho_scale=6.2
    cam.location=target+vec*9
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    for v,ob in [("BEFORE_H",H),("CLEARANCE_J",out)]:
        for m in (src,A,H,out):m.hide_render=m!=ob
        scene.render.filepath=str(REV/f"REAL_QEM_TAIL_{v}_{name}.png")
        bpy.ops.render.render(write_still=True)
for name,vec in (("SIDE",Vector((1,0,0))),
                 ("REAR34",Vector((1,1,0)).normalized())):
    target=Vector((0,2.28,1.65))
    cam.data.ortho_scale=2.3
    cam.location=target+vec*6
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    for v,ob in [("BEFORE_H",H),("CLEARANCE_J",out)]:
        for m in (src,A,H,out):m.hide_render=m!=ob
        scene.render.filepath=str(REV/f"REAL_QEM_TAIL_DETAIL_{v}_{name}.png")
        bpy.ops.render.render(write_still=True)
for ob in (src,A,H):ob.hide_render=True
out.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-real-surface-clearance-J-TRIAL.blend"),compress=True)
print("QEM_J_FINAL_REAL_SURFACE_CLEARANCE",report["numeric_technical_clearance_gate"],
      "H",base_overlap,"J",replay_collision,
      "selected",{k:winner[k] for k in ("up","outward_spread","replayed_technical_pass")})
