"""EvoWild Run S type: true-QEM core with sewn swept volumetric armor O.

Starts from zero-tail-intersection 24-seam M (not the rejected bumpy N).
For each selected SKIN PATCH on M, carve a single connected hole, replace
it with a multi-ring tapered leaf (one closed volume, all faces continuous).
No disconnected/proxy meshes, no billboard, no C-F squared caps. Do not
inherit any rig or S visual approval. Exact reference and QEM donor locked.
"""
import bpy,bmesh,math,json,hashlib,os,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
NAME=os.environ.get("Q_PANEL_NAME","")
assert NAME in ("PROXIMAL_RIGHT","MID_LEFT","DISTAL_RIGHT"),NAME
OUT=BASE/("tail-panel-isolation-q-"+NAME.lower())
REVIEW=OUT/"review"
REVIEW.mkdir(parents=True,exist_ok=True)
REF=ROOT/"references/00_s_type_modeling_image_v1.png"
DONOR=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
REF_SHA="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
DONOR_SHA="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
assert hashlib.sha256(REF.read_bytes()).hexdigest()==REF_SHA
assert hashlib.sha256(DONOR.read_bytes()).hexdigest()==DONOR_SHA
src=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
original_a=bpy.data.objects["S_QEM_TAIL_MORPH_TEST_A_NOT_APPROVED"]
M=bpy.data.objects["S_REAL_QEM_UNIFORM_ANGULAR_TAIL_M_NOT_APPROVED"]
assert len(src.data.vertices)==29948 and len(src.data.polygons)==59932
assert len(M.data.vertices)==31948 and len(M.data.polygons)==63932
scene=bpy.context.scene
scene.frame_set(1)

def xyz(ob):
    bpy.context.view_layer.update()
    target=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=target.to_mesh()
    try:return np.array([target.matrix_world@v.co for v in mesh.vertices],dtype=np.float64)
    finally:target.to_mesh_clear()

srcxyz=xyz(src);mxyz=xyz(M)
src_digest=hashlib.sha256(srcxyz.tobytes()).hexdigest()
m_digest=hashlib.sha256(mxyz.tobytes()).hexdigest()
out=M.copy()
out.data=M.data.copy()
out.name="S_QEM_Q_SINGLE_SEWN_LEAF_"+NAME+"_NOT_APPROVED"
scene.collection.objects.link(out)
out.matrix_world=M.matrix_world.copy()
mw=out.matrix_world.copy();inv=mw.inverted()
bm=bmesh.new()
bm.from_mesh(out.data)
bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.faces.ensure_lookup_table()
initial=list(bm.faces)
ROOT_Y=1.64
TAIL_LEN=1.97
ROOT_Z=1.599118232727
ROOT_X=.008617273531

def smooth(v):
    x=max(0.,min(1.,float(v)))
    return x*x*(3.-2.*x)
def angle_difference(a,b):
    return abs((a-b+math.pi)%(2*math.pi)-math.pi)
def frame(y):
    t=max(0.,min(1.,(y-ROOT_Y)/TAIL_LEN))
    return Vector((ROOT_X+.032*math.sin(math.pi*t),
                   y,
                   ROOT_Z+.065*math.sin(math.pi*t)-.33*t-.12*t*t))
def center(f):
    return mw@(sum((v.co for v in f.verts),Vector())/len(f.verts))
def angle(f):
    p=center(f);fc=frame(p.y)
    return math.atan2(p.z-fc.z,p.x-fc.x)
def islands(fs):
    rest=set(fs);out=[]
    while rest:
        root=rest.pop();group={root};stack=[root]
        while stack:
            f=stack.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g in rest:
                        rest.remove(g);group.add(g);stack.append(g)
        out.append(group)
    return sorted(out,key=len,reverse=True)
