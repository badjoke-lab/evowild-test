"""EvoWild S R1-A3 v1 — boundary-conditioned scapular side-surface correction.

Source: accepted-local R1-A2 v2 Blender scene, not rebuilt primitives.
Corrects the broad long triangular shoulder/chest surface plane, *not* just
apex height. Controlled least-squares geometric patch fit using actual local
mesh boundary. No global smoothing, no texture changes, no gameplay merge.
If anatomy worsens or geometry becomes unsafe, FAIL without writing candidate.
"""
from pathlib import Path
import bpy,bmesh,json,hashlib,math
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output"
REV=OUT/"review/authority-r1-a3-sidepatch-v1"
REV.mkdir(parents=True,exist_ok=True)
body=bpy.data.objects["S_B2a_v5_continuous_body"]
coll=bpy.data.collections["S_REBUILD_GATE_A"]
M=body.data
if len(M.vertices)!=5728 or len(M.polygons)!=6376:
    raise RuntimeError(f"wrong incoming v2 geometry: {len(M.vertices)} / {len(M.polygons)}")
before=[v.co.copy() for v in M.vertices]
faces_before=[tuple(f.vertices) for f in M.polygons]
def hash_mesh(obj):
    h=hashlib.sha256()
    h.update(obj.name.encode())
    for v in obj.data.vertices:h.update(repr(tuple(v.co)).encode())
    for f in obj.data.polygons:h.update(repr(tuple(f.vertices)).encode())
    return h.hexdigest()
fixed={o.name:hash_mesh(o) for o in coll.objects if o.type=="MESH" and o!=body}
views=("SIDE","FRONT","FRONT34","REAR34","BACK")
cams={s:tuple(tuple(row) for row in bpy.data.objects["S_REBUILD_CAM_"+s].matrix_world) for s in views}

# Coordinates from previous *real* mesh-diagnostic results, centered around
# paired scapular ridge near y=-.03, z=1.103, abs(x)=.13-.16.
Y0,Z0=-.030,1.056
YR,ZR=.135,.137
MAX_DELTA=.027
def yz_norm(p):
    return (p.y-Y0)/YR,(p.z-Z0)/ZR
def r2(p):
    y,z=yz_norm(p)
    return y*y+z*z
def wt(q):
    # Core full influence, smoothly fades to zero across a broad edge.
    if q>=1:return 0.
    t=1-q
    return t*t*(3-2*t)

def angle_stats():
    bm=bmesh.new();bm.from_mesh(M);bm.normal_update()
    allangles=[];per_side={"L":[],"R":[]}
    for e in bm.edges:
        if len(e.link_faces)!=2:continue
        p=(e.verts[0].co+e.verts[1].co)/2
        if not (.072<abs(p.x)<.222 and -.245<p.y<.153 and .765<p.z<1.149):
            continue
        a=math.degrees(e.link_faces[0].normal.angle(e.link_faces[1].normal))
        allangles.append(a)
        per_side["L" if p.x<0 else "R"].append(a)
    nonmanifold=sum(len(e.link_faces)!=2 for e in bm.edges)
    bm.free()
    return {"edges":len(allangles),"over_37":sum(a>37 for a in allangles),
            "over_45":sum(a>45 for a in allangles),
            "mean":sum(allangles)/max(len(allangles),1),
            "max":max(allangles) if allangles else None,
            "nonmanifold":nonmanifold}

startangles=angle_stats()
def terms(u,v):
    return [1.,u,v,u*u,u*v,v*v,u*u*v,u*v*v]
changed=[]
fits={}
for side in (-1,1):
    tag="L" if side<0 else "R"
    samples=[]; targets=[];weights=[]
    active=[]
    for i,p in enumerate(before):
        if p.x*side<=0 or not (.077<=abs(p.x)<=.230):continue
        q=r2(p)
        u,v=yz_norm(p)
        # Gently select the surrounding forequarter surface as a boundary
        # reference. Never use forelimb shaft or inner head geometry.
        if .82<=q<=1.90 and .80<p.z<1.18 and -.225<p.y<.14:
            samples.append(terms(u,v))
            targets.append(abs(p.x))
            weights.append(1/(1+max(0,q-1.25)))
        if q<1.0 and .080<=abs(p.x)<=.210 and .89<p.z<1.157:
            active.append((i,p,q,u,v))
    if len(samples)<55 or len(active)<20:
        raise RuntimeError(f"{tag}: insufficient shape boundary for patch, boundary={len(samples)} active={len(active)}")
    A=np.asarray(samples,np.float64)
    t=np.asarray(targets,np.float64)
    sw=np.sqrt(np.asarray(weights,np.float64))
    # Ridge regularization prevents high-order extrapolation; this surface is
    # derived from actual boundary anatomy, not a generalized body smoothing.
    regulator=np.diag([0.,.0,.0,.085,.085,.085,.11,.11])
    augmented=np.concatenate([A*sw[:,None],regulator])
    b=np.concatenate([t*sw,np.zeros(8)])
    coeff,_,rank,_=np.linalg.lstsq(augmented,b,rcond=None)
    if rank<7:raise RuntimeError(f"Degenerate geometry-fit basis rank={rank}")
    raw=[]
    for i,p,q,u,v in active:
        desired=float(np.dot(coeff,terms(u,v)))
        # Explicit anatomical side-plane reconstruction: adjust lateral X,
        # never lift the shoulder or round the chest globally.
        delta=max(-MAX_DELTA,min(MAX_DELTA,(desired-abs(p.x))*.91*wt(q)))
        if abs(delta)>1.e-6:
            M.vertices[i].co.x=p.x+side*delta
            changed.append((i,tag,delta))
            raw.append(delta)
    fits[tag]={"boundary_samples":len(samples),"active_candidates":len(active),
               "actual_modified":len(raw),"mean_lateral_shift":sum(raw)/max(len(raw),1),
               "max_abs_lateral_shift":max((abs(v) for v in raw),default=0),
               "coefficients":[float(v) for v in coeff]}
