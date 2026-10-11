"""EvoWild Run / S: actual QEM tail TOTAL-CORE replacement L (UNAPPROVED).

Do not paste feathers or reshape failed G-J forks. Cut the verified single
24-edge tail trunk cross-section on the REAL immutable QEM. Rebuild one
continuous 3-D manifold swept feathered tube directly from the genuine open
skin loop with a radial five-groove/feather profile, not separate fin objects.
All assertions are measured on evaluated Blender mesh. The S design and rig
remain unapproved unless visual and collision gates independently PASS.
"""
from pathlib import Path
import bpy,bmesh,math,hashlib,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"tail-core-regularized-m-v1"
REV=OUT/"review"
REV.mkdir(parents=True,exist_ok=True)
R=ROOT/"references/00_s_type_modeling_image_v1.png"
G=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
HREF="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
HDON="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
assert hashlib.sha256(R.read_bytes()).hexdigest()==HREF
assert hashlib.sha256(G.read_bytes()).hexdigest()==HDON
s=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
a=bpy.data.objects["S_QEM_TAIL_MORPH_TEST_A_NOT_APPROVED"]
assert len(s.data.vertices)==29948 and len(s.data.polygons)==59932
assert len(a.data.vertices)==29948
def evalxyz(o):
    bpy.context.view_layer.update()
    eo=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m=eo.to_mesh()
    try:return np.asarray([eo.matrix_world@v.co for v in m.vertices],dtype=np.float64)
    finally:eo.to_mesh_clear()
source=evalxyz(s)
source_sig=hashlib.sha256(source.tobytes()).hexdigest()
out=s.copy()
out.data=s.data.copy()
out.name="S_REAL_QEM_UNIFORM_ANGULAR_TAIL_M_NOT_APPROVED"
bpy.context.scene.collection.objects.link(out)
out.matrix_world=s.matrix_world.copy()
mw=out.matrix_world.copy()
inv=mw.inverted()
bm=bmesh.new()
bm.from_mesh(out.data)
bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.faces.ensure_lookup_table()
faces=list(bm.faces)
def ctr(f):
    return mw@(sum((v.co for v in f.verts),Vector())/len(f.verts))
def connected_groups(fs):
    left=set(fs);out=[]
    while left:
        start=left.pop();group={start};stack=[start]
        while stack:
            f=stack.pop()
            for e in f.edges:
                for x in e.link_faces:
                    if x in left:
                        left.remove(x);group.add(x);stack.append(x)
        out.append(group)
    return sorted(out,key=lambda gg:max(ctr(f).y for f in gg),reverse=True)

# Use actual pre-tested K scan: ycut1.58 zfloor1.32 xlim0.30 -> one closed
# 24-edge tail skin boundary. NEVER guess an attachment or cut body/legs.
cut_y,cut_z,cut_x=1.58,1.32,.30
cand=[f for f in faces if (ctr(f).y>cut_y and
                            ctr(f).z>cut_z and abs(ctr(f).x)<cut_x)]
comps=connected_groups(cand)
assert comps
removed=comps[0]
assert len(removed)==632,(len(removed),"unexpected donor geometry")
boundary=[]
for f in removed:
    vs=list(f.verts)
    for k in range(len(vs)):
        va,vb=vs[k],vs[(k+1)%len(vs)]
        ed=bm.edges.get((va,vb))
        assert ed
        if sum(x in removed for x in ed.link_faces)==1:
            boundary.append((va,vb))
assert len(boundary)==24,len(boundary)
successors={}
for v,w in boundary:
    assert v not in successors
    successors[v]=w
first=boundary[0][0]
ordered=[first]
seen={first}
cur=first
while True:
    cur=successors[cur]
    if cur==first:break
    assert cur not in seen
    seen.add(cur);ordered.append(cur)
assert len(ordered)==24 and len(successors)==24

pts=[mw@v.co for v in ordered]
cbase=sum(pts,Vector())/len(pts)
phi=[math.atan2(v.z-cbase.z,v.x-cbase.x) for v in pts]
# Exclude crossing/anomalous radial order before welding new tail.
phi_diffs=[(phi[(i+1)%24]-phi[i]+math.pi)%(2*math.pi)-math.pi
           for i in range(24)]
positive=sum(d>0 for d in phi_diffs);negative=sum(d<0 for d in phi_diffs)
assert min(positive,negative)<=2,("perimeter not polar ordered",phi_diffs)
# M: the actual original donor loop angles are uneven. Reuse its winding,
# but give every downstream ring an EXACT equally-spaced XZ angular mapping.
# This avoids angular strip fold-overs observed in L's BVH intersection QA.
source_phi=list(phi)
winding=1 if positive>negative else -1
phi=[source_phi[0]+winding*2*math.pi*i/24 for i in range(24)]
orig_old_faces=len(bm.faces)
selected_old_verts=set(v for f in removed for v in f.verts)
for f in list(removed):bm.faces.remove(f)

# Body root original 24 boundary verts retained; replace **all** remaining
# tail with a smoothly curving slender taper plus coherent dorsal feather ribs.
# Swept tube is a single-valued positive radial surface, so unlike G/H, no
# independent loft volumes are inserted through the original tail.
def smooth(t):
    q=max(0.,min(1.,float(t)))
    return q*q*(3-2*q)
