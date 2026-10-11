"""EvoWild S QEM: surgical mid-left real first-ring intersection fix, S.

Source Q midleaf is a saved, deterministic, true mesh; exact SHA and 5 BVH
pairs verified. Non-destructive shape key edits only the NEAR-ROOT new leaf
ring vertices (NOT the original M donor surface). 30 local displacement
proposals are evaluated by actual Blender skinned mesh, BVH self-overlaps and
strict triangle condition checks. Evidence kept even on total failure.
"""
from pathlib import Path
import bpy,numpy as np,hashlib,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"midleaf-rootclearance-s-v1"
REVIEW=OUT/"review"
REVIEW.mkdir(parents=True,exist_ok=True)
ref=ROOT/"references/00_s_type_modeling_image_v1.png"
donor=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
R="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
D="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
assert hashlib.sha256(ref.read_bytes()).hexdigest()==R
assert hashlib.sha256(donor.read_bytes()).hexdigest()==D
src=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
M=bpy.data.objects["S_REAL_QEM_UNIFORM_ANGULAR_TAIL_M_NOT_APPROVED"]
q=bpy.data.objects["S_QEM_Q_SINGLE_SEWN_LEAF_MID_LEFT_NOT_APPROVED"]
assert (len(src.data.vertices),len(src.data.polygons))==(29948,59932)
assert (len(M.data.vertices),len(M.data.polygons))==(31948,63932)
assert (len(q.data.vertices),len(q.data.polygons))==(32232,64500)
bpy.context.scene.frame_set(1)

def evaluated(obj):
    bpy.context.view_layer.update()
    o=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=o.to_mesh()
    try:return np.asarray([o.matrix_world@v.co for v in mesh.vertices],dtype=np.float64)
    finally:o.to_mesh_clear()
original=evaluated(src);m=evaluated(M);before=evaluated(q)
sig=[hashlib.sha256(x.tobytes()).hexdigest() for x in (original,m,before)]
qhash=hashlib.sha256(np.round(before,6).tobytes()).hexdigest()
assert qhash=="b5e0cdc2d15a79e3f15d6dcfff686fd053651e2d5844cae2e2479aeb96055130",qhash
tri=np.asarray([tuple(f.vertices) for f in q.data.polygons],dtype=np.int32)
assert len(tri)==64500
face=before[tri]
reference_normal=np.cross(face[:,1]-face[:,0],face[:,2]-face[:,0])
ref_len=np.linalg.norm(reference_normal,axis=1)
assert (ref_len>1e-10).all()
cent=face.mean(axis=1)
ROI=np.flatnonzero((cent[:,1]>1.50)&(cent[:,2]>.94)&(np.abs(cent[:,0])<.7))
tris_in_roi=[tuple(map(int,tri[k])) for k in ROI]
assert 6500<len(ROI)<6800
def overlaps(xyz):
    # Stable ROI IDs across all small local changes, identical to Q forensic.
    tree=BVHTree.FromPolygons([Vector(p) for p in xyz],tris_in_roi,
                              all_triangles=True,epsilon=1.e-7)
    hits=[]
    for i,j in tree.overlap(tree):
        if i>=j:continue
        if set(tris_in_roi[i])&set(tris_in_roi[j]):continue
        hits.append((int(ROI[i]),int(ROI[j])))
    return sorted(hits)
old_pairs=overlaps(before)
assert old_pairs==[(60009,62057),(60009,64233),(62057,62069),
                  (62069,64233),(64233,64236)],old_pairs

# These vertex IDs are new rings in deterministic, exactly-digested Q
# topology: original source M old rings remain indices < 31948. Manipulate
# continuous near-root leaf first/second ring only; DO NOT move M skin verts.
vertex_ids=np.arange(len(before))
new=(vertex_ids>=31948)
relative=before-np.array([-.023,2.309,1.545])
radius_x=np.exp(-(relative[:,0]/.070)**2)
radius_y=np.exp(-(relative[:,1]/.085)**2)
radius_z=np.exp(-(relative[:,2]/.11)**2)
influence=radius_x*radius_y*radius_z*new.astype(float)
near_m=(influence>.22)
assert 3<=near_m.sum()<=120,("local support rings selection out of range",int(near_m.sum()))
assert all(influence[x]>.12 for x in (31956,31958,31959)),[(x,influence[x]) for x in (31956,31958,31959)]
print("S_MIDLEAF_ROOT_LOCAL_VERTICES",int(near_m.sum()),
      "critical3",[(int(x),float(influence[x])) for x in (31956,31958,31959)])

