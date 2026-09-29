"""Deterministic v9 local sternum relax from S-blockout-v8.

Keeps the v8 lighter side-profile position but removes the new front/front34 fold
with a constrained, topology-preserving Laplacian relaxation on Y/Z only.
X, topology, vertex count, neck width, forelimb roots, scapular outer ridges,
region boundaries, and all other areas remain fixed.
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
protected=[False]*len(me.vertices)
active=[]

for i,v in enumerate(me.vertices):
    p=v.co
    x,y,z=p.x,p.y,p.z
    if not (abs(x)<0.30 and -1.00<y<-0.46 and 1.76<z<2.16):
        continue

    wx=1.0-smooth01((abs(x)-0.12)/0.18)
    wy=bump(y,-1.00,-0.75,-0.46)
    wz=bump(z,1.76,1.96,2.16)
    w=wx*wy*wz
    if w<=0.0:
        continue

    pw=body.matrix_world @ p
    dr=nearest_dist(pw,root_bvhs)
    if dr is None:
        raise RuntimeError("Root protection query failed")
    wr=smooth01((dr-0.055)/0.095)
    w*=wr
    if w<=0.0:
        protected[i]=True
        continue

    if z>2.09 or y<-0.94:
        dn=nearest_dist(pw,neck_bvhs)
        if dn is None:
            raise RuntimeError("Neck protection query failed")
        wn=smooth01((dn-0.045)/0.075)
        w*=wn
        if w<=0.0:
            protected[i]=True
            continue

    # Keep explicit region boundaries fixed; only true interior vertices relax.
    boundary=min(
        smooth01((0.30-abs(x))/0.055),
        smooth01((y+1.00)/0.075),
        smooth01((-0.46-y)/0.075),
        smooth01((z-1.76)/0.060),
        smooth01((2.16-z)/0.060),
    )
    w*=boundary
    if w>0.02:
        weights[i]=w
        active.append(i)

if not active:
    raise RuntimeError("No active vertices for v9 relaxation")

iterations=5
base_factor=0.24
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
        me.vertices[i].co.x=snap[i].x
        me.vertices[i].co.y=ny
        me.vertices[i].co.z=nz
    me.update()

changed=[]
max_delta=0.0
for i,p0 in enumerate(orig):
    p1=me.vertices[i].co
    if abs(p1.x-p0.x)>1e-9:
        raise RuntimeError(f"X changed at {i}")
    d=(p1-p0).length
    if d>1e-9:
        changed.append(i)
        max_delta=max(max_delta,d)

if not changed:
    raise RuntimeError("v9 changed zero vertices")
if len(me.vertices)!=len(orig):
    raise RuntimeError("Vertex count changed")

body.name="S_organism_blockout_v9"
bpy.context.scene.camera=bpy.data.objects.get("CAM_FRONT34")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"S-blockout-v9.blend"),compress=True)

report={
    "input":"S-blockout-v8.blend",
    "output":"S-blockout-v9.blend",
    "scope":"local sternum Y/Z surface relaxation only",
    "iterations":iterations,
    "base_factor":base_factor,
    "active_vertices":len(active),
    "changed_vertices":len(changed),
    "total_vertices":len(orig),
    "max_total_vertex_delta":max_delta,
    "lateral_x_unchanged":True,
    "topology_unchanged":True,
    "vertex_count_unchanged":True,
    "neck_width_reduction_preserved":True,
    "forelimb_and_scapular_roots_protected":True,
    "accepted":False
}
json.dump(report,open(os.path.join(OUT,"thorax-v9-validation.json"),"w"),indent=2)

hp=os.path.join(ROOT,"HANDOFF_STATE.json")
state=json.load(open(hp))
state.update(
    stage="S-blockout-v9",
    current_stage="S-blockout-v9 constrained sternum relax saved, review pending",
    current_model_file="output/S-blockout-v9.blend",
    next_action="Inspect v9 front/front34/side against reference 01. Confirm the v8 sternum fold is reduced without restoring the old hanging chest bulge or altering neck width/root silhouettes.",
    blockers=[],
    accepted=False
)
json.dump(state,open(hp,"w"),ensure_ascii=False,indent=2)

cp=os.path.join(ROOT,"CHECKPOINT.md")
s=open(cp).read()
lines=[]
for line in s.splitlines():
    if line.startswith("current_stage:"):
        line="current_stage: S-blockout-v9 constrained sternum relax saved, review pending"
    elif line.startswith("current_model_file:"):
        line="current_model_file: output/S-blockout-v9.blend"
    elif line.startswith("next_action:"):
        line="next_action: Inspect v9 front/front34/side against reference 01. Confirm the v8 sternum fold is reduced without restoring the old hanging chest bulge or altering neck width/root silhouettes."
    lines.append(line)
s="\n".join(lines)+"\n"
if "Applied v9 constrained Y/Z sternum relaxation" not in s:
    s=s.replace("next_action:","- Applied v9 constrained Y/Z sternum relaxation from v8: five weighted local iterations, X/topology/count/neck width/root protections and boundaries fixed.\n\nnext_action:",1)
open(cp,"w").write(s)

print("S_V9",json.dumps(report))
