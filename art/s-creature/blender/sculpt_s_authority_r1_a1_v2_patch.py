"""S-type R1-A1 v2: true restricted quad-patch retopology and curvature fairing.

SOURCE: accepted S-authority-r0-a5-v2.blend. NOT the rejected R1A1v1.
This is a single bounded trial; no production promotion.
Existing R0 head/crest/limb shafts/feet/tail and 5 cameras are locked.
"""
import bpy,bmesh,os,math,json,hashlib
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"output")
REV=os.path.join(OUT,"review","authority-r1-a1-v2-topology")
os.makedirs(REV,exist_ok=True)
body=bpy.data.objects["S_B2a_v5_continuous_body"]
cage=bpy.data.collections["S_REBUILD_GATE_A"]
mesh=body.data
def clamp01(x):return max(0.0,min(1.0,x))
def ease(x):
    t=clamp01(x);return t*t*(3.-2.*t)
def axis(v,a,b,c,d):
    if v<=a or v>=d:return 0.
    if b<=v<=c:return 1.
    if v<b:return ease((v-a)/(b-a))
    return ease((d-v)/(d-c))
def rw(p):
    x=abs(p.x)
    lateral=axis(x,.045,.085,.205,.245)
    z=axis(p.z,.575,.645,1.058,1.155)
    fore=axis(p.y,-.24,-.14,.160,.30)
    hind=axis(p.y,.52,.63,.925,1.055)
    return min(lateral,z,max(fore,hind))
# Exact locks outside the main body.
fixed_meshes={}
for o in cage.objects:
    if o.type=="MESH" and o!=body:
        fixed_meshes[o.name]=hashlib.sha256(repr([
          [tuple(v.co) for v in o.data.vertices],
          [tuple(f.vertices) for f in o.data.polygons]]).encode()).hexdigest()
cam_before={name:tuple(tuple(row) for row in bpy.data.objects["S_REBUILD_CAM_"+name].matrix_world)
            for name in ("SIDE","FRONT","FRONT34","REAR34","BACK")}
count_before=len(mesh.vertices);faces_before=len(mesh.polygons)

bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table();bm.normal_update()
original={v:v.co.copy() for v in bm.verts}
all_orig_vertices=list(bm.verts)

# Fingerprint original sharp physical angles to locate actual stepped root.
sharp={v:0.0 for v in all_orig_vertices}
def region_angles(obj):
    obj.normal_update()
    edge_angles=[]
    for e in obj.edges:
        if len(e.link_faces)!=2:continue
        p=(e.verts[0].co+e.verts[1].co)/2
        if rw(p)<=.12:continue
        a=e.link_faces[0].normal.angle(e.link_faces[1].normal)*180/math.pi
        edge_angles.append(a)
    edge_angles.sort()
    return {
      "count":len(edge_angles),
      "gt_60":sum(a>60 for a in edge_angles),
      "gt_90":sum(a>90 for a in edge_angles),
      "p90":edge_angles[min(len(edge_angles)-1,int(.9*len(edge_angles)))] if edge_angles else None
    }
angles_before=region_angles(bm)
for e in bm.edges:
    if len(e.link_faces)!=2:continue
    p=(e.verts[0].co+e.verts[1].co)/2
    if rw(p)<=.05:continue
    angle=e.link_faces[0].normal.angle(e.link_faces[1].normal)*180/math.pi
    score=ease((angle-35)/65)
    for v in e.verts:sharp[v]=max(sharp[v],score)
# Local face splits change the topology in two small support volumes.
# Re-topologize quads only around the actual region, not arbitrary outer body.
candidate_edges=[e for e in bm.edges
          if len(e.link_faces)==2
          and rw((e.verts[0].co+e.verts[1].co)/2)>.55
          and rw(e.verts[0].co)>.42
          and rw(e.verts[1].co)>.42]
# The joint zones contain >4k edges, but only the sharpest 1600
# are needed for the local topology test; do not indiscriminately split all.
selected=sorted(candidate_edges,
  key=lambda e:max(sharp.get(e.verts[0],0.),sharp.get(e.verts[1],0.))
     *rw((e.verts[0].co+e.verts[1].co)/2),reverse=True)[:1600]
if not (100<=len(selected)<=2800):
    raise RuntimeError(f"unsafe retopology edge budget {len(selected)}")
ret=bmesh.ops.subdivide_edges(bm,edges=selected,cuts=1,use_grid_fill=True)
bm.verts.ensure_lookup_table()
new_vertices=[v for v in bm.verts if v not in original]
if not (100<=len(new_vertices)<=6000):
    raise RuntimeError(f"unsafe new vertex count {len(new_vertices)}")
# High-angle guided local surface correction: unlike previous four Taubin
# cycles this rebuild introduces NEW quad control vertices within the patch.
# No negative Taubin expansion, no global Laplacian modifier.
weights={}
for v in bm.verts:
    spatial=rw(v.co)
    if v in original:
        feature=.28+.72*sharp.get(v,0.)
        weights[v]=spatial*feature
    else:
        weights[v]=.84*spatial