# Edge winding: a consistent closed triangular 2-manifold must have exactly
# two incident directed halfedges with opposite traversal (no hidden flipped
# skin even if BVH reports zero).
edge_signed={}
for a,b,c in tri:
    a,b,c=int(a),int(b),int(c)
    for i,j in ((a,b),(b,c),(c,a)):
        key=(min(i,j),max(i,j))
        edge_signed.setdefault(key,[]).append(1 if i<j else -1)
bad_edge_winding=sum(len(v)!=2 or sum(v)!=0 for v in edge_signed.values())
boundary=sum(len(v)==1 for v in edge_signed.values())
assert boundary==0,("Q baseline has boundary",boundary)

def triangle_quality(xyz):
    t=xyz[tri]
    n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
    leng=np.linalg.norm(n,axis=1)
    ratio=leng/ref_len
    return {
     "new_inverted_face_count":int(np.count_nonzero(np.sum(n*reference_normal,axis=1)<0)),
     "degenerate_face_count":int(np.count_nonzero(leng<1e-10)),
     "area_under_half_face_count":int(np.count_nonzero(ratio<.5)),
     "area_over_double_face_count":int(np.count_nonzero(ratio>2)),
     "smallest_ratio":float(ratio.min()),
     "largest_ratio":float(ratio.max())
    }

out=q.copy()
out.data=q.data.copy()
out.name="S_QEM_S_SINGLE_LEAF_LOCAL_ROOT_REPAIR_UNAPPROVED"
bpy.context.scene.collection.objects.link(out)
out.matrix_world=q.matrix_world.copy()
out.shape_key_add(name="Q_MID_LEFT_PRESERVED_REST",from_mix=False)
key=out.shape_key_add(name="S_FIRST_RING_SURGICAL_CLEARANCE",from_mix=False)
key.value=1.
matrix_inv=out.matrix_world.inverted()
def set_shape(world_positions):
    for i,p in enumerate(world_positions):
        key.data[i].co=matrix_inv@Vector(p)

candidates=[]
best=None
best_actual=None
# Local clearance directs first two new support rings outboard from the
# original left flank, with small dorsal/ventral bias alternatives.
for shift in (.006,.010,.014,.020,.028,.040,.055):
    for dz_ratio in (0.,.35,-.35,.70,-.70):
        target=before.copy()
        target[:,0]-=shift*influence
        target[:,2]+=shift*dz_ratio*influence
        set_shape(target)
        actual=evaluated(out)
        pairs=overlaps(actual)
        qa=triangle_quality(actual)
        quality=all(qa[k]==0 for k in (
            "new_inverted_face_count","degenerate_face_count",
            "area_under_half_face_count","area_over_double_face_count"))
        row={
         "outward_negative_X_shift":shift,"Z_ratio":dz_ratio,
         "real_BVH_nonshared_overlap_pairs":len(pairs),
         "remaining_overlap_face_IDs":pairs[:20],
         "face_quality":qa,"face_quality_PASS":quality,
         "collision_clear_PASS":len(pairs)==0,
         "technical_both_PASS":quality and len(pairs)==0,
         "max_real_vertex_movement":float(np.linalg.norm(actual-before,axis=1).max())
        }
        candidates.append(row)
        print("S_MIDLEAF_ROOT_FACE_QA",shift,dz_ratio,"collision",len(pairs),
              "quality",quality,qa["new_inverted_face_count"],qa["area_under_half_face_count"],
              qa["area_over_double_face_count"])
        score=(0 if quality else 1,len(pairs),qa["new_inverted_face_count"],qa["area_over_double_face_count"])
        if best is None or score<best[0]:
            best=(score,row)
            best_actual=actual.copy()
        if row["technical_both_PASS"]:break
    if best and best[1]["technical_both_PASS"]:break
assert best is not None
chosen=best[1]
set_shape(best_actual)
after=evaluated(out)
replay_pairs=overlaps(after)
replay_quality=triangle_quality(after)
replay_ok=(len(replay_pairs)==0 and all(replay_quality[k]==0 for k in (
    "new_inverted_face_count","degenerate_face_count",
    "area_under_half_face_count","area_over_double_face_count")))
