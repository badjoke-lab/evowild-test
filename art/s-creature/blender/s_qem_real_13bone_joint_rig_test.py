"""EvoWild S: QEM actual THREE SEGMENT limb ARMATURE experiment.

13 editable Blender bones: root plus 4 x shoulder/elbow/wrist OR
hip/stifle/hock chains. Twelve surface-located candidate joints are derived
from a source-locked joint survey. Uses real Armature modifier and overlapping
smooth skin weights, conservative pose safety line-search, 5 fixed cameras.

NO generated low-poly substitute; no retopology; no claim of complete race rig.
"""
from pathlib import Path
import bpy,math,json,hashlib
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"three-segment-armature-v1"
REV=OUT/"review"
REV.mkdir(parents=True,exist_ok=True)
DONOR=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
assert hashlib.sha256(DONOR.read_bytes()).hexdigest()=="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
survey=json.loads((BASE/"joint-anatomy-survey-v2/JOINT_CANDIDATE_SURVEY.json").read_text())
assert survey["marker_count"]==12 and survey["original_mesh_untouched"]
J=survey["joint_candidates"]
scene=bpy.context.scene
source=[o for o in scene.objects if o.type=="MESH"]
assert len(source)==1,[(o.name,o.type) for o in source]
src=source[0]
src.name="QEM_PRESERVED_ORIGINAL"
assert len(src.data.vertices)==29948 and len(src.data.polygons)==59932
orig=np.asarray([src.matrix_world@v.co for v in src.data.vertices],dtype=np.float64)
faces=np.asarray([tuple(f.vertices) for f in src.data.polygons],dtype=np.int32)
assert faces.shape==(59932,3)
signature=hashlib.sha256(orig.tobytes()).hexdigest()
dst=src.copy();dst.data=src.data.copy()
dst.name="QEM_REAL_13BONE_WEIGHTED_TEST"
scene.collection.objects.link(dst)
dst.matrix_world=src.matrix_world.copy()
bpy.ops.object.select_all(action="DESELECT");dst.select_set(True)
bpy.context.view_layer.objects.active=dst
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.context.view_layer.update()
q=np.asarray([dst.matrix_world@v.co for v in dst.data.vertices],dtype=np.float64)
assert np.max(np.abs(q-orig))<2e-5

# A true editable THREE-LINK armature per limb, with parented transforms.
armd=bpy.data.armatures.new("S_QEM_JOINT_CHAIN_ARMATURE")
arm=bpy.data.objects.new("S_QEM_JOINT_CHAIN_ARMATURE",armd)
scene.collection.objects.link(arm)
bpy.ops.object.select_all(action="DESELECT");arm.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.object.mode_set(mode="EDIT")
root=armd.edit_bones.new("BODY_ROOT")
root.head=(0,0,1.05);root.tail=(0,0,1.89)
NAMES=("FORE_L","FORE_R","HIND_L","HIND_R")
points={}
for name in NAMES:
    side="L" if name.endswith("L") else "R"
    is_fore=name.startswith("FORE")
    labels=("FORE_SHOULDER","FORE_ELBOW","FORE_WRIST") if is_fore else ("HIND_HIP","HIND_STIFLE","HIND_HOCK")
    ids=[side+"_"+tag for tag in labels]
    heads=[Vector(J[s]["xyz"]) for s in ids]
    if not all(J[s]["source_region_vertex_count"]>=50 for s in ids):
        raise RuntimeError(f"underconstrained limb landmark for {name}")
    foot=Vector((heads[2].x,heads[2].y+(-.23 if is_fore else .16),.045))
    # Verify descending topological candidate joint vertical coordinate.
    if not (heads[0].z>heads[1].z+.12 and heads[1].z>heads[2].z+.12 and heads[2].z>.15):
        raise RuntimeError(f"bad limb structure {name}: {heads}")
    chain=(heads[0],heads[1],heads[2],foot)
    points[name]=[list(v) for v in chain]
    parent=root
    for i,segment in enumerate(("UPPER","MIDDLE","LOWER")):
        bone=armd.edit_bones.new(name+"_"+segment)
        bone.head=chain[i]
        bone.tail=chain[i+1]
        bone.parent=parent
        bone.use_connect=False
        parent=bone
bpy.ops.object.mode_set(mode="OBJECT")
assert len(arm.data.bones)==13

# Normalized weight sharing uses original source vertices only, with
# Y-axis region discrimination and gradually decaying weights at torso.
def sm(t):
    p=max(0.,min(1.,float(t)));return p*p*(3-2*p)
GR={}
for name in NAMES:
    GR[name]={seg:dst.vertex_groups.new(name=name+"_"+seg) for seg in ("UPPER","MIDDLE","LOWER")}