def winding_loop(fs):
    fs=set(fs)
    links=[]
    for f in fs:
        v=list(f.verts)
        for i in range(len(v)):
            a,b=v[i],v[(i+1)%len(v)]
            e=bm.edges.get((a,b))
            if sum(neighbor in fs for neighbor in e.link_faces)==1:
                links.append((a,b))
    succ={}
    for a,b in links:
        if a in succ:return [],len(links),"multiple_next"
        succ[a]=b
    if len(links)<8:return [],len(links),"too_short"
    ordered=[links[0][0]]
    seen=set(ordered)
    cur=ordered[0]
    while True:
        if cur not in succ:return [],len(links),"open"
        cur=succ[cur]
        if cur==ordered[0]:break
        if cur in seen:return [],len(links),"cycle_duplicate"
        seen.add(cur);ordered.append(cur)
    if len(links)!=len(ordered):return [],len(links),"multi_loop"
    return ordered,len(links),"SINGLE_CLOSED"

# Substantial side-profile leaves rather than radially raised roof bumps.
# Each root on ACTUAL M shell. Separation chosen to permit independent
# collision inspection and avoid fabricating 5 overlapping self-piercing fins.
plans=[
 {"name":"PROXIMAL_RIGHT","y0":1.79,"y1":1.91,
  "angle":.40,"angular_halfwidth":.59,"length":.59,"spread":.19,"rise":.12,"blade_width":.13},
 {"name":"MID_LEFT","y0":2.17,"y1":2.31,
  "angle":2.63,"angular_halfwidth":.57,"length":.68,"spread":.18,"rise":.10,"blade_width":.14},
 {"name":"DISTAL_RIGHT","y0":2.63,"y1":2.75,
  "angle":.52,"angular_halfwidth":.56,"length":.64,"spread":.15,"rise":.07,"blade_width":.11}
]
plans=[p for p in plans if p['name']==NAME]
assert len(plans)==1
choices=[]
all_members=set()
for plan in plans:
    eligible=[f for f in initial if
        plan["y0"]<center(f).y<plan["y1"]
        and angle_difference(angle(f),plan["angle"])<plan["angular_halfwidth"]]
    comp=islands(eligible)
    assert comp and len(comp[0])>=10,(plan["name"],len(eligible),[len(x) for x in comp[:4]])
    patch=set(comp[0])
    assert not patch&all_members,("overlapping patches",plan["name"])
    loop,edge_count,status=winding_loop(patch)
    assert status=="SINGLE_CLOSED",(plan["name"],status,edge_count)
    assert 8<=len(loop)<=80,(plan["name"],len(loop))
    choices.append((plan,patch,loop,{"candidate_face_count":len(eligible),
        "patch_faces":len(patch),"root_boundary_vertices":len(loop),"other_islands":[len(x) for x in comp[1:4]]}))
    all_members.update(patch)

