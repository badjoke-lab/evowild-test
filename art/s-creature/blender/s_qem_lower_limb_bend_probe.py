"""QEM real-mesh four-leg lower-joint bend feasibility probe, NOT a rig.

Uses observed fore/hind foot coordinate strips. Deforms a separate copy of
original 29,948-vertex watertight TRELLIS2 QEM geometry with deterministic
localized YZ hinge probe angles and 3D weight falloff. Actual five-camera
render comparisons & inverted face/area/topology audits. Does NOT claim
anatomical landmark approval, armature, skinning, or gameplay readiness.
"""
from pathlib import Path
import bpy,bmesh,json,hashlib,math
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/"experiments"
ROOT_OUT=EXP/"qem-deformation-gate-20261010"
OUT=ROOT_OUT/"bend-probe-v1";REV=OUT/"review"
REV.mkdir(parents=True,exist_ok=True)
src_file=ROOT_OUT/"S-QEM-pre-rig-source-review.blend"
glb=EXP/"trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
donor_sha=hashlib.sha256(glb.read_bytes()).hexdigest()
assert donor_sha=="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f",donor_sha

scene=bpy.context.scene
orig=[o for o in scene.objects if o.type=="MESH"]
if len(orig)!=1:raise RuntimeError(f"Expected one original QEM mesh, got {[o.name for o in orig]}")
source=orig[0];source.name="SOURCE_QEM_REAL_GEOMETRY_IMMUTABLE"
assert len(source.data.vertices)==29948 and len(source.data.polygons)==59932
xyz=np.asarray([source.matrix_world@v.co for v in source.data.vertices],dtype=np.float64)
lower=xyz.min(axis=0);upper=xyz.max(axis=0)
assert 2.54<upper[2]-lower[2]<2.56 and upper[1]-lower[1]>3.5
cam=bpy.data.objects.get("SURVEY_SAME_ORTHOGRAPHIC")
if not cam or cam.type!="CAMERA":raise RuntimeError("Unchanged donor camera missing")
cameram=tuple(tuple(r) for r in cam.matrix_world)
camd=(cam.data.type,float(cam.data.ortho_scale))

posed=source.copy()
posed.data=source.data.copy()
posed.name="QEM_SAME_TRIANGLES_FOUR_LOWER_LIMB_BEND_PROBE"
scene.collection.objects.link(posed)
posed.matrix_world=source.matrix_world.copy()
source.hide_render=True

# Infer regional hinge locations from REAL source vertices in low-mid limb
# bands. These are landmark CANDIDATES, NOT clinically/anatomically approved.
REGIONS={
 "FORE_L":(-1,-1.83,-.34,14.0),
 "FORE_R":(+1,-1.83,-.34,-14.0),
 "HIND_L":(-1,1.03,2.31,-12.0),
 "HIND_R":(+1,1.03,2.31,12.0),
}
def smoothstep(x):
    v=max(0.,min(1.,float(x)))
    return v*v*(3-2*v)
pivots={}
for name,(side,y0,y1,angle) in REGIONS.items():
    eligibility=((side*xyz[:,0])>.115)&(xyz[:,1]>=y0)&(xyz[:,1]<=y1)&(xyz[:,2]>.47)&(xyz[:,2]<.84)
    sample=xyz[eligibility]
    if not 70<len(sample)<4500:
        raise RuntimeError(f"Landmark {name} ungrounded in real mesh: points {len(sample)}")
    # Median of actual limb band, not guessed centroids from concept art.
    mid=np.median(sample,axis=0)
    pivots[name]={"xyz":[float(x) for x in mid],"samples":len(sample),
                  "bend_degrees":angle,"region_y_bounds":[y0,y1],
                  "status":"KINEMATIC_PROBE_CANDIDATE_NOT_ANATOMICAL_APPROVAL"}

