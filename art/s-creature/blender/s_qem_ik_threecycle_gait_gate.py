"""EvoWild S | actual QEM / 13-deform-bone 3-cycle IK contact experiment.

ONLY uses existing TRELLIS2 QEM weighted mesh + Blender 3-link IK in the
validated V1 .blend; no remeshing, no R1/R0 replacement, no geometry edits.
Perform three alternating-diagonal swing cycles with translating body root.
Every actual evaluated vertex is checked at integer AND half-integer frames,
with exact source-fixed contact patches and explicit cycle-seam measurements.
This tests repeated locomotion mechanics, NOT full-speed racing or final anatomy.
"""
from pathlib import Path
import bpy, numpy as np, math, json, hashlib
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"threecycle-ik-gait-v1"
REV=OUT/"review"
REV.mkdir(parents=True,exist_ok=True)
V1=json.loads((BASE/"ik-contact-v1/REAL_IK_CONTACT_QA.json").read_text())
V2=json.loads((BASE/"rootmotion-contact-v2c/ROOT_MOTION_CONTACT_QA.json").read_text())
assert V1["gate"]=="PASS_LIMITED_IK_CONTACT"
assert V2["gate"]=="PASS_LIMITED_ROOT_MOTION_IK"
assert V1["original_glb_sha256"]=="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
src=bpy.data.objects["QEM_PRESERVED_ORIGINAL"]
dst=bpy.data.objects["QEM_REAL_13BONE_WEIGHTED_TEST"]
arm=bpy.data.objects["S_QEM_JOINT_CHAIN_ARMATURE"]
assert len(src.data.vertices)==len(dst.data.vertices)==29948
assert len(src.data.polygons)==len(dst.data.polygons)==59932
assert len(arm.data.bones)==13
assert any(m.type=="ARMATURE" and m.object==arm for m in dst.modifiers)

donor=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
assert hashlib.sha256(donor.read_bytes()).hexdigest()==V1["original_glb_sha256"]
scene=bpy.context.scene
scene.frame_set(1)
NAMES=("FORE_L","FORE_R","HIND_L","HIND_R")
A=("FORE_L","HIND_R")
B=("FORE_R","HIND_L")
targets={name:bpy.data.objects["IK_FOOT_TARGET_"+name] for name in NAMES}
assert all(any(c.type=="IK" and c.chain_count==3 and c.target==targets[name]
                   for c in arm.pose.bones[name+"_LOWER"].constraints)
           for name in NAMES)
source=np.asarray([src.matrix_world @ v.co for v in src.data.vertices],dtype=np.float64)
source_hash=hashlib.sha256(source.tobytes()).hexdigest()
tris=np.asarray([tuple(f.vertices) for f in src.data.polygons],dtype=np.int32)
orig_tri=source[tris]
n0=np.cross(orig_tri[:,1]-orig_tri[:,0],orig_tri[:,2]-orig_tri[:,0])
area0=np.linalg.norm(n0,axis=1)
valid=area0>1e-10
assert valid.sum()>59000

def mask(side,ylo,yhi):
    idx=np.flatnonzero((side*source[:,0]>.155)&(source[:,1]>=ylo)&
                       (source[:,1]<=yhi)&(source[:,2]<.285))
    assert len(idx)>=50
    low=np.quantile(source[idx,2],.08)
    patch=idx[source[idx,2]<=low+.025]
    assert len(patch)>=15
    return idx,patch

feet={
 "FORE_L":mask(-1,-1.75,-.65),
 "FORE_R":mask(+1,-1.4,-.44),
 "HIND_L":mask(-1,1.62,2.30),
 "HIND_R":mask(+1,1.62,2.30),
}
ref={name:{"xy":source[p,:2].mean(axis=0),"z":float(source[idx,2].min())}
     for name,(idx,p) in feet.items()}
initial_targets={n:Vector(targets[n].location) for n in NAMES}
CYCLES=3
FRAMES=16*CYCLES+1
LIFT=.026

def smooth(u):
    return u*u*(3-2*u)