def pulse(t,start,end):
    if t<=start or t>=end:return 0.
    u=(t-start)/(end-start)
    # Wider longitudinal overlap and a sustained trailing slope, rather than
    # L's sawtooth late cutoff. Still part of ONE continuous closed tail shell.
    return smooth(u/.48) * (1.-smooth((u-.66)/.34))
def angular_profile(phi,phi0,spread):
    diff=(phi-phi0+math.pi)%(2*math.pi)-math.pi
    return math.exp(-.5*(diff/spread)**2)
# 5 overlapping feather ridges molded into one surface, on posterior dorsal
# and lateral sectors, distributed by real angular shell vertices.
feathers=[
    {"name":"F1","start":.035,"end":.29,"amp":.21,"angle":1.28,"spread":.48},
    {"name":"F2","start":.15,"end":.43,"amp":.19,"angle":2.12,"spread":.42},
    {"name":"F3","start":.30,"end":.57,"amp":.20,"angle":1.16,"spread":.42},
    {"name":"F4","start":.45,"end":.73,"amp":.17,"angle":1.96,"spread":.43},
    {"name":"F5","start":.62,"end":.89,"amp":.13,"angle":1.29,"spread":.49}
]
# Existing root median at y≈1.58 and z≈1.60. New spine sweeps back and down
# as the S-type reference does, rather than branching over straight A stub.
START=max(v.y for v in pts)+.055
LENGTH=1.97
def position(t,angle,rootp):
    y=START+LENGTH*t
    cen_z=cbase.z+.065*math.sin(math.pi*t)-.33*t-.12*t*t
    cen_x=cbase.x+.032*math.sin(math.pi*t)
    base_rx=.084*(1.-t)**1.15+.006
    base_rz=.073*(1.-t)**1.35+.005
    raised=sum(f["amp"]*pulse(t,f["start"],f["end"])*
       angular_profile(angle,f["angle"],f["spread"]) for f in feathers)
    # Feather ribs increase dorsal positive-Z radius only. The angular
    # blend is positive: no self-intersecting radial shells across the spine.
    wx=base_rx*math.cos(angle)
    wz=(base_rz+raised)*math.sin(angle)
    regular=Vector((cen_x+wx,y,cen_z+wz))
    # Transition smoothly out of the true donor border, preventing abrupt
    # root position/proportions and preserving original head/limb vertices.
    blend=smooth(t/.13)
    root_target=Vector((rootp.x,START+LENGTH*t,rootp.z))
    return regular*blend+root_target*(1.-blend)

# A longitudinally constant vertex correspondence with real root topology
# avoids topology of extra branches. 96 support cross-sections.
previous=ordered
ring_ts=[.014,.030,.048,.066]+[i/100 for i in range(8,100)]
ring_ts=sorted(set(ring_ts))
for t in ring_ts:
    ring=[]
    for angle,root in zip(phi,pts):
        p=position(t,angle,root)
        ring.append(bm.verts.new(inv@p))
    for i in range(24):
        j=(i+1)%24
        bm.faces.new((previous[i],previous[j],ring[j],ring[i]))
    previous=ring
# Finish at a sharp but nondegenerate tip, single shared apex.
endroot=pts[0]
tip=bm.verts.new(inv@Vector((cbase.x,START+LENGTH,
          cbase.z-.33-.12)))
for i in range(24):
    bm.faces.new((previous[i],previous[(i+1)%24],tip))
# Remove orphaned original 632-face tail topology, retain original root.
for v in selected_old_verts:
    if v.is_valid and len(v.link_faces)==0:bm.verts.remove(v)
for e in list(bm.edges):
    if e.is_valid and len(e.link_faces)==0:bm.edges.remove(e)
bm.faces.ensure_lookup_table()
bmesh.ops.triangulate(bm,faces=list(bm.faces))
bm.normal_update()
bm.to_mesh(out.data)
bm.free()
out.data.update()
assert np.isfinite(evalxyz(out)).all()
assert hashlib.sha256(evalxyz(s).tobytes()).hexdigest()==source_sig
assert len(s.data.vertices)==29948 and len(s.data.polygons)==59932

# Precise face edge counts and physically evaluated mesh intersection BVH.
vworld=evalxyz(out)
tri=np.asarray([tuple(f.vertices) for f in out.data.polygons],dtype=np.int32)
N=len(vworld)
edgeuse={};adj=[[] for _ in range(N)]
polygons=vworld[tri]
areas=np.linalg.norm(np.cross(polygons[:,1]-polygons[:,0],
                               polygons[:,2]-polygons[:,0]),axis=1)
for x,y,z in tri:
    x,y,z=int(x),int(y),int(z)
    for i,j in ((x,y),(y,z),(z,x)):
        key=(min(i,j),max(i,j))
        edgeuse[key]=edgeuse.get(key,0)+1
        adj[i].append(j);adj[j].append(i)