chosen["replay_BVH_pairs"]=len(replay_pairs)
chosen["replay_face_quality"]=replay_quality
chosen["replay_PASS"]=replay_ok

# exact unchanged original reference donor and underlying M/base Q
for obj,s in zip((src,M,q),sig):
    assert hashlib.sha256(evaluated(obj).tobytes()).hexdigest()==s
assert (len(out.data.vertices),len(out.data.polygons))==(32232,64500)
report={
 "canonical_reference_SHA256":R,"donor_original_QEM_SHA256":D,
 "source_M_and_original_Q_preserved":True,
 "Q_mid_input_evaluated_SHA256_six_dp":qhash,
 "Q_actual_five_collision_polygon_pairs":old_pairs,
 "Q_topology":{"verts":32232,"tris":64500,"boundary_edges":boundary,
                "bad_edge_winding":bad_edge_winding},
 "local_near_first_ring_vertices_weight_gt_0_22":int(near_m.sum()),
 "critical_new_vertex_weights":{str(v):float(influence[v]) for v in (31956,31958,31959)},
 "tested_local_deformation_variants":len(candidates),
 "all_candidates":candidates,"selected":chosen,
 "final_replayed_actual_pairs":replay_pairs,
 "final_replayed_geometry_quality":replay_quality,
 "technical_pass":replay_ok and bad_edge_winding==0,
 "geometry_gate":"PASS_LOCAL_ROOT" if replay_ok and bad_edge_winding==0 else "FAIL",
 "design_S_reference_match":"UNAPPROVED_PENDING_VISUAL_REVIEW",
 "rig_new_skin_weights":"NOT_VERIFIED",
 "gait_97frames":"NOT_VERIFIED",
 "production_creature":False
}
(OUT/"REAL_QEM_MIDLEAF_ROOT_S_QA.json").write_text(json.dumps(report,indent=2)+"\n")
cam=bpy.context.scene.camera
assert cam and cam.type=="CAMERA"
bpy.context.scene.render.engine="BLENDER_WORKBENCH"
bpy.context.scene.display.shading.show_cavity=True
bpy.context.scene.render.image_settings.file_format="PNG"
bpy.context.scene.render.resolution_x=980
bpy.context.scene.render.resolution_y=735
bpy.context.scene.render.resolution_percentage=100
cam.data.type="ORTHO"
views={
 "SIDE":Vector((1,0,0)),
 "FRONT":Vector((0,-1,0)),
 "FRONT34":Vector((1,-1,0)).normalized(),
 "REAR34":Vector((1,1,0)).normalized(),
 "BACK":Vector((0,1,0))
}
for label,direction in views.items():
    center=Vector((0,.22,1.25))
    cam.data.ortho_scale=6.5
    cam.location=center+direction*8
    cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
    for title,obj in (("BASE_Q",q),("ROOT_S",out)):
        for o in (src,M,q,out):o.hide_render=o!=obj
        bpy.data.objects["S_QEM_TAIL_MORPH_TEST_A_NOT_APPROVED"].hide_render=True
        bpy.context.scene.render.filepath=str(REVIEW/f"REAL_QEM_MIDLEAF_{title}_{label}.png")
        bpy.ops.render.render(write_still=True)
for label,direction in (("SIDE",Vector((1,0,0))),
                        ("REAR34",Vector((1,1,0)).normalized())):
    center=Vector((0,2.35,1.55))
    cam.data.ortho_scale=1.65
    cam.location=center+direction*5
    cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
    for title,obj in (("BASE_Q",q),("ROOT_S",out)):
        for o in (src,M,q,out):o.hide_render=o!=obj
        bpy.context.scene.render.filepath=str(REVIEW/f"REAL_QEM_MIDLEAF_CLOSE_{title}_{label}.png")
        bpy.ops.render.render(write_still=True)
for o in (src,M,q):o.hide_render=True
out.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-MIDLEFT-first-ring-root-repair-S-TRIAL.blend"),compress=True)
print("S_FINAL_REAL_MESH_GATE",report["geometry_gate"],
      "baseline",len(old_pairs),"after",len(replay_pairs),
      "tests",len(candidates),"chosen",chosen["outward_negative_X_shift"],chosen["Z_ratio"])