rootgroup=dst.vertex_groups.new(name="BODY_ROOT")
counts={name:{"UPPER":0,"MIDDLE":0,"LOWER":0} for name in NAMES}
maxweights={name:0. for name in NAMES}
for idx,p in enumerate(orig):
    contributions=[]
    for name in NAMES:
        side=-1 if name.endswith("L") else 1
        fore=name.startswith("FORE")
        ylo,yhi=(-1.77,-.12) if fore else (.66,2.33)
        ceiling=1.58 if fore else 1.84
        # Require positive 3D evidence of the corresponding limb region.
        w_side=sm((side*p[0]-.05)/.16)
        w_y=sm((p[1]-ylo)/.22)*sm((yhi-p[1])/.22)
        w_z=sm((ceiling-p[2])/.48)
        strength=w_side*w_y*w_z
        if strength<1.e-5:continue
        neck=points[name]
        # Fractional segmentation centered on the actual ELBOW / STIFLE
        # and WRIST / HOCK landmark heights, not a generic body midpoint.
        zu=neck[1][2];zl=neck[2][2]
        upper=sm((p[2]-(zu-.075))/.23)
        middle=(1-upper)*sm((p[2]-(zl-.075))/.24)
        lower=max(0.,1-upper-middle)
        proportions={"UPPER":upper,"MIDDLE":middle,"LOWER":lower}
        for seg,prop in proportions.items():
            weight=strength*prop
            if weight>1.e-5:
                contributions.append((name,seg,weight))
    total=sum(w for _,_,w in contributions)
    if total>1.0001:
        # Rare surface overlap of left/right or front/hind: normalize,
        # never create >100% total skinning influence.
        contributions=[(n,s,w/total) for n,s,w in contributions]
        total=1.0
    root_w=max(.000001,1.-total)
    rootgroup.add([idx],root_w,"REPLACE")
    for n,s,w in contributions:
        GR[n][s].add([idx],w,"REPLACE")
        counts[n][s]+=1
        maxweights[n]=max(maxweights[n],w)
if any(z<20 for v in counts.values() for z in v.values()):
    raise RuntimeError("A limb chain has an unweighted segment: "+repr(counts))
if min(maxweights.values())<.22:raise RuntimeError("Limb influence strength too small "+repr(maxweights))
modifier=dst.modifiers.new("ACTUAL_SQEM_ARMATURE",type="ARMATURE")
modifier.object=arm
modifier.use_vertex_groups=True
modifier.use_deform_preserve_volume=True

# Keyframe amplitude search: do not claim large-angle success if flips occur.
requested={
 "FORE_L":(10.0,-17.0,11.0),
 "FORE_R":(-10.0,17.0,-11.0),
 "HIND_L":(-8.0,15.0,-11.0),
 "HIND_R":(8.0,-15.0,11.0)
}
# Bone local X is used for sagittal flexion test, not anatomically verified IK.
for n in NAMES:
    for seg in ("UPPER","MIDDLE","LOWER"):
        pb=arm.pose.bones[n+"_"+seg]
        pb.rotation_mode="XYZ"
def pose(alpha):
    scene.frame_set(8)
    for n in NAMES:
        for i,seg in enumerate(("UPPER","MIDDLE","LOWER")):
            pb=arm.pose.bones[n+"_"+seg]
            pb.rotation_euler=(math.radians(requested[n][i]*alpha),0.,0.)
    bpy.context.view_layer.update()
def evaluated_world():
    dg=bpy.context.evaluated_depsgraph_get()
    ob=dst.evaluated_get(dg)
    m=ob.to_mesh()
    try:
        return np.asarray([ob.matrix_world@v.co for v in m.vertices],dtype=np.float64)
    finally:ob.to_mesh_clear()

P=orig[faces]
normal0=np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0])
norm0=np.linalg.norm(normal0,axis=1)
leg_samples=[];choice=None
for alpha in (1.,.85,.70,.55,.42,.32,.24,.17,.11):
    pose(alpha)
    actual=evaluated_world()
    tri=actual[faces]
    norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    leng=np.linalg.norm(norm,axis=1)
    valid=norm0>1e-10
    ratio=np.divide(leng,norm0,out=np.ones_like(leng),where=valid)
    flipped=int(np.count_nonzero((np.sum(normal0*norm,axis=1)<0)&valid))
    collapsed=int(np.count_nonzero((leng<1e-10)&valid))
    shrink=int(np.count_nonzero((ratio<.5)&valid))
    expand=int(np.count_nonzero((ratio>2)&valid))
    displacement=np.linalg.norm(actual-orig,axis=1)
    moved=int(np.count_nonzero(displacement>1.e-5))
    row={"strength":alpha,"flipped_faces":flipped,"collapsed_faces":collapsed,
         "area_below_half":shrink,"area_above_double":expand,"moved_vertices":moved,
         "max_move":float(displacement.max()),
         "ratio_p5":float(np.quantile(ratio[valid],.05)),"ratio_p95":float(np.quantile(ratio[valid],.95))}
    leg_samples.append(row)
    if not flipped and not collapsed and not shrink and not expand and moved>350:
        choice=row
        break
