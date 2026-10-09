"""S QEM actual Blender ARMATURE four lower limb weight/pose animation test.

Same unaltered original 29,948-vertex TRELLIS2 QEM donor. Copy mesh data for
skinning. Four editable bones + a body root, named vertex groups, 1/8/16
keyframes, original vs pose five matched views and evaluated mesh face QA.

This is FIRST armature test, not completed anatomical skeleton / gait.
"""
from pathlib import Path
import bpy,bmesh,math,json,hashlib
import numpy as np
from mathutils import Matrix,Vector

ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/"experiments"
BASE=EXP/"qem-deformation-gate-20261010"
OUT=BASE/"armature-test-v1"
REV=OUT/"review"
REV.mkdir(parents=True,exist_ok=True)
GLB=EXP/"trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
sha=hashlib.sha256(GLB.read_bytes()).hexdigest()
assert sha=="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
previous=json.loads((BASE/"bend-probe-v2/BEND_PROBE_QA.json").read_text())
assert previous["mechanical_probe_gate"]=="PASS_NO_FLIPS_OR_2X_AREA_DISTORTION"
pivots=previous["candidate_pivots"]
angles=previous["effective_joint_angles_approx_degrees"]

scene=bpy.context.scene
originals=[o for o in scene.objects if o.type=="MESH"]
assert len(originals)==1
src=originals[0]
src.name="QEM_SOURCE_IMMUTABLE_29948_VERTICES"
source_world=np.asarray([src.matrix_world@v.co for v in src.data.vertices],dtype=np.float64)
assert source_world.shape==(29948,3)
source_sig=hashlib.sha256(source_world.tobytes()).hexdigest()
faces=np.asarray([tuple(p.vertices) for p in src.data.polygons],dtype=np.int32)
assert faces.shape==(59932,3)

skinned=src.copy()
skinned.data=src.data.copy()
skinned.name="QEM_EXACT_SURFACE_ARMATURE_SKIN_TEST"
scene.collection.objects.link(skinned)
skinned.matrix_world=src.matrix_world.copy()
# Apply world normalization to the DUPLICATE only. Armature bones live in
# the same normalized world coordinate frame as geometry and pivot survey.
bpy.ops.object.select_all(action="DESELECT")
skinned.select_set(True)
bpy.context.view_layer.objects.active=skinned
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.context.view_layer.update()
test_world=np.asarray([skinned.matrix_world@v.co for v in skinned.data.vertices],dtype=np.float64)
if np.max(np.abs(test_world-source_world))>2e-5:
    raise RuntimeError("Original vs mesh rig duplicate changed at rest")

# Create real armature and editable pose bones (not a procedural vertex tweak).
arm_data=bpy.data.armatures.new("S_QEM_ARMATURE_DEFORMATION_PROOF")
arm=bpy.data.objects.new("S_QEM_ARMATURE_DEFORMATION_PROOF",arm_data)
scene.collection.objects.link(arm)
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.object.mode_set(mode="EDIT")
root=arm_data.edit_bones.new("ROOT_TORSO")
root.head=(0.,0.,1.08);root.tail=(0.,0.,1.90)
for key in ("FORE_L","FORE_R","HIND_L","HIND_R"):
    p=pivots[key]["xyz"]
    bone=arm_data.edit_bones.new(key+"_LOWER_LIMB")
    bone.head=tuple(p)
    bone.tail=(p[0],p[1],p[2]-.45)
    bone.parent=root
    bone.use_connect=False
bpy.ops.object.mode_set(mode="OBJECT")

regions={
 "FORE_L":(-1,-1.83,-.34),
 "FORE_R":(+1,-1.83,-.34),
 "HIND_L":(-1,1.03,2.31),
 "HIND_R":(+1,1.03,2.31)
}
def sm(x):
    t=max(0.,min(1.,float(x)))
    return t*t*(3.-2.*t)
groups={}
for key in regions:
    groups[key]=skinned.vertex_groups.new(name=key+"_LOWER_LIMB")
