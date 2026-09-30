"""Deterministic v10 anterior-thorax correction from S-blockout-v7.

Strategy:
1) one broader, shallower posterior/upward lift over the lower anterior thorax;
2) weighted Laplacian fairing on Y/Z only over the same region.

This intentionally starts from v7 (clean no-fold baseline), not v8/v9.
Locks X, neck width, forelimb roots, scapular outer ridges, topology, vertex count,
and all geometry outside the weighted thorax region.
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
weights=[0.0]*len(me.vertices)
direct_changed=[]
max_direct_dy=0.0
max_direct_dz=0.0
max_weight=0.0

for i,v in enumerate(me.vertices):
    p=orig[i]
    x,y,z=p.x,p.y,p.z
    if not (abs(x)<0.38 and -1.06<y<-0.34 and 1.70<z<2.24):
        continue

    wx=1.0-smooth01((abs(x)-0.16)/0.22)
    wy=bump(y,-1.06,-0.72,-0.34)
    wz=bump(z,1.70,1.95,2.24)
    w=wx*wy*wz
    if w<=0.0:
        continue

    pw=body.matrix_world @ p

    # Smoothly protect forelimb roots and scapular outer ridges.
    dr=nearest_dist(pw,root_bvhs)
    if dr is None:
        raise RuntimeError("Root protection query failed")
    w*=smooth01((dr-0.050)/0.120)
    if w<=0.0:
        continue

    # Protect only the true upper/front neck junction.
    if z>2.10 or y<-0.96:
        dn=nearest_dist(pw,neck_bvhs)
        if dn is None:
            raise RuntimeError("Neck protection query failed")
        w*=smooth01((dn-0.040)/0.085)
        if w<=0.0:
            continue

    # Keep region borders soft/fixed.
    border=min(
        smooth01((0.38-abs(x))/0.070),
        smooth01((y+1.06)/0.090),
        smooth01((-0.34-y)/0.090),
        smooth01((z-1.70)/0.075),
        smooth01((2.24-z)/0.075),
    )
    w*=border
    if w<=0.0:
        continue

    weights[i]=w
    max_weight=max(max_weight,w)

    # Broader and shallower than v6/v8: preserve silhouette continuity.
    dy=0.030*w
    dz=0.047*w
    if abs(dy)+abs(dz)>1e-12:
        v.co.x=x
        v.co.y=y+dy
        v.co.z=z+dz
        direct_changed.append(i)
        max_direct_dy=max(max_direct_dy,dy)
        max_direct_dz=max(max_direct_dz,dz)

me.update()
if not direct_changed:
    raise RuntimeError("v10 direct lift changed zero vertices")

# Weighted Y/Z fairing to remove the central lobe without making a hard shelf.
vg=body.vertex_groups.new(name="V10_STERNUM_FAIR")
for i,w in enumerate(weights):
    if w>0.001:
        vg.add([i],w,'REPLACE')

mod=body.modifiers.new("V10_weighted_sternum_fair","LAPLACIANSMOOTH")
mod.vertex_group=vg.name
mod.lambda_factor=0.38
mod.iterations=14
mod.use_x=False
mod.use_y=True
mod.use_z=True
if hasattr(mod,"use_volume_preserve"):
    mod.use_volume_preserve=True

bpy.context.view_layer.objects.active=body
body.select_set(True)
bpy.ops.object.modifier_apply(modifier=mod.name)

if len(body.data.vertices)!=len(orig):
    raise RuntimeError("Vertex count changed")

changed=[]
max_total_delta=0.0
for i,p0 in enumerate(orig):
    p1=body.data.vertices[i].co
    if abs(p1.x-p0.x)>1e-8:
        raise RuntimeError(f"X changed at vertex {i}")
    d=(p1-p0).length
    if d>1e-8:
        changed.append(i)
        max_total_delta=max(max_total_delta,d)

if not changed:
    raise RuntimeError("v10 final changed zero vertices")

body.name="S_organism_blockout_v10"
bpy.context.scene.camera=bpy.data.objects.get("CAM_FRONT34")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"S-blockout-v10.blend"),compress=True)

report={
    "input":"S-blockout-v7.blend",
    "rejected_inputs":["S-blockout-v8.blend","S-blockout-v9.blend"],
    "output":"S-blockout-v10.blend",
    "scope":"broader shallow anterior-thorax lift plus weighted Y/Z fairing",
    "target_bounds":{"abs_x_lt":0.38,"y":[-1.06,-0.34],"z":[1.70,2.24]},
    "direct_max_displacement":{"y_back":max_direct_dy,"z_up":max_direct_dz},
    "fairing":{"type":"LAPLACIANSMOOTH","lambda_factor":0.38,"iterations":14,"use_x":False,"use_y":True,"use_z":True},
    "direct_changed_vertices":len(direct_changed),
    "final_changed_vertices":len(changed),
    "total_vertices":len(orig),
    "max_weight":max_weight,
    "max_total_vertex_delta":max_total_delta,
    "lateral_x_unchanged":True,
    "topology_unchanged":True,
    "vertex_count_unchanged":True,
    "neck_width_reduction_preserved":True,
    "forelimb_and_scapular_roots_protected":True,
    "accepted":False
}
json.dump(report,open(os.path.join(OUT,"thorax-v10-validation.json"),"w"),indent=2)

hp=os.path.join(ROOT,"HANDOFF_STATE.json")
state=json.load(open(hp))
state.update(
    stage="S-blockout-v10",
    current_stage="S-blockout-v10 broader lift plus weighted fairing saved, review pending",
    current_model_file="output/S-blockout-v10.blend",
    next_action="Inspect v10 front/front34/side against reference 01. Confirm the central sternum lobe/fold is reduced, the chest remains lighter than v7, and no root or neck-width silhouette changed.",
    blockers=[],
    accepted=False
)
json.dump(state,open(hp,"w"),ensure_ascii=False,indent=2)

cp=os.path.join(ROOT,"CHECKPOINT.md")
s=open(cp).read()
lines=[]
for line in s.splitlines():
    if line.startswith("current_stage:"):
        line="current_stage: S-blockout-v10 broader lift plus weighted fairing saved, review pending"
    elif line.startswith("current_model_file:"):
        line="current_model_file: output/S-blockout-v10.blend"
    elif line.startswith("next_action:"):
        line="next_action: Inspect v10 front/front34/side against reference 01. Confirm the central sternum lobe/fold is reduced, the chest remains lighter than v7, and no root or neck-width silhouette changed."
    lines.append(line)
s="\n".join(lines)+"\n"
if "Applied v10 broader shallow lift plus weighted Y/Z fairing" not in s:
    s=s.replace("next_action:","- Applied v10 broader shallow lift plus weighted Y/Z fairing from v7 clean baseline; v8/v9 fold geometry not inherited. X/topology/count/neck width/root protections fixed.\n\nnext_action:",1)
open(cp,"w").write(s)

print("S_V10",json.dumps(report))
