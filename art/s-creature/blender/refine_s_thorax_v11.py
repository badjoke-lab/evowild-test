"""Deterministic v11 anterior-thorax correction from S-blockout-v7.

Replaces the invalid v10 modifier-based fairing with explicit per-vertex updates.
Only vertices in the protected anterior-thorax active set may move, and only in Y/Z.
Every non-active vertex remains exactly unchanged in position. X, topology, vertex
count, neck width, forelimb roots, scapular outer ridges, and all other regions
remain fixed.
"""
import bpy, os, json
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

def nearest_dist(pw,bvhs):
    d=None
    for bvh in bvhs:
        hit=bvh.find_nearest(pw)
        if hit is None:
            continue
        dist=hit[3]
        d=dist if d is None else min(d,dist)
    return d

def smooth01(t):
    t=max(0.0,min(1.0,t))
    return t*t*(3.0-2.0*t)

def bump(q,lo,peak,hi):
    if q<=lo or q>=hi:
        return 0.0
    if q<=peak:
        return smooth01((q-lo)/(peak-lo))
    return smooth01((hi-q)/(hi-peak))

me=body.data
orig=[v.co.copy() for v in me.vertices]
neighbors=[[] for _ in me.vertices]
for e in me.edges:
    a,b=e.vertices
    neighbors[a].append(b)
    neighbors[b].append(a)

weights=[0.0]*len(me.vertices)
active=[]
max_weight=0.0

for i,p in enumerate(orig):
    x,y,z=p.x,p.y,p.z
    if not (abs(x)<0.38 and -1.06<y<-0.34 and 1.70<z<2.24):
        continue

    wx=1.0-smooth01((abs(x)-0.15)/0.23)
    wy=bump(y,-1.06,-0.72,-0.34)
    wz=bump(z,1.70,1.95,2.24)
    w=wx*wy*wz
    if w<=0.0:
        continue

    pw=body.matrix_world @ p

    dr=nearest_dist(pw,root_bvhs)
    if dr is None:
        raise RuntimeError("Root protection query failed")
    w*=smooth01((dr-0.050)/0.120)
    if w<=0.0:
        continue

    if z>2.10 or y<-0.96:
        dn=nearest_dist(pw,neck_bvhs)
        if dn is None:
            raise RuntimeError("Neck protection query failed")
        w*=smooth01((dn-0.040)/0.085)
        if w<=0.0:
            continue

    border=min(
        smooth01((0.38-abs(x))/0.070),
        smooth01((y+1.06)/0.090),
        smooth01((-0.34-y)/0.090),
        smooth01((z-1.70)/0.075),
        smooth01((2.24-z)/0.075),
    )
    w*=border
    if w<=0.015:
        continue

    weights[i]=w
    active.append(i)
    max_weight=max(max_weight,w)

if not active:
    raise RuntimeError("v11 active set is empty")

active_set=set(active)

# Pass 1: broad shallow lift. Explicit active set only.
max_direct_dy=0.0
max_direct_dz=0.0
for i in active:
    p=orig[i]
    w=weights[i]
    dy=0.026*w
    dz=0.044*w
    me.vertices[i].co.x=p.x
    me.vertices[i].co.y=p.y+dy
    me.vertices[i].co.z=p.z+dz
    max_direct_dy=max(max_direct_dy,dy)
    max_direct_dz=max(max_direct_dz,dz)
me.update()

# Pass 2: explicit local fairing in Y/Z only.
# Neighbors outside the active set act as immutable anchors.
iterations=10
base_factor=0.30
for _ in range(iterations):
    snap=[v.co.copy() for v in me.vertices]
    updates={}
    for i in active:
        ns=neighbors[i]
        if not ns:
            continue
        avg_y=sum(snap[j].y for j in ns)/len(ns)
        avg_z=sum(snap[j].z for j in ns)/len(ns)
        p=snap[i]
        f=base_factor*weights[i]
        ny=p.y+(avg_y-p.y)*f
        nz=p.z+(avg_z-p.z)*f
        updates[i]=(ny,nz)
    for i,(ny,nz) in updates.items():
        me.vertices[i].co.x=orig[i].x
        me.vertices[i].co.y=ny
        me.vertices[i].co.z=nz
    me.update()