root_group=skinned.vertex_groups.new(name="ROOT_TORSO")
counts={key:0 for key in regions}
weight_max={key:0. for key in regions}
for i,p in enumerate(source_world):
    total=0.
    for key,(side,y0,y1) in regions.items():
        if side*p[0]<=.025:continue
        weight=sm((.98-p[2])/.66)*sm((side*p[0]-.025)/.15)*sm((p[1]-y0)/.22)*sm((y1-p[1])/.22)
        if weight<=1e-5:continue
        groups[key].add([int(i)],float(weight),"REPLACE")
        total+=weight
        counts[key]+=1
        weight_max[key]=max(weight_max[key],weight)
    if total>1.00001:
        raise RuntimeError(f"Vertex weights exceed one: {i} {total}")
    root_weight=max(1.e-6,1.-total)
    root_group.add([int(i)],float(root_weight),"REPLACE")
if min(counts.values())<100 or min(weight_max.values())<.35:
    raise RuntimeError(f"Armature influences do not reach real QEM limbs: {counts} {weight_max}")
modifier=skinned.modifiers.new(name="ACTUAL_QEM_ARMATURE_LINEAR_SKIN",type="ARMATURE")
modifier.object=arm
modifier.use_vertex_groups=True
# No mesh substitution or retopology.

for key,deg in angles.items():
    pb=arm.pose.bones[key+"_LOWER_LIMB"]
    pb.rotation_mode="XYZ"
    pb.rotation_euler=(0,0,0)
    pb.keyframe_insert(data_path="rotation_euler",frame=1)
    pb.rotation_euler.x=math.radians(deg)
    pb.keyframe_insert(data_path="rotation_euler",frame=8)
    pb.rotation_euler=(0,0,0)
    pb.keyframe_insert(data_path="rotation_euler",frame=16)
scene.frame_start=1;scene.frame_end=16
scene.render.fps=24

def evaluated_world(frame):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get()
    evaluated=skinned.evaluated_get(dg)
    evaluated_mesh=evaluated.to_mesh()
    try:
        points=np.asarray([evaluated.matrix_world@v.co for v in evaluated_mesh.vertices],dtype=np.float64)
    finally:
        evaluated.to_mesh_clear()
    return points

rest=evaluated_world(1)
rest_delta=float(np.max(np.abs(rest-source_world)))
if rest_delta>1e-4:
    raise RuntimeError(f"Real armature deformed source at rest {rest_delta}")
mid=evaluated_world(8)
pose_delta=np.linalg.norm(mid-source_world,axis=1)
changed=int(np.count_nonzero(pose_delta>1e-5))
max_move=float(pose_delta.max())
if not (250<changed<11000 and .008<max_move<.38):
    raise RuntimeError(f"Armature did not move expected QEM leg region: {changed}/{max_move}")
b0=source_world[faces];b1=mid[faces]
n0=np.cross(b0[:,1]-b0[:,0],b0[:,2]-b0[:,0])
n1=np.cross(b1[:,1]-b1[:,0],b1[:,2]-b1[:,0])
size0=np.linalg.norm(n0,axis=1);size1=np.linalg.norm(n1,axis=1)
valid=size0>1e-10
ratio=np.divide(size1,size0,out=np.ones_like(size1),where=valid)
dot=np.sum(n0*n1,axis=1)
flips=int(np.count_nonzero((dot<0)&valid))
collapse=int(np.count_nonzero((size1<1e-10)&valid))
under=int(np.count_nonzero((ratio<.50)&valid))
over=int(np.count_nonzero((ratio>2.0)&valid))
hard_pass=flips==0 and collapse==0 and under==0 and over==0
# Geometry snapshot at pose is evaluated with the modifier; the original
# QEM mesh and vertex order are preserved even if some faces deform poorly.
if len(skinned.data.vertices)!=29948 or len(skinned.data.polygons)!=59932:
    raise RuntimeError("Unexpected topology changes with armature")
