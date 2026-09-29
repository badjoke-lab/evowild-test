"""Deterministic v8 sternum-lobe correction from S-blockout-v7.

Goal: remove the remaining rounded central lower-chest lobe by projecting only the
ventral anterior-thorax surface toward a shallow sloped Y/Z plane. X, topology,
vertex count, neck width, forelimb roots, scapular outer ridges, and all other
regions remain fixed.
"""
import bpy, os, json, math
from mathutils.bvhtree import BVHTree

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"output")
source=bpy.data.collections.get("S_EDITABLE_SOURCE")
model=bpy.data.collections.get("S_MODEL")
if source is None or model is None:
    raise RuntimeError("Missing S_EDITABLE_SOURCE or S_MODEL")

body=next((o for o in model.objects if o.type=="MESH"),None)
if body is None:
    raise RuntimeError("No integrated S mesh")

depsgraph=bpy.context.evaluated_depsgraph_get()

def make_bvh(obj):
    eo=obj.evaluated_get(depsgraph)
    me=eo.to_mesh()
    try:
        verts=[eo.matrix_world @ v.co for v in me.vertices]
        polys=[tuple(p.vertices) for p in me.polygons]
        if not verts or not polys:
            return None
        return BVHTree.FromPolygons(verts,polys,all_triangles=False)
    finally:
        eo.to_mesh_clear()

root_objs=[o for o in source.objects if o.type=="MESH" and (
    o.name.startswith("Forelimb") or o.name.startswith("Scapular_keel")
)]
neck_objs=[o for o in source.objects if o.type=="MESH" and o.name.startswith("Neck_integrated_keel")]
root_bvhs=[b for b in (make_bvh(o) for o in root_objs) if b is not None]
neck_bvhs=[b for b in (make_bvh(o) for o in neck_objs) if b is not None]
if not root_bvhs or not neck_bvhs:
    raise RuntimeError("Protection BVHs missing")

def smooth01(t):
    t=max(0.0,min(1.0,t))
    return t*t*(3.0-2.0*t)

def bump(q,lo,peak,hi):
    if q<=lo or q>=hi:
        return 0.0
    if q<=peak:
        return smooth01((q-lo)/(peak-lo))
    return smooth01((hi-q)/(hi-peak))

def nearest_dist(pw,bvhs):
    d=None
    for bvh in bvhs:
        hit=bvh.find_nearest(pw)
        if hit is None:
            continue
        dist=hit[3]
        d=dist if d is None else min(d,dist)
    return d

original=[v.co.copy() for v in body.data.vertices]
changed=[]
max_dz=0.0
max_dy=0.0
max_w=0.0

for i,v in enumerate(body.data.vertices):
    p=v.co.copy()
    x,y,z=p.x,p.y,p.z

    if not (abs(x)<0.30 and -1.00<y<-0.48 and 1.72<z<2.14):
        continue

    wx=1.0-smooth01((abs(x)-0.12)/0.18)
    wy=bump(y,-1.00,-0.76,-0.48)
    wz=bump(z,1.72,1.94,2.14)
    w=wx*wy*wz
    if w<=0.0:
        continue

    # Desired shallow ventral chest plane:
    # higher at the front/neck side, lower toward the rear chest.
    t=(y+1.00)/0.52
    t=max(0.0,min(1.0,t))
    z_plane=2.075 - 0.155*t
    deficit=max(0.0,z_plane-z)
    if deficit<=0.0:
        continue

    pw=body.matrix_world @ p

    # Smoothly protect forelimb roots and scapular outer ridges.
    dr=nearest_dist(pw,root_bvhs)
    if dr is None:
        raise RuntimeError("Root protection query failed")
    w*=smooth01((dr-0.045)/0.090)
    if w<=0.0:
        continue

    # Protect true neck junction only in the upper/front boundary.
    if z>2.08 or y<-0.94:
        dn=nearest_dist(pw,neck_bvhs)
        if dn is None:
            raise RuntimeError("Neck protection query failed")
        w*=smooth01((dn-0.040)/0.070)
        if w<=0.0:
            continue

    dz=min(0.070,0.60*deficit)*w
    if dz<=1e-9:
        continue
    dy=min(0.032,0.42*dz)

    p2=p.copy()
    p2.x=x
    p2.y=y+dy
    p2.z=z+dz
    v.co=p2
    changed.append(i)
    max_dz=max(max_dz,dz)
    max_dy=max(max_dy,dy)
    max_w=max(max_w,w)