seen=set();components=[]
for i in range(N):
    if i in seen:continue
    todo=[i];seen.add(i);count=0
    while todo:
        x=todo.pop();count+=1
        for y in adj[x]:
            if y not in seen:seen.add(y);todo.append(y)
    components.append(count)
components.sort(reverse=True)
stats={"vertices":N,"triangles":len(tri),
       "component_count":len(components),
       "largest_components":components[:8],
       "boundary_edges":sum(v==1 for v in edgeuse.values()),
       "nonmanifold_edges":sum(v!=2 for v in edgeuse.values()),
       "degenerate_triangles":int(np.count_nonzero(areas<1e-10)),
       "min_twice_face_area":float(areas.min()),
       "max_twice_face_area":float(areas.max())}
# Same ROI as G/H/I/J plus expanded beyond donor tip.
cent=polygons.mean(axis=1)
mask=(cent[:,1]>1.45)&(cent[:,2]>1.08)&(abs(cent[:,0])<.60)
ids=np.flatnonzero(mask)
face_ids=[tuple(map(int,tri[i])) for i in ids]
bvh=BVHTree.FromPolygons([Vector(v) for v in vworld],face_ids,
                          all_triangles=True,epsilon=1e-7)
collisions=[]
for i,j in bvh.overlap(bvh):
    if i>=j:continue
    if set(face_ids[i])&set(face_ids[j]):continue
    collisions.append((int(ids[i]),int(ids[j])))
collision={"tail_roi_faces":len(face_ids),
           "self_intersections_without_shared_vertices":len(collisions),
           "first_60_offending_polygon_pairs":collisions[:60]}
real_gate=(stats["component_count"]==1 and stats["nonmanifold_edges"]==0
           and stats["degenerate_triangles"]==0 and len(collisions)==0)
report={
 "authority_png_sha256":HREF,
 "donor_source_GLb_sha256":HDON,
 "source_untouched":True,
 "source_verts":29948,"source_triangles":59932,
 "old_tail_faces_replaced":len(removed),
 "single_seam_edge_count":len(ordered),
 "section_limit":{"y_cut":cut_y,"z_floor":cut_z,"x_abs_max":cut_x},
 "root_world_center":list(cbase),
 "new_tail_length_world":LENGTH,
 "feather_profile_design":feathers,
 "feather_ridge_count":len(feathers),
 "downstream_uniform_angular_winding":winding,
 "source_perimeter_angles_preserved_only_at_root":True,
 "longitudinal_support_rings":len(ring_ts),
 "watertight_one_component":stats,
 "full_real_tail_3d_self_collision":collision,
 "technical_geometry_gate":"PASS" if real_gate else "FAIL",
 "visual_authority_gate":"NOT_APPROVED_PENDING_REAL_FIVE_VIEW",
 "color_materials":"NOT_TESTED",
 "tail_bones_skinning":"NOT_IMPLEMENTED",
 "three_cycle_gait":"NOT_TESTED_ON_CHANGED_MODEL",
 "game_main_modified":False,
 "production_S_ready":False
}
(OUT/"REAL_QEM_TAIL_CORE_M_QA.json").write_text(json.dumps(report,indent=2)+"\n")
print("TAIL_CORE_M_ACTUAL_GEOMETRY",stats)
print("TAIL_CORE_M_INTERSECTIONS",collision)
# Render genuine source vs one-piece rebuild, same cameras.
scene=bpy.context.scene
cam=scene.camera
assert cam and cam.type=="CAMERA"
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.display.shading.light="STUDIO"
scene.render.resolution_x=1060
scene.render.resolution_y=795
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
cam.data.type="ORTHO"
views={
 "SIDE":Vector((1,0,0)),"FRONT":Vector((0,-1,0)),
 "FRONT34":Vector((1,-1,0)).normalized(),
 "REAR34":Vector((1,1,0)).normalized(),
 "BACK":Vector((0,1,0))}
for label,direction in views.items():
    target=Vector((0,.20,1.25))
    cam.data.ortho_scale=6.5
    cam.location=target+direction*9
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    for tag,obj in (("SOURCE",s),("CORE_M",out)):
        for item in (s,a,out):item.hide_render=item!=obj
        scene.render.filepath=str(REV/f"REAL_QEM_TAIL_{tag}_{label}.png")
        bpy.ops.render.render(write_still=True)
for label,direction in (("SIDE",Vector((1,0,0))),
                        ("REAR34",Vector((1,1,0)).normalized()),
                        ("BACK",Vector((0,1,0)))):
    target=Vector((0,2.35,1.37))
    cam.data.ortho_scale=2.75
    cam.location=target+direction*6
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    for tag,obj in (("SOURCE",s),("CORE_M",out)):
        for item in (s,a,out):item.hide_render=item!=obj
        scene.render.filepath=str(REV/f"REAL_QEM_TAIL_CLOSE_{tag}_{label}.png")
        bpy.ops.render.render(write_still=True)
for item in (s,a):item.hide_render=True
out.hide_render=False
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-true-one-piece-tail-core-M-TRIAL.blend"),compress=True)
print("TAIL_CORE_M_FINAL",report["technical_geometry_gate"],"new",N,len(tri),
      "single_seam",len(ordered),"collisions",len(collisions))