src_again=np.asarray([src.matrix_world@v.co for v in src.data.vertices],dtype=np.float64)
if hashlib.sha256(src_again.tobytes()).hexdigest()!=source_sig:
    raise RuntimeError("Original source figure moved or was edited")

camera=scene.camera
if not camera or camera.type!="CAMERA":raise RuntimeError("Camera missing")
directions={
    "side":Vector((1,0,0)),"front":Vector((0,-1,0)),
    "front34":Vector((1,-1,0)).normalized(),
    "rear34":Vector((1,1,0)).normalized(),
    "back":Vector((0,1,0))}
center=Vector((0,0,1.275))
camera.data.type="ORTHO";camera.data.ortho_scale=5.4
for view,d in directions.items():
    camera.location=center+d*9
    camera.rotation_euler=((center-camera.location).to_track_quat("-Z","Y")).to_euler()
    scene.frame_set(1)
    skinned.hide_render=True;src.hide_render=False;arm.hide_render=True
    scene.render.filepath=str(REV/f"QEM_ARMATURE_source_{view}.png")
    bpy.ops.render.render(write_still=True)
    skinned.hide_render=False;src.hide_render=True;arm.hide_render=True
    scene.frame_set(8)
    scene.render.filepath=str(REV/f"QEM_ARMATURE_pose8_{view}.png")
    bpy.ops.render.render(write_still=True)
# Three frames of visible armature pose from one camera, not an invented GIF.
camera.location=center+directions["front34"]*9
camera.rotation_euler=((center-camera.location).to_track_quat("-Z","Y")).to_euler()
for frame in (1,5,8,12,16):
    scene.frame_set(frame)
    skinned.hide_render=False;src.hide_render=True
    scene.render.filepath=str(REV/f"QEM_ARMATURE_animated_frame_{frame:02d}.png")
    bpy.ops.render.render(write_still=True)

scene.frame_set(8)
src.hide_render=True
skinned.hide_render=False
arm.hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-armature-weighted-16-frame-test.blend"),compress=True)
result={
 "source_sha256":sha,
 "source_GLb_unchanged":True,
 "source_vertices":29948,
 "rigged_mesh_vertices":len(skinned.data.vertices),
 "rigged_mesh_faces":len(skinned.data.polygons),
 "armature_bones":1+len(regions),
 "real_armature_modifier":True,
 "skin_weight_groups":["ROOT_TORSO"]+[key+"_LOWER_LIMB" for key in regions],
 "bone_regions_weighted_vertex_count":counts,
 "max_skin_weights":weight_max,
 "candidate_pivots_from_real_QEM":pivots,
 "pose8_degrees_requested":angles,
 "animation_keyframes":[1,8,16],
 "fps":24,
 "original_rest_max_coordinate_error":rest_delta,
 "evaluated_moved_vertices_at_frame8":changed,
 "max_evaluated_vertex_displacement":max_move,
 "triangles_flipped":flips,
 "triangles_near_collapse":collapse,
 "area_less_than_half":under,
 "area_more_than_double":over,
 "area_quantiles_p5_p95":[float(np.quantile(ratio[valid],.05)),float(np.quantile(ratio[valid],.95))],
 "gate":"PASS_LIMITED_ARMATURE_SKINNING" if hard_pass else "FAIL_ARMATURE_SKINNING_DISTORTION",
 "joint_landmarks_anatomically_approved":False,
 "full_limbs_rigged":False,
 "race_run_cycle_validated":False,
 "game_asset_approved":False,
 "review_requires_actual_5view":True,
 "blender_file":"S-QEM-armature-weighted-16-frame-test.blend"
}
(OUT/"ARMATURE_TEST_QA.json").write_text(json.dumps(result,indent=2)+"\n")
print("QEM_ACTUAL_ARMATURE_TEST",json.dumps({
 k:result[k] for k in ("armature_bones","bone_regions_weighted_vertex_count",
 "evaluated_moved_vertices_at_frame8","max_evaluated_vertex_displacement",
 "triangles_flipped","triangles_near_collapse","area_less_than_half",
 "area_more_than_double","gate")},indent=2))