active=[v for v,w in weights.items() if w>.055]
assert len(active)>500,len(active)
orig_anchor={v:v.co.copy() for v in bm.verts}
CAP=.045
passes=18
max_move=0.0
for it in range(passes):
    bm.normal_update()
    update={}
    for v in active:
        neighbor=[e.other_vert(v) for e in v.link_edges]
        if len(neighbor)<3:continue
        avg=sum((n.co for n in neighbor),Vector())/len(neighbor)
        lap=avg-v.co
        # Sculpt along the surface's normal curvature, with a limited
        # tangential correction to untangle facet directions at joints.
        n=v.normal.normalized()
        parallel=n*lap.dot(n)
        tangent=lap-parallel
        displacement=(parallel*.86+tangent*.14)*(0.42*weights[v])
        p=v.co+displacement
        drift=p-orig_anchor[v]
        if drift.length>CAP:
            p=orig_anchor[v]+drift.normalized()*CAP
        update[v]=p
    for v,p in update.items():v.co=p
# All original vertices outside support are EXACTLY locked.
for v,pos in original.items():
    if rw(pos)==0 and tuple(v.co)!=tuple(pos):
        raise RuntimeError(f"OUTSIDE_ROI_VERTEX_MOVED index={v.index}")
old_changed=sum((v.co-pos).length>1e-7 for v,pos in original.items())
max_original_displacement=max((v.co-pos).length for v,pos in original.items())
max_new_displacement=max((v.co-orig_anchor[v]).length for v in new_vertices)
if not (old_changed>=120 and max_original_displacement<=CAP+1e-6):
    raise RuntimeError(f"model edit size invalid {old_changed}/{max_original_displacement}")
angles_after=region_angles(bm)
before_nonmanifold=0
nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
if nonmanifold:
    raise RuntimeError(f"PATCH_NOT_MANIFOLD {len(nonmanifold)}")
if angles_after["gt_90"]>angles_before["gt_90"]*1.3+3:
    raise RuntimeError(f"WORSE_90_DEG_EDGES: {angles_before} -> {angles_after}")
bm.to_mesh(mesh);bm.free()
mesh.update()
smooth_polygon_count=0
# Per-face normals are softened only around explicitly modified junctions.
# This is a secondary shading improvement, not a substitute for mesh repair.
for p in mesh.polygons:
    if rw(p.center)>.08:
        p.use_smooth=True
        smooth_polygon_count+=1
# Locked crest, feet, and separate tail meshes are bit-exact.
for name,h in fixed_meshes.items():
    o=bpy.data.objects[name]
    now=hashlib.sha256(repr([
       [tuple(v.co) for v in o.data.vertices],
       [tuple(f.vertices) for f in o.data.polygons]]).encode()).hexdigest()
    assert h==now,name
for name,m in cam_before.items():
    assert tuple(tuple(row) for row in bpy.data.objects["S_REBUILD_CAM_"+name].matrix_world)==m
def bbox(points):
    return [tuple(min(v[i] for v in points) for i in range(3)),
            tuple(max(v[i] for v in points) for i in range(3))]
box0=bbox(list(original.values()))
box1=bbox([v.co for v in mesh.vertices])
max_box_drift=max(abs(box0[k][i]-box1[k][i]) for i in range(3) for k in range(2))
if max_box_drift>.028:raise RuntimeError(f"bbox drift {max_box_drift}")
report={
 "status":"REVIEW_PENDING",
 "source":"S-authority-r0-a5-v2.blend",
 "candidate":"S-authority-r1-a1-v2-patch.blend",
 "scope":"restricted shoulder/proximal foreleg and pelvis/proximal hindleg anatomical quad-patch remodel",
 "technique":"local BMesh edge split with two support ROIs; high-dihedral weighted bi-component curvature sculpt",
 "modified_original_vertices":old_changed,
 "original_vertex_count":count_before,
 "original_face_count":faces_before,
 "new_vertex_count":len(new_vertices),
 "new_mesh_vertex_count":len(mesh.vertices),
 "new_face_count":len(mesh.polygons),
 "replaced_edge_count":len(selected),
 "active_sculpt_vertices":len(active),
 "sculpt_iterations":passes,
 "original_max_displacement":max_original_displacement,
 "new_vertex_max_displacement":max_new_displacement,
 "max_allowed_displacement":CAP,
 "outside_support_old_vertices_unchanged":True,
 "separate_crest_tail_foot_meshes_bit_exact":True,
 "cameras_exact":True,
 "nonmanifold_edge_count":0,
 "original_angles":angles_before,
 "repaired_angles":angles_after,
 "smooth_shaded_patch_faces":smooth_polygon_count,
 "bbox_max_drift":max_box_drift,
 "production_gate":"NOT_APPROVED_PENDING_REAL_FIVE_VIEW",
 "rigging_ready":False
}
with open(os.path.join(OUT,"S-authority-r1-a1-v2-patch-validation.json"),"w") as f:json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,report["candidate"]),compress=True)
scene=bpy.context.scene
for view in ("side","front","front34","rear34","back"):
    scene.camera=bpy.data.objects["S_REBUILD_CAM_"+view.upper()]
    scene.render.filepath=os.path.join(REV,f"S_R1_A1_v2_{view}.png")
    bpy.ops.render.render(write_still=True)
print("S_R1_A1_V2_PATCH_ACTUAL_MESH",json.dumps(report))
