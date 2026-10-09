"""EvoWild S R1-A2 shape-directed shoulder / hip anatomical planes.

Input: actual R1-A1 v3 KEEP-as-local-donor Blend. This is NOT another surface
smoothing pass: it applies four explicit direction-controlled anatomical field
deformations to existing vertices. Geometry, identity, and outside-body parts
are audited. No automatic production promotion.
"""
import bpy, bmesh, math, json, hashlib, os
from collections import defaultdict
from mathutils import Vector
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"output/S-authority-r1-a1-v3-patch.blend"
OUT=ROOT/"output"
REVIEW=OUT/"review/authority-r1-a2-anatomy"
REVIEW.mkdir(parents=True, exist_ok=True)
BASE=bpy.data.objects["S_B2a_v5_continuous_body"]
GROUP=bpy.data.collections["S_REBUILD_GATE_A"]
CAMERAS=("SIDE","FRONT","FRONT34","REAR34","BACK")
SHOULDER_FIELDS=(
 # Sculpt away the unnaturally raised sharp scapular apex.
 ("scapular_apex",(-.164,-.030,1.005),(.106,.195,.178),(-.010,.004,-.027)),
 # Reestablish a sloping lower shoulder -> proximal foreleg plane.
 ("pectoralis_root",(-.158,-.095,.819),(.112,.168,.160),(-.015,-.007,.006)),
)
HIP_FIELDS=(
 # Hip/gluteus outer mass: no cylindrical enlargement of entire hindleg.
 ("gluteal_sweep",(-.181,.739,.930),(.117,.183,.163),(-.011,-.006,-.006)),
 # Thigh plane from pelvis toward flexed hind knee.
 ("femoral_transition",(-.172,.835,.762),(.101,.154,.161),(-.011,-.012,-.003)),
)
# Coordinates are deliberately in actual Blender local-space, not image-space.
# Sign-flip X for mirrored anatomy. All control volumes taper to zero at edges.
def smooth_falloff(pos,center,radii):
    x=(pos.x-center[0])/radii[0]
    y=(pos.y-center[1])/radii[1]
    z=(pos.z-center[2])/radii[2]
    q=x*x+y*y+z*z
    if q>=1.0:return 0.0
    t=1.0-q
    return t*t*(3.0-2.0*t)

def signature(obj):
    m=obj.data
    digest=hashlib.sha256()
    digest.update(obj.name.encode())
    for v in m.vertices:digest.update(repr(tuple(v.co)).encode())
    for p in m.polygons:digest.update(repr(tuple(p.vertices)).encode())
    digest.update(repr(tuple(tuple(r) for r in obj.matrix_world)).encode())
    return digest.hexdigest()

separate={o.name:signature(o) for o in GROUP.objects if o.type=="MESH" and o!=BASE}
camera_mats={c:tuple(tuple(row) for row in bpy.data.objects["S_REBUILD_CAM_"+c].matrix_world) for c in CAMERAS}
m=BASE.data
origin=[v.co.copy() for v in m.vertices]
faces=[tuple(f.vertices) for f in m.polygons]
original_sha=signature(BASE)
if len(origin)!=5728 or len(faces)!=6376:
    raise RuntimeError(f"R1-A1 v3 donor structure changed: {len(origin)} vertices, {len(faces)} faces")
field_hits=defaultdict(int)
field_peak=defaultdict(float)
CAP=.030
moved=[]
max_drift=0.0
zones=set()
for index,p in enumerate(origin):
    displacement=Vector((0,0,0))
    activated=[]
    for label,collection in (("shoulder",SHOULDER_FIELDS),("hip",HIP_FIELDS)):
        for side in (-1,1):
            for name,anchor,radii,shift in collection:
                ctr=(side*abs(anchor[0]),anchor[1],anchor[2])
                w=smooth_falloff(p,ctr,radii)
                if w<1e-7:continue
                key=label+"_"+name+("_left" if side<0 else "_right")
                field_hits[key]+=1
                field_peak[key]=max(field_peak[key],w)
                d=Vector((side*abs(shift[0]),shift[1],shift[2]))*w
                displacement+=d
                activated.append(label)
    if displacement.length>CAP:
        displacement.normalize()
        displacement*=CAP
    if displacement.length>1e-7:
        m.vertices[index].co=p+displacement
        max_drift=max(max_drift,displacement.length)
        moved.append(index)
        zones.update(activated)