# Run targeted modeling as a true sewn manifold from original QEM-supported
# tail, with arclength mapping to avoid folding irregular loops at the root.
plate_specs=[]
for plan,patch,loop,scan in choices:
    assert all(f.is_valid for f in patch)
    loop,_,status=winding_loop(patch)
    assert status=="SINGLE_CLOSED"
    pts=[mw@v.co for v in loop]
    n=len(loop)
    root_center=sum(pts,Vector())/n
    theta=plan["angle"]
    nrad=Vector((math.cos(theta),0.,math.sin(theta)))
    tangent=Vector((-math.sin(theta),0.,math.cos(theta)))
    side_sign=1 if math.cos(theta)>=0 else -1
    # Plane orientation is controlled by loop perimeter direction. Consistent
    # corresponding 3D rings; construct continuous thin flattened blades.
    edge_lengths=[(pts[(i+1)%n]-pts[i]).length for i in range(n)]
    perimeter=sum(edge_lengths)
    cumulative=[0.]
    for edge in edge_lengths[:-1]:
        cumulative.append(cumulative[-1]+edge)
    angles=[2*math.pi*q/perimeter for q in cumulative]
    oldverts={v for f in patch for v in f.verts}
    for f in list(patch):bm.faces.remove(f)
    prev=loop
    lengths=[.07,.13,.22,.34,.47,.60,.73,.84,.92,.965]
    for t in lengths:
        # Spine progressively moves AWAY from underlying QEM tube surface.
        # The root perimeter itself remains 100% source-preserved.
        center_pt=(root_center+Vector((0.,plan["length"]*t,0.))
            +nrad*(plan["spread"]*smooth(t/.42))
            +Vector((0.,0.,plan["rise"]*t)))
        width=plan["blade_width"]*max(.018,math.sin(math.pi*t)**.80)
        depth=.023*max(.03,math.sin(math.pi*t)**.68)
        alpha=smooth(t/.15)
        ring=[]
        for i,q in enumerate(angles):
            desired=center_pt+tangent*(width*math.cos(q))+nrad*(depth*math.sin(q))
            # Sidewall smoothly transforms the source boundary into a blade
            # cross section, no disjoint duplicated closed tips.
            matching=pts[i]+Vector((0,plan["length"]*t,0))
            p=matching*(1-alpha)+desired*alpha
            ring.append(bm.verts.new(inv@p))
        for i in range(n):
            j=(i+1)%n
            bm.faces.new((prev[i],prev[j],ring[j],ring[i]))
        prev=ring
    tip_world=root_center+Vector((0.,plan["length"],plan["rise"]))+nrad*plan["spread"]
    tip=bm.verts.new(inv@tip_world)
    for i in range(n):
        bm.faces.new((prev[i],prev[(i+1)%n],tip))
    for v in oldverts:
        if v.is_valid and len(v.link_faces)==0:bm.verts.remove(v)
    scan.update({"name":plan["name"],"root_center_world":list(root_center),
        "tip_world":list(tip_world),
        "shell_side":side_sign,"sweep_length":plan["length"],
        "lateral_clearance":plan["spread"],"blade_half_width":plan["blade_width"],
        "ring_count":len(lengths),"ring_boundary_vertices":n})
    plate_specs.append(scan)

for e in list(bm.edges):
    if e.is_valid and len(e.link_faces)==0:bm.edges.remove(e)
bm.faces.ensure_lookup_table()
bmesh.ops.triangulate(bm,faces=list(bm.faces))
bm.normal_update()
bm.to_mesh(out.data);bm.free()
out.data.update()
actual=xyz(out)
assert np.isfinite(actual).all()
assert hashlib.sha256(xyz(src).tobytes()).hexdigest()==src_digest
assert hashlib.sha256(xyz(M).tobytes()).hexdigest()==m_digest

tris=np.array([tuple(f.vertices) for f in out.data.polygons],dtype=np.int32)
vertex_count=len(actual)
edges={}
neighbors=[[] for _ in range(vertex_count)]
arr=actual[tris]
face2area=np.linalg.norm(np.cross(arr[:,1]-arr[:,0],arr[:,2]-arr[:,0]),axis=1)
for ids in tris:
    v0,v1,v2=map(int,ids)
    for a,b in ((v0,v1),(v1,v2),(v2,v0)):
        x=(min(a,b),max(a,b))
        edges[x]=edges.get(x,0)+1
        neighbors[a].append(b);neighbors[b].append(a)
seen=set();comps=[]
for i in range(vertex_count):
    if i in seen:continue
    stack=[i];seen.add(i);size=0
    while stack:
        j=stack.pop();size+=1
        for k in neighbors[j]:
            if k not in seen:seen.add(k);stack.append(k)
    comps.append(size)
comps.sort(reverse=True)
geometry={
 "vertices":vertex_count,"triangles":len(tris),"components":len(comps),
 "largest_components":comps[:10],
 "boundary_edges":sum(v==1 for v in edges.values()),
 "nonmanifold_or_boundary_edges":sum(v!=2 for v in edges.values()),
 "degenerate_faces":int(np.sum(face2area<1.e-10)),
 "minimum_double_triangle_area":float(face2area.min()),
 "maximum_double_triangle_area":float(face2area.max())
}
cent=arr.mean(axis=1)
roi=(cent[:,1]>1.50)&(cent[:,2]>.94)&(abs(cent[:,0])<.7)
indices=np.flatnonzero(roi)
faces=[tuple(map(int,tris[i])) for i in indices]
tree=BVHTree.FromPolygons([Vector(v) for v in actual],faces,
                          all_triangles=True,epsilon=1.e-7)