body.data.update()
if not changed:
    raise RuntimeError("v8 changed zero vertices")
if len(body.data.vertices)!=len(original):
    raise RuntimeError("Vertex count changed")

changed_set=set(changed)
for i,p0 in enumerate(original):
    p1=body.data.vertices[i].co
    if abs(p1.x-p0.x)>1e-9:
        raise RuntimeError(f"X changed at {i}")
    if i not in changed_set and (p1-p0).length>1e-9:
        raise RuntimeError(f"Unexpected non-target change at {i}")

body.name="S_organism_blockout_v8"
bpy.context.scene.camera=bpy.data.objects.get("CAM_FRONT34")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"S-blockout-v8.blend"),compress=True)

report={
    "input":"S-blockout-v7.blend",
    "output":"S-blockout-v8.blend",
    "scope":"central sternum lobe to shallow sloped ventral chest plane",
    "target_bounds":{"abs_x_lt":0.30,"y":[-1.00,-0.48],"z":[1.72,2.14]},
    "plane":{"front_z":2.075,"rear_z":1.920,"y_front":-1.00,"y_rear":-0.48},
    "max_applied_displacement":{"y_back":max_dy,"z_up":max_dz},
    "changed_vertices":len(changed),
    "total_vertices":len(original),
    "max_weight":max_w,
    "lateral_x_unchanged":True,
    "topology_unchanged":True,
    "vertex_count_unchanged":True,
    "neck_width_reduction_preserved":True,
    "forelimb_and_scapular_roots_protected":True,
    "accepted":False
}
json.dump(report,open(os.path.join(OUT,"thorax-v8-validation.json"),"w"),indent=2)

hp=os.path.join(ROOT,"HANDOFF_STATE.json")
state=json.load(open(hp))
state.update(
    stage="S-blockout-v8",
    current_stage="S-blockout-v8 sternum-plane correction saved, review pending",
    current_model_file="output/S-blockout-v8.blend",
    next_action="Inspect v8 front/front34/side against reference 01. Confirm the central sternum lobe is no longer rounded/hanging and the ventral chest reads as a shallow sloped plane without a new crease.",
    blockers=[],
    accepted=False
)
json.dump(state,open(hp,"w"),ensure_ascii=False,indent=2)

cp=os.path.join(ROOT,"CHECKPOINT.md")
s=open(cp).read()
lines=[]
for line in s.splitlines():
    if line.startswith("current_stage:"):
        line="current_stage: S-blockout-v8 sternum-plane correction saved, review pending"
    elif line.startswith("current_model_file:"):
        line="current_model_file: output/S-blockout-v8.blend"
    elif line.startswith("next_action:"):
        line="next_action: Inspect v8 front/front34/side against reference 01. Confirm the central sternum lobe is no longer rounded/hanging and the ventral chest reads as a shallow sloped plane without a new crease."
    lines.append(line)
s="\n".join(lines)+"\n"
if "Applied v8 sternum-plane correction from v7" not in s:
    s=s.replace("next_action:","- Applied v8 sternum-plane correction from v7: only the remaining central lower-chest lobe was moved toward a shallow sloped ventral plane; X/topology/count/neck width/root protections remain fixed.\n\nnext_action:",1)
open(cp,"w").write(s)

print("S_V8",json.dumps(report))
