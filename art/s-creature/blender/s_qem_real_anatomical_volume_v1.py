"""EvoWild S: real, source-QEM 3D shoulder/chest and haunch volume trial.

Read exact immutable original source GLB and sole S-type design PNG.
Preserve M donor, vertex count, indices, triangle topology and all weights.
Select among physically evaluated deformation variants by geometric strain and
collision safety. Never equate limited anatomical change to canonical visual
design acceptance. Real 5-view Blender renders are mandatory.
"""
import bpy, numpy as np, math, hashlib, json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"body-mass-shoulder-haunch-v1"
REVIEW=OUT/"review"
REVIEW.mkdir(parents=True,exist_ok=True)
R="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
G="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
ref=ROOT/"references/00_s_type_modeling_image_v1.png"
donor=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
assert hashlib.sha256(ref.read_bytes()).hexdigest()==R
assert hashlib.sha256(donor.read_bytes()).hexdigest()==G
orig=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
a=bpy.data.objects["S_QEM_TAIL_MORPH_TEST_A_NOT_APPROVED"]
m=bpy.data.objects["S_REAL_QEM_UNIFORM_ANGULAR_TAIL_M_NOT_APPROVED"]
assert (len(orig.data.vertices),len(orig.data.polygons))==(29948,59932)
assert (len(m.data.vertices),len(m.data.polygons))==(31948,63932)
bpy.context.scene.frame_set(1)
def getworld(ob):
    bpy.context.view_layer.update()
    eo=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=eo.to_mesh()
    try:return np.array([eo.matrix_world@v.co for v in me.vertices],dtype=np.float64)
    finally:eo.to_mesh_clear()
base=getworld(m)
source_sig=hashlib.sha256(getworld(orig).tobytes()).hexdigest()
m_sig=hashlib.sha256(base.tobytes()).hexdigest()
tri=np.array([list(f.vertices) for f in m.data.polygons],dtype=np.int32)
assert tri.shape==(63932,3)
base_tri=base[tri]
base_normals=np.cross(base_tri[:,1]-base_tri[:,0],base_tri[:,2]-base_tri[:,0])
base_areas=np.linalg.norm(base_normals,axis=1)
assert (base_areas>1e-10).all()
base_cent=base_tri.mean(axis=1)

candidate=m.copy()
candidate.data=m.data.copy()
candidate.name="S_QEM_ACTUAL_BODY_SHOULDER_HAUNCH_VOLUME_V1_NOT_APPROVED"
bpy.context.scene.collection.objects.link(candidate)
candidate.matrix_world=m.matrix_world.copy()
inv=candidate.matrix_world.inverted()

# Only the core torso, not foot, long neck, head or long tail, is deformed.
# Anatomical ROI measured by Blender survey in prior executed workflow.
cx=-.030
sx=.12
# shoulder center is y=-.70 z=1.53; hip center y=1.03 z=1.45.
y,z=base[:,1],base[:,2]
x=base[:,0]
weight_s=np.exp(-.5*((y+.73)/.37)**2)*np.exp(-.5*((z-1.49)/.34)**2)
weight_h=np.exp(-.5*((y-1.00)/.36)**2)*np.exp(-.5*((z-1.42)/.29)**2)
# Preserve all below mid-leg region and non-anatomical head/tail.
def smooth(v):
    q=np.maximum(0.,np.minimum(1.,v))
    return q*q*(3.-2.*q)
gnd=smooth((z-.83)/.29)
slimit=smooth((y+1.46)/.34)*(1.-smooth((y-.15)/.45))
hlimit=smooth((y-.22)/.32)*(1.-smooth((y-1.43)/.33))
ws=weight_s*gnd*slimit
wh=weight_h*gnd*hlimit
# Source-QEM survey shows 5,916 real vertices under shoulder falloff;
# ROI size is a measured quantity, not a small-asset constraint.
assert 250<np.count_nonzero(ws>.12)<12000,np.count_nonzero(ws>.12)
assert 250<np.count_nonzero(wh>.12)<12000,np.count_nonzero(wh>.12)
print("S_QEM_REAL_ANATOMY_ROI_VERTEX_COUNTS",int(np.count_nonzero(ws>.12)),int(np.count_nonzero(wh>.12)))
assert np.max(ws*wh)<.02
radial_x=np.tanh((x-cx)/sx)
radial_z_s=np.tanh((z-1.50)/.23)
radial_z_h=np.tanh((z-1.45)/.23)
# Positive strengths expand existing anatomical shell continuously.
# Use 2D cross section volume instead of fake detached plate proxies.
def propose(sh,hip):
    xyz=base.copy()
    xyz[:,0]+=sh*ws*radial_x + hip*wh*radial_x
    xyz[:,2]+=.74*sh*ws*radial_z_s + .80*hip*wh*radial_z_h
    # Keep world-space model axis/rig coordinates invariant.
    return xyz