movement=np.zeros_like(xyz)
weights=np.zeros(len(xyz),dtype=np.float64)
member_counts={key:0 for key in REGIONS}
for i,p in enumerate(xyz):
    delta=np.zeros(3,dtype=np.float64)
    active=[]
    for name,(side,y0,y1,deg) in REGIONS.items():
        if side*p[0]<=.025:continue
        pivot=np.asarray(pivots[name]["xyz"])
        # Lower limb deformation weight with smooth, bounded transition:
        # full distal contact below z=.32, no movement above z=.98.
        w_z=smoothstep((.98-p[2])/.66)
        w_x=smoothstep((side*p[0]-.025)/.15)
        w_y=smoothstep((p[1]-y0)/.22)*smoothstep((y1-p[1])/.22)
        w=w_z*w_x*w_y
        if w<=1e-6:continue
        theta=math.radians(deg)
        dy=p[1]-pivot[1];dz=p[2]-pivot[2]
        rotated_y=dy*math.cos(theta)-dz*math.sin(theta)
        rotated_z=dy*math.sin(theta)+dz*math.cos(theta)
        delta+=np.asarray([0.,rotated_y-dy,rotated_z-dz])*w
        active.append(name)
    if active:
        movement[i]=delta
        weights[i]=max(weights[i],np.linalg.norm(delta))
        for name in active:member_counts[name]+=1
source_signature=hashlib.sha256(xyz.tobytes()).hexdigest()
if min(member_counts.values())<80:raise RuntimeError(f"Leg influence too weak: {member_counts}")
moved_idx=np.where(np.linalg.norm(movement,axis=1)>1e-5)[0]
max_movement=float(np.linalg.norm(movement,axis=1).max())
if not (350<len(moved_idx)<11000 and .015<max_movement<.38):
    raise RuntimeError(f"Unsafe/unmeaningful bend {len(moved_idx)} vertices max {max_movement}")
W=np.linalg.inv(np.asarray(posed.matrix_world,dtype=np.float64).reshape(4,4)) if False else None
# Convert output world-space deformation to original local vertex coords via
# 3x3 inverse matrix; source GLB and same positions are otherwise unchanged.
matrix=posed.matrix_world.to_3x3().inverted()
for i in moved_idx:
    local_diff=matrix@Vector(tuple(float(a) for a in movement[i]))
    posed.data.vertices[int(i)].co+=local_diff
posed.data.update()
new_xyz=np.asarray([posed.matrix_world@v.co for v in posed.data.vertices],dtype=np.float64)
actual=np.linalg.norm(new_xyz-xyz,axis=1)
if float(np.abs(new_xyz-xyz-movement).max())>2e-5:
    raise RuntimeError("Unexpected world-vs-local deformation disagreement")
if len(posed.data.vertices)!=len(source.data.vertices) or len(posed.data.polygons)!=len(source.data.polygons):
    raise RuntimeError("Mesh topology size changed during bend test")
for i,(a,b) in enumerate(zip(source.data.polygons,posed.data.polygons)):
    if tuple(a.vertices)!=tuple(b.vertices):raise RuntimeError(f"Source topology changed at face {i}")

# All affected triangles are measured, not silently treated as deformation safe.
face_distortion=[]
flipped=[]
area_shrink=[]
area_expand=[]
near_collapse=[]
for face in source.data.polygons:
    ix=list(face.vertices)
    if not any(j in moved_idx for j in ix):continue
    if len(ix)!=3:raise RuntimeError("QEM expected triangulated surface")
    a0,a1,a2=xyz[ix]
    b0,b1,b2=new_xyz[ix]
    na=np.cross(a1-a0,a2-a0);nb=np.cross(b1-b0,b2-b0)
    before_len=float(np.linalg.norm(na));after_len=float(np.linalg.norm(nb))
    if before_len<1e-10 or after_len<1e-10:
        near_collapse.append(face.index)
        continue
    ratio=after_len/before_len
    cosine=float(np.dot(na,nb)/(before_len*after_len))
    if cosine<0:flipped.append(face.index)
    if ratio<.50:area_shrink.append(face.index)
    if ratio>2:area_expand.append(face.index)
    face_distortion.append((ratio,cosine))
triangles=len(source.data.polygons)
affected_faces=len(face_distortion)+len(near_collapse)
# Failure is an OBSERVED outcome, not a pretext to discard the actual model.
# One face inverted is sufficient to fail the feasibility gate.
quality_pass=len(flipped)==0 and len(near_collapse)==0 and len(area_shrink)==0 and len(area_expand)==0

