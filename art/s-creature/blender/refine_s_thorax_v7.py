"""Deterministic v7 anterior-thorax correction from accepted v5 baseline.

v6 is intentionally discarded because its narrow central field plus protection mask
created a visible horizontal smile-crease in front/front34.

v7 broadens the thorax field, lowers peak displacement, preserves X/topology/count,
protects forelimb/scapular roots, and protects only the true upper neck junction.
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
root_bvhs=[make_bvh(o) for o in root_objs]
root_bvhs=[b for b in root_bvhs if b is not None]
neck_bvhs=[make_bvh(o) for o in neck_objs]
neck_bvhs=[b for b in neck_bvhs if b is not None]
if not root_bvhs or not neck_bvhs:
    raise RuntimeError("Required protection BVHs missing")

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
max_w=0.0
min_root_d=None
min_neck_d=None

for i,v in enumerate(body.data.vertices):
    p=v.co.copy()
    x,y,z=p.x,p.y,p.z
    if not (abs(x)<0.32 and -1.02<y<-0.40 and 1.72<z<2.22):
        continue

    wx=1.0-smooth01((abs(x)-0.14)/0.18)
    w=wx*bump(y,-1.02,-0.74,-0.40)*bump(z,1.72,1.96,2.22)
    if w<=0.0:
        continue

    pw=body.matrix_world @ p

    # Keep forelimb roots and outer scapular ridges fixed with a smooth buffer.
    dr=nearest_dist(pw,root_bvhs)
    if dr is None:
        raise RuntimeError("Root protection query failed")
    min_root_d=dr if min_root_d is None else min(min_root_d,dr)
    w*=smooth01((dr-0.045)/0.090)
    if w<=0.0:
        continue

    # Protect only the actual upper neck junction. Do not let neck protection
    # cut a horizontal band through the lower chest as happened in v6.
    if z>2.10 or y<-0.94:
        dn=nearest_dist(pw,neck_bvhs)
        if dn is None:
            raise RuntimeError("Neck protection query failed")
        min_neck_d=dn if min_neck_d is None else min(min_neck_d,dn)
        w*=smooth01((dn-0.040)/0.070)
        if w<=0.0:
            continue

    p2=p.copy()
    p2.x=x
    p2.y=y+0.040*w
    p2.z=z+0.060*w
    v.co=p2
    changed.append(i)
    max_w=max(max_w,w)

body.data.update()
if not changed:
    raise RuntimeError("v7 changed zero vertices")
if len(body.data.vertices)!=len(original):
    raise RuntimeError("Vertex count changed")

changed_set=set(changed)
for i,p0 in enumerate(original):
    p1=body.data.vertices[i].co
    if abs(p1.x-p0.x)>1e-9:
        raise RuntimeError(f"X changed at {i}")
    if i not in changed_set and (p1-p0).length>1e-9:
        raise RuntimeError(f"Unexpected non-target change at {i}")

body.name="S_organism_blockout_v7"
scene=bpy.context.scene
scene.camera=bpy.data.objects.get("CAM_FRONT34")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"S-blockout-v7.blend"),compress=True)

report={
    "input":"S-blockout-v5.blend",
    "discarded_iteration":"S-blockout-v6.blend",
    "output":"S-blockout-v7.blend",
    "scope":"broader shallower anterior thorax lower-front correction",
    "target_bounds":{"abs_x_lt":0.32,"y":[-1.02,-0.40],"z":[1.72,2.22]},
    "max_displacement":{"y_back":0.040,"z_up":0.060},
    "changed_vertices":len(changed),
    "total_vertices":len(original),
    "max_weight":max_w,
    "root_protection_objects":len(root_bvhs),
    "neck_protection_objects":len(neck_bvhs),
    "min_root_distance_seen":min_root_d,
    "min_neck_distance_seen":min_neck_d,
    "lateral_x_unchanged":True,
    "topology_unchanged":True,
    "vertex_count_unchanged":True,
    "neck_width_reduction_preserved":True,
    "v6_smile_crease_not_inherited":True,
    "accepted":False
}
json.dump(report,open(os.path.join(OUT,"thorax-v7-validation.json"),"w"),indent=2)

hp=os.path.join(ROOT,"HANDOFF_STATE.json")
state=json.load(open(hp))
state.update(
    stage="S-blockout-v7",
    current_stage="S-blockout-v7 broader anterior thorax correction saved, review pending",
    current_model_file="output/S-blockout-v7.blend",
    next_action="Inspect v7 side/front/front34 against reference 01. Specifically confirm the v6 smile-crease is gone and the anterior thorax no longer hangs as a rounded lower bulge.",
    blockers=[],
    accepted=False
)
json.dump(state,open(hp,"w"),ensure_ascii=False,indent=2)

cp=os.path.join(ROOT,"CHECKPOINT.md")
s=open(cp).read()
lines=[]
for line in s.splitlines():
    if line.startswith("current_stage:"):
        line="current_stage: S-blockout-v7 broader anterior thorax correction saved, review pending"
    elif line.startswith("current_model_file:"):
        line="current_model_file: output/S-blockout-v7.blend"
    elif line.startswith("next_action:"):
        line="next_action: Inspect v7 side/front/front34 against reference 01. Specifically confirm the v6 smile-crease is gone and the anterior thorax no longer hangs as a rounded lower bulge."
    lines.append(line)
s="\n".join(lines)+"\n"
if "Applied v7 broader thorax correction from v5 baseline" not in s:
    s=s.replace("next_action:","- Applied v7 broader thorax correction from v5 baseline; v6 was not used as input. Field widened laterally and displacement reduced to avoid the central smile-crease while keeping X/topology/count/neck width/root protections fixed.\n\nnext_action:",1)
open(cp,"w").write(s)

print("S_V7",json.dumps(report))