def putworld(xyz):
    for i,co in enumerate(xyz):
        candidate.data.vertices[i].co=inv@Vector(co)
    candidate.data.update()
def facemetrics(world):
    t=world[tri]
    n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
    leng=np.linalg.norm(n,axis=1)
    ratio=leng/base_areas
    return {
      "flipped_face_normal":int(np.count_nonzero((n*base_normals).sum(axis=1)<0)),
      "degenerate_face":int(np.count_nonzero(leng<1e-10)),
      "face_area_under_0p5":int(np.count_nonzero(ratio<.5)),
      "face_area_above_2":int(np.count_nonzero(ratio>2.)),
      "min_ratio":float(np.min(ratio)),
      "max_ratio":float(np.max(ratio))
    }

# Compare torso-only BVH overlap to unmodified M; accept only no worse.
body_indices=np.flatnonzero((base_cent[:,1]>-1.25)&
    (base_cent[:,1]<1.35)&(base_cent[:,2]>.99)&(base_cent[:,2]<2.27))
bodyfaces=[tuple(map(int,tri[i])) for i in body_indices]
def overlaps(world):
    tree=BVHTree.FromPolygons([Vector(v) for v in world],bodyfaces,
        all_triangles=True,epsilon=1e-7)
    hit=set()
    for a,b in tree.overlap(tree):
        if a>=b:continue
        if set(bodyfaces[a])&set(bodyfaces[b]):continue
        hit.add((int(body_indices[a]),int(body_indices[b])))
    return sorted(hit)
baseline_pairs=overlaps(base)
# Cross-section physical volume metrics in fixed world slabs.
def region_stats(world):
    result={}
    for name,lo,hi,zlo,zhi in [
      ("SHOULDER",-1.10,-.40,1.09,1.95),
      ("HIP",.65,1.30,1.07,1.90),
      ("WAIST",-.05,.55,1.07,1.95)]:
        a=world[(world[:,1]>lo)&(world[:,1]<hi)&(world[:,2]>zlo)&(world[:,2]<zhi)]
        assert len(a)>150
        result[name]={"count":len(a),
          "x_5_to_95_spread":float(np.percentile(a[:,0],95)-np.percentile(a[:,0],5)),
          "z_5_to_95_spread":float(np.percentile(a[:,2],95)-np.percentile(a[:,2],5))}
    return result
baseline_region=region_stats(base)
candidates=[]
winner=None;win_world=None
strengths=[(.04,.04),(.06,.055),(.08,.07),(.10,.085),(.12,.10),
           (.14,.11),(.16,.12),(.18,.13)]
for sh,hip in strengths:
    putworld(propose(sh,hip))
    world=getworld(candidate)
    face=facemetrics(world)
    pairs=overlaps(world)
    roi=region_stats(world)
    num_moved=int(np.count_nonzero(np.linalg.norm(world-base,axis=1)>.003))
    assert num_moved>400
    outside=(z<.8)|(y< -1.55)|(y>1.75)
    max_out=float(np.linalg.norm((world-base)[outside],axis=1).max())
    maxdist=float(np.linalg.norm(world-base,axis=1).max())
    no_face_change=all(face[k]==0 for k in
       ("flipped_face_normal","degenerate_face","face_area_under_0p5","face_area_above_2"))
    no_new_collision=(len(pairs)<=len(baseline_pairs))
    # Preserve feet and head geometry: tiny tails of Gaussian are documented.
    outside_ok=max_out<.001
    pass_gate=no_face_change and no_new_collision and outside_ok
    delta_sh=roi["SHOULDER"]["x_5_to_95_spread"]-baseline_region["SHOULDER"]["x_5_to_95_spread"]
    delta_hip=roi["HIP"]["x_5_to_95_spread"]-baseline_region["HIP"]["x_5_to_95_spread"]
    row={"shoulder_strength":sh,"hip_strength":hip,
        "body_face_quality":face,"M_torso_BVH_pairs":len(baseline_pairs),
        "candidate_torso_BVH_pairs":len(pairs),
        "new_body_intersecting_pair_count":len(set(pairs)-set(baseline_pairs)),
        "max_evaluated_vertex_shift":maxdist,
        "changed_vertex_count_at_0p003":num_moved,
        "max_head_foot_tail_protected_region_displacement":max_out,
        "shoulder_x_width_increment":delta_sh,
        "hip_x_width_increment":delta_hip,
        "world_region_metrics":roi,"numerical_candidate_PASS":pass_gate}
    candidates.append(row)
    print("S_QEM_ACTUAL_BODY_MASS",sh,hip,"PASS",pass_gate,
       "BODY_BVH",len(pairs),"/",len(baseline_pairs),
       "DEGEN",face["degenerate_face"],
       "FLIP",face["flipped_face_normal"],"WIDTH",delta_sh,delta_hip,
       "Protected",max_out)
    # Bigger allowable controlled change prioritized, not auto visually accepted.
    if pass_gate and (winner is None or (delta_sh+delta_hip)>(winner["shoulder_x_width_increment"]+winner["hip_x_width_increment"])):
        winner=row;win_world=world.copy()