collisions=[]
for i,j in tree.overlap(tree):
    if i>=j:continue
    if set(faces[i])&set(faces[j]):continue
    collisions.append((int(indices[i]),int(indices[j])))
collisions.sort()
collision_qa={"tested_roi_faces":len(faces),"nonshared_polygon_intersections":len(collisions),
              "first_60_polygon_pairs":collisions[:60]}
technical_ok=(geometry["components"]==1 and geometry["nonmanifold_or_boundary_edges"]==0
              and geometry["degenerate_faces"]==0 and len(collisions)==0)

result={
 "authoritative_S_reference_sha256":REF_SHA,
 "original_QEM_donor_sha256":DONOR_SHA,
 "original_QEM_untouched":True,"original_M_untouched":True,
 "original_QEM_vertices":29948,"original_QEM_triangles":59932,
 "M_core_vertices":31948,"M_core_triangles":63932,
 "new_S_skin_connected_armor_plate_count":len(plate_specs),
 "isolation_panel":NAME,
 "blades":plate_specs,"topology":geometry,"tail_roi_self_intersection":collision_qa,
 "geometry_gate":"PASS_CONNECTED_NO_TAIL_INTERSECTION" if technical_ok else "FAIL_TOPOLOGY_OR_INTERSECTION",
 "canonical_S_visual_review":"NOT_APPROVED_REQUIRES_ACTUAL_VISUAL_INSPECTION",
 "armature_transferred":False,"foot_contact_3_cycle_verified":False,
 "production_game_approved":False
}
(OUT/"REAL_QEM_Q_SINGLE_ARMOR_PANEL_QA.json").write_text(json.dumps(result,indent=2)+"\n")
print("REAL_QEM_O_TECHNICAL",result["geometry_gate"],"topology",geometry,
      "overlapping_faces",len(collisions),"patches",plate_specs)

# Blender renders, not new AI concept art. Original camera poses fixed.
camera=scene.camera
assert camera and camera.type=="CAMERA"
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.render.resolution_x=1080
scene.render.resolution_y=810
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
camera.data.type="ORTHO"
views={
 "SIDE":Vector((1,0,0)), "FRONT":Vector((0,-1,0)),
 "FRONT34":Vector((1,-1,0)).normalized(),
 "REAR34":Vector((1,1,0)).normalized(), "BACK":Vector((0,1,0))
}
for name,vec in views.items():
    p=Vector((0,.20,1.25))
    camera.data.ortho_scale=6.5
    camera.location=p+vec*9
    camera.rotation_euler=(p-camera.location).to_track_quat("-Z","Y").to_euler()
    for title,obj in (("BASE_M",M),("SINGLE_Q",out)):
        for x in (src,original_a,M,out):x.hide_render=(x!=obj)
        scene.render.filepath=str(REVIEW/f"REAL_QEM_{title}_{name}.png")
        bpy.ops.render.render(write_still=True)
for name,vec in (("SIDE",Vector((1,0,0))),
                 ("FRONT34",Vector((1,-1,0)).normalized()),
                 ("REAR34",Vector((1,1,0)).normalized())):
    p=Vector((0,2.35,1.36))
    camera.data.ortho_scale=2.95
    camera.location=p+vec*6
    camera.rotation_euler=(p-camera.location).to_track_quat("-Z","Y").to_euler()
    for title,obj in (("BASE_M",M),("ARMOR_O",out)):
        for x in (src,original_a,M,out):x.hide_render=(x!=obj)
        scene.render.filepath=str(REVIEW/f"REAL_QEM_CLOSE_{title}_{name}.png")
        bpy.ops.render.render(write_still=True)
for ob in (src,original_a,M):ob.hide_render=True
out.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-single-panel-Q-"+NAME+".blend"),compress=True)
print("O_FINAL_GATE",result["geometry_gate"],"real_blades",len(plate_specs))