if choice is None:
    choice=leg_samples[-1]
passing=(choice["flipped_faces"]==0 and choice["collapsed_faces"]==0
  and choice["area_below_half"]==0 and choice["area_above_double"]==0)
selected=choice["strength"]
# Blender keyframed action: rest->swing->rest, 16 frames.
for n in NAMES:
    for i,seg in enumerate(("UPPER","MIDDLE","LOWER")):
        pb=arm.pose.bones[n+"_"+seg]
        for frame,angle in ((1,0),(8,math.radians(requested[n][i]*selected)),(16,0)):
            scene.frame_set(frame)
            pb.rotation_euler=(angle,0.,0.)
            pb.keyframe_insert(data_path="rotation_euler",frame=frame)
scene.frame_start=1;scene.frame_end=16
scene.render.fps=24
scene.frame_set(1)
rest=evaluated_world()
rest_max=float(np.abs(rest-orig).max())
if rest_max>1e-4:raise RuntimeError(f"Rest geometry already damaged {rest_max}")
saved=np.asarray([src.matrix_world@v.co for v in src.data.vertices],dtype=np.float64)
if hashlib.sha256(saved.tobytes()).hexdigest()!=signature:raise RuntimeError("Original QEM modified")

cam=scene.camera
assert cam and cam.type=="CAMERA"
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.render.resolution_x=1024
scene.render.resolution_y=768
scene.render.resolution_percentage=100
cam.data.type="ORTHO";cam.data.ortho_scale=5.4
center=Vector((0,0,1.275))
dirs={
 "side":Vector((1,0,0)),"front":Vector((0,-1,0)),
 "front34":Vector((1,-1,0)).normalized(),
 "rear34":Vector((1,1,0)).normalized(),
 "back":Vector((0,1,0))}
arm.hide_render=True
for v,d in dirs.items():
    cam.location=center+d*9
    cam.rotation_euler=((center-cam.location).to_track_quat("-Z","Y")).to_euler()
    src.hide_render=False;dst.hide_render=True;scene.frame_set(1)
    scene.render.filepath=str(REV/f"QEM_13bone_SOURCE_{v}.png")
    bpy.ops.render.render(write_still=True)
    src.hide_render=True;dst.hide_render=False;scene.frame_set(8)
    scene.render.filepath=str(REV/f"QEM_13bone_POSE8_{v}.png")
    bpy.ops.render.render(write_still=True)
# Sample of real evaluated time-series from fixed front quarter camera.
cam.location=center+dirs["front34"]*9
cam.rotation_euler=((center-cam.location).to_track_quat("-Z","Y")).to_euler()
for frame in (1,5,8,12,16):
    src.hide_render=True;dst.hide_render=False
    scene.frame_set(frame)
    scene.render.filepath=str(REV/f"QEM_13bone_FRAME_{frame:02d}.png")
    bpy.ops.render.render(write_still=True)
scene.frame_set(8)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-real-13-bone-joint-chain-test.blend"),compress=True)
qa={
 "input_original_GLb_sha256":"e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f",
 "source_preserved_unchanged":True,"source_vertices":29948,"source_faces":59932,
 "deformed_vertices":len(dst.data.vertices),"deformed_faces":len(dst.data.polygons),
 "armature_bone_count":13,"real_skinning_modifier":True,
 "joint_candidate_survey":"joint-anatomy-survey-v2/JOINT_CANDIDATE_SURVEY.json",
 "joint_candidate_positions":points,
 "weight_counts_per_bone":counts,
 "max_limb_weights":maxweights,
 "attempted_local_bone_angles_deg":requested,
 "actual_local_bone_angles_deg":{k:[round(v*selected,3) for v in values] for k,values in requested.items()},
 "strength_candidates":leg_samples,"selected_strength":selected,
 "frame8_metrics":choice,
 "rest_pose_max_coordinate_error":rest_max,
 "frames_keyed":[1,8,16],
 "rendered_sample_frames":[1,5,8,12,16],
 "rig_gate":"PASS_LIMITED_MULTI_JOINT_SKINNING" if passing else "FAIL_MULTI_JOINT_SKINNING",
 "anatomical_joints_verified":False,"ground_contacts_verified":False,
 "full_quadruped_gait_verified":False,"production_approved":False,
 "input_geometry_changed":False,
 "notes":"Actual upper/middle/lower parented bone chains and evaluated mesh; 12 surface candidates not final anatomy; no simplified replacement."
}
(OUT/"13_BONE_REAL_ARMATURE_QA.json").write_text(json.dumps(qa,indent=2)+"\n")
print("QEM_REAL_13_BONE_ARMATURE",json.dumps({
  k:qa[k] for k in ("weight_counts_per_bone","selected_strength","frame8_metrics","rig_gate")
},indent=2))