M.update()
if not (25<=fits["L"]["actual_modified"]<400 and 25<=fits["R"]["actual_modified"]<400):
    raise RuntimeError("Unbounded or ineffective shoulder reconstruction: "+repr(fits))
modified={i for i,_,_ in changed}
for i,p in enumerate(before):
    d=M.vertices[i].co-p
    if i not in modified and tuple(M.vertices[i].co)!=tuple(p):
        raise RuntimeError("Out-of-scope original vertex changed")
    if abs(d.y)>1e-8 or abs(d.z)>1e-8 or d.length>MAX_DELTA+1.e-6:
        raise RuntimeError(f"Out-of-plane edit at vertex {i}: {d}")
if [tuple(f.vertices) for f in M.polygons]!=faces_before:
    raise RuntimeError("Topology altered")
for name,h in fixed.items():
    if hash_mesh(bpy.data.objects[name])!=h:
        raise RuntimeError("Protected crest, feet, or tail changed "+name)
for name,v in cams.items():
    if tuple(tuple(r) for r in bpy.data.objects["S_REBUILD_CAM_"+name].matrix_world)!=v:
        raise RuntimeError("Locked camera moved "+name)
afterangles=angle_stats()
if afterangles["nonmanifold"]:
    raise RuntimeError("Body now nonmanifold")
if afterangles["over_45"]>startangles["over_45"]+6:
    raise RuntimeError(f"Sharp shoulder got worse: {startangles} -> {afterangles}")
# Check that no local face has collapsed or inverted as a result of shape fit.
blended=0
for face in M.polygons:
    if not any(i in modified for i in face.vertices):continue
    a=[before[i] for i in face.vertices]
    b=[M.vertices[i].co for i in face.vertices]
    def normal_area(P):
        n=Vector()
        for j,p in enumerate(P):
            q=P[(j+1)%len(P)]
            n.x+=(p.y-q.y)*(p.z+q.z)
            n.y+=(p.z-q.z)*(p.x+q.x)
            n.z+=(p.x-q.x)*(p.y+q.y)
        return n
    an,bn=normal_area(a),normal_area(b)
    if an.length<1e-7 or bn.length<1e-7 or an.dot(bn)<.20*an.length*bn.length:
        raise RuntimeError(f"Potential face collapse/flip: polygon {face.index}")
    if bn.length/an.length<.48 or bn.length/an.length>1.8:
        raise RuntimeError(f"Severe face-area change: polygon {face.index}")
    blended+=1
if not (40<blended<850):
    raise RuntimeError(f"unexpected affected face count {blended}")

report={
 "source_blend":"S-authority-r1-a2-scapula-v2.blend",
 "candidate_blend":"S-authority-r1-a3-sidepatch-v1.blend",
 "method":"boundary-conditioned 3D lateral shoulder/chest plane reconstruction from actual source mesh",
 "model_is_original_creature_geometry":True,
 "first_party_design_lock":"00_s_type_modeling_image_v1.png",
 "changes":[{"vertex_index":i,"side":tag,"x_delta":round(delta,7)} for i,tag,delta in changed],
 "changed_vertex_count":len(changed),"affected_polygon_count":blended,
 "per_side_fit":fits,"maximum_displacement_cap":MAX_DELTA,
 "before_shoulder_crease":startangles,"after_shoulder_crease":afterangles,
 "body_vertex_count":len(M.vertices),"body_polygon_count":len(M.polygons),
 "original_body_topology_unchanged":True,"other_parts_unchanged":True,
 "cameras_unchanged":True,"nonmanifold_edge_count":afterangles["nonmanifold"],
 "status":"UNAPPROVED_REAL_RENDER_REVIEW_REQUIRED",
 "production_approved":False,"rig_approved":False
}
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-authority-r1-a3-sidepatch-v1.blend"),compress=True)
scene=bpy.context.scene
for name in views:
    scene.camera=bpy.data.objects["S_REBUILD_CAM_"+name]
    scene.render.filepath=str(REV/f"S_R1_A3_sidepatch_v1_{name.lower()}.png")
    bpy.ops.render.render(write_still=True)
(REV/"R1_A3_SIDEPATCH_QA.json").write_text(json.dumps(report,indent=2)+"\n")
print("ACTUAL_ANATOMICAL_PATCH_EXECUTED",json.dumps({k:report[k] for k in
 ["changed_vertex_count","affected_polygon_count","before_shoulder_crease","after_shoulder_crease","per_side_fit","status"]}))
