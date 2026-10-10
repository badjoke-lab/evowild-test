"""Render 16 actual frames from 13-bone QEM and MEASURE real foot contacts.

13-bone model is source of frames. Classify observed distal foot VERTICES
into L/R fore/hind by 3D source coordinates, track per-foot vertical and
horizontal drift on evaluated Armature mesh. No IK/root locomotion here.
Contact gate should NOT be conflated with collision-free 3D mesh test.
"""
from pathlib import Path
import bpy,numpy as np,hashlib,json
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010/three-segment-armature-v1"
REV=BASE/"contact-motion-review"
REV.mkdir(parents=True,exist_ok=True)
qa=json.loads((BASE/"13_BONE_REAL_ARMATURE_QA.json").read_text())
assert qa["armature_bone_count"]==13 and qa["rig_gate"]=="PASS_LIMITED_MULTI_JOINT_SKINNING"
src=bpy.data.objects["QEM_PRESERVED_ORIGINAL"]
dst=bpy.data.objects["QEM_REAL_13BONE_WEIGHTED_TEST"]
arm=bpy.data.objects["S_QEM_JOINT_CHAIN_ARMATURE"]
assert len(arm.data.bones)==13
assert len(src.data.vertices)==len(dst.data.vertices)==29948
source=np.asarray([src.matrix_world@v.co for v in src.data.vertices],dtype=np.float64)
signature=hashlib.sha256(source.tobytes()).hexdigest()
scene=bpy.context.scene
def evaluated():
    bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get()
    ob=dst.evaluated_get(dg)
    mesh=ob.to_mesh()
    try:return np.asarray([ob.matrix_world@v.co for v in mesh.vertices],dtype=np.float64)
    finally:ob.to_mesh_clear()
def footmask(side,lower_y,upper_y):
    sel=(side*source[:,0]>.155)&(source[:,1]>=lower_y)&(source[:,1]<=upper_y)&(source[:,2]<.285)
    out=np.flatnonzero(sel)
    if len(out)<50:raise RuntimeError(f"Not enough actual foot mesh vertices: {side} {lower_y} {len(out)}")
    return out
feet={
 "FORE_L":footmask(-1,-1.75,-.65),
 "FORE_R":footmask(+1,-1.4,-.44),
 "HIND_L":footmask(-1,1.62,2.30),
 "HIND_R":footmask(+1,1.62,2.30)
}
baseline={}
for name,idx in feet.items():
    a=source[idx]
    lowest=np.quantile(a[:,2],.08)
    close=a[a[:,2]<=lowest+.025]
    baseline[name]={"selected_vertices":int(len(idx)),
        "lowest_z":float(a[:,2].min()),
        "contact_patch_baseline_xy":close[:,:2].mean(axis=0).tolist(),
        "contact_patch_vertices":int(len(close))}
camera=scene.camera
assert camera and camera.data.type=="ORTHO"
camera.data.ortho_scale=4.55
center=Vector((0,0,1.275))
angle=Vector((1,-1,0)).normalized()
camera.location=center+angle*9
camera.rotation_euler=((center-camera.location).to_track_quat("-Z","Y")).to_euler()
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.render.resolution_x=960;scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
src.hide_render=True;dst.hide_render=False;arm.hide_render=True
sequence={}
for f in range(1,17):
    scene.frame_set(f)
    actual=evaluated()
    t={}
    for name,idx in feet.items():
        pts=actual[idx]
        prior=baseline[name]
        # Compare same ORIGINAL contact patch vertices across frames,
        # not a newly chosen patch each frame.
        base=source[idx]
        selected=(base[:,2]<=np.quantile(base[:,2],.08)+.025)
        contact=pts[selected]
        center_xy=contact[:,:2].mean(axis=0)
        dx=float(np.linalg.norm(center_xy-np.asarray(prior["contact_patch_baseline_xy"])))
        t[name]={
          "lowest_world_z":float(pts[:,2].min()),
          "delta_lowest_z_vs_rest":float(pts[:,2].min()-prior["lowest_z"]),
          "baseline_contact_patch_horizontal_drift":dx,
          "average_contact_patch_z":float(contact[:,2].mean()),
          "contact_patch_size":int(len(contact))
        }
    sequence[str(f)]=t
    scene.render.filepath=str(REV/f"QEM_13BONE_actual_frame_{f:02d}.png")
    bpy.ops.render.render(write_still=True)
orig_again=np.asarray([src.matrix_world@v.co for v in src.data.vertices],dtype=np.float64)
assert hashlib.sha256(orig_again.tobytes()).hexdigest()==signature
max_slip={name:max(sequence[str(f)][name]["baseline_contact_patch_horizontal_drift"] for f in range(1,17)) for name in feet}
max_zdrift={name:max(abs(sequence[str(f)][name]["delta_lowest_z_vs_rest"]) for f in range(1,17)) for name in feet}
# This is not claimed as real running: static root and no floor-contact solve.
summary={
 "source_sha256":qa["input_original_GLb_sha256"],
 "source_geometry_unchanged":True,
 "armature_bone_count":13,
 "frames":list(range(1,17)),
 "original_contact_vertices_by_foot":baseline,
 "frame_by_frame_foot_tracking":sequence,
 "max_horizontal_foot_drift_per_foot":max_slip,
 "max_delta_lowest_z_per_foot":max_zdrift,
 "root_locomotion_implemented":False,
 "IK_contact_solver_implemented":False,
 "running_gait_implemented":False,
 "ground_contact_gate":"NOT_VALIDATED_NO_CONTACT_SOLVER",
 "video_preview_claim":"13-bone sample hinge animation; NOT a run",
 "production_approved":False,
}
(REV/"REAL_FOOT_CONTACT_AUDIT.json").write_text(json.dumps(summary,indent=2)+"\n")
print("QEM_13_BONE_FOOT_CONTACT_TRUTH",json.dumps({k:summary[k] for k in
 ("max_horizontal_foot_drift_per_foot","max_delta_lowest_z_per_foot","ground_contact_gate")},indent=2))