def desired_foot(name,t,stride):
    cycle=min(int(t//16),CYCLES-1)
    within=t-cycle*16
    if t>=CYCLES*16:
        cycle=CYCLES-1
        within=16.
    if name in B:
        moving=within<8.
        u=min(1.,max(0.,within/8.))
        world_forward=-stride*(cycle+smooth(u))
    else:
        moving=within>=8. and within<16.
        u=min(1.,max(0.,(within-8.)/8.))
        world_forward=-stride*(cycle+smooth(u))
    lift=LIFT*(math.sin(math.pi*u)**2) if moving else 0.
    target_xy=ref[name]["xy"].copy()
    target_xy[1]+=world_forward
    return {
      "phase":"SWING" if moving else "STANCE",
      "xy":target_xy,
      "z":max(.001,ref[name]["z"])+lift,
      "lift":lift,"foot_world_y_offset":world_forward,
    }

def evaluated():
    bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get()
    ob=dst.evaluated_get(dg)
    mesh=ob.to_mesh()
    try:
        return np.asarray([ob.matrix_world @ v.co for v in mesh.vertices],dtype=np.float64)
    finally:
        ob.to_mesh_clear()

def mesh_metrics(v):
    face=v[tris]
    norm=np.cross(face[:,1]-face[:,0],face[:,2]-face[:,0])
    leng=np.linalg.norm(norm,axis=1)
    ratio=np.divide(leng,area0,out=np.ones_like(leng),where=valid)
    return {
       "flipped":int(np.count_nonzero((np.sum(norm*n0,axis=1)<0)&valid)),
       "collapsed":int(np.count_nonzero((leng<1e-10)&valid)),
       "area_below_half":int(np.count_nonzero((ratio<.5)&valid)),
       "area_above_double":int(np.count_nonzero((ratio>2.)&valid)),
       "min_area_ratio":float(ratio[valid].min()),
       "max_area_ratio":float(ratio[valid].max()),
       "vertices_moved":int(np.count_nonzero(np.linalg.norm(v-source,axis=1)>1e-5)),
    }

def check_frame(v,t,stride):
    feet_stats={}
    for name,(idx,p) in feet.items():
        expected=desired_foot(name,t,stride)
        patch_xy=v[p,:2].mean(axis=0)
        xyerr=float(np.linalg.norm(patch_xy-expected["xy"]))
        minz=float(v[idx,2].min())
        phase=expected["phase"]
        feet_stats[name]={
           "phase":phase,
           "min_world_z":minz,
           "xy_patch_error":xyerr,
           "foot_target_lift":expected["lift"],
           "stance_gate":"PASS" if
              (phase=="STANCE" and -.002<=minz<=.006 and xyerr<=.01)
              else ("FAIL" if phase=="STANCE" else "NOT_STANCE"),
           "actual_patch_xy":patch_xy.tolist(),
           "expected_patch_xy":expected["xy"].tolist(),
        }
    return {"feet":feet_stats,"mesh":mesh_metrics(v)}

def collect_failures(integer,subframe,relative_seam,stride):
    ifr=[(t,n) for t,entry in integer.items()
         for n,item in entry["feet"].items()
         if item["phase"]=="STANCE" and item["stance_gate"]!="PASS"]
    sfr=[(t,n) for t,entry in subframe.items()
         for n,item in entry["feet"].items()
         if item["phase"]=="STANCE" and item["stance_gate"]!="PASS"]
    badmesh=[t for t,entry in list(integer.items())+list(subframe.items())
            if any(entry["mesh"][k] for k in
                   ("flipped","collapsed","area_below_half","area_above_double"))]
    badswing=[(t,n) for t,entry in list(integer.items())+list(subframe.items())
              for n,item in entry["feet"].items()
              if item["phase"]=="SWING" and item["min_world_z"] < -.002]
    peaks={name:max(entry["feet"][name]["min_world_z"]
                   for entry in integer.values()
                   if entry["feet"][name]["phase"]=="SWING") for name in NAMES}
    # Compare whole original vertex-coordinate geometry after subtracting root
    # translation: a cycle seam must recover the SAME pose, not a static screenshot.
    seam_violations=[q for q,x in relative_seam.items() if x>.0015]
    criteria={
      "three_complete_keyframed_cycles":len(integer)==49 and len(subframe)==48,
      "planted_feet_integer":not ifr,
      "planted_feet_subframe":not sfr,
      "mesh_integer_and_subframe":not badmesh,
      "swing_not_below_ground":not badswing,
      "four_real_swing_lifts":all(v>=.012 for v in peaks.values()),
      "cycle_seam_shape_continuity":not seam_violations,
      "nonzero_root_travel":stride*CYCLES>.035,
      "preserved_original_geometry_and_rig":True
    }
    return {
       "gate":"PASS_LIMITED_THREE_CYCLE_IK" if all(criteria.values())
             else "FAIL_THREE_CYCLE_IK",
       "criteria":criteria,
       "fail_stance_integer":ifr,
       "fail_stance_half_frame":sfr,
       "fail_geometry_frames":badmesh,
       "fail_swing_penetration":badswing,
       "swing_peak_min_world_z":peaks,
       "seam_failures":seam_violations,
    }

def run(stride,retain=False):
    # Discard animation data only on this experimental duplicate .blend.
    scene.frame_set(1)
    arm.animation_data_clear()
    arm.location=(0.,0.,0.)
    for name,tgt in targets.items():
        tgt.animation_data_clear()
        tgt.location=initial_targets[name].copy()
    frames={}
    seams={}
    base_local=None
    source_rest_check=evaluated()
    assert float(np.max(np.abs(source_rest_check-source))) < 1e-4
    for f in range(1,FRAMES+1):
        t=float(f-1)
        scene.frame_set(f)
        arm.location=(0.,-stride*t/16.,0.)
        desired={name:desired_foot(name,t,stride) for name in NAMES}
        for name in NAMES:
            z=desired[name]
            targets[name].location=initial_targets[name]+Vector((
                 0.,z["foot_world_y_offset"],z["lift"]))
        # Feedback is based on original *mesh* patch, not unverified IK empty.
        for _ in range(9):
            v=evaluated()
            for name in NAMES:
                idx,patch=feet[name]
                z=desired[name]
                xy_err=z["xy"]-v[patch,:2].mean(axis=0)
                errz=z["z"]-float(v[idx,2].min())
                delta=np.clip(.75*np.array((xy_err[0],xy_err[1],errz)), -.010,.010)
                targets[name].location+=Vector(tuple(float(x) for x in delta))
        v=evaluated()
        frames[str(f)]=check_frame(v,t,stride)
        for name in NAMES:
            targets[name].keyframe_insert(data_path="location",frame=f)
        arm.keyframe_insert(data_path="location",frame=f)
        if f in (1,17,33,49):
            local=v.copy()
            local[:,1]-=arm.location.y
            if base_local is None:base_local=local
            else:
                seams[str(f)]=float(np.max(np.linalg.norm(local-base_local,axis=1)))
    # Exact linear root interpolation: no "hiding" foot slip with eased root.
    for ob in [arm]+list(targets.values()):
        if ob.animation_data and ob.animation_data.action:
            for fc in ob.animation_data.action.fcurves:
                for key in fc.keyframe_points:
                    key.interpolation="LINEAR"
    # Replay previously keyed samples, including halfway samples. This is
    # essential: contact can FAIL between artist-visible integer keyframes.
    ints={}
    halves={}
    for f in range(1,FRAMES+1):
        scene.frame_set(f)
        ints[str(f)]=check_frame(evaluated(),float(f-1),stride)
        if f<FRAMES:
            scene.frame_set(f,subframe=.5)
            halves[str(f)+".5"]=check_frame(evaluated(),float(f-1)+.5,stride)
    # Correctly audit cycle-rest seams from baked interpolation, not solver state.
    baseline=None
    seams_replay={}
    for f in (1,17,33,49):
        scene.frame_set(f)
        v=evaluated()
        v[:,1]-=arm.location.y
        if baseline is None:baseline=v
        else:seams_replay[str(f)]=float(np.max(np.linalg.norm(v-baseline,axis=1)))
    failures=collect_failures(ints,halves,seams_replay,stride)
    failures["candidate_stride"]=stride
    failures["seam_solver"]=seams
    failures["seam_replay"]=seams_replay
    maxstance=0.
    for seq in (ints,halves):
        for item in seq.values():
            for x in item["feet"].values():
                if x["phase"]=="STANCE":
                    maxstance=max(maxstance,x["xy_patch_error"])
    failures["max_stance_patch_xy_error"]=maxstance
    max_overstretch=max(x["mesh"]["max_area_ratio"] for x in list(ints.values())+list(halves.values()))
    failures["max_triangle_area_ratio"]=max_overstretch
    if retain:
        return failures,ints,halves
    return failures,None,None

candidates=[]
winning=None
winning_data=None
for stride in (.024,.020,.016,.012):
    record,ints,halves=run(stride,retain=True)
    candidates.append(record)
    print("THREE_CYCLE_STRIDE_GATE",stride,record["gate"],
          "meshfail",record["fail_geometry_frames"][:8],
          "slip",record["max_stance_patch_xy_error"],
          "seam",record["seam_replay"])
    if record["gate"]=="PASS_LIMITED_THREE_CYCLE_IK":
        winning=record
        winning_data=(ints,halves)
        break
if winning is None:
    # Honest evidence of failure: leave smallest candidate posed and keyframed,
    # preserve its metrics/visuals and stop before claiming gait success.
    winning=candidates[-1]
    winning,ints,halves=run(.012,retain=True)
    winning_data=(ints,halves)

original_after=np.asarray([src.matrix_world @ v.co for v in src.data.vertices],dtype=np.float64)
assert hashlib.sha256(original_after.tobytes()).hexdigest()==source_hash
assert len(arm.data.bones)==13 and len(dst.data.vertices)==29948 and len(dst.data.polygons)==59932

report={
  "input_GLb_sha256":V1["original_glb_sha256"],
  "reference_source_mesh_hash_before_after":source_hash,
  "source_geometry_preserved":True,
  "vertex_count":29948,"triangle_count":59932,"deform_bones":13,
  "source_rig":"ik-contact-v1/S-QEM-real-13bone-IK-contact-v1.blend",
  "cycle_count":CYCLES,"cycle_key_interval":16,
  "integer_frames":FRAMES,"halfway_frames":FRAMES-1,
  "body_height_ref":2.55,
  "step_travel_per_cycle":winning["candidate_stride"],
  "total_world_root_translation":winning["candidate_stride"]*CYCLES,
  "candidate_scan":candidates,
  "selected":winning,
  "keyframe_data":winning_data[0],
  "midframe_data":winning_data[1],
  "fully_running_race_gait":False,
  "art_design_gate_approved":False,
  "game_production_approved":False,
  "limitation":"Alternating diagonal contact/short root locomotion; does not establish full gallop, high speed, dynamics, collision, anatomy or game fitness."
}
(OUT/"REAL_THREE_CYCLE_IK_QA.json").write_text(json.dumps(report,indent=2)+"\n")
scene.frame_start=1
scene.frame_end=FRAMES
scene.render.fps=24
cam=scene.camera
assert cam and cam.type=="CAMERA"
cam.data.type="ORTHO"
cam.data.ortho_scale=5.15
center=Vector((0,-.04,1.275))
cam.location=center+Vector((1,-1,.25)).normalized()*9
cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.render.resolution_x=800
scene.render.resolution_y=600
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
src.hide_render=True
dst.hide_render=False
arm.hide_render=True
for ob in targets.values():ob.hide_render=True
# One entire 16-frame genuine Blender cycle plus additional seam confirmations.
render_frames=sorted(set(list(range(1,18))+[25,33,41,49]))
for f in render_frames:
    scene.frame_set(f)
    scene.render.filepath=str(REV/("S_QEM_REAL_MULTICYCLE_F%02d.png"%f))
    bpy.ops.render.render(write_still=True)
scene.frame_set(33)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-13bone-threecycle-IK-v1.blend"),compress=True)
print("QEM_THREE_CYCLE_FINAL",json.dumps({
 "result":winning["gate"],"stride":winning["candidate_stride"],
 "root_travel":winning["candidate_stride"]*CYCLES,
 "checks":winning["criteria"],
 "max_contact_patch_error":winning["max_stance_patch_xy_error"],
 "geometry_violations":winning["fail_geometry_frames"][:20],
 "seam_residuals":winning["seam_replay"]
},indent=2))