# On QA failure, still save the least-damaging real mesh as rejected evidence.
if winner is None:
    winner=min(candidates,key=lambda d:(
       d["body_face_quality"]["flipped_face_normal"]+
       d["body_face_quality"]["degenerate_face"]+
       d["body_face_quality"]["face_area_under_0p5"]+
       d["body_face_quality"]["face_area_above_2"],
       d["candidate_torso_BVH_pairs"],
       d["max_head_foot_tail_protected_region_displacement"]))
    win_world=propose(winner["shoulder_strength"],winner["hip_strength"])
putworld(win_world)
replay=getworld(candidate)
replay_face=facemetrics(replay)
replay_pairs=overlaps(replay)
replay_ok=(replay_face==winner["body_face_quality"] and
           len(replay_pairs)==winner["candidate_torso_BVH_pairs"])
assert replay_ok
assert hashlib.sha256(getworld(orig).tobytes()).hexdigest()==source_sig
assert hashlib.sha256(getworld(m).tobytes()).hexdigest()==m_sig
assert len(candidate.data.vertices)==31948 and len(candidate.data.polygons)==63932
result={
 "canonical_S_design_sha256":R,"original_QEM_GLb_sha256":G,
 "source_QEM_unchanged":True,"M_source_unchanged":True,
 "mesh_topology_exactly_preserved":True,
 "body_shape_change_is_real_QEM_vertex_edit":True,
 "original_vertices":29948,"original_triangles":59932,
 "M_and_candidate_vertices":31948,"M_and_candidate_triangles":63932,
 "shoulder_hip_real_QEM_ROI_center_yz":[[-.73,1.49],[1.00,1.42]],
 "candidate_count":len(candidates),"all_candidates":candidates,
 "selected":winner,"replay_face_quality":replay_face,
 "replay_BVH_body_intersections":len(replay_pairs),
 "replay_integrity":replay_ok,
 "original_M_body_BVH_intersections":len(baseline_pairs),
 "original_M_body_dims":baseline_region,
 "limited_3D_geometry_gate":"PASS" if winner["numerical_candidate_PASS"] else "FAIL",
 "canonical_S_silhouette_gate":"REVIEW_PENDING_NOT_APPROVED",
 "canonical_S_head_crest_armor_feathers_complete":False,
 "new_blender_rig_validated":False,
 "gait_real_running_passed":False,
 "production_S_approved":False}
(OUT/"REAL_QEM_SHOULDER_HIP_MASS_QA.json").write_text(json.dumps(result,indent=2)+"\n")

scene=bpy.context.scene
cam=scene.camera;assert cam and cam.type=="CAMERA"
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.render.resolution_x=1120;scene.render.resolution_y=840
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
cam.data.type="ORTHO"
views={
"SIDE":Vector((1,0,0)),
"FRONT":Vector((0,-1,0)),
"FRONT34":Vector((1,-1,0)).normalized(),
"REAR34":Vector((1,1,0)).normalized(),
"BACK":Vector((0,1,0))}
for name,direction in views.items():
    focus=Vector((0,.15,1.30))
    cam.data.ortho_scale=6.5
    cam.location=focus+direction*9
    cam.rotation_euler=(focus-cam.location).to_track_quat("-Z","Y").to_euler()
    for tag,obj in (("SOURCE_M",m),("VOLUME_A",candidate)):
        for item in (orig,a,m,candidate):item.hide_render=(item!=obj)
        scene.render.filepath=str(REVIEW/f"ACTUAL_QEM_{tag}_{name}.png")
        bpy.ops.render.render(write_still=True)
for name,direction in (("SIDE",Vector((1,0,0))),
                        ("FRONT34",Vector((1,-1,0)).normalized()),
                        ("REAR34",Vector((1,1,0)).normalized())):
    focus=Vector((0,.05,1.58))
    cam.data.ortho_scale=3.55
    cam.location=focus+direction*7
    cam.rotation_euler=(focus-cam.location).to_track_quat("-Z","Y").to_euler()
    for tag,obj in (("SOURCE_M",m),("VOLUME_A",candidate)):
        for item in (orig,a,m,candidate):item.hide_render=(item!=obj)
        scene.render.filepath=str(REVIEW/f"ACTUAL_QEM_BODY_CLOSE_{tag}_{name}.png")
        bpy.ops.render.render(write_still=True)
for ob in (orig,a,m):ob.hide_render=True
candidate.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-genuine-body-anatomical-mass-v1-REVIEW.blend"),compress=True)
print("S_QEM_TRUE_BODY_MASS_FINAL",result["limited_3D_geometry_gate"],
      "strength",winner["shoulder_strength"],winner["hip_strength"],
      "body_delta",winner["shoulder_x_width_increment"],winner["hip_x_width_increment"],
      "BVH",len(replay_pairs))