bm=bmesh.new();bm.from_mesh(posed.data)
boundary=sum(len(e.link_faces)==1 for e in bm.edges)
nonmanifold=sum(len(e.link_faces)!=2 for e in bm.edges)
bm.free()
if nonmanifold or boundary:raise RuntimeError("Topology damaged by bend in-place")

# Locked original preserved byte-exact in same .blend (no coordinate changes).
source_after=np.asarray([source.matrix_world@v.co for v in source.data.vertices],dtype=np.float64)
if hashlib.sha256(source_after.tobytes()).hexdigest()!=source_signature:
    raise RuntimeError("Source geometry changed in runtime")
if camd!=(cam.data.type,float(cam.data.ortho_scale)) or tuple(tuple(r) for r in cam.matrix_world)!=cameram:
    raise RuntimeError("Camera configuration changed")
views=["side","front","front34","rear34","back"]
directions={
 "side":Vector((1,0,0)),"front":Vector((0,-1,0)),
 "front34":Vector((1,-1,0)).normalized(),
 "rear34":Vector((1,1,0)).normalized(),
 "back":Vector((0,1,0))}
center=Vector((0,0,1.275))
for name in views:
    cam.location=center+directions[name]*9
    cam.rotation_euler=((center-cam.location).to_track_quat("-Z","Y")).to_euler()
    # Clean geometry before and after, no guide spheres in production renders.
    source.hide_render=False
    posed.hide_render=True
    scene.render.filepath=str(REV/f"QEM_before_{name}.png")
    bpy.ops.render.render(write_still=True)
    source.hide_render=True
    posed.hide_render=False
    scene.render.filepath=str(REV/f"QEM_bend_probe_{name}.png")
    bpy.ops.render.render(write_still=True)
# Saved native scene contains immutable source and named deformed test copy.
# This is a mesh-space probe, NOT a skinned armature: do not mislabel it.
source.hide_render=False
posed.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-real-geometry-bend-probe-v1.blend"),compress=True)
facts={
 "source_glb_sha256":donor_sha,
 "original_verts":len(source.data.vertices),
 "posed_verts":len(posed.data.vertices),
 "source_faces":len(source.data.polygons),
 "posed_faces":len(posed.data.polygons),
 "source_topology_unchanged":True,
 "same_geometry_no_lowpoly_substitution":True,
 "source_coordinates_unchanged":True,
 "deformation_method":"candidate ankle/hock bend in sagittal YZ plane via local smooth vertex weights on a duplicate real mesh; NOT skeletal skinning",
 "candidate_pivots":pivots,
 "active_limb_region_vertex_counts":member_counts,
 "moved_vertices":int(len(moved_idx)),
 "max_world_vertex_displacement":max_movement,
 "affected_faces":affected_faces,
 "flipped_faces":len(flipped),
 "face_collapse":len(near_collapse),
 "face_area_less_than_half":len(area_shrink),
 "face_area_greater_than_double":len(area_expand),
 "area_ratio_p5":float(np.quantile([r for r,c in face_distortion],.05)) if face_distortion else None,
 "area_ratio_p95":float(np.quantile([r for r,c in face_distortion],.95)) if face_distortion else None,
 "nonmanifold_edges":nonmanifold,
 "watertight_mesh_topology":boundary==0,
 "mechanical_probe_gate":"PASS_NO_FLIPS_OR_2X_AREA_DISTORTION" if quality_pass else "FAIL_FACIAL_COLLAPSE_OR_DISTORTION",
 "joint_anatomy_verified":False,
 "armature_created":False,
 "skinning_tested":False,
 "game_run_tested":False,
 "production_approved":False,
 "views_rendered":views
}
(OUT/"BEND_PROBE_QA.json").write_text(json.dumps(facts,indent=2)+"\n")
print("REAL_SOURCE_QEM_MESH_BEND_PROBE",json.dumps({k:facts[k] for k in (
 "candidate_pivots","active_limb_region_vertex_counts","moved_vertices",
 "max_world_vertex_displacement","affected_faces","flipped_faces",
 "face_collapse","face_area_less_than_half","face_area_greater_than_double",
 "mechanical_probe_gate"
)},indent=2))