if len(me.vertices)!=len(orig):
    raise RuntimeError("Vertex count changed")

changed=[]
max_total_delta=0.0
for i,p0 in enumerate(orig):
    p1=me.vertices[i].co
    if abs(p1.x-p0.x)>1e-12:
        raise RuntimeError(f"X changed at vertex {i}")
    d=(p1-p0).length
    if i not in active_set:
        if d>1e-12:
            raise RuntimeError(f"Non-active vertex moved at {i}: {d}")
    elif d>1e-12:
        changed.append(i)
        max_total_delta=max(max_total_delta,d)

if not changed:
    raise RuntimeError("v11 changed zero vertices")
if any(i not in active_set for i in changed):
    raise RuntimeError("Changed set escaped active set")

body.name="S_organism_blockout_v11"
bpy.context.scene.camera=bpy.data.objects.get("CAM_FRONT34")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"S-blockout-v11.blend"),compress=True)

report={
    "input":"S-blockout-v7.blend",
    "rejected_iterations":["S-blockout-v8.blend","S-blockout-v9.blend","S-blockout-v10.blend"],
    "output":"S-blockout-v11.blend",
    "scope":"explicit-local anterior thorax lift plus manual Y/Z fairing",
    "target_bounds":{"abs_x_lt":0.38,"y":[-1.06,-0.34],"z":[1.70,2.24]},
    "direct_max_displacement":{"y_back":max_direct_dy,"z_up":max_direct_dz},
    "fairing":{"type":"manual_neighbor_average","iterations":iterations,"base_factor":base_factor,"axes":["Y","Z"]},
    "active_vertices":len(active),
    "changed_vertices":len(changed),
    "non_active_vertices_unchanged":len(orig)-len(active),
    "total_vertices":len(orig),
    "max_weight":max_weight,
    "max_total_vertex_delta":max_total_delta,
    "all_changed_vertices_within_active_set":True,
    "all_non_active_vertices_position_unchanged":True,
    "lateral_x_unchanged":True,
    "topology_unchanged":True,
    "vertex_count_unchanged":True,
    "neck_width_reduction_preserved":True,
    "forelimb_and_scapular_roots_protected":True,
    "accepted":False
}
json.dump(report,open(os.path.join(OUT,"thorax-v11-validation.json"),"w"),indent=2)

hp=os.path.join(ROOT,"HANDOFF_STATE.json")
state=json.load(open(hp))
state.update(
    stage="S-blockout-v11",
    current_stage="S-blockout-v11 explicit-local thorax correction saved, review pending",
    current_model_file="output/S-blockout-v11.blend",
    next_action="Inspect v11 front/front34/side against reference 01. Confirm the sternum lobe is reduced without a smile-fold, and verify the unchanged neck/root silhouettes.",
    blockers=[],
    accepted=False
)
json.dump(state,open(hp,"w"),ensure_ascii=False,indent=2)

cp=os.path.join(ROOT,"CHECKPOINT.md")
s=open(cp).read()
lines=[]
for line in s.splitlines():
    if line.startswith("current_stage:"):
        line="current_stage: S-blockout-v11 explicit-local thorax correction saved, review pending"
    elif line.startswith("current_model_file:"):
        line="current_model_file: output/S-blockout-v11.blend"
    elif line.startswith("next_action:"):
        line="next_action: Inspect v11 front/front34/side against reference 01. Confirm the sternum lobe is reduced without a smile-fold, and verify the unchanged neck/root silhouettes."
    lines.append(line)
s="\n".join(lines)+"\n"
if "Applied v11 explicit-local thorax correction" not in s:
    s=s.replace("next_action:","- Applied v11 explicit-local thorax correction from v7 clean baseline. Manual Y/Z fairing touched active vertices only; all non-active vertices and all X coordinates remained unchanged.\n\nnext_action:",1)
open(cp,"w").write(s)

print("S_V11",json.dumps(report))