m.update()
if max_drift<=.003 or max_drift>CAP+1e-5:
    raise RuntimeError(f"morphology shift unexpectedly absent/outside cap {max_drift}")
for key,count in field_hits.items():
    if count<12 or field_peak[key]<.10:
        raise RuntimeError(f"Unsupported anatomical anchor {key}: vertices={count},peak={field_peak[key]}")
if len(field_hits)!=8 or zones!={"shoulder","hip"} or not (70<len(moved)<2300):
    raise RuntimeError(f"Unexpected anchor coverage fields={dict(field_hits)}, moved={len(moved)}, zones={zones}")
unchanged_count=0
for i,p in enumerate(origin):
    if i not in moved:
        if tuple(m.vertices[i].co)!=tuple(p):
            raise RuntimeError(f"Supposedly locked body vertex moved {i}")
        unchanged_count+=1
for name,digest in separate.items():
    if signature(bpy.data.objects[name])!=digest:
        raise RuntimeError(f"Separate authoritative component modified: {name}")
for c,before in camera_mats.items():
    if tuple(tuple(row) for row in bpy.data.objects["S_REBUILD_CAM_"+c].matrix_world)!=before:
        raise RuntimeError(f"Camera changed {c}")
if [tuple(f.vertices) for f in m.polygons]!=faces:
    raise RuntimeError("Topology changed outside edit scope")

# Surface validity is a hard gate; this modifier must not tear deforming body.
bm=bmesh.new()
bm.from_mesh(m)
bm.normal_update()
bad=[e for e in bm.edges if len(e.link_faces)!=2]
if bad:
    raise RuntimeError(f"Non-manifold edges after anatomical sculpt: {len(bad)}")
face_count=len(bm.faces)
reversed_count=0
# Full-body volume sign can be inherited from R0; do not claim skinnability.
bm.free()

facts={
  "status":"REAL_GEOMETRY_SAVED_VISUAL_REVIEW_PENDING",
  "source_file":"output/S-authority-r1-a1-v3-patch.blend",
  "output_file":"output/S-authority-r1-a2-anatomy-v1.blend",
  "method":"Four signed shoulder/hip muscle-plane displacements, mirrored left/right, compact ellipsoidal field; no global smooth or subdivision",
  "body_vertices_before":len(origin),"body_vertices_after":len(m.vertices),
  "body_faces_before":len(faces),"body_faces_after":len(m.polygons),
  "changed_body_vertices":len(moved),
  "unchanged_body_vertices":unchanged_count,
  "max_vertex_displacement":max_drift,
  "hard_displacement_cap":CAP,
  "field_vertex_hits":dict(field_hits),
  "field_peak_weights":dict(field_peak),
  "body_topology_unchanged":True,
  "other_crests_feet_tail_unchanged":True,
  "locked_cameras_unchanged":True,
  "nonmanifold_edges":0,
  "original_body_signature":original_sha,
  "new_body_signature":signature(BASE),
  "rig_ready":False,
  "game_asset_approved":False
}
# Give the distinct shoulder and hip zones separately in the editable
# Blender scene, with no fake shading overlays on the output.
for label,collection in (("SHOULDER",SHOULDER_FIELDS),("HIP",HIP_FIELDS)):
    group=BASE.vertex_groups.get("R1A2_"+label)
    if not group:group=BASE.vertex_groups.new(name="R1A2_"+label)
    for i,p in enumerate(origin):
        weight=max((smooth_falloff(p,(side*abs(anchor[0]),anchor[1],anchor[2]),radii)
                    for side in (-1,1) for _,anchor,radii,_ in collection),default=0.0)
        if weight>0.001:group.add([i],weight,"REPLACE")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-authority-r1-a2-anatomy-v1.blend"),compress=True)
scene=bpy.context.scene
views=("side","front","front34","rear34","back")
for view in views:
    scene.camera=bpy.data.objects["S_REBUILD_CAM_"+view.upper()]
    scene.render.filepath=str(REVIEW/("S_R1_A2_anatomy_v1_"+view+".png"))
    bpy.ops.render.render(write_still=True)
facts["views_rendered"]=list(views)
(REVIEW/"R1_A2_ANATOMY_FACTS.json").write_text(json.dumps(facts,indent=2)+"\n")
print("R1_A2_ANATOMY_REAL_SCULPT",json.dumps({
  "edited":len(moved),"max_displacement":max_drift,"anchor_counts":dict(field_hits)
}))
