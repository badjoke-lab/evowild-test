"""S R1-A2 v2 - measured scapular spike reconstruction.

Input is the completed actual R1-A2 v1 model. Vertex coordinate evidence
is from R1_A2_SCAPULAR_APEX_SURVEY.json. No texture edits, smoothing pass,
subdivision, or whole-body changes. Only physical left/right upper scapular
ridge correction; no game or rig approval implied.
"""
from pathlib import Path
import bpy,bmesh,json,hashlib,math
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output"
REV=OUT/"review/authority-r1-a2-scapula-v2"
REV.mkdir(parents=True,exist_ok=True)
base=bpy.data.objects["S_B2a_v5_continuous_body"]
collection=bpy.data.collections["S_REBUILD_GATE_A"]
cams=("SIDE","FRONT","FRONT34","REAR34","BACK")
survey=json.loads((OUT/"review/authority-r1-a2-anatomy/R1_A2_SCAPULAR_APEX_SURVEY.json").read_text())
if len(base.data.vertices)!=5728 or len(base.data.polygons)!=6376:
    raise RuntimeError("Wrong anatomy model; source R1-A2 mesh not found")

def hash_obj(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(repr(tuple(v.co)).encode())
    for f in o.data.polygons:h.update(repr(tuple(f.vertices)).encode())
    return h.hexdigest()

locked={o.name:hash_obj(o) for o in collection.objects if o.type=="MESH" and o!=base}
cam_matrices={c:tuple(tuple(row) for row in bpy.data.objects["S_REBUILD_CAM_"+c].matrix_world) for c in cams}
mesh=base.data
original=[v.co.copy() for v in mesh.vertices]
poly_before=[tuple(p.vertices) for p in mesh.polygons]
field_centers={"L":survey["tips"]["L"][0],"R":survey["tips"]["R"][0]}
for s in ("L","R"):
    peak=field_centers[s]
    if abs(abs(peak["x"])-.112)>.03 or abs(peak["y"]+.013)>.025 or not 1.13<=peak["z"]<=1.17:
        raise RuntimeError("Unexpected real measured shoulder apex "+repr(peak))
    # Ensure the top vertex really belongs to the input.
    actual=mesh.vertices[peak["index"]].co
    if (Vector((peak["x"],peak["y"],peak["z"]))-actual).length>.000005:
        raise RuntimeError("Source vertex differs from survey; cannot safely sculpt")

def taper(q):
    if q>=1:return 0.
    t=1-q
    return t*t*(3-2*t)

hits={"L":0,"R":0}
moved=[]
CAP=.05
for i,p in enumerate(original):
    if p.z<1.085:continue
    side="L" if p.x<0 else "R"
    tip=field_centers[side]
    # Elliptic XY shoulder roof, not neck and not limb shaft.
    q=((p.x-tip["x"])/.084)**2+((p.y-tip["y"])/.090)**2
    w=taper(q)
    if w<=0:continue
    # Target follows the upper shoulder plane to remove the triangular
    # single-point spike, not flatten the entire upper torso.
    target=1.100+0.012*abs(p.y-tip["y"])/.09
    excess=max(0.,p.z-target)
    dz=-min(CAP,excess*w)
    if abs(dz)<=1e-7:continue
    mesh.vertices[i].co.z=p.z+dz
    moved.append((i,side,float(dz)))
    hits[side]+=1
mesh.update()
if not (12<=hits["L"]<350 and 12<=hits["R"]<350):
    raise RuntimeError("Ridge edit hit abnormal vertex count: "+repr(hits))
for s in ("L","R"):
    tip=field_centers[s]
    p=mesh.vertices[tip["index"]].co
    if not .020<=tip["z"]-p.z<=CAP+1e-5:
        raise RuntimeError("Measured spike not reduced enough "+repr((s,tip["z"],p.z)))
    # The surrounding 3D morphology should not change in the lower body.
for i,p in enumerate(original):
    delta=mesh.vertices[i].co-p
    if abs(delta.x)>1e-9 or abs(delta.y)>1e-9 or delta.z>1e-9 or delta.length>CAP+1e-5:
        raise RuntimeError(f"Out-of-scope displacement vertex {i}: {tuple(delta)}")
assert [tuple(p.vertices) for p in mesh.polygons]==poly_before
for name,d in locked.items():
    if hash_obj(bpy.data.objects[name])!=d:raise RuntimeError("Other S part altered "+name)
for c,mat in cam_matrices.items():
    if tuple(tuple(row) for row in bpy.data.objects["S_REBUILD_CAM_"+c].matrix_world)!=mat:
        raise RuntimeError("S camera altered "+c)
bm=bmesh.new();bm.from_mesh(mesh)
nonmanifold=sum(len(e.link_faces)!=2 for e in bm.edges)
bm.free()
if nonmanifold:raise RuntimeError(f"Retopo nonmanifold {nonmanifold}")

newpeak={s:{"original_xyz":[v["x"],v["y"],v["z"]],
    "edited_xyz":list(mesh.vertices[v["index"]].co),
    "delta_z":float(mesh.vertices[v["index"]].co.z-v["z"])} for s,v in field_centers.items()}
facts={
 "source":"output/S-authority-r1-a2-anatomy-v1.blend",
 "candidate":"output/S-authority-r1-a2-scapula-v2.blend",
 "geometry_edit":"bounded 3D measured paired scapular spike height correction toward surrounding thorax roof",
 "actual_survey":"output/review/authority-r1-a2-anatomy/R1_A2_SCAPULAR_APEX_SURVEY.json",
 "apex_before_after":newpeak,
 "modified_vertices":len(moved),
 "per_side_vertex_count":hits,
 "max_applied_displacement":max(-dz for _,_,dz in moved),
 "original_body_vertex_count":5728,"body_vertex_count_after":len(mesh.vertices),
 "original_body_face_count":6376,"body_face_count_after":len(mesh.polygons),
 "all_xy_body_coords_unchanged":True,
 "non_roi_vertices_unchanged":True,
 "all_other_meshes_unchanged":True,
 "all_five_cameras_unchanged":True,
 "nonmanifold_edges":nonmanifold,
 "production_approved":False,"rig_approved":False,
 "gate":"ACTUAL_IMAGE_REVIEW_REQUIRED"
}
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-authority-r1-a2-scapula-v2.blend"),compress=True)
scene=bpy.context.scene
views=("side","front","front34","rear34","back")
for view in views:
    scene.camera=bpy.data.objects["S_REBUILD_CAM_"+view.upper()]
    scene.render.filepath=str(REV/f"S_scapula_v2_{view}.png")
    bpy.ops.render.render(write_still=True)
facts["actual_render_views"]=list(views)
(REV/"R1_A2_SCAPULA_V2_GEOMETRY.json").write_text(json.dumps(facts,indent=2)+"\n")
print("SCAPULAR_SPIKE_R2_SCULPT_DONE",json.dumps({k:v for k,v in facts.items() if k not in ("apex_before_after",)}))
